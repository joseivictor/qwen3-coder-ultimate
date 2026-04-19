"""
Seed do PromptEngine com exemplos de alta qualidade.
Execute uma vez: python -m core.seed_prompt_engine
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

EXAMPLES = [
    # ── BUG FIX ───────────────────────────────────────────────────────────────
    ("bug_fix",
     "meu código dá KeyError quando o usuário não tem 'email' no dict",
     """O problema é acesso direto ao dict sem verificar a chave.

```python
# Antes (quebra):
email = user['email']

# Depois (correto):
email = user.get('email', '')
# ou se o campo é obrigatório:
email = user.get('email') or raise ValueError("user.email obrigatório")
```

Se o campo for sempre esperado, valide na entrada do sistema, não no meio da lógica."""),

    ("bug_fix",
     "TypeError: 'NoneType' object is not subscriptable",
     """Uma função está retornando `None` onde você espera uma lista ou dict.

Diagnóstico:
1. Identifique qual variável é `None` pelo traceback (linha exata)
2. Rastreie onde ela é atribuída
3. Verifique se a função que a preenche tem um `return` em todos os caminhos

Padrão de correção:
```python
result = buscar_dados()
if result is None:
    return []   # ou logue o erro e retorne valor padrão seguro
items = result['items']
```

Nunca use `try/except` genérico para esconder esse erro — corrija a causa."""),

    ("bug_fix",
     "minha função async não está esperando o resultado, retorna coroutine",
     """Você esqueceu o `await` na chamada.

```python
# Errado — retorna coroutine object:
result = minha_func_async()

# Correto:
result = await minha_func_async()
```

Se estiver fora de contexto async, use:
```python
import asyncio
result = asyncio.run(minha_func_async())
```

Nunca misture `asyncio.run()` dentro de função que já está em loop async — vai dar RuntimeError."""),

    # ── CODE GENERATION ───────────────────────────────────────────────────────
    ("code_generation",
     "cria uma função pra paginar resultados de uma query SQLite",
     """```python
def paginar(db_path: str, query: str, params: tuple = (),
            page: int = 1, per_page: int = 20) -> dict:
    offset = (page - 1) * per_page
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        total = cur.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()[0]
        rows  = cur.execute(f"{query} LIMIT ? OFFSET ?", params + (per_page, offset)).fetchall()
    return {
        "items":       [dict(r) for r in rows],
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }
```"""),

    ("code_generation",
     "preciso de um decorator pra medir tempo de execução de funções",
     """```python
import time
import functools
from typing import Callable

def timer(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start  = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__}: {elapsed*1000:.2f}ms")
        return result
    return wrapper

# Uso:
@timer
def processar_dados(items: list) -> list:
    ...
```

Para async:
```python
def timer(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start  = time.perf_counter()
        result = await func(*args, **kwargs)
        print(f"{func.__name__}: {(time.perf_counter()-start)*1000:.2f}ms")
        return result
    return wrapper
```"""),

    ("code_generation",
     "função pra fazer retry automático em chamadas de API com backoff exponencial",
     """```python
import time
import functools
from typing import Callable, Type

def retry(max_attempts: int = 3,
          exceptions: tuple[Type[Exception], ...] = (Exception,),
          backoff: float = 1.5):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = 1.0
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    time.sleep(wait)
                    wait *= backoff
        return wrapper
    return decorator

# Uso:
@retry(max_attempts=4, exceptions=(requests.HTTPError, ConnectionError))
def chamar_api(url: str) -> dict:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()
```"""),

    # ── REFACTORING ───────────────────────────────────────────────────────────
    ("refactoring",
     "essa função tem 150 linhas, como refatorar?",
     """Quebre pelo princípio de responsabilidade única — cada função faz uma coisa.

Processo:
1. Identifique blocos coesos dentro da função (geralmente separados por comentários ou linhas em branco)
2. Extraia cada bloco como função com nome descritivo
3. A função original vira um orquestrador de 5-10 linhas

Exemplo:
```python
# Antes: 150 linhas fazendo parse + validação + persistência + notificação
def processar_pedido(dados: dict): ...

# Depois:
def processar_pedido(dados: dict) -> Pedido:
    pedido   = _parse_pedido(dados)
    _validar_pedido(pedido)
    _salvar_pedido(pedido)
    _notificar_cliente(pedido)
    return pedido
```

Execute os testes após cada extração — não faça tudo de uma vez."""),

    ("refactoring",
     "tenho muito código duplicado, como consolidar?",
     """Antes de extrair, confirme que é duplicação real (mesma lógica) e não coincidência similar.

Regra: 3 ocorrências = extrair. 2 = considere. 1 = não extraia.

```python
# Duplicado em 3 lugares:
if user.role == 'admin' and user.active and user.verified:
    ...

# Extraia:
def pode_acessar_area_restrita(user: User) -> bool:
    return user.role == 'admin' and user.active and user.verified
```

Para lógica variável, use parâmetros — não crie uma abstração genérica demais na primeira iteração."""),

    # ── TESTING ───────────────────────────────────────────────────────────────
    ("testing",
     "como escrever testes para uma função que acessa o banco de dados?",
     """Use banco em memória (SQLite `:memory:`) — não mocke o banco. Mock que passa ≠ código que funciona.

```python
import pytest, sqlite3

@pytest.fixture
def db():
    conn = sqlite3.connect(':memory:')
    conn.execute('''CREATE TABLE users
                    (id INTEGER PRIMARY KEY, name TEXT, email TEXT)''')
    conn.execute("INSERT INTO users VALUES (1, 'João', 'joao@ex.com')")
    conn.commit()
    yield conn
    conn.close()

def test_buscar_usuario(db):
    from meu_modulo import buscar_usuario
    user = buscar_usuario(db, user_id=1)
    assert user['name'] == 'João'

def test_usuario_inexistente(db):
    from meu_modulo import buscar_usuario
    assert buscar_usuario(db, user_id=999) is None
```

Teste o comportamento esperado, não a implementação interna."""),

    ("testing",
     "como testar código que faz requests HTTP sem chamar a API real?",
     """Use `responses` ou `httpx` mock — mais confiável que monkeypatching.

```python
# pip install responses
import responses
import requests

@responses.activate
def test_buscar_clima():
    responses.add(
        responses.GET,
        'https://api.weather.com/v1/current',
        json={'temp': 25, 'city': 'São Paulo'},
        status=200,
    )
    from meu_modulo import buscar_clima
    resultado = buscar_clima('São Paulo')
    assert resultado['temp'] == 25

@responses.activate
def test_api_fora_do_ar():
    responses.add(responses.GET, 'https://api.weather.com/v1/current', status=503)
    from meu_modulo import buscar_clima
    with pytest.raises(RuntimeError, match='serviço indisponível'):
        buscar_clima('São Paulo')
```"""),

    # ── SECURITY ──────────────────────────────────────────────────────────────
    ("security",
     "meu código tem SQL com f-string, como corrigir?",
     """Troque imediatamente — f-string em SQL = injeção de SQL garantida.

```python
# VULNERÁVEL — nunca faça isso:
query = f"SELECT * FROM users WHERE email = '{email}'"
conn.execute(query)

# CORRETO — sempre use parâmetros:
conn.execute("SELECT * FROM users WHERE email = ?", (email,))

# Com SQLAlchemy:
stmt = select(User).where(User.email == email)  # já é seguro
```

Busque todas as ocorrências: `search_in_files` com padrão `f".*SELECT|INSERT|UPDATE|DELETE`."""),

    ("security",
     "como armazenar senhas dos usuários de forma segura?",
     """Use `bcrypt` ou `argon2` — nunca MD5, SHA1, SHA256 direto, ou texto claro.

```python
# pip install bcrypt
import bcrypt

def hash_senha(senha: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha.encode(), salt).decode()

def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    return bcrypt.checkpw(senha.encode(), hash_armazenado.encode())

# Na criação de conta:
hash_armazenado = hash_senha(senha_do_usuario)
salvar_no_banco(hash_armazenado)

# No login:
if not verificar_senha(senha_digitada, hash_do_banco):
    raise ValueError("Credenciais inválidas")
```

`rounds=12` é o mínimo aceitável em 2025. Aumente se o hardware permitir."""),

    # ── PERFORMANCE ───────────────────────────────────────────────────────────
    ("performance",
     "meu loop está lento, como otimizar?",
     """Primeiro meça — não otimize no escuro.

```python
import cProfile
cProfile.run('sua_funcao(dados)', sort='cumulative')
```

Otimizações por ordem de impacto:
1. **Algoritmo** — O(n²) → O(n log n) > qualquer micro-otimização
2. **Estrutura de dados** — list lookup O(n) → set/dict lookup O(1)
3. **Batch operations** — N queries → 1 query com IN (...)
4. **Lazy evaluation** — gere só o que vai usar
5. **Cache** — `@functools.lru_cache` para resultados determinísticos

```python
# Antes — O(n²):
for item in items:
    if item in lista_grande:  # O(n) por iteração
        processar(item)

# Depois — O(n):
set_grande = set(lista_grande)  # O(n) uma vez
for item in items:
    if item in set_grande:      # O(1) por iteração
        processar(item)
```"""),

    # ── ARCHITECTURE ──────────────────────────────────────────────────────────
    ("architecture",
     "devo usar REST ou GraphQL para minha API?",
     """Depende do problema, não de tendência.

**REST quando:**
- Recursos bem definidos e estáveis (CRUD simples)
- Clientes variados (mobile, web, third-party)
- Cache é importante (REST usa HTTP cache nativamente)
- Time conhece REST, prazo é curto

**GraphQL quando:**
- Cliente precisa de flexibilidade no que busca (evita over/under-fetching)
- Múltiplas telas com necessidades diferentes do mesmo recurso
- Schema é o contrato entre times — autodocumentação importa
- Você aceita a complexidade: N+1 queries, resolvers, DataLoader

**Regra prática:** comece com REST. Migre para GraphQL quando sentir a dor que ele resolve — não antes."""),

    ("architecture",
     "quando usar microserviços vs monolito?",
     """**Comece com monolito.** Quase sempre.

Microserviços resolvem problemas de escala organizacional (times grandes, deploys independentes) — não de performance.

**Monolito é certo quando:**
- Time < 10 pessoas
- Domínio ainda está sendo descoberto
- Latência de rede entre serviços seria problema
- Você não tem infra para orquestrar serviços (K8s, service mesh, tracing)

**Microserviços fazem sentido quando:**
- Times diferentes precisam deployar independentemente
- Partes do sistema têm requisitos de escala radicalmente diferentes
- Você já tem um monolito e encontrou os pontos de corte naturais

"Distributed monolith" (microserviços com acoplamento forte) é o pior dos dois mundos."""),

    # ── DOCUMENTATION ─────────────────────────────────────────────────────────
    ("documentation",
     "como documentar uma API FastAPI?",
     """FastAPI gera docs automáticos (Swagger + ReDoc) a partir dos type hints. Enriqueça com:

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="Minha API",
    description="API para gerenciar pedidos",
    version="1.0.0",
)

class CriarPedidoRequest(BaseModel):
    produto_id: int = Field(..., description="ID do produto", example=42)
    quantidade: int = Field(..., ge=1, le=100, description="Entre 1 e 100")

@app.post(
    "/pedidos",
    summary="Criar novo pedido",
    response_description="Pedido criado com sucesso",
    status_code=201,
)
async def criar_pedido(body: CriarPedidoRequest) -> dict:
    \"\"\"
    Cria um pedido no sistema.

    - **produto_id**: deve existir no catálogo
    - **quantidade**: respeitará estoque disponível
    \"\"\"
    ...
```

Acesse `/docs` (Swagger) e `/redoc` automaticamente."""),

    # ── EXPLANATION ───────────────────────────────────────────────────────────
    ("explanation",
     "o que é um context manager e quando usar?",
     """Context manager garante que recursos sejam liberados mesmo se ocorrer erro.

```python
# Sem context manager — arquivo pode não fechar se der erro:
f = open('dados.txt')
dados = f.read()  # se isso der erro, f.close() nunca é chamado
f.close()

# Com context manager — fecha sempre:
with open('dados.txt') as f:
    dados = f.read()  # erro aqui → Python ainda fecha o arquivo
```

Crie o seu com `__enter__` / `__exit__` ou `@contextmanager`:

```python
from contextlib import contextmanager

@contextmanager
def transacao(db):
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

with transacao(conexao) as db:
    db.execute("INSERT INTO ...")
    db.execute("UPDATE ...")
```

Use quando precisar garantir cleanup: arquivos, conexões, locks, timers."""),
]


def seed():
    try:
        from core.prompt_engine import PromptEngine
        from openai import OpenAI

        # Dummy client — seed só usa o DB, não chama API
        client = OpenAI(api_key="dummy", base_url="http://localhost:9999")
        engine = PromptEngine(client, "dummy-model")

        added = 0
        for task_type, user_msg, assistant_msg in EXAMPLES:
            engine.record_example(task_type, user_msg, assistant_msg)
            added += 1

        print(f"[OK] Seeded {added} examples into PromptEngine DB")

    except Exception as e:
        print(f"[ERR] Seed failed: {e}")
        raise


if __name__ == "__main__":
    seed()
