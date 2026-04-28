# Arquitetura

## Decisão técnica

Foi usado CEP por compatibilidade com Premiere Pro e After Effects em versões mais amplas. A interface é HTML/CSS/JS modular, sem dependência obrigatória de build, para facilitar instalação direta em `CEP/extensions`.

## Fluxo

1. UI importa SRT/TXT.
2. `srt.js` transforma em captions normalizadas.
3. `cache.js` salva por projeto/sequência.
4. `viralAnalyzer.js` pontua e escolhe destaques.
5. `lineBreaker.js` define linhas legíveis.
6. `templates.js` lista modelos locais.
7. `app.js` monta payload.
8. `hostscript.jsx` aplica no Premiere/After.

## Premiere Pro

Quando há `.mogrt`, o hostscript tenta aplicar com `importMGT`.

Quando há `.cgt` ou `.cga`, como na biblioteca do `Legendas Master 3.7`, o hostscript importa o item para o projeto e tenta inserir na sequência ativa pelo track de vídeo. Se houver SFX na pasta do modelo, ele tenta importar e aplicar no track de áudio.

Quando não há modelo válido, cria marcadores com o texto processado. Esse fallback evita perda de timing e permite validar a análise antes de finalizar os modelos.

## After Effects

Cria camadas de texto no comp ativo com o timing original.

## Segurança do plugin antigo

O plugin antigo é somente referência. Nada é editado dentro de:

```text
C:\Program Files (x86)\Common Files\Adobe\CEP\extensions\Legendas Master 3.7
```

O plugin novo pode ler a biblioteca de templates dessa pasta para usar as mesmas animações/SFX, mas não altera os arquivos originais.
