# Admin online

O painel em `/painel` abre no Vercel e funciona bem para revisar/editar pelo celular.

Estado atual:
- Edita videos, experts, categorias, planos e capas em modo rascunho no navegador.
- Exporta backup JSON pelo proprio painel.
- Nao depende do PC para abrir.

Para publicar alteracoes para todos sem depender do PC, falta ligar um storage persistente:

1. Supabase: tabelas/JSON para `config`, `videos`, `experts`, `courses`, `motion` e `flyers`.
2. Storage de arquivos: Supabase Storage ou Vercel Blob para capas e videos novos.
3. Variaveis no Vercel: URL/chaves do backend.
4. API serverless: endpoints para salvar e ler os dados com senha.

Recomendacao: Supabase para dados + Supabase Storage para imagens. Videos grandes podem continuar em Vercel/GitHub se forem poucos, mas o ideal e storage dedicado.
