# code-smells-project

API de E-commerce em Python/Flask, refatorada para MVC pela skill `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt

cp .env.example .env                 # preencha LOJA_SECRET_KEY (obrigatória)
python -m scripts.migrate            # cria/evolui o schema — a DDL não roda mais no boot
python -m scripts.seed_dev           # dados de demonstração; recusa rodar em produção
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (mude com `LOJA_HOST`/`LOJA_PORT` no `.env`).

O boot apenas **verifica** a versão de schema aplicada e falha com mensagem clara se estiver
defasada — rode `python -m scripts.migrate` quando isso acontecer.

### Autenticação

As rotas de escrita e as de leitura de dados administrativos exigem credencial. Obtenha uma em
`POST /login` e envie como `Authorization: Bearer <token>`:

```bash
TOKEN=$(curl -s -X POST localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","senha":"123456"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["dados"]["token"])')

curl localhost:5000/usuarios -H "Authorization: Bearer $TOKEN"
```

Públicas: `GET /`, `GET /health`, `GET /produtos*`, `POST /usuarios`, `POST /login`,
`POST /pedidos`. Toda rota nova nasce **protegida** — a exceção é declarada em
`middlewares/auth.py::POLITICAS_PADRAO`.

## Estrutura

| Diretório | Responsabilidade única |
|---|---|
| `config/` | Ler o ambiente, validar o obrigatório, expor valores tipados. Falha no boot se faltar. |
| `models/` | Forma dos dados e invariantes que valem sempre. |
| `repositories/` | Traduzir entre entidade e persistência. Único lugar que conhece o driver do banco. |
| `services/` | Regra de negócio e orquestração. Único lugar que decide *o quê* acontece. |
| `controllers/` | Traduzir entre protocolo HTTP e domínio. |
| `routes/` | Declarar `método + path → handler + política de acesso`. Sem lógica. |
| `middlewares/` | Autenticação, autorização, tratamento de erro, limite de taxa. |
| `dto/` | Projeção de saída com allowlist de campos. |
| `validators/` | Invariantes de entrada e allowlist de bind. |
| `security/` | Derivação de senha e credencial assinada. |
| `infra/` | Conexão e migração versionada. |
| `observability/` | Logger com níveis, timestamp e redação de sensíveis. |
| `infra/migrations/` | Schema versionado, com FK, CHECK, UNIQUE, NOT NULL e índices. |

`app.py` é o composition root: o único ponto autorizado a instanciar infraestrutura.

## Paginação

`GET /produtos`, `GET /produtos/busca`, `GET /usuarios` e `GET /pedidos` aceitam `limit` e
`offset`. Default: 20 itens (`LOJA_PAGE_SIZE_DEFAULT`). Teto: 100 (`LOJA_PAGE_SIZE_MAX`).

## Erros

Envelope único em todos os caminhos de erro:

```json
{"error": {"code": "nao_encontrado", "message": "Produto não encontrado", "correlation_id": "e166135d2c89"}}
```

Cite o `correlation_id` ao reportar um problema: ele aparece no log do servidor.
