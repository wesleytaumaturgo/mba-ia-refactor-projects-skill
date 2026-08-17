# Run 1 — Fase 1 (refactor-arch)

Saída literal da Fase 1 da skill `refactor-arch`, executada em 2026-08-17 sobre
`code-smells-project/`. Invocação: `/refactor-arch` **sem argumento** — os caminhos
dos artefatos são os defaults resolvidos pela própria skill nas pré-condições.

---

## Pré-condições (saída literal)

```console
$ git rev-parse --show-toplevel
/home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill
$ git status --porcelain
(fim — vazio acima significa limpo)
$ git rev-parse --short HEAD
ec6d1d4
```

Working tree limpo. SHA do commit de baseline: `ec6d1d4`.

### Caminhos dos artefatos resolvidos pela skill

Nenhum argumento foi passado na invocação, então a skill aplicou seus defaults
(`<raiz>/reports/audit-<nome do diretório>.md` e `<raiz>/reports/baseline-<nome do diretório>.json`),
ancorados na raiz devolvida por `git rev-parse --show-toplevel`:

```console
REPORT_PATH   = /home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/audit-code-smells-project.md
BASELINE_PATH = /home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/baseline-code-smells-project.json
```

Declaração exigida pela pré-condição 4: *"auditoria read-only até o gate da Fase 2"*.

---

## Determinação do runtime real (executado, não lido do manifesto)

```console
$ python3 --version
Python 3.12.3
$ <venv>/bin/python --version
Python 3.12.3
$ <venv>/bin/python -c "import flask, flask_cors, sqlite3, sys; ..."
<string>:1: DeprecationWarning: The '__version__' attribute is deprecated and will be removed in Flask 3.2. Use feature detection or 'importlib.metadata.version("flask")' instead.
<string>:1: DeprecationWarning: version is deprecated and will be removed in Python 3.14
flask 3.1.1
flask_cors 5.0.1
sqlite3 module 2.6.0 lib 3.45.1
sys.version 3.12.3 (main, Jun 19 2026, 12:46:00) [GCC 13.3.0]
```

## Grafo de resolução (mecanismo: import explícito)

```console
$ grep -n "^import \|^from " *.py
app.py:1:from flask import Flask, jsonify, request
app.py:2:from flask_cors import CORS
app.py:3:import controllers
app.py:4:from database import get_db
database.py:1:import sqlite3
database.py:2:import os
models.py:1:from database import get_db
models.py:2:import sqlite3
controllers.py:1:from flask import request, jsonify
controllers.py:2:import models
controllers.py:3:from database import get_db
```

```console
$ grep -c "controllers\." app.py      # 16
$ grep -c "models\." controllers.py   # 17
$ grep -n "get_db()" app.py controllers.py models.py | wc -l   # 19
$ grep -n "\bos\." database.py        # (vazio — import não utilizado)
$ grep -n "sqlite3" models.py
2:import sqlite3                      # (única ocorrência — import não utilizado)
```

---

## BLOCO PHASE 1 — saída literal

```console
PHASE 1: PROJECT ANALYSIS
─────────────────────────────────────────────
Language      : Python (runtime in use: 3.12.3)
Framework     : Flask 3.1.1 (+ flask-cors 5.0.1)
Package mgr   : requirements.txt (pip)
Database      : SQLite · sqlite3 stdlib (lib 3.45.1) · 4 tables
Domain        : E-commerce — catálogo de produtos, usuários, pedidos e relatório de vendas
Entry points  : app.py (único; `if __name__ == "__main__"` + app.run)
Resolution    : explicit import
Architecture  : Pseudo-camadas — 3 módulos nomeados por camada (controllers/models/database),
                mas o entry point e a camada de controller acessam a persistência diretamente
Source files  : 4 files · 780 LOC
Endpoints     : 19 mapped · baseline captured (19 responses)
Baseline SHA  : ec6d1d4
Baseline file : /home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/baseline-code-smells-project.json
─────────────────────────────────────────────
```

---

## Captura do baseline (§2 do validation-protocol)

Comando de boot descoberto pela precedência da §1 do `validation-protocol.md`:
`requirements.txt` não declara script (pip não tem campo de script), não há entry point
declarado em configuração de empacotamento; a convenção da stack aplicada ao arquivo que
instancia o servidor dá `python app.py` — confirmado pelo README do projeto.

Critério de "subiu com sucesso" (§3): porta escutando, processo vivo após o boot, e
primeira requisição respondida.

```console
processo vivo: sim
captured 19 responses -> /home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/baseline-code-smells-project.json
```

Encerramento verificado (§3, derrubar o processo):

```console
pgrep_exit=1
http_code=000
curl_exit=7
```

19 registros gravados em `BASELINE_PATH`, todos com `method`, `path`, `status`, `media` e
`shape` (todos os 19 responderam `application/json`, nenhum exigiu `selector`).

**Nenhum endpoint pré-existente quebrado.**

## Registro de ondas (§6.1) — linha de baseline

```console
| stage    | sha       | smoke  | status |
|----------|-----------|--------|--------|
| baseline | ec6d1d4   | —      | green  |
```
