# Legendas Viral Pro

Novo plugin CEP para Adobe Premiere Pro e After Effects, criado do zero para o fluxo de legendas com destaque automático.

## Função principal

**Destaque Automático Viral** analisa o SRT ou transcrição importada, pontua trechos com maior potencial de retenção e separa cada legenda em:

- texto de destaque;
- texto de apoio;
- quantidade de linhas ideal;
- modelo recomendado de 1 a 5 linhas;
- opção de efeito sonoro.

Ele procura sinais como palavras fortes, números, perguntas, promessas, contraste, curiosidade e ganchos de retenção.

## Estrutura

- `index.html`: painel CEP.
- `css/app.css`: interface.
- `js/app.js`: controle da UI.
- `js/core/srt.js`: parser SRT e transcrição.
- `js/core/cache.js`: cache por projeto/sequência.
- `js/core/viralAnalyzer.js`: motor do Destaque Automático Viral.
- `js/core/lineBreaker.js`: quebra inteligente de linhas.
- `js/core/templates.js`: leitura de modelos.
- `jsx/hostscript.jsx`: ponte com Premiere Pro/After Effects.
- `templates/`: modelos por quantidade de linhas.
- `tests/`: testes do core.

## Estado atual

Esta versão é uma base funcional limpa:

- importa SRT e transcrições no formato dos arquivos de referência;
- cacheia por projeto/sequência;
- analisa e escolhe destaques;
- lista modelos por 1 a 5 linhas;
- envia aplicação para Premiere/After;
- no After Effects cria camadas de texto;
- no Premiere importa `.mogrt` quando houver modelo válido e cria marcador de fallback quando não houver.

Para uso final no Premiere, coloque seus `.mogrt` nas pastas de `templates/`.
