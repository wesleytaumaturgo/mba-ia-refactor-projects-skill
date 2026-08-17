# task-manager-api

API de Task Manager em Python/Flask, refatorada para MVC pela skill `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt

cp .env.example .env                 # preencha SECRET_KEY (obrigatória em produção)
python -m infra.migrator upgrade     # cria/evolui o schema — a DDL não roda mais no boot
python seed.py                       # dados de demonstração; recusa rodar em produção
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (mude com `HOST`/`PORT` no `.env`).

O boot apenas **verifica** a versão de schema aplicada e falha com mensagem clara se estiver
defasada — rode `python -m infra.migrator upgrade` quando isso acontecer, ou
`python -m infra.migrator status` para ver o que está pendente.

### Autenticação

As rotas de escrita, as destrutivas e as de leitura de dados de terceiros exigem credencial.
Obtenha uma em `POST /login` e envie como `Authorization: Bearer <token>`:

```bash
TOKEN=$(curl -s -X POST localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"1234"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

curl localhost:5000/users -H "Authorization: Bearer $TOKEN"
```

Públicas: `GET /`, `GET /health`, `POST /login`, `GET /tasks*`, `GET /categories`,
`GET /reports/*`. Toda rota nova nasce **protegida** — a exceção é declarada com `@public`.

## Estrutura

| Diretório | Responsabilidade única |
|---|---|
| `config/` | Ler o ambiente, validar o obrigatório, expor valores tipados. Falha no boot se faltar. |
| `models/` | Forma dos dados e invariantes que valem sempre. |
| `repositories/` | Traduzir entre entidade e persistência. Único lugar que conhece o ORM. |
| `services/` | Regra de negócio e orquestração. Único lugar que decide *o quê* acontece. |
| `controllers/` | Traduzir entre protocolo e domínio. |
| `routes/` | Declarar `método + path → handler + middlewares`. Sem lógica. |
| `middlewares/` | Autenticação, autorização, tratamento de erro, limite de taxa. |
| `dto/` | Projeção de saída com allowlist de campos. |
| `validators/` | Invariantes de entrada e allowlist de bind. |
| `security/` | Derivação de senha e credencial assinada. |
| `infra/` | Migração versionada. |
| `observability/` | Logger com níveis, timestamp e redação de sensíveis. |
| `utils/` | Utilitários com chamador real. |
| `migrations/` | Schema versionado, com FK, CHECK, UNIQUE, NOT NULL e índices. |

`app.py` é o composition root: o único ponto autorizado a instanciar infraestrutura.

## Desenvolvimento

```bash
pip install -r requirements-dev.txt
ruff check .        # inclui a regra que barra o retorno das APIs deprecated
```

## Paginação

`GET /tasks`, `GET /tasks/search`, `GET /users` e `GET /categories` aceitam `limit` e `offset`.
Default: 50 itens. Teto: 200. A raiz da resposta continua sendo um array — sem envelope.

## Erros

Envelope único em todos os caminhos de erro:

```json
{"error": {"code": "not_found", "message": "Task não encontrada", "correlation_id": "e166135d2c89"}}
```

Cite o `correlation_id` ao reportar um problema: ele aparece no log do servidor.
