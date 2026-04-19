"""
QWEN3-CODER ULTIMATE — VSCode Bridge v1.0
Real IDE integration via WebSocket + Language Server Protocol.
Connects to VSCode extension, streams responses, handles diagnostics.
"""

import asyncio
import json
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class Diagnostic:
    file:     str
    line:     int
    col:      int
    severity: str   # error | warning | info | hint
    message:  str
    source:   str = ""
    code:     str = ""


@dataclass
class TextEdit:
    file:      str
    start_line: int
    start_col:  int
    end_line:   int
    end_col:    int
    new_text:   str


@dataclass
class FileContext:
    path:       str
    content:    str
    language:   str
    cursor_line: int = 0
    cursor_col:  int = 0
    selection:  Optional[str] = None


@dataclass
class BridgeEvent:
    type:    str   # diagnostics | file_opened | file_saved | cursor_moved | selection | command
    payload: dict
    ts:      float = field(default_factory=time.time)


# ── VSCODE BRIDGE ─────────────────────────────────────────────────────────────

class VSCodeBridge:
    """
    Real VSCode integration. Two transport modes:
    1. WebSocket server — extension connects to us (default, port 3579)
    2. stdio pipe — for direct subprocess launch

    Capabilities:
    - Stream AI responses as inline diffs (accept/reject)
    - Read active file + cursor position + selection
    - Apply edits atomically
    - Subscribe to real-time diagnostics
    - Trigger LSP actions (rename, format, go-to-def)
    - Show progress notifications in VSCode UI
    """

    DEFAULT_PORT = 3579
    PROTOCOL_VERSION = "1.0"

    def __init__(self, port: int = DEFAULT_PORT, on_event: Callable = None):
        self.port      = port
        self.on_event  = on_event or (lambda e: None)
        self._clients: dict[str, object] = {}   # client_id → websocket
        self._pending:  dict[str, asyncio.Future] = {}
        self._server   = None
        self._loop:    Optional[asyncio.AbstractEventLoop] = None
        self._thread:  Optional[threading.Thread] = None
        self._running  = False
        self._diagnostics: dict[str, list[Diagnostic]] = {}
        self._open_files:  dict[str, FileContext] = {}
        self._stats = {"msgs_in": 0, "msgs_out": 0, "edits_applied": 0}

    # ── SERVER LIFECYCLE ──────────────────────────────────────────────────────

    def start(self) -> bool:
        """Start WebSocket server in background thread. Returns True if started."""
        try:
            import websockets
        except ImportError:
            print("[VSCodeBridge] websockets not installed — pip install websockets")
            return False

        self._loop = asyncio.new_event_loop()
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        time.sleep(0.3)  # let server bind
        return True

    def stop(self):
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self):
        try:
            import websockets
            async with websockets.serve(self._handle_client, "localhost", self.port):
                print(f"[VSCodeBridge] Listening on ws://localhost:{self.port}")
                while self._running:
                    await asyncio.sleep(0.5)
        except Exception as e:
            print(f"[VSCodeBridge] Server error: {e}")

    async def _handle_client(self, ws, path="/"):
        client_id = str(uuid.uuid4())[:8]
        self._clients[client_id] = ws
        try:
            await self._send(ws, {"type": "hello", "version": self.PROTOCOL_VERSION, "client_id": client_id})
            async for raw in ws:
                self._stats["msgs_in"] += 1
                try:
                    msg = json.loads(raw)
                    await self._dispatch(client_id, ws, msg)
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        finally:
            del self._clients[client_id]

    async def _dispatch(self, client_id: str, ws, msg: dict):
        msg_type = msg.get("type", "")
        payload  = msg.get("payload", {})
        req_id   = msg.get("id")

        if msg_type == "diagnostics":
            file = payload.get("file", "")
            diags = [
                Diagnostic(
                    file=file,
                    line=d.get("line", 0),
                    col=d.get("col", 0),
                    severity=d.get("severity", "error"),
                    message=d.get("message", ""),
                    source=d.get("source", ""),
                    code=str(d.get("code", "")),
                )
                for d in payload.get("diagnostics", [])
            ]
            self._diagnostics[file] = diags
            self.on_event(BridgeEvent("diagnostics", {"file": file, "items": diags}))

        elif msg_type == "file_opened":
            ctx = FileContext(
                path=payload.get("path", ""),
                content=payload.get("content", ""),
                language=payload.get("language", ""),
                cursor_line=payload.get("cursor_line", 0),
                cursor_col=payload.get("cursor_col", 0),
            )
            self._open_files[ctx.path] = ctx
            self.on_event(BridgeEvent("file_opened", {"context": ctx}))

        elif msg_type == "file_saved":
            path = payload.get("path", "")
            if path in self._open_files:
                self._open_files[path].content = payload.get("content", self._open_files[path].content)
            self.on_event(BridgeEvent("file_saved", payload))

        elif msg_type == "cursor_moved":
            path = payload.get("path", "")
            if path in self._open_files:
                self._open_files[path].cursor_line = payload.get("line", 0)
                self._open_files[path].cursor_col  = payload.get("col", 0)

        elif msg_type == "selection":
            path = payload.get("path", "")
            if path in self._open_files:
                self._open_files[path].selection = payload.get("text", "")
            self.on_event(BridgeEvent("selection", payload))

        elif msg_type == "response":
            # Reply to a request we sent
            if req_id and req_id in self._pending:
                fut = self._pending.pop(req_id)
                if not fut.done():
                    fut.set_result(payload)

        elif msg_type == "command":
            self.on_event(BridgeEvent("command", payload))

    async def _send(self, ws, msg: dict):
        try:
            await ws.send(json.dumps(msg))
            self._stats["msgs_out"] += 1
        except Exception:
            pass

    def _send_sync(self, msg: dict, client_id: str = None):
        """Fire-and-forget send from sync context."""
        if not self._loop or not self._clients:
            return
        targets = [self._clients[client_id]] if client_id and client_id in self._clients else list(self._clients.values())
        for ws in targets:
            asyncio.run_coroutine_threadsafe(self._send(ws, msg), self._loop)

    def _request_sync(self, msg: dict, timeout: float = 5.0) -> Optional[dict]:
        """Send request and wait for response."""
        if not self._loop or not self._clients:
            return None
        req_id = str(uuid.uuid4())[:8]
        msg["id"] = req_id
        fut = self._loop.create_future()
        self._pending[req_id] = fut
        ws = next(iter(self._clients.values()))
        asyncio.run_coroutine_threadsafe(self._send(ws, msg), self._loop)
        try:
            result = asyncio.run_coroutine_threadsafe(
                asyncio.wait_for(asyncio.shield(fut), timeout=timeout), self._loop
            ).result(timeout=timeout + 1)
            return result
        except Exception:
            self._pending.pop(req_id, None)
            return None

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    @property
    def connected(self) -> bool:
        return len(self._clients) > 0

    def get_active_file(self) -> Optional[FileContext]:
        """Return the most recently active file context."""
        if not self._open_files:
            return None
        return next(reversed(self._open_files.values()))

    def get_diagnostics(self, file: str = None) -> list[Diagnostic]:
        if file:
            return self._diagnostics.get(file, [])
        return [d for diags in self._diagnostics.values() for d in diags]

    def get_errors(self, file: str = None) -> list[Diagnostic]:
        return [d for d in self.get_diagnostics(file) if d.severity == "error"]

    def apply_edit(self, edit: TextEdit) -> bool:
        """Apply a text edit to a file in VSCode."""
        msg = {
            "type": "apply_edit",
            "payload": {
                "file":       edit.file,
                "start_line": edit.start_line,
                "start_col":  edit.start_col,
                "end_line":   edit.end_line,
                "end_col":    edit.end_col,
                "new_text":   edit.new_text,
            }
        }
        resp = self._request_sync(msg)
        if resp and resp.get("success"):
            self._stats["edits_applied"] += 1
            if edit.file in self._open_files:
                self._open_files[edit.file].content = self._apply_edit_to_content(
                    self._open_files[edit.file].content, edit
                )
            return True
        return False

    def apply_edits(self, edits: list[TextEdit]) -> bool:
        """Apply multiple edits atomically (sorted reverse order to preserve offsets)."""
        edits_sorted = sorted(edits, key=lambda e: (e.start_line, e.start_col), reverse=True)
        return all(self.apply_edit(e) for e in edits_sorted)

    def stream_response(self, text: str, mode: str = "inline") -> bool:
        """
        Stream AI response to VSCode.
        mode: 'inline' (show as ghost text), 'diff' (show diff panel), 'chat' (sidebar)
        """
        self._send_sync({
            "type": "stream_response",
            "payload": {"text": text, "mode": mode}
        })
        return self.connected

    def show_diff(self, file: str, original: str, modified: str, title: str = "AI Suggestion") -> bool:
        """Open diff panel in VSCode for user to accept/reject."""
        resp = self._request_sync({
            "type": "show_diff",
            "payload": {
                "file":     file,
                "original": original,
                "modified": modified,
                "title":    title,
            }
        })
        if resp:
            return resp.get("accepted", False)
        return False

    def show_progress(self, message: str, increment: int = None):
        """Show progress notification in VSCode status bar."""
        self._send_sync({
            "type": "progress",
            "payload": {"message": message, "increment": increment}
        })

    def show_info(self, message: str):
        self._send_sync({"type": "info", "payload": {"message": message}})

    def show_error(self, message: str):
        self._send_sync({"type": "error", "payload": {"message": message}})

    def open_file(self, path: str, line: int = None, col: int = None) -> bool:
        resp = self._request_sync({
            "type": "open_file",
            "payload": {"path": path, "line": line, "col": col}
        })
        return bool(resp and resp.get("success"))

    def get_file_content(self, path: str) -> Optional[str]:
        if path in self._open_files:
            return self._open_files[path].content
        resp = self._request_sync({
            "type": "read_file",
            "payload": {"path": path}
        })
        if resp and "content" in resp:
            return resp["content"]
        # Fallback: read from disk
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    # ── LSP ACTIONS ───────────────────────────────────────────────────────────

    def lsp_rename(self, file: str, line: int, col: int, new_name: str) -> dict:
        """Trigger LSP rename refactoring at position."""
        resp = self._request_sync({
            "type": "lsp_rename",
            "payload": {"file": file, "line": line, "col": col, "new_name": new_name}
        }, timeout=10.0)
        return resp or {"success": False, "error": "no response"}

    def lsp_format(self, file: str) -> bool:
        resp = self._request_sync({"type": "lsp_format", "payload": {"file": file}})
        return bool(resp and resp.get("success"))

    def lsp_go_to_definition(self, file: str, line: int, col: int) -> Optional[dict]:
        resp = self._request_sync({
            "type": "lsp_go_to_definition",
            "payload": {"file": file, "line": line, "col": col}
        })
        return resp

    def lsp_find_references(self, file: str, line: int, col: int) -> list[dict]:
        resp = self._request_sync({
            "type": "lsp_find_references",
            "payload": {"file": file, "line": line, "col": col}
        })
        return resp.get("references", []) if resp else []

    def lsp_hover(self, file: str, line: int, col: int) -> str:
        resp = self._request_sync({
            "type": "lsp_hover",
            "payload": {"file": file, "line": line, "col": col}
        })
        return resp.get("text", "") if resp else ""

    def lsp_completions(self, file: str, line: int, col: int) -> list[dict]:
        resp = self._request_sync({
            "type": "lsp_completions",
            "payload": {"file": file, "line": line, "col": col}
        }, timeout=3.0)
        return resp.get("items", []) if resp else []

    # ── CONTEXT HELPERS ───────────────────────────────────────────────────────

    def build_context_message(self) -> str:
        """Build a context string from active file + diagnostics for AI."""
        parts = []
        ctx = self.get_active_file()
        if ctx:
            lang = ctx.language or _detect_language(ctx.path)
            parts.append(f"**Active file:** `{ctx.path}` ({lang})")
            parts.append(f"**Cursor:** line {ctx.cursor_line + 1}, col {ctx.cursor_col + 1}")
            if ctx.selection:
                parts.append(f"**Selected text:**\n```{lang}\n{ctx.selection}\n```")
            else:
                # Show ±20 lines around cursor
                lines = ctx.content.splitlines()
                start = max(0, ctx.cursor_line - 20)
                end   = min(len(lines), ctx.cursor_line + 20)
                snippet = "\n".join(lines[start:end])
                parts.append(f"**Code context (lines {start+1}-{end}):**\n```{lang}\n{snippet}\n```")

        errors = self.get_errors()
        if errors:
            err_lines = [f"  {e.file}:{e.line}: {e.message}" for e in errors[:10]]
            parts.append("**Active errors:**\n" + "\n".join(err_lines))

        return "\n\n".join(parts) if parts else ""

    def _apply_edit_to_content(self, content: str, edit: TextEdit) -> str:
        lines = content.splitlines(keepends=True)
        if edit.start_line >= len(lines):
            return content
        start_pos = sum(len(lines[i]) for i in range(edit.start_line)) + edit.start_col
        end_pos   = sum(len(lines[i]) for i in range(edit.end_line)) + edit.end_col
        flat = content
        return flat[:start_pos] + edit.new_text + flat[end_pos:]

    # ── INLINE DIFF APPLY ─────────────────────────────────────────────────────

    def apply_code_block(self, file: str, code: str, show_diff_first: bool = True) -> bool:
        """
        Replace file content with AI-generated code.
        If show_diff_first=True, opens diff panel for user to accept/reject.
        """
        original = self.get_file_content(file) or ""
        if show_diff_first:
            accepted = self.show_diff(file, original, code)
            if not accepted:
                return False
        lines_orig = len(original.splitlines())
        edit = TextEdit(
            file=file,
            start_line=0, start_col=0,
            end_line=lines_orig, end_col=0,
            new_text=code,
        )
        return self.apply_edit(edit)

    # ── STATS ─────────────────────────────────────────────────────────────────

    def stats(self) -> str:
        return (
            f"VSCodeBridge: {'connected' if self.connected else 'no clients'} | "
            f"{self._stats['msgs_in']} in / {self._stats['msgs_out']} out | "
            f"{self._stats['edits_applied']} edits applied | "
            f"{len(self._open_files)} open files | "
            f"{sum(len(v) for v in self._diagnostics.values())} diagnostics"
        )


# ── STUB MODE (no extension connected) ───────────────────────────────────────

class VSCodeBridgeStub:
    """
    Drop-in replacement when VSCode extension is not available.
    Reads files from disk, applies edits directly, prints diffs to terminal.
    """

    def __init__(self):
        self._open_files: dict[str, FileContext] = {}
        self.connected = False

    def start(self) -> bool:
        return True

    def stop(self): pass

    def get_active_file(self) -> Optional[FileContext]:
        return next(reversed(self._open_files.values())) if self._open_files else None

    def get_diagnostics(self, file: str = None) -> list:
        return []

    def get_errors(self, file: str = None) -> list:
        return []

    def get_file_content(self, path: str) -> Optional[str]:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            lang = _detect_language(path)
            self._open_files[path] = FileContext(path=path, content=content, language=lang)
            return content
        except Exception:
            return None

    def apply_edit(self, edit: TextEdit) -> bool:
        try:
            with open(edit.file, encoding="utf-8") as f:
                content = f.read()
            lines = content.splitlines(keepends=True)
            start = sum(len(lines[i]) for i in range(min(edit.start_line, len(lines))))
            end   = sum(len(lines[i]) for i in range(min(edit.end_line, len(lines)))) + edit.end_col
            new_content = content[:start] + edit.new_text + content[end:]
            with open(edit.file, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
        except Exception as e:
            print(f"[VSCodeBridgeStub] Edit failed: {e}")
            return False

    def apply_edits(self, edits: list[TextEdit]) -> bool:
        edits_sorted = sorted(edits, key=lambda e: (e.start_line, e.start_col), reverse=True)
        return all(self.apply_edit(e) for e in edits_sorted)

    def stream_response(self, text: str, mode: str = "inline") -> bool:
        return True

    def show_diff(self, file: str, original: str, modified: str, title: str = "") -> bool:
        print(f"\n[VSCodeBridgeStub] Diff for {file} — auto-accepted")
        return True

    def show_progress(self, message: str, increment: int = None):
        pass

    def show_info(self, message: str):
        print(f"[INFO] {message}")

    def show_error(self, message: str):
        print(f"[ERROR] {message}")

    def open_file(self, path: str, line: int = None, col: int = None) -> bool:
        return True

    def lsp_rename(self, *a, **kw) -> dict:
        return {"success": False, "error": "stub mode"}

    def lsp_format(self, file: str) -> bool:
        return False

    def lsp_go_to_definition(self, *a, **kw):
        return None

    def lsp_find_references(self, *a, **kw):
        return []

    def lsp_hover(self, *a, **kw):
        return ""

    def lsp_completions(self, *a, **kw):
        return []

    def build_context_message(self) -> str:
        ctx = self.get_active_file()
        if not ctx:
            return ""
        lang = ctx.language or _detect_language(ctx.path)
        lines = ctx.content.splitlines()
        snippet = "\n".join(lines[:50])
        return f"**Active file:** `{ctx.path}`\n```{lang}\n{snippet}\n```"

    def apply_code_block(self, file: str, code: str, show_diff_first: bool = True) -> bool:
        try:
            with open(file, "w", encoding="utf-8") as f:
                f.write(code)
            return True
        except Exception:
            return False

    def stats(self) -> str:
        return "VSCodeBridgeStub: running in fallback mode (no extension)"


# ── FACTORY ───────────────────────────────────────────────────────────────────

def create_vscode_bridge(port: int = VSCodeBridge.DEFAULT_PORT,
                         on_event: Callable = None,
                         auto_start: bool = True):
    """Create and start a VSCodeBridge, falling back to stub if websockets missing."""
    try:
        import websockets  # noqa
        bridge = VSCodeBridge(port=port, on_event=on_event)
        if auto_start:
            bridge.start()
        return bridge
    except ImportError:
        return VSCodeBridgeStub()


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _detect_language(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {
        ".py":   "python",
        ".js":   "javascript",
        ".ts":   "typescript",
        ".tsx":  "typescriptreact",
        ".jsx":  "javascriptreact",
        ".go":   "go",
        ".rs":   "rust",
        ".java": "java",
        ".cpp":  "cpp",
        ".c":    "c",
        ".cs":   "csharp",
        ".rb":   "ruby",
        ".php":  "php",
        ".sh":   "shellscript",
        ".md":   "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml":  "yaml",
        ".toml": "toml",
        ".html": "html",
        ".css":  "css",
    }.get(ext, "plaintext")
