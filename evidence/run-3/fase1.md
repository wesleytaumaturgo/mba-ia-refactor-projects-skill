# Run-3 · Fase 1 — Análise (read-only) · `task-manager-api`

Execução da skill `refactor-arch` copiada para `task-manager-api/.claude/skills/refactor-arch/`.
Comando invocado **sem argumento** — os defaults das pré-condições §3 valem.

---

## 0. Invocação e descoberta da skill

Primeira tentativa de invocar a skill falhou porque a sessão está ancorada na raiz do
monorepo e a skill é escopada a `task-manager-api/`:

```console
> Skill(skill: refactor-arch)
Unknown skill: refactor-arch
```

Após ler `task-manager-api/.claude/commands/refactor-arch.md`, o harness indexou a skill
(`from task-manager-api/.claude/skills — applies when working on files under task-manager-api/`)
e a invocação passou:

```console
> Skill(skill: refactor-arch)
Launching skill: refactor-arch
Base directory for this skill: …/task-manager-api/.claude/skills/refactor-arch
```

> Fato de ambiente, não defeito da skill: skills escopadas a subdiretório só entram no
> índice quando a sessão toca aquele subdiretório. Um operador que rodasse
> `claude` de dentro de `task-manager-api/` não veria isso.

---

## 1. Pré-condições (SKILL.md §Pré-condições)

```console
$ git rev-parse --show-toplevel
/home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill

$ git status --porcelain
(fim — vazio acima significa working tree limpo)

$ git rev-parse HEAD
f580ee5ae44cba9cce170bdef1a1d3c70fbb4e1b

$ git rev-parse --short HEAD
f580ee5
```

Working tree **limpo** → pré-condição 1 satisfeita, não abortar.

### Registro de ondas — linha 1 (validation-protocol §6.1)

| stage    | sha       | smoke  | status |
|----------|-----------|--------|--------|
| baseline | `f580ee5` | —      | green  |

### Caminhos resolvidos (ancorados na raiz, não no cwd)

```console
REPORT_PATH   : /home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/audit-task-manager-api.md
BASELINE_PATH : /home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/baseline-task-manager-api.json
```

Nenhum argumento foi passado ao comando, então `REPORT_PATH` cai no default
`<raiz>/reports/audit-<nome do diretório do projeto>.md`.

> **Ambiguidade observada (não bloqueante).** A pré-condição §3 deriva o nome do artefato
> do "nome do diretório do projeto", e o comando manda executar "sobre o diretório de
> trabalho atual". Numa raiz que contém três projetos irmãos, "diretório de trabalho
> atual" é a raiz, e o nome do projeto não sai dela. Resolvi como `task-manager-api`
> por ser o alvo declarado da tarefa. Anotado para a checagem (CA-3).

**Declaração exigida pela pré-condição 4:** *auditoria read-only até o gate da Fase 2.*

---

## 2. Os oito fatos (project-analysis.md §0)

### Fato 1 — Linguagem dominante

Duas fontes cruzadas, conforme §1:

```console
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

- **Extensões:** 15 arquivos `.py`, 1158 LOC. Nenhuma outra extensão de código.
- **Manifesto:** `requirements.txt` (pip) — Python.

Sem divergência. **Python**, sem linguagens secundárias (nenhum `.sql`, `.sh`, `.js`).

### Fato 2 — Framework efetivo

> declarado no manifesto ∩ resolvido por arquivo alcançável

```console
pacote                 declarado    instalado    importavel   importado pelo codigo?
flask                  3.0.0        3.0.0        sim          SIM
flask-sqlalchemy       3.1.1        3.1.1        sim          SIM
flask-cors             4.0.0        4.0.0        sim          SIM
marshmallow            3.20.1       3.20.1       sim          NAO
requests               2.31.0       2.31.0       sim          NAO
python-dotenv          1.0.0        1.0.0        sim          NAO
```

- **Framework efetivo:** Flask 3.0.0, com Flask-SQLAlchemy 3.1.1 (ORM) e Flask-CORS 4.0.0.
- **Declarado e não resolvido → candidatos a AP-26:** `marshmallow`, `requests`,
  `python-dotenv`. Os três estão instaláveis e instalados, mas **nenhum arquivo do projeto
  os importa**. Conforme §2, isso "revela a arquitetura pretendida e não implementada":
  `marshmallow` = camada de validação/serialização planejada e nunca escrita;
  `python-dotenv` = externalização de configuração planejada e nunca feita (e o projeto tem
  segredos hardcoded — ver Fase 2). Sinal de alto valor, levado à Fase 2.
- **Importado e não declarado:** nenhum. Todos os imports de terceiros resolvem contra o
  manifesto.

### Fato 3 — Versão real do runtime

Obtida **executando o runtime**, nunca lida do manifesto:

```console
$ python3 --version
Python 3.12.3
```

O `requirements.txt` **não declara versão de Python**, e não há `.python-version`,
`setup.py`, `pyproject.toml` nem `Pipfile`. Portanto:

| Fonte | Valor |
|---|---|
| Ambiente (executado) | **3.12.3** |
| Declarado no manifesto | *ausente* |
| Exigido pelas dependências | Flask 3.0.0 → ≥3.8 |

AP-16 é **verificável** nesta execução, contra 3.12.3.

### Fato 4 — Mecanismo de persistência

Quatro sinais cruzados (§4):

| Sinal | Achado |
|---|---|
| ORM no manifesto | `flask-sqlalchemy==3.1.1` |
| Import efetivo | `database.py:1` `from flask_sqlalchemy import SQLAlchemy`; `db` importado por app.py e pelos 3 blueprints |
| DDL no repositório | **Nenhuma migração.** DDL nasce de `db.create_all()` em `app.py:31` |
| Banco embarcado / string de conexão | `app.py:11` `'sqlite:///tasks.db'` → resolvido para `instance/tasks.db` |

**DDL executada no caminho de boot — `app.py:30-31`, em escopo de módulo. Registrado agora
como insumo direto de AP-21**, conforme instrução da §4.

Schema efetivo e restrições de integridade declaradas:

```console
TABELAS: ['categories', 'tasks', 'users'] (3)

--- categories ---
  id              INTEGER         notnull=1 pk=1
  name            VARCHAR(100)    notnull=1 pk=0
  description     VARCHAR(300)    notnull=0 pk=0
  color           VARCHAR(7)      notnull=0 pk=0
  created_at      DATETIME        notnull=0 pk=0
  FKs: NENHUMA
  indices: NENHUM

--- tasks ---
  id              INTEGER         notnull=1 pk=1
  title           VARCHAR(200)    notnull=1 pk=0
  description     TEXT            notnull=0 pk=0
  status          VARCHAR(50)     notnull=0 pk=0
  priority        INTEGER         notnull=0 pk=0
  user_id         INTEGER         notnull=0 pk=0
  category_id     INTEGER         notnull=0 pk=0
  created_at      DATETIME        notnull=0 pk=0
  updated_at      DATETIME        notnull=0 pk=0
  due_date        DATETIME        notnull=0 pk=0
  tags            VARCHAR(500)    notnull=0 pk=0
  FKs: [('category_id', 'categories', 'id'), ('user_id', 'users', 'id')]
  indices: NENHUM

--- users ---
  id              INTEGER         notnull=1 pk=1
  name            VARCHAR(100)    notnull=1 pk=0
  email           VARCHAR(150)    notnull=1 pk=0
  password        VARCHAR(255)    notnull=1 pk=0
  role            VARCHAR(50)     notnull=0 pk=0
  active          BOOLEAN         notnull=0 pk=0
  created_at      DATETIME        notnull=0 pk=0
  FKs: NENHUMA
  indices: [('sqlite_autoindex_users_1', 'UNIQUE')]

PRAGMA foreign_keys (enforcement em runtime): 0
```

Insumos que a §4 pede para levar a AP-11/AP-12/AP-21:

- **FKs declaradas em `tasks` mas NÃO aplicadas em runtime** — `PRAGMA foreign_keys = 0`, o
  default do SQLite, e nenhum listener as liga. A integridade referencial é decorativa.
- **Nenhum CHECK** sobre `status` (4 valores válidos no código) nem sobre `priority` (1..5 no
  código). Regra de domínio existe só em Python.
- **Nenhum índice** em `tasks.user_id`, `tasks.category_id`, `tasks.status` — exatamente as
  colunas que as rotas filtram.
- `status`, `priority`, `active`, `created_at` são `nullable` no banco embora tenham default
  no ORM: o default é aplicado pelo Python, não pelo schema.

### Fato 5 — Domínio de negócio

Três vocabulários, na ordem da §5:

- **Tabelas:** `tasks`, `users`, `categories`
- **Segmentos de path:** `/tasks`, `/users`, `/categories`, `/reports`, `/login`
- **Entidades no código:** `Task`, `User`, `Category`

> **Domínio:** gestão de tarefas — *tasks* atribuídas a *users*, agrupadas por *categories*,
> com relatórios de produtividade por usuário e por status.

Vocabulário **coerente** entre as três fontes (`task`↔`tasks`↔`Task`). Nenhuma divergência
tabela↔rota↔código → nada a levar para AP-27 por esse eixo.

Agregados candidatos: **Task** (raiz), **User**, **Category**.

### Fato 6 — Arquitetura efetiva (grafo de resolução)

**Passo 1 da §6 — qual mecanismo a stack usa.** Python resolve símbolo **exclusivamente por
import explícito**. Não há autoload por convenção de caminho (não é PHP/Composer PSR-4), não
há varredura de pacote por anotação (não é Spring `@ComponentScan`), não há registro em
container. `app.py` não faz `pkgutil.walk_packages`, `importlib.import_module` dinâmico,
`__init_subclass__` ou entry-points de setuptools:

```console
$ grep -rnE 'importlib|pkgutil|__import__|walk_packages|entry_points' --include='*.py' . | grep -v '^./.claude'
(nenhuma saída)
```

> **Portanto, para esta stack, o grafo de imports É o grafo de resolução.** A armadilha
> que a §6 alerta — tratar como morto o que a stack resolve por convenção — **não se aplica
> aqui**, porque não existe convenção que resolva. Ausência de import é ausência de
> alcançabilidade, e isso é conclusão, não atalho.

**Passo 1 (localizar entry points).** Precedência da §6.1: não há script no manifesto
(`requirements.txt` não expressa scripts), não há entry point empacotado. Sobra a convenção
da stack aplicada ao arquivo que instancia o servidor:

- `app.py` — instancia `Flask(__name__)` (`app.py:9`) e chama `app.run()` (`app.py:34`). **Entry point do servidor.**
- `seed.py` — tem `if __name__ == '__main__': seed_data()` (`seed.py:98-99`). **Segundo entry point**, script separado. O README o documenta como passo manual anterior ao boot.

**Passo 2 (conjunto alcançável).** Imports explícitos, transitivos, a partir de `app.py`:

```console
$ grep -rn -E '^\s*(from|import)\s' --include='*.py' . | grep -v '^./.claude'
app.py:3:from database import db
app.py:4:from routes.task_routes import task_bp
app.py:5:from routes.user_routes import user_bp
app.py:6:from routes.report_routes import report_bp
routes/task_routes.py:2:from database import db
routes/task_routes.py:3:from models.task import Task
routes/task_routes.py:4:from models.user import User
routes/task_routes.py:5:from models.category import Category
routes/user_routes.py:2:from database import db
routes/user_routes.py:3:from models.user import User
routes/user_routes.py:4:from models.task import Task
routes/report_routes.py:2:from database import db
routes/report_routes.py:3:from models.task import Task
routes/report_routes.py:4:from models.user import User
routes/report_routes.py:5:from models.category import Category
routes/report_routes.py:7:from utils.helpers import format_date, calculate_percentage
models/task.py:1:from database import db
models/user.py:1:from database import db
models/category.py:1:from database import db
models/__init__.py:1:from models.task import Task
models/__init__.py:2:from models.user import User
models/__init__.py:3:from models.category import Category
seed.py:2:from app import app, db
seed.py:3:from models.task import Task
seed.py:4:from models.user import User
seed.py:5:from models.category import Category
services/notification_service.py:1:import smtplib
services/notification_service.py:2:from datetime import datetime
```

```text
app.py  (entry point)
├── database                    ✓ alcançável
├── routes.task_routes          ✓ ──> models.task, models.user, models.category, database
├── routes.user_routes          ✓ ──> models.user, models.task, database
└── routes.report_routes        ✓ ──> models.*, database, utils.helpers
                                          └── utils.helpers  ✓ alcançável

seed.py (entry point próprio) ──> app  [reimporta todo o grafo acima]

services.notification_service   ✗ INALCANÇÁVEL — zero importadores
```

**Passo 3 (§6.3) — cada diretório que aparenta ser camada tem ao menos um símbolo alcançável?**

Esta é a regra decisiva para este projeto, aplicada com rigor:

| Diretório | Símbolo alcançável? | Evidência do mecanismo (import explícito) | Veredito |
|---|---|---|---|
| `models/` | **SIM** — `Task`, `User`, `Category` | `routes/task_routes.py:3-5`, `routes/user_routes.py:3-4`, `routes/report_routes.py:3-5`; as rotas entram pelo `app.py:4-6` | **Camada adotada** |
| `routes/` | **SIM** — `task_bp`, `user_bp`, `report_bp` | `app.py:4-6` importa os três; `app.py:18-20` registra os três | **Camada adotada** |
| `utils/` | **SIM** — `format_date`, `calculate_percentage` | `routes/report_routes.py:7` importa nominalmente os dois símbolos; o módulo é carregado no boot | **Camada adotada**, com ressalva forte (abaixo) |
| `services/` | **NÃO** — nenhum | busca literal exaustiva abaixo | **AP-26** |

Prova de inalcançabilidade de `services/`:

```console
$ grep -rn -E 'services|Notification|notification' --include='*.py' . | grep -v '^./.claude'
services/notification_service.py:4:class NotificationService:
services/notification_service.py:6:        self.notifications = []
services/notification_service.py:31:        self.notifications.append({
services/notification_service.py:43:    def get_notifications(self, user_id):
services/notification_service.py:45:        for n in self.notifications:
```

Todas as cinco ocorrências são **internas ao próprio arquivo**. Nenhum importador. Como o
único mecanismo de resolução do Python é o import explícito, e não existe import, o símbolo
**não é carregado em execução alguma** — nem por `app.py`, nem por `seed.py`.
`services/__init__.py` é vazio (1 byte), logo nem sequer reexporta.

> `services/` é o caso literal que a §6 descreve: *"Uma pasta chamada `services/` que nada
> resolve não é uma camada de serviço — é código morto com nome bonito."* Aciona
> `mvc-guidelines.md` §6 e vira finding antes de qualquer proposta de remoção — e ela carrega
> uma credencial SMTP versionada (`notification_service.py:10`), que o SKILL.md §Fase 2.6 manda
> reportar explicitamente.

**Passo 4 (§6.4) — referências a cada símbolo exportado FORA do módulo de origem.**
"Importar não é usar": é o número que evidencia AP-17.

| Símbolo | Módulo | Importado fora? | **Invocado** fora? |
|---|---|---|---|
| `Task`, `User`, `Category` | `models/*` | sim (3 rotas) | sim |
| `task_bp`, `user_bp`, `report_bp` | `routes/*` | sim (app.py) | sim |
| `db` | `database` | sim (4 arquivos) | sim |
| `format_date` | `utils.helpers` | **sim** (report_routes:7) | **NÃO — 0 chamadas** |
| `calculate_percentage` | `utils.helpers` | **sim** (report_routes:7) | **NÃO — 0 chamadas** |
| `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data` | `utils.helpers` | **não** | não |
| `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR` | `utils.helpers` | **não** | não |
| `NotificationService` | `services.notification_service` | **não** | não |
| `Task.validate_status`, `Task.validate_priority`, `Task.is_overdue`, `User.is_admin` | `models/*` | (métodos) | **NÃO — 0 chamadas** |

Comprovação de que os dois símbolos importados de `utils` nunca são chamados:

```console
$ grep -rn -E 'format_date|calculate_percentage' --include='*.py' . | grep -v '^./.claude'
utils/helpers.py:9:def format_date(date_obj):
utils/helpers.py:14:def calculate_percentage(part, total):
routes/report_routes.py:7:from utils.helpers import format_date, calculate_percentage
```

Três linhas: duas definições e um import. **Zero sítios de chamada.**

> **A distinção que a §6.3 impõe.** `utils/` **é** alcançável — a linha 7 de
> `report_routes.py` é import explícito, o mecanismo real desta stack, e o módulo entra na
> memória no boot. Logo a camada é **adotada**, e **não** vira AP-26. Mas dos seus 17
> símbolos públicos, 2 são importados e **0 invocados**: a camada existe, é carregada, e não
> presta serviço a ninguém. Isso é AP-17 (símbolo importado e não usado) + código morto —
> categoria diferente de AP-26, e é essa diferença que a regra de alcançabilidade preserva.
> Rebaixar `utils/` a AP-26 seria o erro simétrico ao de promover `services/` a camada.

**Passo 5 (§6.5) — arestas que violam a direção de dependência.** Levadas para a Fase 2 com
evidência: rotas chamando `db.session` direto (sem repositório), rotas contendo regra de
negócio (sem serviço), e `report_routes.py` hospedando CRUD de `Category`.

**Uma frase por módulo alcançável — responsabilidade acumulada:**

| Módulo | Responsabilidade acumulada |
|---|---|
| `app.py` | Instancia o app, **carrega configuração**, registra CORS, registra blueprints, **executa DDL**, e ainda serve 2 rotas próprias — 5 responsabilidades |
| `database.py` | Instancia o objeto `SQLAlchemy` — 1 responsabilidade, coesa |
| `models/task.py` | Mapeamento ORM **+ serialização** (`to_dict`) **+ validação** (`validate_*`) **+ regra de negócio** (`is_overdue`) — 4 responsabilidades |
| `models/user.py` | Mapeamento ORM **+ serialização** **+ hashing de credencial** **+ autorização** (`is_admin`) — 4 responsabilidades |
| `models/category.py` | Mapeamento ORM + serialização — 2 responsabilidades |
| `routes/task_routes.py` | HTTP **+ validação** **+ regra de negócio** **+ acesso a dados** **+ serialização** **+ log** — 6 responsabilidades |
| `routes/user_routes.py` | idem, **+ autenticação** — 7 responsabilidades |
| `routes/report_routes.py` | idem, **+ CRUD de outro agregado (Category)** — 7 responsabilidades |
| `utils/helpers.py` | Formatação + cálculo + validação + logging + constantes de domínio — 5 responsabilidades, **nenhuma exercida** |

Todos os módulos com >1 responsabilidade são candidatos a AP-06, conforme a §6.

**Arquitetura efetiva, em uma frase:**

> MVC **parcial e assimétrico**: existem Model (3 entidades alcançáveis) e uma View-como-rota
> (3 blueprints alcançáveis), mas o Controller está fundido à View e as camadas de serviço e
> de repositório **não existem** — a que tem o nome (`services/`) é inalcançável, e a que é
> alcançável (`utils/`) não é invocada por ninguém.

### Fato 7 — Inventário de endpoints

Enumerado a partir do `url_map` efetivo do Flask (§7: "enumere o resultado efetivo"), não do
`grep` dos decoradores — os dois coincidem aqui, mas o `url_map` é a fonte de verdade.

```console
  # METODO  PATH                             ENDPOINT (blueprint.handler)
  1 GET     /                                index
  2 GET     /categories                      reports.get_categories
  3 POST    /categories                      reports.create_category
  4 DELETE  /categories/<int:cat_id>         reports.delete_category
  5 PUT     /categories/<int:cat_id>         reports.update_category
  6 GET     /health                          health
  7 POST    /login                           users.login
  8 GET     /reports/summary                 reports.summary_report
  9 GET     /reports/user/<int:user_id>      reports.user_report
 10 GET     /tasks                           tasks.get_tasks
 11 POST    /tasks                           tasks.create_task
 12 DELETE  /tasks/<int:task_id>             tasks.delete_task
 13 GET     /tasks/<int:task_id>             tasks.get_task
 14 PUT     /tasks/<int:task_id>             tasks.update_task
 15 GET     /tasks/search                    tasks.search_tasks
 16 GET     /tasks/stats                     tasks.task_stats
 17 GET     /users                           users.get_users
 18 POST    /users                           users.create_user
 19 DELETE  /users/<int:user_id>             users.delete_user
 20 GET     /users/<int:user_id>             users.get_user
 21 PUT     /users/<int:user_id>             users.update_user
 22 GET     /users/<int:user_id>/tasks       users.get_user_tasks

TOTAL: 22 rotas efetivas (url_map, exclui static/HEAD/OPTIONS)
```

Tabela completa com os sete campos obrigatórios da §7:

| # | Método | Path | Handler | arquivo:linha (registro) | Autenticação | Corpo esperado | Efeito |
|---|---|---|---|---|---|---|---|
| 1 | GET | `/` | `index` | `app.py:26` | **nenhuma** | — | leitura |
| 2 | GET | `/health` | `health` | `app.py:22` | **nenhuma** | — | leitura |
| 3 | GET | `/tasks` | `get_tasks` | `routes/task_routes.py:11` | **nenhuma** | — | leitura |
| 4 | GET | `/tasks/<int:task_id>` | `get_task` | `routes/task_routes.py:65` | **nenhuma** | — | leitura |
| 5 | POST | `/tasks` | `create_task` | `routes/task_routes.py:85` | **nenhuma** | `title, description, status, priority, user_id, category_id, due_date, tags` | **escrita** |
| 6 | PUT | `/tasks/<int:task_id>` | `update_task` | `routes/task_routes.py:156` | **nenhuma** | idem (parcial) | **escrita** |
| 7 | DELETE | `/tasks/<int:task_id>` | `delete_task` | `routes/task_routes.py:225` | **nenhuma** | — | **destrutivo** |
| 8 | GET | `/tasks/search` | `search_tasks` | `routes/task_routes.py:240` | **nenhuma** | query: `q, status, priority, user_id` | leitura |
| 9 | GET | `/tasks/stats` | `task_stats` | `routes/task_routes.py:273` | **nenhuma** | — | leitura |
| 10 | GET | `/users` | `get_users` | `routes/user_routes.py:10` | **nenhuma** | — | leitura |
| 11 | GET | `/users/<int:user_id>` | `get_user` | `routes/user_routes.py:27` | **nenhuma** | — | leitura (**vaza hash de senha**) |
| 12 | POST | `/users` | `create_user` | `routes/user_routes.py:42` | **nenhuma** | `name, email, password, role` | **escrita privilegiada** (aceita `role:'admin'`) |
| 13 | PUT | `/users/<int:user_id>` | `update_user` | `routes/user_routes.py:92` | **nenhuma** | `name, email, password, role, active` | **escrita privilegiada** (permite auto-promoção a admin) |
| 14 | DELETE | `/users/<int:user_id>` | `delete_user` | `routes/user_routes.py:134` | **nenhuma** | — | **destrutivo em cascata** (apaga as tasks do usuário) |
| 15 | GET | `/users/<int:user_id>/tasks` | `get_user_tasks` | `routes/user_routes.py:153` | **nenhuma** | — | leitura |
| 16 | POST | `/login` | `login` | `routes/user_routes.py:185` | é o próprio login | `email, password` | leitura (**devolve hash de senha**) |
| 17 | GET | `/reports/summary` | `summary_report` | `routes/report_routes.py:12` | **nenhuma** | — | leitura |
| 18 | GET | `/reports/user/<int:user_id>` | `user_report` | `routes/report_routes.py:103` | **nenhuma** | — | leitura |
| 19 | GET | `/categories` | `get_categories` | `routes/report_routes.py:157` | **nenhuma** | — | leitura |
| 20 | POST | `/categories` | `create_category` | `routes/report_routes.py:167` | **nenhuma** | `name, description, color` | **escrita** |
| 21 | PUT | `/categories/<int:cat_id>` | `update_category` | `routes/report_routes.py:190` | **nenhuma** | `name, description, color` | **escrita** |
| 22 | DELETE | `/categories/<int:cat_id>` | `delete_category` | `routes/report_routes.py:211` | **nenhuma** | — | **destrutivo** |

**Armadilhas da §7, ambas verificadas:**

1. **Rotas registradas em mais de um lugar — CONFIRMADO.** 20 rotas vêm dos 3 blueprints,
   mas **2 são declaradas inline no bootstrap** (`app.py:22` `/health` e `app.py:26` `/`).
   A §7 avisa que as inline "são as mais propensas a saltar camadas" — e de fato: `/health`
   (`app.py:24`) monta a resposta com `datetime.datetime.now()` direto no bootstrap.
2. **Rotas montadas dinamicamente:** nenhuma. Todos os 22 registros são decoradores
   estáticos. O inventário é completo, sem lacuna a declarar na §9.

**Rotas destrutivas** (4, tratadas por último no baseline): #7, #14, #21(update não), #22 —
precisamente `DELETE /tasks/<id>`, `DELETE /users/<id>`, `DELETE /categories/<id>`.
**Rotas privilegiadas:** #12 e #13 — criam/alteram `role`, sem qualquer verificação.

### Fato 8 — Baseline de comportamento

Capturado **por último, com o código intocado** (§8 + validation-protocol §2).

**Comando de boot** (validation-protocol §1, precedência): não há script no manifesto
(fonte 1 ausente), não há entry point empacotado (fonte 2 ausente); a fonte 3 (convenção da
stack sobre o arquivo que instancia o servidor) e a fonte 4 (README) **concordam** em
`python app.py`. Host `0.0.0.0`, porta `5000`, **nenhuma variável de ambiente exigida**
(toda a config é literal em `app.py:11-13` — o que é finding, e significa que o falso
vermelho "boot falha após TR-01 por env var ausente" da §8 será um risco real na Fase 3).

```console
$ python seed.py          # estado conhecido antes da captura
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks

$ python app.py
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.100.120:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 505-623-803
```

**"Subiu com sucesso" pelos três critérios observáveis da §3** — nenhum deles usa string de
log de framework:

```console
--- (1) porta escutando? ---
LISTEN 0  128  0.0.0.0:5000  0.0.0.0:*  users:(("python",pid=747547,fd=7),…)
--- (2) processo vivo? (4s depois) ---
747500 747545 747547
--- (3) primeira requisicao respondida? ---
HTTP 200
```

Captura dos 22 endpoints, destrutivas por último e só sobre dado descartável criado pelo
próprio roteiro (`smoke@baseline.test`, `Smoke Cat`, `Smoke Task descartavel`):

```console
$ python capture_baseline.py "$BASELINE_PATH"
22 endpoints capturados -> /home/wesley/…/reports/baseline-task-manager-api.json
  GET    /                                  200  application/json
  GET    /health                            200  application/json
  GET    /tasks                             200  application/json
  GET    /tasks/1                           200  application/json
  GET    /tasks/search?q=API&status=pending 200  application/json
  GET    /tasks/stats                       200  application/json
  GET    /users                             200  application/json
  GET    /users/1                           200  application/json
  GET    /users/1/tasks                     200  application/json
  GET    /categories                        200  application/json
  GET    /reports/summary                   200  application/json
  GET    /reports/user/1                    200  application/json
  POST   /login                             200  application/json
  POST   /users                             201  application/json
  PUT    /users/4                           200  application/json
  POST   /categories                        201  application/json
  PUT    /categories/5                      200  application/json
  POST   /tasks                             201  application/json
  PUT    /tasks/11                          200  application/json
  DELETE /tasks/11                          200  application/json
  DELETE /categories/5                      200  application/json
  DELETE /users/4                           200  application/json
```

Resumo (a forma que o `report-template.md` reproduz no relatório):

```console
total M = 22
por metodo: {'GET': 12, 'POST': 4, 'PUT': 3, 'DELETE': 3}
por status: {200: 19, 201: 3}
por media : {'application/json': 22}
com shape : 22 | com selector: 0
```

Todos os 22 corpos são estruturados (`application/json`), logo **todos** foram registrados com
`shape` — chaves e tipos, nunca valores voláteis. Nenhum endpoint exigiu `selector`.

Amostra do artefato gravado:

```json
[
  {
    "method": "GET",
    "path": "/",
    "status": 200,
    "media": "application/json",
    "shape": { "message": "string", "version": "string" }
  },
  {
    "method": "GET",
    "path": "/tasks",
    "status": 200,
    "media": "application/json",
    "shape": [ { "category_id": "number", "category_name": "string", "created_at": "string",
                 "description": "string", "due_date": "string", "id": "number",
                 "overdue": "boolean", "priority": "number", "status": "string",
                 "tags": ["<empty>"], "title": "string", "updated_at": "string",
                 "user_id": "number", "user_name": "string" } ]
  }
]
```

**Endpoints pré-existentes quebrados: NENHUM.** Os 22 respondem 2xx à requisição
representativa. `M = 22`.

> Nota que a Fase 2 vai usar: sob requisição **inválida** (tipo errado), 3 desses endpoints
> respondem 500 com `text/html` do debugger. Isso não os torna *pré-existente quebrado* —
> a requisição representativa é válida e responde 2xx. Entra na Fase 2 como finding de
> tratamento de erro, não como lacuna de baseline.

Servidor derrubado ao fim (§3, última instrução — evita o falso vermelho mais frequente):

```console
$ pkill -f "python app.py"
$ curl --max-time 2 http://127.0.0.1:5000/health
curl_rc=7 (7 = conexao recusada = servidor derrubado)
```

---

## 3. Fatos que não se determinaram (§9)

**Nenhum.** Os oito fatos foram determinados com evidência executada:

| # | Fato | Determinado | Como |
|---|---|---|---|
| 1 | Linguagem | ✓ Python | contagem de extensões ∩ manifesto |
| 2 | Framework efetivo | ✓ Flask 3.0.0 | declarado ∩ resolvido, com 3 candidatos a AP-26 isolados |
| 3 | Versão real do runtime | ✓ 3.12.3 | **executado** (`python3 --version`) — AP-16 **verificável** |
| 4 | Persistência | ✓ SQLite/SQLAlchemy, 3 tabelas | 4 sinais cruzados + PRAGMA no banco real |
| 5 | Domínio | ✓ gestão de tarefas | 3 vocabulários coerentes |
| 6 | Arquitetura efetiva | ✓ MVC parcial | grafo de resolução por import explícito, mecanismo confirmado por ausência de `importlib`/`pkgutil`/entry-points |
| 7 | Endpoints | ✓ 22 | `url_map` efetivo; 0 rotas dinâmicas → sem lacuna de smoke test |
| 8 | Baseline | ✓ 22/22 capturados | boot real + 22 requisições, gravado em `BASELINE_PATH` |

Consequência de §9 sobre "aplicação que não sobe": **não se aplica** — a aplicação sobe e
responde. A Fase 3 tem critério de validação executável (`M = 22`).

---

## 4. Saída da Fase 1

```console
PHASE 1: PROJECT ANALYSIS
─────────────────────────────────────────────
Language      : Python (runtime in use: 3.12.3, obtido por `python3 --version`)
Framework     : Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 + Flask-CORS 4.0.0 (declarados E resolvidos)
Package mgr   : requirements.txt (pip)
Database      : SQLite (instance/tasks.db, via SQLAlchemy 2.0.52) · 3 tabelas
Domain        : Gestão de tarefas — tasks atribuídas a users, agrupadas por categories, com relatórios de produtividade
Entry points  : app.py (servidor)  ·  seed.py (script separado, ponto de entrada próprio, NÃO alcançável a partir de app.py)
Resolution    : explicit import (Python não tem autoload por convenção; nenhum container, nenhuma varredura de pacote)
Architecture  : MVC parcial — Model(3)+View-como-rota(3 blueprints) alcançáveis; SEM camada de serviço efetiva, SEM repositório; utils/ alcançável porém 100% não-invocado; services/ INALCANÇÁVEL
Source files  : 15 files · 1158 LOC
Endpoints     : 22 mapped · baseline captured (22 responses)
Baseline SHA  : f580ee5
Baseline file : /home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/baseline-task-manager-api.json
─────────────────────────────────────────────
```

**Escritas desta fase:** exclusivamente `BASELINE_PATH`. Nenhum arquivo do projeto tocado —
confirmado no §5 abaixo.

## 5. Prova de que a Fase 1 não escreveu em código do projeto

```console
$ git status --porcelain
?? reports/baseline-task-manager-api.json
```

Único caminho alterado é o artefato aditivo previsto. `task-manager-api/` intacto.
