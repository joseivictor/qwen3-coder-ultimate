"""
Imprime QR code ASCII no terminal pra escanear com o celular.
Uso:
    python show_qr.py http://192.168.0.15:8765/
    python show_qr.py                           # auto-detect IP local
"""
import sys, socket, subprocess

def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def ensure_qrcode():
    try:
        import qrcode  # noqa
        return True
    except ImportError:
        print("[show_qr] instalando qrcode (1x só)...", flush=True)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "qrcode"])
            return True
        except Exception as e:
            print(f"[show_qr] não consegui instalar qrcode: {e}")
            return False

def print_qr(url: str):
    if not ensure_qrcode():
        # fallback: link em api.qrserver.com pra abrir no navegador
        print(f"\n  Sem qrcode lib. Abra esta URL pra ver o QR:")
        print(f"  https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={url}\n")
        return
    import qrcode
    qr = qrcode.QRCode(border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        port = sys.argv[2] if len(sys.argv) > 2 else "8765"
        url = f"http://{lan_ip()}:{port}/"

    print()
    print("  ┌─────────────────────────────────────────────────")
    print(f"  │  📱  ABRA NO CELULAR:  {url}")
    print("  ├─────────────────────────────────────────────────")
    print("  │  Aponta a câmera do celular pro QR abaixo:")
    print("  └─────────────────────────────────────────────────")
    print()
    print_qr(url)
    print()
    print(f"  ↑↑↑  Escaneia ou digita: {url}")
    print()

if __name__ == "__main__":
    main()
