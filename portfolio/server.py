"""
JOSÉ VICTOR — Portfolio server
Stdlib only. Serves static files + admin API protected by session token.

Run:
    python server.py                            # localhost só
    python server.py 8765                       # porta custom, localhost só
    python server.py 8765 --lan                 # escuta na rede (celular/LAN)
    python server.py 8765 --lan --public        # OK pra Cloudflare Tunnel etc

Admin panel: http://localhost:8765/admin.html
Default password: joseivictor2026  (change in data/admin.json)

Modos de bind:
  default    127.0.0.1   só este PC
  --lan      0.0.0.0     aceita LAN (mesma WiFi)
  --public   ainda 0.0.0.0 mas marca header — admin bloqueia acesso de IP externo
             (use junto com --lan quando estiver compartilhando publicamente)
"""

from __future__ import annotations
import json, os, sys, hashlib, secrets, time, mimetypes, shutil, urllib.parse, ipaddress
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT  = Path(__file__).resolve().parent
DATA  = ROOT / "data"
ADMIN = DATA / "admin.json"
SESSIONS: dict[str, float] = {}
SESSION_TTL = 8 * 3600  # 8 horas

# Set por main() conforme flags de CLI:
PUBLIC_MODE = False   # True = está sendo servido publicamente (Cloudflare/LAN aberto)
                      # → admin é bloqueado pra IPs não-locais

DEFAULT_ADMIN = {
    "password_hash": hashlib.sha256(b"joseivictor2026").hexdigest(),
    "site_status":   "active",   # ou "frozen" pra colocar o site offline
    "owner_email":   "joseivictorvieiraandrade82@gmail.com"
}

# Endpoints permitidos pra escrita (data files)
WRITE_TARGETS = {
    "videos":  DATA / "videos.json",
    "experts": DATA / "experts.json",
    "courses": DATA / "courses.json",
    "motion":  DATA / "motion.json",
    "flyers":  DATA / "flyers.json",
    "config":  DATA / "config.json",
}

# ---------- helpers ----------
def ensure_admin():
    if not ADMIN.exists():
        ADMIN.write_text(json.dumps(DEFAULT_ADMIN, indent=2, ensure_ascii=False), encoding="utf-8")

def load_admin() -> dict:
    ensure_admin()
    return json.loads(ADMIN.read_text(encoding="utf-8"))

def save_admin(data: dict) -> None:
    ADMIN.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def issue_token() -> str:
    tok = secrets.token_urlsafe(32)
    SESSIONS[tok] = time.time() + SESSION_TTL
    cleanup_sessions()
    return tok

def cleanup_sessions():
    now = time.time()
    for k in list(SESSIONS.keys()):
        if SESSIONS[k] < now: del SESSIONS[k]

def is_authed(token: str | None) -> bool:
    if not token: return False
    cleanup_sessions()
    return token in SESSIONS and SESSIONS[token] > time.time()


# ---------- HTTP handler ----------
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def log_message(self, fmt, *args):
        # Compact log
        sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] {fmt%args}\n")

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, status: int, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n: return {}
        raw = self.rfile.read(n)
        try: return json.loads(raw.decode("utf-8"))
        except Exception: return {}

    def _token_from_headers(self) -> str | None:
        cookie = self.headers.get("Cookie", "")
        for kv in cookie.split(";"):
            kv = kv.strip()
            if kv.startswith("admtok="):
                return kv[7:]
        return self.headers.get("X-Admin-Token")

    def _client_ip(self) -> str:
        # Cloudflare Tunnel passa CF-Connecting-IP, ngrok passa X-Forwarded-For
        for h in ("CF-Connecting-IP", "X-Forwarded-For", "X-Real-IP"):
            v = self.headers.get(h)
            if v: return v.split(",")[0].strip()
        return self.client_address[0]

    def _is_local_client(self) -> bool:
        ip = self._client_ip()
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return False
        # localhost ou rede privada (LAN OK; público não)
        if addr.is_loopback: return True
        if PUBLIC_MODE:
            # quando estamos em modo público (Cloudflare etc), admin só por localhost
            return False
        return addr.is_private  # 192.168.*, 10.*, 172.16-31.* — LAN

    def _block_admin_if_public(self, path: str) -> bool:
        """Retorna True se a rota foi bloqueada (já enviou resposta)."""
        # Bloqueia admin.html e /api/* quando vindo de IP externo em modo público
        is_admin_route = (path == "/admin.html") or path.startswith("/api/")
        if is_admin_route and not self._is_local_client():
            self.send_response(403)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>403 Forbidden</h1><p>Admin only available locally.</p>")
            return True
        return False

    # --- POST router ---
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if self._block_admin_if_public(path): return

        # /api/login
        if path == "/api/login":
            data = self._read_json()
            pw   = (data.get("password") or "").encode("utf-8")
            adm  = load_admin()
            if hashlib.sha256(pw).hexdigest() == adm.get("password_hash"):
                tok = issue_token()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Set-Cookie", f"admtok={tok}; HttpOnly; Path=/; Max-Age={SESSION_TTL}")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "token": tok}).encode("utf-8"))
                return
            return self._json(401, {"ok": False, "error": "Senha incorreta"})

        # /api/logout
        if path == "/api/logout":
            tok = self._token_from_headers()
            if tok and tok in SESSIONS: del SESSIONS[tok]
            return self._json(200, {"ok": True})

        # All routes below require auth
        if not is_authed(self._token_from_headers()):
            return self._json(401, {"ok": False, "error": "Não autenticado"})

        # /api/save/<key>
        if path.startswith("/api/save/"):
            key = path.split("/")[-1]
            target = WRITE_TARGETS.get(key)
            if not target:
                return self._json(400, {"ok": False, "error": f"Alvo inválido: {key}"})
            payload = self._read_json()
            try:
                # backup before write
                if target.exists():
                    bak = target.with_suffix(target.suffix + f".bak.{int(time.time())}")
                    shutil.copy2(target, bak)
                target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
                return self._json(200, {"ok": True, "saved": str(target.name)})
            except Exception as e:
                return self._json(500, {"ok": False, "error": str(e)})

        # /api/upload — mp4, jpg, png, webp
        if path == "/api/upload":
            ctype = self.headers.get("Content-Type", "")
            if not ctype.startswith("multipart/form-data"):
                return self._json(400, {"ok": False, "error": "multipart obrigatório"})
            try:
                kind, fname, data = self._parse_multipart()
                if not data:
                    return self._json(400, {"ok": False, "error": "arquivo vazio"})
                # determine subdir
                ext = Path(fname).suffix.lower()
                if   ext in (".mp4",".mov",".webm"): subdir = ROOT/"assets"/"videos"
                elif ext in (".jpg",".jpeg",".png",".webp",".gif"):
                    subdir = ROOT/"assets"/"thumbs" if kind=="thumb" else ROOT/"assets"/"experts"
                else:
                    return self._json(400, {"ok": False, "error": f"extensão não suportada: {ext}"})
                subdir.mkdir(parents=True, exist_ok=True)
                # safe filename
                safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in fname)[-80:]
                dst = subdir / safe
                # avoid overwrite — append timestamp if existing
                if dst.exists():
                    dst = subdir / f"{int(time.time())}_{safe}"
                dst.write_bytes(data)
                rel = dst.relative_to(ROOT).as_posix()
                return self._json(200, {"ok": True, "path": rel, "size": len(data)})
            except Exception as e:
                return self._json(500, {"ok": False, "error": str(e)})

        # /api/admin-config — change password / site status
        if path == "/api/admin-config":
            payload = self._read_json()
            adm = load_admin()
            if "new_password" in payload and payload["new_password"]:
                adm["password_hash"] = hashlib.sha256(payload["new_password"].encode("utf-8")).hexdigest()
            if "site_status" in payload:
                adm["site_status"] = payload["site_status"]
            save_admin(adm)
            return self._json(200, {"ok": True})

        return self._json(404, {"ok": False, "error": "rota não encontrada"})

    def _parse_multipart(self):
        """Minimal multipart parser. Returns (kind, filename, bytes)."""
        ctype = self.headers.get("Content-Type", "")
        bound_marker = "boundary="
        if bound_marker not in ctype:
            raise ValueError("sem boundary")
        boundary = ("--" + ctype.split(bound_marker, 1)[1].strip()).encode("utf-8")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        parts = body.split(boundary)
        kind = "video"
        fname = ""
        data = b""
        for part in parts:
            if not part or part in (b"--\r\n", b"--"): continue
            if b"\r\n\r\n" not in part: continue
            head, val = part.split(b"\r\n\r\n", 1)
            head_text = head.decode("utf-8", errors="ignore")
            val = val.rsplit(b"\r\n", 1)[0]
            if 'name="kind"' in head_text:
                kind = val.decode("utf-8", errors="ignore").strip()
            elif 'name="file"' in head_text and "filename=" in head_text:
                # extract filename
                fn = head_text.split('filename="', 1)[1].split('"', 1)[0]
                fname = fn
                data = val
        return kind, fname, data

    # --- GET: also expose admin status ---
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if self._block_admin_if_public(path): return
        if path == "/api/whoami":
            return self._json(200, {"authed": is_authed(self._token_from_headers())})
        if path == "/api/admin-config":
            if not is_authed(self._token_from_headers()):
                return self._json(401, {"ok": False, "error": "auth"})
            adm = load_admin()
            adm.pop("password_hash", None)
            return self._json(200, adm)
        # site_status check — block app if frozen?
        # (não bloqueia, só informa pelo /api/whoami se quiser)
        return super().do_GET()


def get_lan_ip() -> str:
    """Best-effort detect IP da LAN (192.168.x.x ou 10.x.x.x)."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    global PUBLIC_MODE
    ensure_admin()

    args = sys.argv[1:]
    port = 8765
    bind = "127.0.0.1"
    for a in args:
        if a.isdigit(): port = int(a)
        elif a == "--lan":     bind = "0.0.0.0"
        elif a == "--public":  PUBLIC_MODE = True
        elif a in ("-h","--help"):
            print(__doc__); return

    httpd = ThreadingHTTPServer((bind, port), Handler)
    lan = get_lan_ip()
    print("=" * 64)
    print(f"  JOSÉ VICTOR — Portfolio")
    print(f"  → Local:  http://localhost:{port}/")
    if bind == "0.0.0.0":
        print(f"  → Rede:   http://{lan}:{port}/         (celular mesma WiFi)")
    print(f"  → Admin:  http://localhost:{port}/admin.html  (senha: joseivictor2026)")
    if PUBLIC_MODE:
        print(f"  ⚠️  Modo PUBLIC: admin bloqueado pra IPs externos")
    print("=" * 64)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[bye]")


if __name__ == "__main__":
    main()
