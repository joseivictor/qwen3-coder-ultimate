# Instalar a Extensão QWEN no VSCode

## Método 1 — Desenvolvimento (mais rápido)

```bash
cd ui/vscode_extension
npm install
npm run compile
```

No VSCode: **F5** → abre nova janela com a extensão ativa.

## Método 2 — Instalar permanentemente

```bash
cd ui/vscode_extension
npm install
npm run compile
npx vsce package   # gera qwen-ultimate-1.0.0.vsix
code --install-extension qwen-ultimate-1.0.0.vsix
```

## Como usar

1. Inicie o QWEN normalmente: `python qwen_ultimate.py`
2. O bridge WebSocket sobe automaticamente na porta **3579**
3. A extensão conecta automática — veja `$(check) QWEN` na barra de status

## Comandos disponíveis

| Comando | Atalho | O que faz |
|---|---|---|
| QWEN: Connect | — | Conecta ao bridge |
| QWEN: Send Selection | `Ctrl+Shift+Q` | Envia seleção para o AI |
| QWEN: Fix All Errors | `Ctrl+Shift+E` | Manda todos os erros para o AI corrigir |
| QWEN: Explain Current File | — | Explica o arquivo aberto |

## O que acontece automaticamente

- Arquivo aberto → AI recebe conteúdo + linguagem
- Arquivo salvo → AI vê a versão mais nova
- Cursor movido → AI sabe onde você está
- Texto selecionado → AI sabe o que você quer
- Erros/warnings → AI recebe diagnósticos em tempo real
