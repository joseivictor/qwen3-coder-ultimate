# qwen_api.py — Qwen3-Coder-480B via API  (script de teste/demonstração)
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN", "")
if not HF_TOKEN:
    print("⚠  HF_TOKEN não encontrado. Configure o arquivo .env (veja .env.example).")
    exit(1)

client = InferenceClient(token=HF_TOKEN)

print("🚀 Qwen3-480B online! Digite 'sair' para encerrar.\n")

while True:
    try:
        msg = input("Você: ").strip()
        if msg.lower() in ['sair', 'exit', 'quit', 'q']:
            print("👋 Até mais!")
            break
        if not msg:
            continue

        print("🤖 Pensando...", end="", flush=True)

        resp = client.chat.completions.create(
            model="Qwen/Qwen3-Coder-480B-A35B-Instruct",
            messages=[{"role": "user", "content": msg}],
            max_tokens=2048,
            temperature=0.7
        )

        resposta = resp.choices[0].message.content
        print(f"\r🤖 {resposta}\n")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        break
