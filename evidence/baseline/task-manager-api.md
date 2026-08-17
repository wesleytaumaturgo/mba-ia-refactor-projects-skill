# Baseline manual — `task-manager-api`

> Levantamento **manual**, feito **antes** de qualquer invocação da skill `refactor-arch`
> e **antes** de ler a análise manual prévia em `.planning/analise-manual/`.
> Serve como termo de comparação independente para a checagem do run-3.

- **Data:** 2026-08-17
- **Commit base:** `cf93c7f` (`chore(skill): copy refactor-arch to task-manager-api`)
- **Stack:** Python 3.12 / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 + SQLite
- **Escopo:** `task-manager-api/` (exclui `.claude/`)

---

## 1. Inventário

### 1.1 LOC por arquivo (console literal)

```
$ find . -name '*.py' -not -path './.claude/*' | sort | xargs wc -l
   34 ./app.py
    3 ./database.py
   21 ./models/category.py
    3 ./models/__init__.py
   60 ./models/task.py
   38 ./models/user.py
    1 ./routes/__init__.py
  223 ./routes/report_routes.py
  299 ./routes/task_routes.py
  211 ./routes/user_routes.py
   99 ./seed.py
    1 ./services/__init__.py
   48 ./services/notification_service.py
  116 ./utils/helpers.py
    1 ./utils/__init__.py
 1158 total
```

**Distribuição:** 733 LOC (63,3%) concentrados em `routes/` — 3 arquivos de 211 a 299 linhas.

### 1.2 Dependências declaradas

```
$ cat requirements.txt
flask==3.0.0
flask-sqlalchemy==3.1.1
flask-cors==4.0.0
marshmallow==3.20.1
requests==2.31.0
python-dotenv==1.0.0
```

Três dependências declaradas e **nunca importadas** no código: `marshmallow`, `requests`,
`python-dotenv`. Nenhuma ocorrência em nenhum `.py` do projeto.

---

## 2. Grafo de imports e alcançabilidade

Mecanismo de resolução da stack: **import explícito** (Python não tem autoload por convenção).
Entry point: `app.py` (executado via `python app.py`).

```
$ grep -rn -E '^\s*(from|import)\s' --include='*.py' . | grep -v '^./.claude'
database.py:1:from flask_sqlalchemy import SQLAlchemy
app.py:1:from flask import Flask
app.py:2:from flask_cors import CORS
app.py:3:from database import db
app.py:4:from routes.task_routes import task_bp
app.py:5:from routes.user_routes import user_bp
app.py:6:from routes.report_routes import report_bp
app.py:7:import os, sys, json, datetime
seed.py:2:from app import app, db
seed.py:3:from models.task import Task
seed.py:4:from models.user import User
seed.py:5:from models.category import Category
seed.py:6:from datetime import datetime, timedelta
services/notification_service.py:1:import smtplib
services/notification_service.py:2:from datetime import datetime
models/category.py:1:from database import db
models/category.py:2:from datetime import datetime
utils/helpers.py:1:from datetime import datetime
utils/helpers.py:2:import re
utils/helpers.py:3:import os
utils/helpers.py:4:import json
utils/helpers.py:5:import sys
utils/helpers.py:6:import math
utils/helpers.py:7:import hashlib
utils/helpers.py:33:    import uuid
routes/user_routes.py:1:from flask import Blueprint, request, jsonify
routes/user_routes.py:2:from database import db
routes/user_routes.py:3:from models.user import User
routes/user_routes.py:4:from models.task import Task
routes/user_routes.py:5:from datetime import datetime
routes/user_routes.py:6:import hashlib, json, re
routes/task_routes.py:1:from flask import Blueprint, request, jsonify
routes/task_routes.py:2:from database import db
routes/task_routes.py:3:from models.task import Task
routes/task_routes.py:4:from models.user import User
routes/task_routes.py:5:from models.category import Category
routes/task_routes.py:6:from datetime import datetime
routes/task_routes.py:7:import json, os, sys, time
routes/report_routes.py:1:from flask import Blueprint, request, jsonify
routes/report_routes.py:2:from database import db
routes/report_routes.py:3:from models.task import Task
routes/report_routes.py:4:from models.user import User
routes/report_routes.py:5:from models.category import Category
routes/report_routes.py:6:from datetime import datetime, timedelta
routes/report_routes.py:7:from utils.helpers import format_date, calculate_percentage
routes/report_routes.py:8:import json
models/task.py:1:from database import db
models/task.py:2:from datetime import datetime
models/task.py:3:import json
models/__init__.py:1:from models.task import Task
models/__init__.py:2:from models.user import User
models/__init__.py:3:from models.category import Category
```

### 2.1 Grafo a partir do entry point

```
app.py
├── database (db)
├── routes.task_routes    ──> models.task, models.user, models.category, database
├── routes.user_routes    ──> models.user, models.task, database
└── routes.report_routes  ──> models.task, models.user, models.category, database,
                              utils.helpers (format_date, calculate_percentage)

seed.py  (NÃO importado por ninguém; ponto de entrada próprio)
└── app  ──> [todo o grafo acima]

services.notification_service  ── ÓRFÃO: zero importadores
```

### 2.2 Veredito de alcançabilidade das 4 camadas preexistentes

| Camada | Alcançável a partir do entry point? | Evidência |
|---|---|---|
| `models/` | **SIM** | `routes/task_routes.py:3-5`, `routes/user_routes.py:3-4`, `routes/report_routes.py:3-5` importam `models.task`/`models.user`/`models.category`; as rotas são importadas por `app.py:4-6` |
| `routes/` | **SIM** | `app.py:4-6` importa os três blueprints e registra em `app.py:18-20` |
| `utils/` | **SIM** (com ressalva) | `routes/report_routes.py:7` importa `format_date` e `calculate_percentage` de `utils.helpers`. O módulo **é carregado** no boot. Ressalva: os dois símbolos importados **nunca são chamados** no arquivo (ver §3, achado B-24) |
| `services/` | **NÃO** | Busca literal por `services`/`Notification`/`notification` em todo o projeto retorna **apenas ocorrências dentro do próprio `services/notification_service.py`**. Zero importadores. Camada morta |

```
$ grep -rn -E 'services|Notification|notification' --include='*.py' . | grep -v '^./.claude'
services/notification_service.py:4:class NotificationService:
services/notification_service.py:6:        self.notifications = []
services/notification_service.py:31:        self.notifications.append({
services/notification_service.py:43:    def get_notifications(self, user_id):
services/notification_service.py:45:        for n in self.notifications:
```

### 2.3 Status do `seed.py`

`seed.py` **não é alcançável a partir do entry point** — `app.py` não o importa em lugar nenhum.
A relação é inversa: `seed.py:2` faz `from app import app, db`, ou seja, é um **script separado**
com ponto de entrada próprio (`if __name__ == '__main__'`, linha 98), consumidor do entry point.
O README confirma: `python seed.py` é passo manual, executado antes de `python app.py`.

Consequência colateral: como `app.py:30-31` roda `db.create_all()` no escopo de módulo (não
protegido por `if __name__`), o mero `import app` do `seed.py` já cria o schema como efeito
colateral.

---

## 3. Achados manuais (baseline)

Numerados `B-nn`. Severidade na minha escala: CRÍTICO / ALTO / MÉDIO / BAIXO.

### Segurança

| ID | Sev | Achado | Local |
|---|---|---|---|
| B-01 | CRÍTICO | Senhas com **MD5 sem salt**. `hashlib.md5(pwd.encode()).hexdigest()` | `models/user.py:29,32` |
| B-02 | CRÍTICO | **Hash da senha vazado em toda resposta JSON** — `to_dict()` inclui `'password'`; usado em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e no payload do `POST /login` | `models/user.py:21` |
| B-03 | CRÍTICO | **`debug=True` no `app.run()`** do entry point → Werkzeug interactive debugger exposto em `0.0.0.0:5000`; qualquer 500 devolve console de execução remota | `app.py:34` |
| B-04 | CRÍTICO | **Segredos hardcoded**: `SECRET_KEY = 'super-secret-key-123'` e credencial SMTP `email_password = 'senha123'` no fonte | `app.py:13`, `services/notification_service.py:10` |
| B-05 | ALTO | **Nenhuma autenticação/autorização em nenhum endpoint.** `POST /login` devolve `'fake-jwt-token-' + str(user.id)` — token forjável, e nada o valida. Qualquer anônimo cria/edita/apaga users e tasks | `routes/user_routes.py:210`; todos os blueprints |
| B-06 | ALTO | `CORS(app)` sem restrição de origem — libera qualquer origem | `app.py:15` |
| B-07 | MÉDIO | Política de senha de 4 caracteres | `routes/user_routes.py:64,115` |
| B-08 | MÉDIO | `is_admin()` existe no model mas **nunca é chamado** — controle de acesso projetado e não ligado | `models/user.py:34-38` |

### Arquitetura / camadas

| ID | Sev | Achado | Local |
|---|---|---|---|
| B-09 | ALTO | **Camada `services/` morta.** `NotificationService` (48 LOC) tem zero importadores. Regra do §2.2: camada não adotada | `services/notification_service.py` |
| B-10 | ALTO | **Ausência de camada de serviço efetiva**: toda a regra de negócio (validação, orquestração, cálculo de relatório) vive dentro das funções de rota. As rotas falam direto com `db.session` e com o ORM | `routes/*.py` |
| B-11 | ALTO | **Ausência de camada de repositório**: `Task.query`, `User.query`, `Category.query`, `db.session.add/commit/rollback/delete` espalhados por 3 arquivos de rota | `routes/task_routes.py`, `user_routes.py`, `report_routes.py` |
| B-12 | MÉDIO | **Blueprint com responsabilidade trocada**: CRUD completo de `Category` (`/categories`, 4 endpoints, ~67 LOC) mora dentro de `report_routes.py`. Não é relatório | `routes/report_routes.py:157-223` |
| B-13 | MÉDIO | **Ausência de camada de serialização/DTO**: `to_dict()` no model é a única serialização, e mesmo assim as rotas montam dicts à mão em paralelo a ele | `models/*.py` + `routes/*.py` |
| B-14 | BAIXO | `models/__init__.py` reexporta os 3 models, mas nenhum consumidor importa do pacote — todos importam o submódulo direto. Reexport sem uso | `models/__init__.py` |
| B-15 | BAIXO | `routes/__init__.py`, `services/__init__.py`, `utils/__init__.py` vazios (1 byte) — nenhuma composição de pacote | — |

### Duplicação

| ID | Sev | Achado | Local |
|---|---|---|---|
| B-16 | ALTO | **Regra "task atrasada" reimplementada 7×**, sempre com o mesmo ninho de 3 `if`: `models/task.py:50-60` (`is_overdue`, nunca chamado), `routes/task_routes.py:30-39`, `:71-80`, `:283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43`, `:132-135` | 7 locais |
| B-17 | ALTO | **Lista de status válidos hardcoded 5×** — `['pending','in_progress','done','cancelled']` em `models/task.py:39`, `routes/task_routes.py:110`, `:177`, `utils/helpers.py:75` e `utils/helpers.py:110` (`VALID_STATUSES`, constante nunca usada) | 5 locais |
| B-18 | MÉDIO | **Faixa de prioridade 1..5 hardcoded 4×**: `models/task.py:46`, `routes/task_routes.py:113`, `:182`, `utils/helpers.py:84` | 4 locais |
| B-19 | MÉDIO | **Regex de e-mail duplicado 3×**: `routes/user_routes.py:61`, `:106`, `utils/helpers.py:21` (`validate_email`, nunca chamada) | 3 locais |
| B-20 | MÉDIO | **Roles válidos hardcoded 2×** + constante `VALID_ROLES` não usada: `routes/user_routes.py:71`, `:120`, `utils/helpers.py:111` | 3 locais |
| B-21 | MÉDIO | **Serialização de Task reimplementada à mão 3×** em vez de usar `to_dict()`: `routes/task_routes.py:17-28`, `routes/user_routes.py:162-169`, e o próprio `models/task.py:23-36` | 3 locais |
| B-22 | MÉDIO | **Cálculo de completion_rate duplicado 3×** com a mesma expressão inline `round((x/total)*100, 2) if total > 0 else 0`, existindo `calculate_percentage()` importada e não usada: `routes/task_routes.py:296`, `routes/report_routes.py:67`, `:151` | 3 locais + helper morto |
| B-23 | MÉDIO | **Parsing de tags reimplementado 5×**: `models/task.py:35`, `routes/task_routes.py:28`, `:141-144`, `:210-213`, `utils/helpers.py:103-106` | 5 locais |

### Código morto

| ID | Sev | Achado | Local |
|---|---|---|---|
| B-24 | MÉDIO | **`utils/helpers.py` é 100% não-invocado.** Dos 16 símbolos públicos, apenas 2 são importados (`format_date`, `calculate_percentage`) — **e nenhum dos dois é chamado**. Nunca referenciados: `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data` (52 LOC, reimplementa validação das rotas), `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR` | `utils/helpers.py` |
| B-25 | MÉDIO | **Métodos de model nunca chamados**: `Task.validate_status`, `Task.validate_priority`, `Task.is_overdue`, `User.is_admin` — 4 métodos que codificam regra de negócio que as rotas reimplementam inline | `models/task.py:38-60`, `models/user.py:34-38` |
| B-26 | BAIXO | **Imports não usados em massa**: `app.py:7` (`os, sys, json` — só `datetime` é usado); `routes/task_routes.py:7` (`json, os, sys, time` — nenhum usado); `routes/user_routes.py:6` (`hashlib, json` não usados); `routes/report_routes.py:8` (`json`); `models/task.py:3` (`json`); `utils/helpers.py:3-6` (`os, json, sys, math`) | 6 arquivos |
| B-27 | BAIXO | 3 dependências declaradas e não usadas: `marshmallow`, `requests`, `python-dotenv` | `requirements.txt` |

### Tratamento de erro

| ID | Sev | Achado | Local |
|---|---|---|---|
| B-28 | ALTO | **`except:` pelado engolindo tudo** (inclui `KeyboardInterrupt`/`SystemExit`): `routes/task_routes.py:62`, `:137`, `:204`, `:236`, `routes/user_routes.py:130`, `:149`, `routes/report_routes.py:186`, `:207`, `:221`, `utils/helpers.py:46`, `:49`, `:88` | 12 ocorrências |
| B-29 | ALTO | **Validação de tipo ausente → 500 não tratado.** Confirmado em execução (§4.3): `priority` como string, `title` como int e `?priority=abc` derrubam o request com stacktrace | `routes/task_routes.py:113,182,261` |
| B-30 | MÉDIO | **Nenhum error handler global** (`@app.errorhandler`). Cada rota trata (ou não) o próprio erro | `app.py` |
| B-31 | MÉDIO | **`print()` como log** — 11 ocorrências fora do `seed.py`; sem `logging`, sem níveis, sem correlação | `routes/task_routes.py:149,153,219,234`, `routes/user_routes.py:83,89,147`, `services/notification_service.py:21,24`, `utils/helpers.py:39,41` |
| B-32 | BAIXO | Mensagem genérica `'Erro interno'` mascarando a causa em `GET /tasks` | `routes/task_routes.py:63` |

### Performance

| ID | Sev | Achado | Local |
|---|---|---|---|
| B-33 | ALTO | **N+1 em `GET /tasks`** — loop dispara `User.query.get()` e `Category.query.get()` por task. Medido: 17 queries para 10 tasks (§4.4) | `routes/task_routes.py:41-57` |
| B-34 | ALTO | **N+1 em `GET /reports/summary`** — loop por usuário dispara `Task.query.filter_by(user_id=...)`. Medido: 21 queries para 3 usuários (§4.4). Além disso faz 5 `COUNT` separados só para o histograma de prioridade (`:24-28`) | `routes/report_routes.py:53-68` |
| B-35 | MÉDIO | **Contagem em memória**: `overdue` calculado carregando `Task.query.all()` e iterando em Python, em vez de filtrar no banco | `routes/task_routes.py:281-287`, `routes/report_routes.py:30-43` |
| B-36 | MÉDIO | **Nenhuma paginação** em `GET /tasks`, `GET /users`, `GET /categories`, `GET /tasks/search` — todos retornam a tabela inteira | 4 rotas |
| B-37 | MÉDIO | **N+1 em `GET /categories`** — `Task.query.filter_by(category_id=...).count()` dentro do loop. Medido: 5 queries para 4 categorias | `routes/report_routes.py:163` |
| B-38 | BAIXO | `GET /users` usa `len(u.tasks)` — força carregar todas as tasks de cada usuário só para contá-las. Medido: 6 queries para 3 usuários | `routes/user_routes.py:22` |

### Estilo / correção

| ID | Sev | Achado | Local |
|---|---|---|---|
| B-39 | MÉDIO | **Delete de usuário não é transacional**: `db.session.delete(t)` das tasks acontece **fora** do `try`, o `rollback` só cobre o delete do user | `routes/user_routes.py:140-151` |
| B-40 | MÉDIO | **`update_category` não valida payload nulo** — `data.get`/`in data` sobre `None` se o corpo vier vazio (as outras rotas checam `if not data`) | `routes/report_routes.py:196-197` |
| B-41 | MÉDIO | **Config no entry point**, sem `.env`/objeto de configuração, apesar de `python-dotenv` estar no `requirements.txt` | `app.py:11-13` |
| B-42 | BAIXO | **`db.create_all()` em escopo de módulo** — roda como efeito colateral de qualquer `import app`; sem migrations (nenhum Alembic) | `app.py:30-31` |
| B-43 | BAIXO | **`if/else` retornando booleano literal** — `User.is_admin`, `Task.validate_status`, `Task.validate_priority`, `Task.is_overdue`, `helpers.validate_email`, `helpers.is_valid_color` | 6 funções |
| B-44 | BAIXO | **`type(x) == list`** em vez de `isinstance` — `routes/task_routes.py:141`, `:210`, `utils/helpers.py:103` | 3 locais |
| B-45 | BAIXO | **`datetime.utcnow()` deprecado** no Python 3.12 — warnings reais no console (§4.2). 18 ocorrências | 6 arquivos |
| B-46 | BAIXO | **Zero testes** — nenhum arquivo `test_*.py`, nenhum framework de teste no `requirements.txt` | projeto inteiro |

**Total: 46 achados manuais.**

---

## 4. Execução — evidência de console

### 4.1 Ambiente

```
$ python3 --version
Python 3.12.3
$ pip install -r requirements.txt   # em venv isolada
$ pip freeze
blinker==1.9.0
certifi==2026.7.22
charset-normalizer==3.5.1
click==8.4.2
Flask==3.0.0
Flask-Cors==4.0.0
Flask-SQLAlchemy==3.1.1
greenlet==3.5.5
idna==3.18
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.3
marshmallow==3.20.1
packaging==26.3
python-dotenv==1.0.0
requests==2.31.0
SQLAlchemy==2.0.52
typing_extensions==4.16.0
urllib3==2.7.0
Werkzeug==3.1.8
```

Boot limpo:

```
$ python -c "import app; print('IMPORT OK')"
IMPORT OK
```

### 4.2 `python seed.py` — sucesso, com 5 DeprecationWarning

```
$ python seed.py
/…/task-manager-api/seed.py:66: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  {'title': 'Implementar autenticação JWT', …, 'due_date': datetime.utcnow() - timedelta(days=3)},
/…/task-manager-api/seed.py:67: DeprecationWarning: datetime.datetime.utcnow() is deprecated …
/…/task-manager-api/seed.py:69: DeprecationWarning: datetime.datetime.utcnow() is deprecated …
/…/task-manager-api/seed.py:70: DeprecationWarning: datetime.datetime.utcnow() is deprecated …
/…/task-manager-api/seed.py:74: DeprecationWarning: datetime.datetime.utcnow() is deprecated …
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks
```

### 4.3 Endpoints — caminho feliz e caminho de erro

Caminho feliz (todos 200):

```
$ curl -s http://localhost:5000/health           → 200
$ curl -s http://localhost:5000/                 → 200
$ curl -s http://localhost:5000/tasks/1          → 200
$ curl -s http://localhost:5000/tasks/stats      → 200 {"total":10,"pending":6,"in_progress":2,"done":1,"cancelled":1,"overdue":2,"completion_rate":10.0}
$ curl -s http://localhost:5000/users            → 200
$ curl -s http://localhost:5000/categories       → 200
$ curl -s http://localhost:5000/reports/user/1   → 200
$ curl -s http://localhost:5000/tasks/9999       → 404 {"error":"Task não encontrada"}
```

**Vazamento de hash de senha** (B-02), confirmado em duas rotas:

```
$ curl -s -X POST http://localhost:5000/login -H 'Content-Type: application/json' \
       -d '{"email":"joao@email.com","password":"1234"}'
{
  "message": "Login realizado com sucesso",
  "token": "fake-jwt-token-1",
  "user": {
    "active": true,
    "created_at": "2026-08-17 19:28:10.756405",
    "email": "joao@email.com",
    "id": 1,
    "name": "João Silva",
    "password": "81dc9bdb52d04dc20036dbd8313ed055",
    "role": "admin"
  }
}
 [HTTP 200]

$ curl -s -X POST http://localhost:5000/users -H 'Content-Type: application/json' \
       -d '{"name":"Novo","email":"novo-baseline@x.com","password":"1234"}'
{
  "active": true,
  "created_at": "2026-08-17 19:28:48.399348",
  "email": "novo-baseline@x.com",
  "id": 5,
  "name": "Novo",
  "password": "81dc9bdb52d04dc20036dbd8313ed055",
  "role": "user"
}
 [HTTP 201]
```

> `81dc9bdb52d04dc20036dbd8313ed055` é o MD5 de `"1234"` — reversível por rainbow table
> em segundos. Confirma B-01 + B-02 juntos.

**500 não tratado com debugger exposto** (B-03 + B-29):

```
$ curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:5000/tasks/search?priority=abc"
500
$ curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:5000/tasks \
       -H 'Content-Type: application/json' -d '{"title":"Teste ABC","priority":"alta"}'
500
$ curl -s -o /dev/null -w "%{http_code}\n" -X PUT http://localhost:5000/tasks/1 \
       -H 'Content-Type: application/json' -d '{"title":123}'
500
```

Corpo devolvido nos três casos — console interativo do Werkzeug, com o `SECRET` do
debugger no HTML:

```
<!doctype html>
<html lang=en>
  <head>
    <title>ValueError: invalid literal for int() with base 10: &#39;abc&#39;
 // Werkzeug Debugger</title>
    …
    <script>
      var CONSOLE_MODE = false,
          EVALEX = true,
          EVALEX_TRUSTED = false,
          SECRET = "mOqOIPsn3ruTqb0O5npC";
    </script>
```

```
$ curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:5000/?__debugger__=yes&cmd=resource&f=debugger.js"
200
```

`EVALEX = true` + endpoint do debugger servindo 200 = execução remota de código na
interface `0.0.0.0`.

### 4.4 N+1 medido (contador em `before_cursor_execute`)

```
/tasks               HTTP 200  queries SQL = 17
/users               HTTP 200  queries SQL = 6
/reports/summary     HTTP 200  queries SQL = 21
/categories          HTTP 200  queries SQL = 5
```

Base: 10 tasks, 3 usuários (5 após os probes), 4 categorias.

---

## 5. Resumo do baseline

| Métrica | Valor |
|---|---|
| LOC totais (`.py`, exclui `.claude/`) | 1158 |
| Arquivos `.py` | 15 |
| Maior arquivo | `routes/task_routes.py` — 299 LOC |
| Concentração em `routes/` | 733 LOC (63,3%) |
| Camadas preexistentes alcançáveis | 3 de 4 (`models/`, `routes/`, `utils/`) |
| Camadas preexistentes órfãs | 1 — `services/` |
| Achados manuais | 46 (B-01 … B-46) |
| Críticos | 4 |
| Altos | 11 |
| Rotas registradas | 22 (20 nos blueprints + 2 no `app.py`) |
| Testes | 0 |
| `except:` pelados | 12 |
| Aplicação sobe? | Sim |
| Suite de testes passa? | N/A — não existe |
