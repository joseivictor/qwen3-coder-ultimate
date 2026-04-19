import * as vscode from 'vscode';
import * as WebSocket from 'ws';
import * as path from 'path';
import * as fs from 'fs';

// ── State ─────────────────────────────────────────────────────────────────────
let ws: WebSocket | null = null;
let statusBar: vscode.StatusBarItem;
let reconnectTimer: NodeJS.Timeout | null = null;
let pendingRequests = new Map<string, (payload: any) => void>();
let diagListener: vscode.Disposable | null = null;

// ── Activation ────────────────────────────────────────────────────────────────
export function activate(ctx: vscode.ExtensionContext) {
    statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBar.command = 'qwen.connect';
    statusBar.text = '$(plug) QWEN';
    statusBar.tooltip = 'QWEN3-CODER: Click to connect';
    statusBar.show();
    ctx.subscriptions.push(statusBar);

    ctx.subscriptions.push(
        vscode.commands.registerCommand('qwen.connect',       () => connect()),
        vscode.commands.registerCommand('qwen.disconnect',    () => disconnect()),
        vscode.commands.registerCommand('qwen.sendSelection', () => sendSelection()),
        vscode.commands.registerCommand('qwen.fixErrors',     () => fixErrors()),
        vscode.commands.registerCommand('qwen.explainFile',   () => explainFile()),
    );

    // File open events
    ctx.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument(doc => sendFileOpened(doc)),
        vscode.workspace.onDidSaveTextDocument(doc => sendFileSaved(doc)),
        vscode.window.onDidChangeTextEditorSelection(e => sendCursorMoved(e)),
        vscode.window.onDidChangeActiveTextEditor(ed => { if (ed) sendFileOpened(ed.document); }),
    );

    const cfg = vscode.workspace.getConfiguration('qwen');
    if (cfg.get<boolean>('autoConnect', true)) {
        connect();
    }
}

export function deactivate() {
    disconnect();
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        return;
    }
    const port = vscode.workspace.getConfiguration('qwen').get<number>('bridgePort', 3579);
    try {
        ws = new WebSocket(`ws://localhost:${port}`);
    } catch (e) {
        scheduleReconnect();
        return;
    }

    ws.on('open', () => {
        setStatus('connected');
        if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
        startDiagnosticsListener();
        // Send currently open file immediately
        const editor = vscode.window.activeTextEditor;
        if (editor) sendFileOpened(editor.document);
    });

    ws.on('message', raw => {
        try {
            const msg = JSON.parse(raw.toString());
            handleIncoming(msg);
        } catch (_) {}
    });

    ws.on('close', () => {
        setStatus('disconnected');
        ws = null;
        scheduleReconnect();
    });

    ws.on('error', () => {
        setStatus('disconnected');
    });
}

function disconnect() {
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    if (diagListener) { diagListener.dispose(); diagListener = null; }
    if (ws) { ws.close(); ws = null; }
    setStatus('disconnected');
}

function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(() => { reconnectTimer = null; connect(); }, 5000);
}

function send(msg: object) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(msg));
    }
}

function sendWithId(msg: any): Promise<any> {
    return new Promise((resolve, reject) => {
        const id = Math.random().toString(36).slice(2, 10);
        msg.id = id;
        pendingRequests.set(id, resolve);
        setTimeout(() => { pendingRequests.delete(id); reject(new Error('timeout')); }, 8000);
        send(msg);
    });
}

// ── Incoming message handler ──────────────────────────────────────────────────
async function handleIncoming(msg: any) {
    const { type, payload, id } = msg;

    const reply = (p: object) => { if (id) send({ type: 'response', id, payload: p }); };

    // Resolve pending request
    if (type === 'response' && id && pendingRequests.has(id)) {
        pendingRequests.get(id)!(payload);
        pendingRequests.delete(id);
        return;
    }

    switch (type) {
        case 'hello':
            vscode.window.setStatusBarMessage(`QWEN Bridge connected (client ${payload?.client_id})`, 3000);
            break;

        case 'apply_edit': {
            const { file, start_line, start_col, end_line, end_col, new_text } = payload;
            const uri  = vscode.Uri.file(file);
            const edit = new vscode.WorkspaceEdit();
            const range = new vscode.Range(start_line, start_col, end_line, end_col);
            edit.replace(uri, range, new_text);
            const ok = await vscode.workspace.applyEdit(edit);
            reply({ success: ok });
            break;
        }

        case 'show_diff': {
            const { file, original, modified, title } = payload;
            const accepted = await showDiff(file, original, modified, title);
            reply({ accepted });
            break;
        }

        case 'open_file': {
            const { path: filePath, line, col } = payload;
            try {
                const doc = await vscode.workspace.openTextDocument(filePath);
                const ed  = await vscode.window.showTextDocument(doc);
                if (line !== null && line !== undefined) {
                    const pos = new vscode.Position(line, col ?? 0);
                    ed.selection = new vscode.Selection(pos, pos);
                    ed.revealRange(new vscode.Range(pos, pos));
                }
                reply({ success: true });
            } catch (e) {
                reply({ success: false, error: String(e) });
            }
            break;
        }

        case 'read_file': {
            const { path: filePath } = payload;
            try {
                const content = fs.readFileSync(filePath, 'utf-8');
                reply({ content });
            } catch (e) {
                reply({ content: null, error: String(e) });
            }
            break;
        }

        case 'progress': {
            const { message } = payload;
            vscode.window.setStatusBarMessage(`⚡ QWEN: ${message}`, 4000);
            break;
        }

        case 'info':
            vscode.window.showInformationMessage(`QWEN: ${payload.message}`);
            break;

        case 'error':
            vscode.window.showErrorMessage(`QWEN: ${payload.message}`);
            break;

        case 'stream_response': {
            const { text, mode } = payload;
            if (mode === 'chat' || mode === 'inline') {
                vscode.window.setStatusBarMessage(`QWEN: ${text.slice(0, 80)}`, 5000);
            }
            break;
        }

        // ── LSP actions ──────────────────────────────────────────────────────
        case 'lsp_rename': {
            const { file, line, col, new_name } = payload;
            try {
                const uri = vscode.Uri.file(file);
                const pos = new vscode.Position(line, col);
                const edit = await vscode.commands.executeCommand<vscode.WorkspaceEdit>(
                    'vscode.executeDocumentRenameProvider', uri, pos, new_name
                );
                if (edit) {
                    await vscode.workspace.applyEdit(edit);
                    reply({ success: true });
                } else {
                    reply({ success: false, error: 'no rename edit returned' });
                }
            } catch (e) {
                reply({ success: false, error: String(e) });
            }
            break;
        }

        case 'lsp_format': {
            const { file } = payload;
            try {
                const uri  = vscode.Uri.file(file);
                const edits = await vscode.commands.executeCommand<vscode.TextEdit[]>(
                    'vscode.executeFormatDocumentProvider', uri, {}
                );
                if (edits && edits.length > 0) {
                    const we = new vscode.WorkspaceEdit();
                    we.set(uri, edits);
                    await vscode.workspace.applyEdit(we);
                }
                reply({ success: true });
            } catch (e) {
                reply({ success: false, error: String(e) });
            }
            break;
        }

        case 'lsp_go_to_definition': {
            const { file, line, col } = payload;
            try {
                const uri  = vscode.Uri.file(file);
                const pos  = new vscode.Position(line, col);
                const locs = await vscode.commands.executeCommand<vscode.Location[]>(
                    'vscode.executeDefinitionProvider', uri, pos
                );
                if (locs && locs.length > 0) {
                    const loc = locs[0];
                    reply({ file: loc.uri.fsPath, line: loc.range.start.line, col: loc.range.start.character });
                } else {
                    reply(null);
                }
            } catch (e) {
                reply(null);
            }
            break;
        }

        case 'lsp_find_references': {
            const { file, line, col } = payload;
            try {
                const uri  = vscode.Uri.file(file);
                const pos  = new vscode.Position(line, col);
                const locs = await vscode.commands.executeCommand<vscode.Location[]>(
                    'vscode.executeReferenceProvider', uri, pos
                );
                const refs = (locs || []).map(l => ({
                    file: l.uri.fsPath, line: l.range.start.line, col: l.range.start.character
                }));
                reply({ references: refs });
            } catch (e) {
                reply({ references: [] });
            }
            break;
        }

        case 'lsp_hover': {
            const { file, line, col } = payload;
            try {
                const uri    = vscode.Uri.file(file);
                const pos    = new vscode.Position(line, col);
                const hovers = await vscode.commands.executeCommand<vscode.Hover[]>(
                    'vscode.executeHoverProvider', uri, pos
                );
                const text = (hovers || [])
                    .flatMap(h => h.contents)
                    .map(c => typeof c === 'string' ? c : c.value)
                    .join('\n');
                reply({ text });
            } catch (e) {
                reply({ text: '' });
            }
            break;
        }

        case 'lsp_completions': {
            const { file, line, col } = payload;
            try {
                const uri   = vscode.Uri.file(file);
                const pos   = new vscode.Position(line, col);
                const list  = await vscode.commands.executeCommand<vscode.CompletionList>(
                    'vscode.executeCompletionItemProvider', uri, pos
                );
                const items = (list?.items || []).slice(0, 20).map(i => ({
                    label: typeof i.label === 'string' ? i.label : i.label.label,
                    kind:  i.kind,
                    detail: i.detail || ''
                }));
                reply({ items });
            } catch (e) {
                reply({ items: [] });
            }
            break;
        }
    }
}

// ── Outgoing events ───────────────────────────────────────────────────────────
function sendFileOpened(doc: vscode.TextDocument) {
    if (doc.uri.scheme !== 'file') return;
    const editor = vscode.window.visibleTextEditors.find(e => e.document === doc);
    send({
        type: 'file_opened',
        payload: {
            path:        doc.uri.fsPath,
            content:     doc.getText(),
            language:    doc.languageId,
            cursor_line: editor?.selection.active.line ?? 0,
            cursor_col:  editor?.selection.active.character ?? 0,
        }
    });
}

function sendFileSaved(doc: vscode.TextDocument) {
    if (doc.uri.scheme !== 'file') return;
    send({
        type: 'file_saved',
        payload: { path: doc.uri.fsPath, content: doc.getText() }
    });
}

function sendCursorMoved(e: vscode.TextEditorSelectionChangeEvent) {
    const doc = e.textEditor.document;
    if (doc.uri.scheme !== 'file') return;
    const sel     = e.textEditor.selection;
    const hasText = !sel.isEmpty;
    if (hasText) {
        send({
            type: 'selection',
            payload: {
                path: doc.uri.fsPath,
                text: doc.getText(sel),
                start_line: sel.start.line,
                end_line:   sel.end.line,
            }
        });
    } else {
        send({
            type: 'cursor_moved',
            payload: { path: doc.uri.fsPath, line: sel.active.line, col: sel.active.character }
        });
    }
}

function startDiagnosticsListener() {
    if (diagListener) return;
    const sendDiags = (uri: vscode.Uri) => {
        const cfg = vscode.workspace.getConfiguration('qwen');
        if (!cfg.get<boolean>('sendDiagnostics', true)) return;
        const diags = vscode.languages.getDiagnostics(uri);
        send({
            type: 'diagnostics',
            payload: {
                file: uri.fsPath,
                diagnostics: diags.map(d => ({
                    line:     d.range.start.line,
                    col:      d.range.start.character,
                    severity: severityName(d.severity),
                    message:  d.message,
                    source:   d.source || '',
                    code:     String(d.code || ''),
                }))
            }
        });
    };

    diagListener = vscode.languages.onDidChangeDiagnostics(e => {
        e.uris.forEach(sendDiags);
    });
}

// ── Commands ──────────────────────────────────────────────────────────────────
function sendSelection() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const sel  = editor.selection;
    const text = editor.document.getText(sel);
    if (!text.trim()) { vscode.window.showWarningMessage('QWEN: Select some code first.'); return; }
    send({
        type: 'command',
        payload: { command: 'ask_about_selection', text, file: editor.document.uri.fsPath }
    });
    vscode.window.showInformationMessage('QWEN: Selection sent to AI.');
}

function fixErrors() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const uri   = editor.document.uri;
    const diags = vscode.languages.getDiagnostics(uri).filter(d => d.severity === vscode.DiagnosticSeverity.Error);
    if (!diags.length) { vscode.window.showInformationMessage('QWEN: No errors found.'); return; }
    send({
        type: 'command',
        payload: {
            command: 'fix_errors',
            file:    uri.fsPath,
            errors:  diags.map(d => ({ line: d.range.start.line, message: d.message }))
        }
    });
    vscode.window.showInformationMessage(`QWEN: Sending ${diags.length} error(s) to AI...`);
}

function explainFile() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    send({
        type: 'command',
        payload: { command: 'explain_file', file: editor.document.uri.fsPath }
    });
}

// ── Diff helper ───────────────────────────────────────────────────────────────
async function showDiff(filePath: string, original: string, modified: string, title: string): Promise<boolean> {
    const origUri = vscode.Uri.parse(`qwen-diff:original/${path.basename(filePath)}`).with({ query: original });
    const modUri  = vscode.Uri.parse(`qwen-diff:modified/${path.basename(filePath)}`).with({ query: modified });

    // Register a simple content provider for the diff
    const provider = vscode.workspace.registerTextDocumentContentProvider('qwen-diff', {
        provideTextDocumentContent(uri: vscode.Uri) { return uri.query; }
    });

    await vscode.commands.executeCommand('vscode.diff', origUri, modUri, title || `QWEN: ${path.basename(filePath)}`);
    provider.dispose();

    const choice = await vscode.window.showInformationMessage(
        'Apply AI suggestion?', { modal: false }, 'Accept', 'Reject'
    );
    return choice === 'Accept';
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function setStatus(state: 'connected' | 'disconnected') {
    if (state === 'connected') {
        statusBar.text    = '$(check) QWEN';
        statusBar.tooltip = 'QWEN3-CODER: Connected — click to reconnect';
        statusBar.backgroundColor = undefined;
    } else {
        statusBar.text    = '$(plug) QWEN';
        statusBar.tooltip = 'QWEN3-CODER: Disconnected — click to connect';
    }
}

function severityName(s: vscode.DiagnosticSeverity): string {
    return ['error', 'warning', 'info', 'hint'][s] ?? 'info';
}
