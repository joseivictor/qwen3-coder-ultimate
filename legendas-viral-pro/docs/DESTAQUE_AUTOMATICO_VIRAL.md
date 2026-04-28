# Destaque Automático Viral

## Objetivo

Encontrar automaticamente os melhores trechos de uma legenda para receber destaque visual, sem destruir o SRT original e sem destacar tudo.

## O que o motor procura

- palavras fortes;
- números;
- perguntas;
- promessas;
- contrastes;
- frases emocionais;
- curiosidade;
- ganchos de retenção;
- termos como `segredo`, `verdade`, `nunca`, `impossível`, `cuidado`, `atenção`, `erro`, `dinheiro`, `resultado`, `rápido`, `simples`, `importante`, `chocante`, `absurdo`, `ninguém`, `todo mundo`, `você precisa`, `olha isso`, `presta atenção`.

## Intensidade

- `Baixa`: seleciona menos trechos, com score mais alto.
- `Média`: equilíbrio para vídeos normais.
- `Alta`: pega mais oportunidades, útil para vídeos curtos e agressivos.

## Tipo

- `Palavra`: destaca o termo mais forte.
- `Frase curta`: destaca uma frase de impacto.
- `Agressivo/Viral`: prioriza gancho forte, promessa, curiosidade e contraste.

## Regras aplicadas

- preserva timing original;
- cria versão processada/cacheada;
- mantém o texto original disponível;
- evita legenda longa;
- tenta linhas entre 14 e 18 caracteres quando possível;
- respeita modelos de 1 a 5 linhas;
- separa destaque e apoio;
- limita a quantidade máxima de destaques;
- quando há muitas palavras fortes, escolhe pelo maior score.

## Saída por legenda processada

Cada item processado pode receber:

- `viralScore`
- `selectedForViral`
- `highlightText`
- `supportText`
- `highlightLines`
- `supportLines`
- `templateLineCount`
- `templateId`
- `reasons`

## Próxima evolução

A base está preparada para receber:

- presets por nicho;
- aprendizado com escolhas manuais;
- blacklist de palavras;
- ranking por ritmo do vídeo;
- exportação de SRT processado.
