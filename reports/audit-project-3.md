# Auditoria de Arquitetura — `task-manager-api`

> Fase 2 de `/refactor-arch`. Auditoria somente leitura. Nenhum arquivo do projeto foi
> modificado. Todo `arquivo:linha` foi obtido por leitura direta nesta execução.

## Contexto

| Item | Valor |
|---|---|
| Linguagem | Python (runtime do ambiente: **3.12.3**, obtido executando `python3 --version`) |
| Framework | Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 + Flask-CORS 4.0.0 |
| Persistência | SQLAlchemy 2.0.52 sobre SQLite (`instance/tasks.db`) · 3 tabelas |
| Domínio | Gestão de tarefas — *tasks* atribuídas a *users*, agrupadas por *categories*, com relatórios de produtividade |
| Arquivos-fonte / LOC | 15 arquivos, 1158 linhas |
| Endpoints | 22 — baseline capturado em 22 respostas |
| Commit de baseline | `f580ee5` |

### Arquitetura efetiva

O mecanismo de resolução desta stack é **import explícito**: Python não tem autoload por
convenção, e a varredura confirmou que o projeto não usa nenhum mecanismo alternativo — não há
`importlib`, `pkgutil.walk_packages`, `__import__` dinâmico nem entry-points de setuptools em
arquivo algum. Para este projeto, portanto, o grafo de imports **é** o grafo de resolução, e
ausência de import é ausência de alcançabilidade — conclusão, não atalho.

A partir do entry point `app.py`, o grafo alcança: `database` (o objeto `SQLAlchemy`), os três
blueprints de `routes/`, os três models de `models/`, e `utils.helpers`. O segundo entry point,
`seed.py`, é script separado com `if __name__ == '__main__'` próprio — não é alcançável a partir
de `app.py`; a relação é inversa (`seed.py:2` importa `app`), e o README o documenta como passo
manual anterior ao boot.

Das quatro pastas com nome de camada, **três são alcançáveis e uma não é**. `models/` e `routes/`
são adotadas sem ressalva. `utils/` é adotada porque `routes/report_routes.py:7` importa
nominalmente `format_date` e `calculate_percentage` — o módulo entra na memória no boot —, mas
**nenhum dos dois símbolos é invocado em lugar algum**, e 14 dos seus 16 símbolos públicos não são
sequer importados: a camada existe, é carregada, e não presta serviço a ninguém (F-010, AP-17).
`services/` é **inalcançável**: a busca literal por `services`/`Notification`/`notification` em
todo o projeto devolve apenas ocorrências internas ao próprio `services/notification_service.py`,
e `services/__init__.py` é vazio. É AP-26 (F-020), e carrega uma credencial SMTP versionada que
este relatório registra **antes** de qualquer proposta de remoção, conforme `mvc-guidelines.md` §6.

O resultado é um MVC **parcial e assimétrico**: existe Model e existe uma View-como-rota, mas o
Controller está fundido à View, e as camadas de serviço e de repositório não existem — a que tem
o nome é morta, e a que é viva não é chamada. Cada módulo de rota acumula seis ou sete
responsabilidades no mesmo corpo: HTTP, validação, regra de negócio, acesso a dados, serialização
e log — e `report_routes.py` ainda hospeda o CRUD completo de um segundo agregado (`Category`).

> **Nota sobre `mvc-guidelines.md` §1, regra 4.** As pastas de camada preexistentes **não**
> constituem "stack que já materializa as responsabilidades": o gatilho daquela regra não é
> alcançabilidade, e sim a existência de uma **convenção declarada** pelo framework — raiz de
> autoload, pacote-base varrido ou estrutura imposta. Flask não declara nenhuma. Este é
> literalmente o caso que a regra exclui: *"um monólito cujos módulos são apenas alcançáveis por
> import explícito não tem convenção a adotar, por mais que seus arquivos tenham nome de camada"*.
> A Fase 3 cai, portanto, na §4 **precedência 1** — convenção já praticada e alcançável dentro do
> próprio projeto —, o que significa preservar os nomes `models/`, `routes/`, `utils/` e criar
> apenas as responsabilidades ausentes.

### Baseline de comportamento

| Método | Endpoints | Status codes observados |
|---|---|---|
| GET | 12 | 200 ×12 |
| POST | 4 | 200 ×1 · 201 ×3 |
| PUT | 3 | 200 ×3 |
| DELETE | 3 | 200 ×3 |
| **Total (`M`)** | **22** | 200 ×19 · 201 ×3 |

Media type: `application/json` em 22/22 — todos os corpos são estruturados, logo todos foram
registrados com `shape` (chaves e tipos, nunca valores voláteis) e **nenhum** exigiu `selector`.

Baseline completo, com media type e forma do corpo por endpoint, em
`/home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/baseline-task-manager-api.json`.

Pré-existentes quebrados: **nenhum** — os 22 respondem 2xx à requisição representativa.
Não enumeráveis, fora de `M`: **nenhum** — as 22 rotas são decoradores estáticos, sem montagem
dinâmica; o inventário é completo.

> Sob requisição **inválida**, três desses endpoints respondem 500 `text/html` (F-013). Isso não
> os torna *pré-existente quebrado*: a requisição representativa é válida e responde 2xx. Entra
> como finding de tratamento de erro, não como lacuna de baseline.

`M = 22` é o denominador de toda onda da Fase 3: onda verde exige **22/22** conformes.

## Sumário

| Severidade | Findings | Ocorrências |
|---|---|---|
| CRITICAL | 4 | 38 |
| HIGH | 5 | 56 |
| MEDIUM | 9 | 103 |
| LOW | 5 | 55 |
| **Total** | **23** | **252** |

**Um finding por causa, não por ocorrência.** "Ocorrências" conta os `arquivo:linha` distintos
citados dentro de cada finding — 34 chamadas deprecated são **um** finding (F-016) com 34
ocorrências, não 34 findings. Detalhamento:

| Finding | Ocorrências | | Finding | Ocorrências |
|---|---|---|---|---|
| F-001 | 3 literais sensíveis | | F-013 | 12 `except:` pelados |
| F-002 | 1 mapeamento × 4 rotas = 5 | | F-014 | 4 divergências de contrato |
| F-003 | 2 definições + 6 chamadas = 8 | | F-015 | 4 listagens |
| F-004 | 22 rotas sem verificação | | F-016 | 18 `utcnow()` + 16 `Query.get()` = 34 |
| F-005 | 3 imports + 25 sessões + 1 consulta = 29 | | F-017 | 1 registro de middleware |
| F-006 | 14 blocos de regra no handler | | F-018 | 1 endpoint de autenticação |
| F-007 | 1 DDL + 4 lacunas de schema = 5 | | F-019 | 11 `print()` |
| F-008 | 3 escritas não transacionadas | | F-020 | 1 camada + 14 símbolos + 4 métodos + 6 imports + 3 deps = 28 |
| F-009 | 1 root + 1 singleton + 3 imports = 5 | | F-021 | 6 literais fora de blocos AP-12 |
| F-010 | 21 cópias + 6 abstrações mortas = 27 | | F-022 | 4 rotas + 5 abreviações = 9 |
| F-011 | 16 invariantes inline | | F-023 | 1 manifesto |
| F-012 | 4 endpoints com N+1 | | | |

Cobertura da varredura: os 28 APs do catálogo foram percorridos na ordem do índice.
23 viraram finding; 5 estão na seção "O que não foi encontrado". 23 + 5 = 28.

---

## Findings

### [CRITICAL] F-001 — Segredo de assinatura, credencial SMTP e debug ligado, todos literais no código

- **Anti-pattern:** AP-02 · **Transformação:** TR-01 · **Onda:** 1
- **Arquivo:** `app.py:13`, `app.py:34`, `services/notification_service.py:7-10`
- **Evidência:**

```python
# app.py:11-15
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super-secret-key-123'

CORS(app)
```

```python
# app.py:33-34
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

```python
# services/notification_service.py:7-10
        self.email_host = 'smtp.gmail.com'
        self.email_port = 587
        self.email_user = 'taskmanager@gmail.com'
        self.email_password = 'senha123'
```

Confirmação de que nenhum arquivo do projeto lê o ambiente para nenhuma dessas chaves —
requisito de evidência mínima do AP:

```console
$ grep -rnE 'os\.environ|getenv|load_dotenv|dotenv' --include='*.py' . | grep -v '^./.claude'
  NENHUMA leitura de variavel de ambiente em todo o projeto
```

- **Descrição:** três valores sensíveis fixados em literal, sem precedência de ambiente em ponto
  algum. O `SECRET_KEY` tem nome que sugere uso produtivo (`super-secret-key-123`), não é
  placeholder declaradamente inválido, e **nunca é referenciado em nenhum outro ponto do projeto**
  — é um segredo versionado que não protege nada, o reforço de confiança que o próprio AP nomeia.
  O `debug=True` aparece junto de `host='0.0.0.0'`, isto é, bind em todas as interfaces. A
  credencial SMTP vive dentro da camada inalcançável (F-020), o que **não** a torna inofensiva:
  ela está no histórico do repositório.
- **Impacto:** verificado em execução. Com `debug=True`, qualquer 500 devolve o console
  interativo do Werkzeug, com `EVALEX = true`:

```console
$ curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:5000/tasks/search?priority=abc"
500
$ curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:5000/?__debugger__=yes&cmd=resource&f=debugger.js"
200
```

```html
    <script>
      var CONSOLE_MODE = false,
          EVALEX = true,
          EVALEX_TRUSTED = false,
          SECRET = "mOqOIPsn3ruTqb0O5npC";
    </script>
```

  Um chamador anônimo na rede alcança um endpoint que estoura 500 (F-013 mostra três caminhos
  triviais) e recebe de volta um console de execução de código no processo do servidor, exposto
  em `0.0.0.0:5000`.
- **Correção esperada:** módulo de configuração que lê o ambiente com fail-fast no boot, `.env.example`
  publicado, `debug` e `host` derivados de variável, e os três segredos rotacionados fora do código.
- **Confiança:** ALTA

---

### [CRITICAL] F-002 — Hash de senha projetado na resposta de quatro endpoints

- **Anti-pattern:** AP-03 · **Transformação:** TR-04 · **Onda:** 1
- **Arquivo:** `models/user.py:16-25`
- **Evidência:**

```python
# models/user.py:16-25
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }
```

**Reforço decisivo** — outra cópia do mesmo mapeamento, no mesmo projeto, **omite** o campo, o
que caracteriza exposição acidental e não decisão de contrato:

```python
# routes/user_routes.py:15-23  (GET /users)
        user_data = {
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'role': u.role,
            'active': u.active,
            'created_at': str(u.created_at),
            'task_count': len(u.tasks)
        }
```

- **Descrição:** `User.to_dict()` projeta a coluna de credencial. Ela alimenta **quatro** rotas,
  nenhuma delas atrás de verificação de identidade: `routes/user_routes.py:33` (GET /users/<id>),
  `routes/user_routes.py:85-86` (POST /users), `routes/user_routes.py:129` (PUT /users/<id>) e
  `routes/user_routes.py:209` (POST /login, dentro da chave `user`).
- **Impacto:** confirmado em execução — um chamador anônimo lê o hash de qualquer usuário:

```console
$ curl -s http://localhost:5000/users/1
{
  "email": "joao@email.com",
  "id": 1,
  "name": "João Silva",
  "password": "81dc9bdb52d04dc20036dbd8313ed055",
  "role": "admin",
  …
}
```

  Combinado com F-003 (MD5 sem salt), o hash é reversível por rainbow table, então isto não é
  vazamento de derivação irreversível: é vazamento de senha. `81dc9bdb52d04dc20036dbd8313ed055`
  é exatamente `MD5("1234")`.
- **Correção esperada:** DTO de saída com allowlist de projeção, sem a coluna de credencial, em
  todas as rotas que serializam `User`.
- **Confiança:** ALTA

---

### [CRITICAL] F-003 — Senha derivada por MD5 sem salt e verificada por igualdade

- **Anti-pattern:** AP-04 · **Transformação:** TR-03 · **Onda:** 1
- **Arquivo:** `models/user.py:27-32`
- **Evidência:**

```python
# models/user.py:27-32
    def set_password(self, pwd):

        self.password = hashlib.md5(pwd.encode()).hexdigest()

    def check_password(self, pwd):
        return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

- **Descrição:** hash rápido de propósito geral da biblioteca padrão, sem salt e sem fator de
  custo, aplicado direto à senha; verificação por comparação de igualdade simples. O consumidor
  foi verificado antes de classificar — não é integridade nem deduplicação: `check_password` é
  chamado exclusivamente pelo fluxo de autenticação, em `routes/user_routes.py:201`.
  `set_password` é chamado em `routes/user_routes.py:77`, `routes/user_routes.py:117` e
  `seed.py:19,26,33`.
- **Impacto:** verificação decisiva executada — o digest observado no baseline é reproduzível
  offline em tempo constante:

```console
$ python3 -c "import hashlib; print(hashlib.md5(b'1234').hexdigest())"
81dc9bdb52d04dc20036dbd8313ed055
```

  O valor bate com o `password` que `GET /users/1` devolve (F-002). Qualquer pessoa que leia a
  resposta pública recupera a senha em texto claro por consulta a tabela pré-computada. Não há
  dependência de hashing lento declarada no manifesto — nem `bcrypt`, nem `argon2`, nem
  `werkzeug.security` importado —, então este projeto não tem sequer a arquitetura pretendida.
- **Correção esperada:** derivação por primitiva lenta com salt e fator de custo, e migração dos
  hashes existentes por reidratação no próximo login bem-sucedido.
- **Confiança:** ALTA

---

### [CRITICAL] F-004 — As 22 rotas, incluindo destrutivas e privilegiadas, sem nenhuma verificação de identidade

- **Anti-pattern:** AP-05 (e AP-24, que TR-05 fecha junto) · **Transformação:** TR-05 · **Onda:** 1
- **Arquivo:** `routes/user_routes.py:185-211`, `routes/user_routes.py:134-151`, `routes/user_routes.py:92-132`
- **Evidência** — a credencial emitida pelo login é derivada de forma previsível do identificador
  do sujeito, sem assinatura e sem expiração:

```python
# routes/user_routes.py:207-211
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': 'fake-jwt-token-' + str(user.id)
    }), 200
```

A rota destrutiva em cascata vai do registro ao acesso a dados sem passar por ponto algum de
verificação:

```python
# routes/user_routes.py:134-143
@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    for t in tasks:
        db.session.delete(t)
```

A rota privilegiada aceita o papel vindo do corpo, de chamador anônimo:

```python
# routes/user_routes.py:119-122
    if 'role' in data:
        if data['role'] not in ['user', 'admin', 'manager']:
            return jsonify({'error': 'Role inválido'}), 400
        user.role = data['role']
```

- **Descrição:** o inventário da Fase 1 registra **22 de 22 rotas com autenticação "nenhuma"** —
  não há middleware, `before_request`, decorator de proteção ou verificação inline em nenhum
  handler. O token emitido é a concatenação de uma constante com o `id`, portanto forjável por
  qualquer um que saiba contar, e **nada no projeto o valida**: não existe leitura de
  `Authorization` em arquivo algum.
- **Sinal correlato de alto valor, confirmado:** o papel está modelado no schema
  (`models/user.py:12`, coluna `role`) e o método que o consultaria existe
  (`models/user.py:34-38`, `is_admin`), mas **nenhuma decisão de autorização o chama** — 0
  referências em todo o projeto. A autorização foi projetada e não implementada, e o campo dá
  falsa segurança a quem lê o model.
- **Impacto:** um chamador anônimo apaga qualquer usuário e, em cascata não transacionada
  (F-008), todas as tasks dele; cria um usuário `admin` (`POST /users` aceita `role`,
  `routes/user_routes.py:71-78`); ou promove a si mesmo a `admin` via `PUT /users/<id>`. Também
  lê a base inteira de usuários com hash de senha (F-002). Combinado com CORS irrestrito (F-017),
  qualquer página web executa essas escritas a partir do browser da vítima.
- **Correção esperada:** credencial assinada com expiração emitida no login, ponto de verificação
  aplicado antes do handler, e negação por padrão nas rotas de escrita, destrutivas e de leitura
  de terceiros — com controle de taxa no próprio endpoint de autenticação (F-020).
- **Confiança:** ALTA

---

### [HIGH] F-005 — Rotas manipulam a sessão do ORM e montam consultas, sem repositório nem serviço interposto

- **Anti-pattern:** AP-13 · **Transformação:** TR-06 · **Onda:** 2
- **Arquivo:** `routes/task_routes.py:2`, `routes/user_routes.py:2`, `routes/report_routes.py:2` (imports) e 33 manipulações nos handlers
- **Evidência** — o import da sessão como singleton de módulo, nos três arquivos de rota:

```python
# routes/task_routes.py:1-7
from flask import Blueprint, request, jsonify
from database import db
from models.task import Task
from models.user import User
from models.category import Category
```

E a manipulação dela dentro do handler, com transação decidida no controller:

```python
# routes/task_routes.py:146-154
    try:
        db.session.add(task)
        db.session.commit()
        print(f"Task criada: {task.id} - {task.title}")
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar task: {str(e)}")
        return jsonify({'error': 'Erro ao criar task'}), 500
```

Consulta construída no handler, também:

```python
# routes/task_routes.py:247-264
    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )
    if status:
        tasks = tasks.filter(Task.status == status)
    if priority:
        tasks = tasks.filter(Task.priority == int(priority))
```

- **Descrição:** o contra-exemplo do AP foi aplicado antes de escrever esta entrada. A isenção
  "o handler alcança a persistência pela API de domínio que o framework oferece" **não** vale
  aqui: os handlers não se limitam a usar o model como porta de dados — eles **montam consulta**
  (`task_routes.py:247-264`) e **controlam transação** (`db.session.add/commit/rollback/delete`).
  Ocorrências de manipulação direta de sessão: `task_routes.py:147,148,152,218,222,232,233,237`,
  `user_routes.py:81,82,88,128,131,142,145,146,150`,
  `report_routes.py:183,184,187,205,208,218,219,222`. Não existe camada intermediária alcançável
  a ser saltada — ela simplesmente não existe.
- **Inversão típica, encontrada e relatada como uma causa só:** a decisão de **serialização de
  API** vive no model (`models/task.py:23-36`, `models/user.py:16-25`, `models/category.py:13-21`
  — `to_dict()`) e a decisão de **transação** vive no controller (as 25 linhas acima). As duas
  estão exatamente trocadas.
- **Impacto:** nenhuma regra de leitura ou escrita é exercitável sem subir um servidor HTTP e
  abrir um banco. Trocar SQLite por outro motor, ou introduzir cache, exige editar os 3 arquivos
  de rota. Não há fronteira única onde aplicar política transacional — e é exatamente por isso
  que F-008 existe.
- **Correção esperada:** repositórios como único lugar que conhece o ORM, serviços como único
  lugar que decide, controllers reduzidos a tradução protocolo↔domínio.
- **Confiança:** ALTA

---

### [HIGH] F-006 — Regra de domínio escrita dentro dos handlers de protocolo

- **Anti-pattern:** AP-08 · **Transformação:** TR-07 · **Onda:** 2
- **Arquivo:** `routes/task_routes.py:30-39`, `routes/report_routes.py:53-68`, e mais 12 blocos
- **Evidência** — a regra "task atrasada", que é decisão de domínio pura, escrita dentro do
  handler HTTP:

```python
# routes/task_routes.py:30-39
            if t.due_date:
                if t.due_date < datetime.utcnow():
                    if t.status != 'done' and t.status != 'cancelled':
                        task_data['overdue'] = True
                    else:
                        task_data['overdue'] = False
                else:
                    task_data['overdue'] = False
            else:
                task_data['overdue'] = False
```

Agregação de produtividade — regra de negócio — montada no handler:

```python
# routes/report_routes.py:53-68
    users = User.query.all()
    user_stats = []
    for u in users:
        user_tasks = Task.query.filter_by(user_id=u.id).all()
        total = len(user_tasks)
        completed = 0
        for t in user_tasks:
            if t.status == 'done':
                completed = completed + 1
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0
        })
```

- **Descrição:** aplicado o teste de pertencimento de `mvc-guidelines.md` §2.1 — *"a regra
  continua verdadeira se o protocolo mudar de HTTP para uma fila de mensagens?"* — a resposta é
  **sim** para todos estes blocos, logo pertencem ao service. O contra-exemplo do AP ("handler de
  CRUD puro que delega e mapeia") não se aplica: não há a quem delegar. Demais ocorrências:
  regra de atraso em `task_routes.py:71-80`, `task_routes.py:283-287`, `user_routes.py:171-180`,
  `report_routes.py:33-43`, `report_routes.py:132-135`; taxa de conclusão em
  `task_routes.py:296`, `report_routes.py:151`; contagem por status em `task_routes.py:275-279`,
  `report_routes.py:19-28`, `report_routes.py:119-130`; classificação de prioridade alta em
  `report_routes.py:129`; efeito de cascata de negócio em `user_routes.py:140-142`.
- **Sinal correlato, presente:** o handler inspeciona a **forma** do valor retornado para decidir
  o status code — `if task:` → 200 senão 404 (`task_routes.py:68,83`), `if not user:` → 404
  (`user_routes.py:30-31,95-96,137-138,156-157`, `report_routes.py:106-107`). É regra de domínio
  codificada como formato de retorno, e o catálogo a nomeia como o sintoma mais confiável de que
  não existe service.
- **Impacto:** a definição de "atrasada" está em 7 lugares e já tem uma variante silenciosamente
  divergente — `models/task.py:50-60` implementa exatamente a mesma regra e **ninguém a chama**
  (F-010). Qualquer mudança de política (por exemplo, tolerância de um dia) exige editar 7 blocos
  e acertar todos; errar um produz relatório e listagem discordando sobre a mesma task.
- **Correção esperada:** regra e efeito colateral movidos para serviços de domínio; handlers
  reduzidos a parse, chamada e mapeamento de resultado.
- **Confiança:** ALTA

---

### [HIGH] F-007 — DDL executada no boot, sem migração, e schema sem as restrições que o domínio exige

- **Anti-pattern:** AP-21 · **Transformação:** TR-16 · **Onda:** 2
- **Arquivo:** `app.py:30-31`
- **Evidência:**

```python
# app.py:30-34
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

- **Descrição:** a criação de schema roda em **escopo de módulo**, fora da guarda
  `if __name__ == '__main__'` — portanto é efeito colateral de **qualquer** import de `app`,
  inclusive o que `seed.py:2` faz. Não há ferramenta de migração no manifesto: nem Alembic, nem
  Flask-Migrate. `db.create_all()` só cria tabelas ausentes e **nunca altera coluna existente**.
- **Sinal estrutural adicional, verificado no banco real e reportado junto porque a mesma
  transformação resolve:**

```console
--- tasks ---
  status          VARCHAR(50)     notnull=0
  priority        INTEGER         notnull=0
  FKs: [('category_id','categories','id'), ('user_id','users','id')]
  indices: NENHUM

PRAGMA foreign_keys (enforcement em runtime): 0
```

  - **Chaves estrangeiras declaradas e NÃO aplicadas.** `PRAGMA foreign_keys = 0` é o default do
    SQLite e nenhum listener o liga. A integridade referencial é decorativa — e é o que torna
    F-008 explorável.
  - **Nenhum CHECK** sobre `status` (4 valores fechados no código) nem sobre `priority` (faixa
    1..5 no código). A invariante de domínio existe só em Python, o que é o outro lado de F-011.
  - **Nenhum índice** em `tasks.user_id`, `tasks.category_id`, `tasks.status` — exatamente as três
    colunas que as rotas filtram (`task_routes.py:258,261,264`, `report_routes.py:163`).
  - `status`, `priority`, `active`, `created_at` são `nullable` embora tenham default no ORM: o
    default é aplicado pelo Python, não pelo schema, então escrita por fora da aplicação grava nulo.
- **Impacto nomeado:** como o comando só cria o que falta, **qualquer evolução de coluna passa a
  exigir apagar o banco**. O projeto não tem caminho de evolução de schema — esse é o dano real,
  maior que o incômodo de criar tabela no boot.
- **Nota a favor do projeto:** o seed **não** está no mesmo corpo que cria o schema. `seed.py` é
  script separado, com guarda `if __name__ == '__main__'` (`seed.py:98`), e não roda
  incondicionalmente. A metade "dados de demonstração inseridos em qualquer ambiente" do sinal do
  AP **não** se aplica aqui, e não a reporto.
- **Correção esperada:** migração inicial versionada, DDL fora do caminho de boot, e as
  constraints (FK aplicada, CHECK de vocabulário e de faixa, índices nas colunas de filtro)
  declaradas no schema.
- **Confiança:** ALTA

---

### [HIGH] F-008 — Escritas relacionadas sem fronteira transacional, com órfãos garantidos pela FK não aplicada

- **Anti-pattern:** AP-11 · **Transformação:** TR-10 · **Onda:** 2
- **Arquivo:** `routes/user_routes.py:140-151`, `routes/report_routes.py:211-223`, `routes/user_routes.py:67-82`
- **Evidência** — a deleção em cascata acontece **fora** do bloco protegido; o `rollback` só cobre
  a última operação:

```python
# routes/user_routes.py:140-151
    tasks = Task.query.filter_by(user_id=user_id).all()
    for t in tasks:
        db.session.delete(t)

    try:
        db.session.delete(user)
        db.session.commit()
        print(f"Usuário deletado: {user_id}")
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200
    except:
        db.session.rollback()
        return jsonify({'error': 'Erro ao deletar'}), 500
```

Deleção que remove o principal e deixa dependentes órfãos, em schema cuja integridade
referencial não é aplicada (F-007):

```python
# routes/report_routes.py:211-223
@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    try:
        db.session.delete(cat)
        db.session.commit()
        return jsonify({'message': 'Categoria deletada'}), 200
```

Par verificação/consumação separado, sem atomicidade:

```python
# routes/user_routes.py:67-69   (verificação)
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({'error': 'Email já cadastrado'}), 409
# routes/user_routes.py:80-82   (consumação, 12 linhas depois)
    try:
        db.session.add(user)
        db.session.commit()
```

- **Descrição:** três formas do mesmo defeito — ausência de unidade de trabalho explícita.
  O contra-exemplo foi aplicado: as escritas **não** são idempotentes e independentes (apagar
  tasks e apagar o dono produzem estado inválido se apenas uma ocorrer), **não** há compensação
  no caminho de erro, e o banco **não** declara a constraint que tornaria a corrida impossível —
  `PRAGMA foreign_keys = 0` (F-007).
- **Cenário concreto que produz o estado inválido:** `DELETE /categories/3` remove a linha de
  `categories`; as 2 tasks com `category_id = 3` permanecem apontando para uma categoria
  inexistente. Como a FK não é aplicada, o banco aceita. Na requisição seguinte,
  `GET /tasks` executa `Category.query.get(t.category_id)` (`task_routes.py:51`), recebe `None`,
  e devolve `category_name: null` para uma task que o usuário vê como categorizada. Nenhum erro é
  emitido em lugar algum — o dado fica silenciosamente corrompido.
  Segundo cenário, na unicidade de e-mail: duas requisições concorrentes de `POST /users` com o
  mesmo endereço passam ambas pela verificação da linha 67 antes de qualquer uma chegar à linha
  82. Aqui o índice `UNIQUE` de `users.email` salva o banco — mas o caminho de erro cai no
  `except` genérico e devolve 500 "Erro ao criar usuário" (F-013) em vez do 409 que a linha 69
  reservou para o caso.
- **Correção esperada:** as escritas relacionadas de cada caso de uso envolvidas numa única
  unidade de trabalho, com a política de dependentes (cascata ou recusa) declarada no schema.
- **Confiança:** ALTA

---

### [HIGH] F-009 — Dependências obtidas de singleton global; composition root que não recebe nem injeta nada

- **Anti-pattern:** AP-09 · **Transformação:** TR-09 · **Onda:** 2
- **Arquivo:** `app.py:9-20`, `database.py:1-3`, `services/notification_service.py:5-10`
- **Evidência** — o composition root constrói o objeto principal sem receber dependência alguma,
  com os parâmetros de infraestrutura fixados em literal (checklist §9, linha 10):

```python
# app.py:9-20
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super-secret-key-123'

CORS(app)
db.init_app(app)

app.register_blueprint(task_bp)
app.register_blueprint(user_bp)
app.register_blueprint(report_bp)
```

A infraestrutura instanciada no construtor, em vez de recebida como parâmetro:

```python
# services/notification_service.py:5-10
    def __init__(self):
        self.notifications = []
        self.email_host = 'smtp.gmail.com'
        self.email_port = 587
        self.email_user = 'taskmanager@gmail.com'
        self.email_password = 'senha123'
```

- **Descrição:** o objeto de persistência é um singleton de módulo (`database.py:3`, `db = SQLAlchemy()`)
  que cada módulo de rota alcança por import direto — `task_routes.py:2`, `user_routes.py:2`,
  `report_routes.py:2` — em vez de recebê-lo. Isso é o **salto de camada** que
  `mvc-guidelines.md` §3 nomeia: a apresentação importa a infraestrutura diretamente. O
  contra-exemplo do AP foi aplicado e não isenta: Flask **não** tem container de injeção próprio,
  então não existe "o container é o composition root da stack" a invocar aqui; e a dependência em
  questão não é pura e sem estado — é a sessão de banco.
- **Impacto:** nenhuma camada é instanciável em teste com implementação alternativa. Exercitar a
  regra de "task atrasada" exige `app.app_context()` e um SQLite real. `NotificationService`
  não tem como ser testado sem um servidor SMTP — o que ajuda a explicar por que ele nunca foi
  ligado a nada (F-020).
- **Correção esperada:** composition root único que lê a configuração, constrói repositórios,
  injeta-os nos serviços e estes nos controllers; nenhuma camada abaixo alcança infraestrutura
  por import global.
- **Confiança:** ALTA

---

### [MEDIUM] F-010 — Duplicação massiva com a abstração correta presente no repositório e nunca invocada

- **Anti-pattern:** AP-17 · **Transformação:** TR-15 · **Onda:** 3
- **Arquivo:** `models/task.py:50-60`, `utils/helpers.py:9-116`, e 24 cópias espalhadas
- **Evidência** — a implementação correta existe, no lugar certo, e tem **zero** referências:

```python
# models/task.py:50-60   ← a abstração correta
    def is_overdue(self):
        if self.due_date:
            if self.due_date < datetime.utcnow():
                if self.status != 'done' and self.status != 'cancelled':
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
```

```python
# routes/report_routes.py:33-37   ← cópia 1 de 6, verbatim
    for t in all_tasks:
        if t.due_date:
            if t.due_date < datetime.utcnow():
                if t.status != 'done' and t.status != 'cancelled':
                    overdue_count = overdue_count + 1
```

**Verificação decisiva** — referências fora do módulo de origem, para os dois símbolos de
`utils/` que chegam a ser importados:

```console
$ grep -rn -E 'format_date|calculate_percentage' --include='*.py' . | grep -v '^./.claude'
utils/helpers.py:9:def format_date(date_obj):
utils/helpers.py:14:def calculate_percentage(part, total):
routes/report_routes.py:7:from utils.helpers import format_date, calculate_percentage
```

Três linhas: duas definições e um import. **Zero sítios de chamada.** Importar não é usar.

- **Descrição:** seis regras duplicadas, cada uma com a abstração correta morta ao lado:

  | Regra | Cópias | `arquivo:linha` das cópias | Abstração correta, com refs externas |
  |---|---|---|---|
  | "task atrasada" | 6 | `task_routes.py:30-39`, `:71-80`, `:283-287`, `user_routes.py:171-180`, `report_routes.py:33-43`, `:132-135` | `models/task.py:50-60` `is_overdue` — **0 chamadas** |
  | vocabulário de status | 4 | `models/task.py:39`, `task_routes.py:110`, `:177`, `helpers.py:75` | `helpers.py:110` `VALID_STATUSES` — **0 refs** |
  | taxa de conclusão | 3 | `task_routes.py:296`, `report_routes.py:67`, `:151` | `helpers.py:14` `calculate_percentage` — importada, **0 chamadas** |
  | regex de e-mail | 2 | `user_routes.py:61`, `:106` | `helpers.py:19` `validate_email` — **0 refs** |
  | parsing de tags | 4 | `models/task.py:35`, `task_routes.py:28`, `:141-144`, `:210-213` | `helpers.py:101-106` — **0 refs** |
  | validação de task | 2 | `task_routes.py:92-144`, `:166-213` | `helpers.py:57-108` `process_task_data`, 52 LOC — **0 refs** |

  O contra-exemplo foi aplicado por linha: em nenhum dos seis casos as ocorrências divergem em
  regra de modo a exigir um parâmetro de comportamento — são cópias literais da mesma decisão. O
  limiar de três é atendido nas quatro primeiras; "regex de e-mail" e "validação de task" têm
  duas cópias e entram como ocorrências **desta** causa (abstração morta), não como findings
  próprios.
- **Impacto:** este é o finding de maior rendimento do relatório, na leitura que o próprio
  catálogo recomenda: ele converte a Fase 3 de "criar camadas" em "ligar as camadas que já
  existem". Também explica F-006: a regra de atraso está em 7 lugares porque a sétima — a certa —
  nunca foi ligada.
- **Correção esperada:** consolidar cada regra na abstração que já existe, ligá-la aos chamadores,
  e remover o que sobrar morto.
- **Confiança:** ALTA

---

### [MEDIUM] F-011 — Invariantes de domínio como cadeia de condicionais no handler, divergentes entre criar e atualizar

- **Anti-pattern:** AP-12 · **Transformação:** TR-08 · **Onda:** 3
- **Arquivo:** `routes/task_routes.py:92-124`, `routes/task_routes.py:166-198`, `routes/user_routes.py:54-72`, `routes/user_routes.py:102-125`
- **Evidência:**

```python
# routes/task_routes.py:92-114   (POST /tasks)
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Título é obrigatório'}), 400
    if len(title) < 3:
        return jsonify({'error': 'Título muito curto'}), 400
    if len(title) > 200:
        return jsonify({'error': 'Título muito longo'}), 400
    …
    if status not in ['pending', 'in_progress', 'done', 'cancelled']:
        return jsonify({'error': 'Status inválido'}), 400
    if priority < 1 or priority > 5:
        return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
```

**Agravante decisivo** — a mesma invariante aplicada de forma divergente entre criação e
atualização da mesma entidade, lado a lado:

```python
# routes/task_routes.py:92-94    POST: título é obrigatório
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Título é obrigatório'}), 400

# routes/task_routes.py:166-171  PUT: obrigatoriedade sumiu; só valida se vier
    if 'title' in data:
        if len(data['title']) < 3:
            return jsonify({'error': 'Título muito curto'}), 400
        if len(data['title']) > 200:
            return jsonify({'error': 'Título muito longo'}), 400
        task.title = data['title']
```

Segundo par divergente, em `User`:

```python
# routes/user_routes.py:54-55    POST: nome obrigatório e não-vazio
    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400

# routes/user_routes.py:102-103  PUT: aceita string vazia sem reclamar
    if 'name' in data:
        user.name = data['name']
```

- **Descrição:** as invariantes de domínio — faixa de prioridade 1..5, tamanho de título 3..200,
  vocabulário fechado de `status` e de `role`, formato de e-mail, tamanho mínimo de senha —
  estão escritas como sequência de condicionais com literais dentro dos handlers, **sem constraint
  equivalente no schema** (F-007 comprova: nenhum CHECK em `status` nem em `priority`) e sem
  camada de escrita que as imponha. O contra-exemplo foi aplicado: as verificações de protocolo
  (`if not data:` → payload malformado, em `task_routes.py:89`, `user_routes.py:46`) pertencem à
  borda mesmo e **não** entram neste finding. Demais ocorrências de invariante de domínio inline:
  `user_routes.py:61,64,71` e `:106,115,120`, `report_routes.py:174-175`.
- **Impacto:** `PUT /tasks/1` com `{"title": ""}` grava título vazio — a regra que o `POST`
  impõe, o `PUT` não impõe. A mesma entidade tem duas definições de válido, e elas já discordam.
  Como o banco não tem CHECK algum, qualquer escrita fora do caminho HTTP (o próprio `seed.py`,
  por exemplo) ignora as seis regras inteiramente.
- **Correção esperada:** validador declarativo por entidade, aplicado uniformemente nos dois
  caminhos de escrita, com as invariantes também declaradas no schema.
- **Confiança:** ALTA

---

### [MEDIUM] F-012 — N+1 em quatro endpoints, com o relacionamento de eager loading já declarado e não usado

- **Anti-pattern:** AP-15 · **Transformação:** TR-11 · **Onda:** 3
- **Arquivo:** `routes/task_routes.py:41-57`, `routes/report_routes.py:53-68`, `routes/report_routes.py:161-164`, `routes/user_routes.py:22`
- **Evidência** — consulta disparada dentro do laço que itera o resultado da consulta anterior:

```python
# routes/task_routes.py:14-16, 41-57
        tasks = Task.query.all()          # ← consulta externa
        result = []
        for t in tasks:                   # ← laço sobre o resultado
            …
            if t.user_id:
                user = User.query.get(t.user_id)      # ← consulta interna, nível 2
                if user:
                    task_data['user_name'] = user.name
                …
            if t.category_id:
                cat = Category.query.get(t.category_id)  # ← consulta interna, nível 2
```

**Agravante confirmado** — o mapeamento objeto-relacional **já declara** o relacionamento que
resolveria por eager loading, e ele não é usado:

```python
# models/task.py:20-21
    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')
```

- **Descrição:** medido com contador em `before_cursor_execute` do SQLAlchemy, contra a base
  semeada (10 tasks, 3 usuários, 4 categorias):

```console
/tasks               HTTP 200  queries SQL = 17
/users               HTTP 200  queries SQL = 6
/reports/summary     HTTP 200  queries SQL = 21
/categories          HTTP 200  queries SQL = 5
```

  Estimativa em função do tamanho do resultado: `GET /tasks` executa `1 + 2N` idas ao banco para
  `N` tasks; `GET /reports/summary` executa `1 + N` para `N` usuários, **somadas** a 5 `COUNT`
  separados só para montar o histograma de prioridade (`report_routes.py:24-28`) e mais 4 para o
  histograma de status (`:19-22`); `GET /categories` executa `1 + N` para `N` categorias
  (`report_routes.py:163`).
- **Variante correlata, presente:** agregação numérica calculada em laço na aplicação sobre a
  tabela inteira, quando exprimível na consulta — `task_routes.py:281-287` carrega
  `Task.query.all()` só para contar atrasadas, e `report_routes.py:30-43` faz o mesmo.
- **Contra-exemplo aplicado:** a isenção "laço externo com cardinalidade fixa e pequena garantida
  pelo domínio" não vale — `tasks`, `users` e `categories` crescem com o uso; não são conjunto
  fechado. E, sem paginação (F-015), o laço externo é a tabela inteira.
- **Impacto:** com 1.000 tasks, `GET /tasks` passa a fazer ~2.001 consultas numa requisição. O
  tempo de resposta é função linear do volume de dados, e não há índice nas colunas envolvidas
  (F-007) para amortecer.
- **Correção esperada:** colapsar cada laço numa ida só, usando os relacionamentos já declarados,
  e mover as agregações para a própria consulta.
- **Confiança:** ALTA

---

### [MEDIUM] F-013 — Captura genérica de exceção em 12 pontos, sem tratador central, transformando erro de cliente em 500

- **Anti-pattern:** AP-18 · **Transformação:** TR-13 · **Onda:** 3
- **Arquivo:** 12 ocorrências; representativa em `routes/task_routes.py:13-63`
- **Evidência** — captura sem tipo que descarta o objeto de erro sem registro algum, envolvendo
  o handler inteiro:

```python
# routes/task_routes.py:13-14, 61-63
    try:
        tasks = Task.query.all()
        …
        return jsonify(result), 200
    except:
        return jsonify({'error': 'Erro interno'}), 500
```

Contagem das ocorrências do mesmo padrão:

```console
$ grep -rn -E '^\s*except\s*:' --include='*.py' . | grep -v '^./.claude'
utils/helpers.py:46:    except:
utils/helpers.py:49:        except:
utils/helpers.py:88:        except:
routes/report_routes.py:186:    except:
routes/report_routes.py:207:    except:
routes/report_routes.py:221:    except:
routes/task_routes.py:62:    except:
routes/task_routes.py:137:        except:
routes/task_routes.py:204:            except:
routes/task_routes.py:236:    except:
routes/user_routes.py:130:    except:
routes/user_routes.py:149:    except:
```

- **Descrição:** 12 blocos `except:` pelados — que em Python capturam inclusive `KeyboardInterrupt`
  e `SystemExit` — repetidos por handler, sem tratador centralizado (`@app.errorhandler` não
  aparece em arquivo algum) e sem distinguir falha de domínio de defeito. Nenhum deles registra o
  erro: `task_routes.py:62` e os três de `report_routes.py` descartam a exceção inteira. O
  contra-exemplo não se aplica — nenhuma dessas capturas está na fronteira do processo nem emite
  identificador de correlação.
- **Consequência confirmada seguindo um caminho concreto** — entrada inválida que deveria virar
  4xx vira 5xx, porque nem a captura genérica nem a sua ausência distinguem:

```console
$ curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:5000/tasks/search?priority=abc"
500        # ValueError: invalid literal for int() — deveria ser 400
$ curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:5000/tasks \
       -H 'Content-Type: application/json' -d '{"title":"Teste ABC","priority":"alta"}'
500        # TypeError: '<' not supported between 'str' and 'int' — deveria ser 400
$ curl -s -o /dev/null -w "%{http_code}\n" -X PUT http://localhost:5000/tasks/1 \
       -H 'Content-Type: application/json' -d '{"title":123}'
500        # TypeError: object of type 'int' has no len() — deveria ser 400
```

- **Impacto:** três entradas triviais de cliente derrubam o request com 500. Como `debug=True`
  (F-001), o corpo devolvido nesses três casos é o console interativo do Werkzeug, não JSON — o
  que faz o contrato de media type mudar sob erro. E o `except:` de `task_routes.py:62` mascara
  qualquer defeito real de `GET /tasks` atrás de `'Erro interno'`, tornando-o invisível em
  produção: não há log, não há stack trace, não há correlação.
- **Correção esperada:** tratador de erro centralizado, exceções de domínio tipadas mapeadas para
  status apropriado, envelope de erro único, e registro do erro completo com identificador de
  correlação.
- **Confiança:** ALTA

---

### [MEDIUM] F-014 — Contrato de resposta divergente entre handlers do mesmo recurso

- **Anti-pattern:** AP-23 · **Transformação:** TR-13 · **Onda:** 3
- **Arquivo:** `routes/task_routes.py:17-59` vs `routes/task_routes.py:67-81`; `routes/user_routes.py:15-23` vs `routes/user_routes.py:33-38`
- **Evidência** — dois handlers do **mesmo recurso**, lado a lado, com envelopes divergentes.
  A listagem enriquece o item:

```python
# routes/task_routes.py:41-57   (GET /tasks — item da coleção)
            if t.user_id:
                user = User.query.get(t.user_id)
                if user:
                    task_data['user_name'] = user.name
                else:
                    task_data['user_name'] = None
            …
                    task_data['category_name'] = cat.name
```

O detalhe do mesmo recurso, não:

```python
# routes/task_routes.py:67-81   (GET /tasks/<id> — o mesmo item)
    task = Task.query.get(task_id)
    if task:
        data = task.to_dict()
        …
        return jsonify(data), 200
```

Segundo par, em `User` — a listagem **omite** a credencial e acrescenta `task_count`; o detalhe
**inclui** a credencial e acrescenta `tasks`:

```python
# routes/user_routes.py:15-23   (GET /users)
        user_data = {
            'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role,
            'active': u.active, 'created_at': str(u.created_at),
            'task_count': len(u.tasks)
        }

# routes/user_routes.py:33-38   (GET /users/<id>)
    data = user.to_dict()          # ← inclui 'password'
    tasks = Task.query.filter_by(user_id=user_id).all()
    data['tasks'] = []
    for t in tasks:
        data['tasks'].append(t.to_dict())
```

- **Descrição:** o mesmo recurso tem duas representações incompatíveis conforme a rota. Um cliente
  que leia `user_name` de `GET /tasks` não o encontra em `GET /tasks/<id>`. Terceira divergência:
  as rotas de remoção devolvem `{'message': …}` (`task_routes.py:235`, `user_routes.py:148`,
  `report_routes.py:220`) enquanto as demais devolvem a entidade — envelope diferente para
  operações do mesmo recurso. Quarta: falha de infraestrutura e erro de cliente colapsam no mesmo
  status 500 (F-013), e sob `debug=True` o erro sai em `text/html` enquanto o sucesso sai em
  `application/json`.
- **Impacto:** o consumidor precisa de dois desserializadores por recurso e não pode confiar em
  nenhum campo derivado. A divergência não é deliberada nem documentada — é consequência de a
  serialização estar em dois lugares (`to_dict()` no model e dicionários montados à mão nos
  handlers), que é a mesma causa de F-005.
- **Correção esperada:** um DTO por recurso, aplicado em listagem e em detalhe, e envelope de
  erro uniforme com código estável.
- **Confiança:** ALTA

---

### [MEDIUM] F-015 — Quatro listagens sem paginação, com o próprio backlog do projeto nomeando a lacuna

- **Anti-pattern:** AP-22 · **Transformação:** TR-17 · **Onda:** 3
- **Arquivo:** `routes/task_routes.py:14`, `routes/task_routes.py:266`, `routes/user_routes.py:12`, `routes/report_routes.py:159`
- **Evidência** — consulta de listagem sem cláusula de limite, resultado serializado inteiro:

```python
# routes/task_routes.py:14        GET /tasks
        tasks = Task.query.all()
# routes/task_routes.py:266       GET /tasks/search
    results = tasks.all()
# routes/user_routes.py:12        GET /users
    users = User.query.all()
# routes/report_routes.py:159     GET /categories
    categories = Category.query.all()
```

**Sinal auxiliar** — o próprio repositório descreve a lacuna, nos dados de seed:

```python
# seed.py:70
{'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros',
 'status': 'pending', 'priority': 3, …},
```

- **Descrição:** nenhum dos quatro handlers aceita parâmetro de limite, offset ou cursor. O
  tamanho da resposta é função dos dados, não do contrato. O contra-exemplo foi aplicado por
  endpoint: `tasks`, `users` e o resultado de busca crescem com o uso. `categories` é a única
  com aparência de cardinalidade fechada, mas **não** é fechada pelo domínio — `POST /categories`
  (`report_routes.py:167`) permite criar quantas o chamador quiser, sem limite e sem
  autenticação (F-004).
- **Impacto:** `GET /tasks` combina ausência de limite com N+1 (F-012): a resposta cresce
  linearmente e o custo em consultas cresce a `2N`. Um chamador anônimo transfere a tabela
  inteira numa requisição, e não há controle de taxa em lugar algum.
- **Correção esperada:** limite e offset com defaults explícitos nos quatro endpoints, e a forma
  do item preservada.
- **Confiança:** ALTA

---

### [MEDIUM] F-016 — Chamadas deprecated no runtime real em uso, em 34 pontos, sem linter que as barre

- **Anti-pattern:** AP-16 · **Transformação:** TR-12 · **Onda:** 3
- **Arquivo:** 18 ocorrências de `datetime.utcnow()` + 16 de `Query.get()`
- **Evidência** — verificado contra a versão **real** do ambiente, obtida executando o runtime na
  Fase 1 (`Python 3.12.3`), e contra a versão **instalada** do ORM (`SQLAlchemy 2.0.52`), não
  contra o manifesto:

```console
$ python seed.py
/…/task-manager-api/seed.py:66: DeprecationWarning: datetime.datetime.utcnow() is deprecated and
scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in
UTC: datetime.datetime.now(datetime.UTC).
```

```console
$ python -W always -c "…; Task.query.get(1)"
LegacyAPIWarning: The Query.get() method is considered legacy as of the 1.x series of SQLAlchemy
and becomes a legacy construct in 2.0. The method is now available as Session.get()
(deprecated since: 2.0)
```

- **Descrição:** duas famílias de chamada deprecated, ambas no caminho quente:

  | Chamada | Ocorrências | Depreciada em | Equivalente moderno |
  |---|---|---|---|
  | `datetime.utcnow()` | **18** — `models/task.py:15,16,52`, `models/user.py:14`, `task_routes.py:31,72,215,285`, `user_routes.py:172`, `report_routes.py:35,42,45,71,133`, `helpers.py:38`, `seed.py:66,67,69,70,74` | Python **3.12** (a versão em uso) | `datetime.now(datetime.UTC)` |
  | `Model.query.get()` | **16** — `task_routes.py:42,51,67,117,122,158,188,195,227`, `user_routes.py:29,94,136,155`, `report_routes.py:105,192,213` | SQLAlchemy **2.0** (a versão instalada) | `db.session.get(Model, pk)` |

  Nenhuma das duas está atrás de camada de compatibilidade, e não há comentário de migração em
  lugar algum do projeto.
- **Reforço, que justifica TR-12 fixar a regra e não só trocar a chamada:** não existe linter
  configurado — nenhum `.flake8`, `.pylintrc`, `ruff.toml`, `setup.cfg` ou `pyproject.toml` no
  projeto nem um nível acima (F-023). É o que explica a sobrevivência das 34 chamadas.
- **Impacto:** `datetime.utcnow()` devolve objeto **naive**, o que já hoje faz todas as
  comparações de "atrasada" (F-006, F-010) operarem sem fuso — correto por acidente enquanto o
  banco também grava naive, e silenciosamente errado no dia em que algo gravar aware. As duas
  APIs estão marcadas para remoção; o projeto não tem teste (F-023) que detecte a quebra.
- **Correção esperada:** substituir as 34 chamadas pelos equivalentes modernos e fixar a regra no
  linter para impedir regressão.
- **Confiança:** ALTA

---

### [MEDIUM] F-017 — Política de origem cruzada totalmente permissiva sobre 22 rotas não autenticadas

- **Anti-pattern:** AP-20 · **Transformação:** TR-18 · **Onda:** 3
- **Arquivo:** `app.py:2`, `app.py:15`
- **Evidência:**

```python
# app.py:2
from flask_cors import CORS
# app.py:15
CORS(app)
```

- **Descrição:** o middleware de origem cruzada é registrado globalmente, **sem argumento de
  restrição algum** — nem `origins`, nem `methods`, nem `resources`. A configuração padrão do
  Flask-CORS 4.0.0 nessa forma libera qualquer origem. Ele cobre indistintamente as 22 rotas do
  inventário, incluindo as 4 de escrita, as 3 destrutivas e as 2 privilegiadas.
- **Contra-exemplo aplicado:** a isenção "API deliberadamente pública e somente leitura" **não**
  vale — há 10 rotas de escrita/remoção. A isenção "origem restrita por allowlist configurável"
  também não: não há configuração de origem em ponto algum do projeto (F-001 comprova que nada
  é lido do ambiente).
- **Impacto:** qualquer página web visitada pela vítima executa `DELETE /users/1` ou
  `PUT /users/1 {"role":"admin"}` contra este servidor a partir do browser dela, e lê a resposta.
  Como não há autenticação (F-004), não existe sequer o cookie que um CSRF clássico precisaria —
  a requisição anônima já basta, e o CORS permissivo apenas remove o último obstáculo à leitura
  do resultado.
- **Severidade mantida em MEDIUM**, conforme a tabela do catálogo. A nota de composição do AP
  ("onde há autenticação por cookie, ele sobe") **não** se aplica: não há autenticação por cookie
  aqui. O dano de escrita anônima já está contabilizado em F-004, e duplicá-lo aqui inflaria o
  relatório.
- **Correção esperada:** allowlist de origens configurável por ambiente, e métodos restritos ao
  necessário.
- **Confiança:** ALTA

---

### [MEDIUM] F-018 — Endpoint de autenticação sem contador, backoff ou bloqueio

- **Anti-pattern:** AP-24 · **Transformação:** TR-05 · **Onda:** 1 *(desce junto de TR-05, que a onda de F-004 fixa)*
- **Arquivo:** `routes/user_routes.py:185-211`
- **Evidência:**

```python
# routes/user_routes.py:185-202
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    email = data.get('email')
    password = data.get('password')
    …
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Credenciais inválidas'}), 401

    if not user.check_password(password):
        return jsonify({'error': 'Credenciais inválidas'}), 401
```

```console
$ grep -rniE 'limiter|ratelimit|rate_limit|attempts|tentativa' --include='*.py' . requirements.txt
  nenhum contador, nenhum middleware, nenhuma dependencia
```

- **Descrição:** o handler de autenticação aceita tentativas ilimitadas do mesmo chamador. Não há
  contador por sujeito, atraso progressivo ou bloqueio; o registro da rota não tem middleware de
  limite, e o manifesto não declara dependência correspondente. O contra-exemplo foi aplicado:
  não há proxy nem gateway verificável no repositório — nenhum `Dockerfile`, nenhum arquivo de
  configuração de servidor —, e supor que "deve haver um" não conta como verificação.
- **Sinal correlato, registrado como o catálogo pede:** hoje a autenticação é tão fraca (F-003)
  que a força bruta é desnecessária — quem lê `GET /users/<id>` já tem o hash MD5. Quando TR-05 e
  TR-03 corrigirem isso, a força bruta passa a ser **o próximo caminho mais barato**, e é por isso
  que o controle de taxa precisa entrar junto e não depois.
- **Impacto:** enumeração de credenciais a taxa limitada apenas pela rede, sobre senhas de no
  mínimo 4 caracteres (`user_routes.py:64`).
- **Correção esperada:** contador por sujeito com backoff progressivo no endpoint de
  autenticação, aplicado junto com TR-05.
- **Confiança:** ALTA

---

### [LOW] F-019 — `print()` como mecanismo de log, com o helper padronizado do próprio projeto morto ao lado

- **Anti-pattern:** AP-19 · **Transformação:** TR-14 · **Onda:** 4
- **Arquivo:** 11 ocorrências fora do `seed.py`
- **Evidência:**

```python
# routes/task_routes.py:146-153
    try:
        db.session.add(task)
        db.session.commit()
        print(f"Task criada: {task.id} - {task.title}")
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar task: {str(e)}")
```

Confirmação de que nenhum arquivo do projeto importa biblioteca de logging:

```console
$ grep -rnE '^\s*(import|from)\s+logging' --include='*.py' . | grep -v '^./.claude'
  NENHUM import de logging em todo o projeto
```

- **Descrição:** saída direta para stdout usada como registro de eventos, sem nível de severidade,
  sem timestamp e sem destino configurável. Ocorrências: `task_routes.py:149,153,219,234`,
  `user_routes.py:83,89,147`, `notification_service.py:21,24`, `helpers.py:39,41`. O
  contra-exemplo foi aplicado: os 4 `print` de `seed.py:93-96` **são** a interface de um script de
  uso único fora do caminho de requisição, e por isso **não** entram na contagem.
- **Reforço, que cruza com F-010:** o próprio projeto define um helper de log padronizado que
  nenhum chamador usa —

```python
# utils/helpers.py:36-41
def log_action(action, details=None):

    timestamp = datetime.utcnow()
    print(f"[{timestamp}] ACTION: {action}")
    if details:
        print(f"  DETAILS: {details}")
```

  `log_action` tem **0 referências** fora do módulo. E os caminhos de erro que respondem ao
  cliente descartam o erro sem registrá-lo em lugar nenhum (F-013), tornando o defeito invisível
  em produção.
- **Impacto:** nenhum evento é filtrável por severidade nem correlacionável a uma requisição; a
  saída se perde quando o processo não tem terminal.
- **Correção esperada:** logger com níveis, timestamp e destino configurável, substituindo as 11
  chamadas, com redação de campos sensíveis.
- **Confiança:** ALTA

---

### [LOW] F-020 — Código morto: uma camada inteira inalcançável, 14 símbolos sem referência e 3 dependências não importadas

- **Anti-pattern:** AP-26 · **Transformação:** TR-15 · **Onda:** 3 *(sobe junto de TR-15, que a onda de F-010 fixa)*
- **Arquivo:** `services/notification_service.py` (48 LOC), `utils/helpers.py`, `requirements.txt`
- **Evidência** — **diretório de camada inteiro inalcançável a partir dos entry points**, que é o
  gatilho da regra de `mvc-guidelines.md` §6:

```console
$ grep -rn -E 'services|Notification|notification' --include='*.py' . | grep -v '^./.claude'
services/notification_service.py:4:class NotificationService:
services/notification_service.py:6:        self.notifications = []
services/notification_service.py:31:        self.notifications.append({
services/notification_service.py:43:    def get_notifications(self, user_id):
services/notification_service.py:45:        for n in self.notifications:
```

Todas as cinco ocorrências são internas ao próprio arquivo. **Zero importadores.**
`services/__init__.py` tem 1 byte e não reexporta nada.

Dependências declaradas no manifesto e não importadas por nenhum arquivo:

```console
pacote                 declarado    instalado    importado pelo codigo?
marshmallow            3.20.1       3.20.1       NAO
requests               2.31.0       2.31.0       NAO
python-dotenv          1.0.0        1.0.0        NAO
```

- **Descrição, com o inventário que `mvc-guidelines.md` §6 exige ANTES de qualquer proposta de
  remoção** — nada desaparece sem constar deste relatório:

  **Conteúdo de `services/notification_service.py`** (a camada inalcançável): a classe
  `NotificationService`, com `send_email` (SMTP via `smtplib`), `notify_task_assigned`,
  `notify_task_overdue`, `get_notifications`, e um acumulador `self.notifications` em memória.
  Carrega **uma credencial SMTP versionada** — `email_user = 'taskmanager@gmail.com'`,
  `email_password = 'senha123'` (`notification_service.py:9-10`), já reportada como parte de
  F-001. **Apagar o arquivo não remove o segredo do histórico do repositório**, e é o histórico
  que precisa ser rotacionado; a rotação é item NEEDS-DECISION do plano.

  **Símbolos de `utils/helpers.py` nunca sequer importados** (14 de 16 — os 2 restantes são
  importados e nunca chamados, ver F-010): `validate_email`,
  `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`,
  `process_task_data` (52 LOC), `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`,
  `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR` — e
  `format_date`/`calculate_percentage`, que são importados mas nunca chamados (F-010).

  **Métodos de model com 0 chamadas:** `Task.validate_status`, `Task.validate_priority`,
  `Task.is_overdue` (`models/task.py:38-60`), `User.is_admin` (`models/user.py:34-38`).

  **Imports não usados:** `app.py:7` (`os, sys, json`), `task_routes.py:7` (`json, os, sys, time`
  — nenhum usado), `user_routes.py:6` (`hashlib, json`), `report_routes.py:8` (`json`),
  `models/task.py:3` (`json`), `helpers.py:3-6` (`os, json, sys, math`).

  `models/__init__.py:1-3` reexporta os três models e nenhum consumidor importa do pacote — todos
  importam o submódulo direto.
- **Leitura de alto valor do sinal** — as dependências mortas correspondem **exatamente** a
  lacunas apontadas por outros findings, o que revela a arquitetura pretendida e não implementada:

  | Dependência morta | Lacuna que ela cobriria | Finding |
  |---|---|---|
  | `marshmallow` (validação/serialização declarativa) | validação inline duplicada e divergente; DTO ausente | F-011, F-002 |
  | `python-dotenv` (configuração por ambiente) | segredos literais, zero leitura de ambiente | F-001 |
  | `requests` (integração HTTP) | nenhuma — sem correspondente | — |

  Isso converte parte deste finding LOW numa observação de projeto e indica que a correção é mais
  barata do que parecia: `marshmallow` e `python-dotenv` já estão no manifesto e instalados, então
  TR-01 e TR-08 não precisam adicionar dependência.
- **Impacto:** 48 LOC de camada morta com nome de camada viva induzem o leitor — e a própria
  Fase 3 — a construir sobre o que não existe. Foi exatamente essa a armadilha que a regra de
  alcançabilidade evitou nesta auditoria.
- **Correção esperada:** consolidar o que tem uso na abstração viva, remover o morto, e rotacionar
  a credencial exposta no histórico.
- **Confiança:** ALTA

---

### [LOW] F-021 — Tradução de valor para rótulo de negócio e limiares sem nome na montagem da resposta

- **Anti-pattern:** AP-25 · **Transformação:** TR-18 · **Onda:** 3 *(sobe junto de TR-18, que a onda de F-017 fixa)*
- **Arquivo:** `routes/report_routes.py:24-28`, `routes/report_routes.py:83-89`, `routes/report_routes.py:129`, `routes/report_routes.py:45`
- **Evidência** — tradução entre valor armazenado e rótulo de negócio embutida na montagem da
  resposta, exatamente a terceira pergunta do sinal do AP:

```python
# routes/report_routes.py:24-28
    p1 = Task.query.filter_by(priority=1).count()
    p2 = Task.query.filter_by(priority=2).count()
    p3 = Task.query.filter_by(priority=3).count()
    p4 = Task.query.filter_by(priority=4).count()
    p5 = Task.query.filter_by(priority=5).count()

# routes/report_routes.py:83-89
        'tasks_by_priority': {
            'critical': p1,
            'high': p2,
            'medium': p3,
            'low': p4,
            'minimal': p5,
        },
```

Limiar de negócio sem constante nomeada:

```python
# routes/report_routes.py:129
        if t.priority <= 2:
            high_priority = high_priority + 1

# routes/report_routes.py:45
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
```

- **Descrição:** o mapeamento `1→critical … 5→minimal` é vocabulário de domínio existente
  **apenas** dentro da montagem de uma resposta, sem enum, sem constante e sem correspondência com
  restrição no schema (F-007 confirma: nenhum CHECK em `priority`). O limiar `<= 2` para
  "prioridade alta" é a mesma decisão de negócio, escrita com outro literal, 40 linhas depois — e
  os dois já podem divergir sem que nada acuse. Demais literais sem nome:
  `report_routes.py:180` (`'#000000'`), `models/category.py:10` (o mesmo default duplicado).
- **Contra-exemplo aplicado com rigor:** os literais de faixa e de vocabulário que vivem dentro
  dos blocos de validação — `1`/`5` em `task_routes.py:113,182`, `3`/`200` em `:96,99`,
  `['pending', …]` em `:110,177`, `4` em `user_routes.py:64` — **não** abrem finding aqui. Eles
  são ocorrências de F-011 (AP-12), como o catálogo determina: *"o mesmo condicional não é dois
  findings — a regra mal alocada é a causa, o literal sem nome é o sintoma"*. Este finding cobre
  apenas os literais **fora** de blocos de AP-12.
- **Impacto:** mudar a escala de prioridade exige encontrar cinco variáveis `pN`, um dicionário de
  rótulos e um limiar solto, em dois pontos distantes do mesmo arquivo.
- **Correção esperada:** vocabulário de prioridade nomeado num só lugar, com o limiar de
  "alta" derivado dele.
- **Confiança:** ALTA

---

### [LOW] F-022 — Nome do contrato público divergente do recurso que ele serve

- **Anti-pattern:** AP-27 · **Transformação:** TR-18 · **Onda:** 3 *(sobe junto de TR-18)*
- **Arquivo:** `routes/report_routes.py:10`, `routes/report_routes.py:157-223`
- **Evidência** — o blueprint declarado como `reports` hospeda o CRUD completo de `Category`:

```python
# routes/report_routes.py:10
report_bp = Blueprint('reports', __name__)

# routes/report_routes.py:157-167  (67 LOC adiante, no mesmo blueprint)
@report_bp.route('/categories', methods=['GET'])
def get_categories():
…
@report_bp.route('/categories', methods=['POST'])
def create_category():
```

O efeito no contrato público, medido no `url_map` efetivo:

```console
  2 GET     /categories                      reports.get_categories
  3 POST    /categories                      reports.create_category
  4 DELETE  /categories/<int:cat_id>         reports.delete_category
  5 PUT     /categories/<int:cat_id>         reports.update_category
```

- **Descrição:** o nome do endpoint Flask — que é contrato público, usado por `url_for` — é
  `reports.get_categories`, divergindo do vocabulário do domínio: `Category` é um agregado
  próprio (Fase 1, fato 5), não um relatório. Quatro das 22 rotas carregam essa divergência.
  Ocorrência secundária: `cat` como abreviação de `Category` em `report_routes.py:192,213`,
  `task_routes.py:51,122,195`.
- **Contra-exemplo aplicado, e dois candidatos descartados:**
  - `id` como nome de coluna em `models/*.py:7-8` **não** é finding: é o nome da coluna no
    schema e o vocabulário do domínio, e não sombreia o builtin em escopo local algum.
  - `t`, `u`, `c` como variáveis de laço **não** são finding: o catálogo exclui explicitamente
    "índice de laço".
- **Impacto:** o consumidor que procura o recurso de categoria não o encontra pelo nome; quem lê
  a árvore de `routes/` conclui que o projeto não tem CRUD de categoria.
- **Correção esperada:** as rotas de `Category` no lugar que o vocabulário do domínio indica,
  com o nome de blueprint correspondente, preservando path e verbo.
- **Confiança:** ALTA

---

### [LOW] F-023 — Ausência completa de infraestrutura de qualidade

- **Anti-pattern:** AP-28 · **Transformação:** *nenhuma — reportado, não corrigido* · **Onda:** —
- **Arquivo:** `requirements.txt` e a raiz do projeto
- **Evidência** — o manifesto completo (é curto, como o AP prevê):

```
flask==3.0.0
flask-sqlalchemy==3.1.1
flask-cors==4.0.0
marshmallow==3.20.1
requests==2.31.0
python-dotenv==1.0.0
```

Listagem que comprova a ausência dos artefatos, **e a verificação um nível acima que o
contra-exemplo do AP exige** (monorepo com configuração na raiz):

```console
--- dentro de task-manager-api/ ---
  test_*.py -> AUSENTE          pytest.ini -> AUSENTE       .flake8 -> AUSENTE
  *_test.py -> AUSENTE          tox.ini -> AUSENTE          .pylintrc -> AUSENTE
  tests/ dir -> AUSENTE         setup.cfg -> AUSENTE        ruff.toml -> AUSENTE
  .github/workflows -> AUSENTE  pyproject.toml -> AUSENTE   .env.example -> AUSENTE
  Makefile -> AUSENTE           Dockerfile -> AUSENTE       .python-version -> AUSENTE

--- um nivel acima (raiz do monorepo) ---
  .github/ na raiz -> AUSENTE
  pyproject/tox/pytest na raiz -> AUSENTE
```

- **Descrição:** o manifesto não declara dependências de desenvolvimento, nem comando reproduzível
  de boot ou de tarefa além da execução, nem versão de runtime. O repositório não tem arquivo de
  teste, configuração de lint, exemplo de variáveis de ambiente nem pipeline de CI — nem no
  projeto, nem um nível acima. Não há lockfile, e as versões são todas fixadas com `==`, o que ao
  menos elimina a combinação "faixa aberta + lockfile" que o AP também procura.
- **Impacto:** as 23 correções deste relatório não têm rede de proteção automatizada; a única
  verificação disponível é o smoke test de 22 endpoints que esta skill captura. É também o que
  explica a sobrevivência das 34 chamadas deprecated de F-016.
- **Correção esperada:** *fora do escopo desta skill.* Faltaria: runner de teste com suíte
  cobrindo os 22 endpoints, linter configurado, `.python-version`, e pipeline de CI executando os
  dois. **Este item não entra no plano do gate** — prometer no gate o que a Fase 3 não vai fazer
  invalidaria o gate.
- **Coberturas parciais que outras transformações produzem, como consequência e não como escopo:**
  TR-01 publica o `.env.example`; TR-12 pode fixar uma regra de linter contra a regressão das
  chamadas deprecated.
- **Confiança:** ALTA

---

## O que não foi encontrado

Cinco dos 28 APs do catálogo foram percorridos e não produziram finding. Cada um com o estado
nomeado, conforme `antipattern-catalog.md`:

- **Injection por concatenação (AP-01) — não encontrado.** O escopo se aplica (há persistência),
  e o sinal foi respondido "não". O único ponto com interpolação perto de uma consulta é
  `routes/task_routes.py:250-255`, e a verificação compilando o statement mostra que a f-string
  monta o **valor do padrão**, não o SQL — o driver o vincula como parâmetro:

  ```console
  SQL: SELECT … FROM tasks WHERE tasks.title LIKE :title_1 OR tasks.description LIKE :description_1
  parametros vinculados: {'title_1': "%' OR 1=1 --%", 'description_1': "%' OR 1=1 --%"}
  ```

  É exatamente o limite superior que o AP declara. Não há `execute()`, SQL textual, nem execução
  dinâmica em arquivo algum do projeto.

- **God class / god module (AP-06) — não encontrado.** O escopo é universal e o sinal foi
  respondido "não": **nenhum arquivo** reúne abertura de conexão, definição de schema, registro de
  rotas e regra de negócio no mesmo corpo. `app.py` (34 LOC) é o **composition root**, que o
  contra-exemplo do AP isenta explicitamente; suas responsabilidades excedentes — configuração
  literal e DDL no boot — já são F-001 (AP-02) e F-007 (AP-21), e reportá-las de novo aqui seria
  contar a mesma causa duas vezes. Os módulos de rota são grandes (299, 223 e 211 LOC) e acumulam
  seis a sete responsabilidades, mas nenhum abre conexão nem define schema, e **existe fronteira
  onde inserir uma camada** — que é o critério do AP. Essa acumulação está reportada onde
  pertence: F-005 (AP-13) e F-006 (AP-08).

  > **Consequência direta desta decisão no plano:** sem AP-06, TR-06 perde o teto da Onda 1 e
  > **desce para a Onda 2**, pela severidade de AP-13 (HIGH). É literalmente o caso que
  > `refactor-playbook.md` descreve — *"TR-06 é rotulado Onda 1 por AP-06 e desce para a Onda 2
  > num projeto que só tem AP-13"*. A Onda 1 não fica vazia porque quatro findings CRITICAL
  > independentes a preenchem.

- **Segredo ou PII em log (AP-07) — não encontrado.** O escopo é universal e o sinal foi
  respondido "não". Há 11 chamadas de saída usadas como log (F-019), mas nenhuma interpola
  credencial, token ou segredo de configuração:

  ```console
  $ grep -rnE 'print\(.*(password|senha|token|secret|SECRET|hash)' --include='*.py' .
    nenhum print com credencial/token/segredo
  ```

  Os templates emitem identificador e nome (`user_routes.py:83`), e o AP isenta explicitamente a
  emissão do identificador opaco de uma entidade. `print(f"ERRO: {str(e)}")` (`user_routes.py:89`)
  emite mensagem de exceção, o que é falha de tratamento (F-013), não vazamento de segredo.

- **Estado global mutável compartilhado (AP-10) — não encontrado.** O escopo é universal e o
  sinal foi respondido "não": não há variável mutável em escopo de módulo escrita pelo caminho de
  requisição. O único handle de recurso global é `db` (`database.py:3`), e o contra-exemplo o
  isenta — é um pool cujo contrato **é** ser compartilhado e que a extensão gerencia por contexto
  de aplicação. O acumulador `self.notifications` de `NotificationService` é estado de instância
  em código que nunca é instanciado (F-020), e portanto não é alcançado por caminho de requisição
  algum.

- **Mass assignment / bind não filtrado (AP-14) — não encontrado.** O escopo é universal e o
  sinal foi respondido "não": nenhum caminho de escrita repassa o payload inteiro. A busca por
  espalhamento não retorna nada, e os quatro handlers de escrita atribuem campo a campo, com
  allowlist explícita pela própria sequência de atribuições (`task_routes.py:126-144`,
  `user_routes.py:74-78`, `report_routes.py:177-180`):

  ```console
  $ grep -rnE '\*\*(data|payload|request|kwargs|body)' --include='*.py' .
    nenhum espalhamento de payload
  ```

  A escrita de `role` por chamador anônimo (`user_routes.py:119-122`) **é** um defeito real, mas
  não deste AP — o campo consta da allowlist deliberadamente; o que falta é a verificação de
  identidade, e isso é F-004 (AP-05).

---

## Breaking changes propostas

Previstas antes de executar cada TR, conforme `mvc-guidelines.md` §8. Path, verbo e status code
de sucesso são preservados por regra; o que segue são mudanças de **forma do corpo**, de **media
type**, e de **status para um mesmo cenário de entrada**.

| # | Endpoint | Mudança | Motivo | TR |
|---|---|---|---|---|
| BC-1 | `GET /users/<user_id>` · `POST /users` · `PUT /users/<user_id>` · `POST /login` | O campo `password` deixa de constar da resposta (em `/login`, dentro do objeto `user`) | Credencial não atravessa a fronteira de saída (F-002) | TR-04 |
| BC-2 | `POST /login` | O campo `token` passa de `fake-jwt-token-<id>` para credencial assinada com expiração. Tipo (string) preservado; **o valor deixa de conter o id do usuário** | Credencial previsível e não verificável (F-004) | TR-05 |
| BC-3 | As 10 rotas de escrita e destrutivas: `POST/PUT/DELETE /tasks*`, `POST/PUT/DELETE /users*`, `POST/PUT/DELETE /categories*` — **e** as 3 de leitura de terceiros: `GET /users`, `GET /users/<id>`, `GET /users/<id>/tasks` | Passam a responder **401** sem credencial válida | Rotas destrutivas e privilegiadas sem verificação de identidade (F-004) | TR-05 |
| BC-4 | `GET /tasks` · `GET /users` · `GET /categories` · `GET /tasks/search` | Passam a aceitar `limit`/`offset` e a retornar no máximo `limit` itens (default 50). **A forma do item e o array na raiz são preservados** — sem envelope | Tamanho da resposta deixa de ser função dos dados (F-015) | TR-17 |
| BC-5 | `GET /tasks` (cada item da coleção) | Os campos `user_name` e `category_name` **deixam** de constar, alinhando a coleção ao detalhe de `GET /tasks/<id>` | Representações divergentes do mesmo recurso (F-014). **Direção alternativa em ND-4** | TR-13 |
| BC-6 | `GET /users` (cada item da coleção) | O campo `task_count` **deixa** de constar, alinhando ao detalhe | idem (F-014) | TR-13 |
| BC-7 | Os 22 endpoints, **no caminho de erro apenas** | Envelope de erro uniformizado de `{"error": "<texto>"}` para `{"error": {"code": "<slug>", "message": "<texto>"}}` | Contrato de erro sem código estável e divergente de handler para handler (F-014) | TR-13 |
| BC-8 | `GET /tasks/search?priority=<não-numérico>` · `POST /tasks` com `priority` não-numérico · `PUT /tasks/<id>` com `title` não-string | Status muda de **500** para **400**, e o media type do corpo de erro muda de `text/html` (console do Werkzeug) para `application/json` | Erro de cliente reportado como falha de servidor (F-013) | TR-13, TR-08 |

**Nenhuma remoção de endpoint é proposta.** As 22 rotas do baseline permanecem, com path, verbo e
status de sucesso idênticos.

> **Efeito sobre o smoke test.** O baseline capturou os 22 endpoints no **caminho de sucesso**.
> BC-7 e BC-8 tocam apenas caminhos de erro, e portanto não aparecem na comparação de `M = 22`.
> BC-1, BC-5 e BC-6 **alteram o `shape` registrado** de 6 dos 22 registros do baseline, e BC-3
> altera o status de 13 deles. Todas as seis são divergências **declaradas**, e portanto contam
> como conformes (`validation-protocol.md` §4.1) — mas só porque estão nesta tabela. O roteiro de
> smoke da Fase 3 precisará autenticar antes de exercer as 13 rotas de BC-3, conforme o falso
> vermelho conhecido da §8 do protocolo.

---

## Plano de refatoração

A onda de cada TR é a onda do **finding de maior severidade que ele resolve**, não o rótulo do
playbook — que é teto.

### Onda 1 — CRITICAL

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| **TR-01** *(primeiro)* | F-001 | `config/__init__.py`, `config/settings.py`, `.env.example` | `app.py`, `services/notification_service.py` | — |
| TR-03 | F-003 | `security/passwords.py` | `models/user.py`, `routes/user_routes.py`, `seed.py` | — |
| TR-04 | F-002 | `dto/user_dto.py` | `models/user.py`, `routes/user_routes.py` | — |
| TR-05 | F-004, F-018 | `security/tokens.py`, `middlewares/auth.py`, `middlewares/rate_limit.py` | `app.py`, `routes/user_routes.py`, `routes/task_routes.py`, `routes/report_routes.py` | — |

Critério de aceite: **smoke test 22/22 endpoints conformes → commit**.

> **Risco conhecido desta onda, declarado no gate.** `refactor-playbook.md` avisa que *"aplicar
> TR-04 antes de haver camadas obriga a refazê-lo"*. Aqui TR-04 cai na Onda 1 (pela severidade de
> F-002, CRITICAL) enquanto TR-06 — que cria as camadas — cai na Onda 2 (pela severidade de
> F-005, HIGH). A regra de onda é a do finding e prevalece, mas a consequência é real: o DTO
> criado em `dto/` na Onda 1 será **movido** para o lugar definitivo quando TR-06 rodar na Onda 2.
> Optei por absorver o retrabalho em vez de antecipar TR-06 acima do seu teto, porque subir um TR
> acima do teto exigiria atribuir a F-005 severidade maior que a tabelada, e não há justificativa
> para isso.

### Onda 2 — HIGH

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| **TR-06** *(primeiro)* | F-005 | `repositories/{task,user,category}_repository.py`, `services/{task,user,category,report}_service.py`, `controllers/{task,user,category,report}_controller.py` | `routes/*.py` (reduzidos a tabela de rotas), `app.py` | — |
| TR-07 | F-006 | — | `services/*.py`, `controllers/*.py`, `models/task.py` | — |
| TR-09 | F-009 | — | `app.py` (composition root), `database.py`, todas as camadas novas | — |
| TR-10 | F-008 | `repositories/unit_of_work.py` | `services/user_service.py`, `services/category_service.py` | — |
| TR-16 | F-007 | `migrations/0001_initial.sql`, `infra/migrator.py` | `app.py` (DDL sai do boot) | — |

Critério de aceite: **smoke test 22/22 endpoints conformes → commit**.

### Onda 3 — MEDIUM

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-08 | F-011 | `validators/{task,user,category}_validator.py` | `controllers/*.py`, `services/*.py` | — |
| TR-11 | F-012 | — | `repositories/*.py` | — |
| TR-12 | F-016 | `.flake8` | 6 arquivos com `utcnow()` · 4 com `Query.get()` | — |
| TR-13 | F-013, F-014 | `middlewares/error_handler.py`, `dto/{task,category}_dto.py` | `app.py`, `controllers/*.py` | — |
| TR-15 | F-010, F-020 | — | `models/task.py`, `utils/helpers.py`, todos os chamadores | `services/notification_service.py`, símbolos mortos de `utils/helpers.py` |
| TR-17 | F-015 | — | `repositories/*.py`, `controllers/*.py` | — |
| TR-18 | F-017, F-021, F-022 | `constants.py` | `app.py` (CORS), `routes/report_routes.py` → rotas de `Category` renomeadas | — |

Critério de aceite: **smoke test 22/22 endpoints conformes → commit**.

### Onda 4 — LOW

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-14 | F-019 | `observability/logger.py` | 5 arquivos com `print()` no caminho de requisição | — |

Critério de aceite: **smoke test 22/22 endpoints conformes → commit**.

> TR-14 chega à Onda 4 **por descida**: seu teto é a Onda 1 (resolve AP-07, CRITICAL), mas AP-07
> não virou finding, e o finding mais severo que ele resolve é F-019 (AP-19, LOW). É o caso que
> `SKILL.md` descreve para a Onda 4 — *"recebe TR por descida, quando só o AP LOW virou finding"*.

### Ondas vazias

**Nenhuma.** As quatro ondas receberam TR. `F-023` (AP-28) não agenda TR algum e, por isso,
**não consta deste plano** — ele é reportado e não corrigido.

### Cobertura do plano

23 findings · 22 endereçados por TR · 1 (`F-023`) reportado sem correção, por estar fora do
escopo da skill.

### Itens NEEDS-DECISION

Cada item traz a opção recomendada e a alternativa, para que um único `y` continue sendo
suficiente. Responder apenas `y` significa adotar todas as recomendações abaixo.

| # | Decisão | Recomendado | Alternativa |
|---|---|---|---|
| **ND-1** | **Quais rotas passam a exigir autenticação** (define BC-3). | As 10 de escrita/remoção **+** as 3 de leitura de dados de terceiros (`GET /users`, `GET /users/<id>`, `GET /users/<id>/tasks`). `GET /tasks*`, `GET /categories`, `GET /reports/*`, `/`, `/health` seguem públicas. | Exigir autenticação em **todas** as 22 — mais seguro, mas quebra 20 dos 22 registros do baseline e transforma quase todo o smoke test em fluxo autenticado. |
| **ND-2** | **Migração dos hashes MD5 existentes** (TR-03). Os hashes atuais não são convertíveis para uma primitiva lenta sem a senha em claro. | Reidratação no próximo login bem-sucedido: manter a coluna, detectar o formato antigo, validar por MD5 uma última vez e regravar com a primitiva nova. Zero impacto no usuário. | Invalidar todas as senhas e exigir redefinição — mais seguro (os MD5 já vazaram por `GET /users/<id>`), porém derruba os 3 usuários semeados e exige fluxo de reset que o projeto não tem. |
| **ND-3** | **Rotação da credencial SMTP** exposta em `services/notification_service.py:9-10`. Apagar o arquivo **não** remove o segredo do histórico do git. | Rotacionar a senha da conta `taskmanager@gmail.com` fora deste repositório, **antes** do merge, e tratar o valor atual como comprometido. A skill não pode fazer isso. | Reescrever o histórico do repositório — invasivo, e ainda assim exige a rotação. |
| **ND-4** | **Direção da uniformização de contrato** (BC-5/BC-6). Alinhar a coleção ao detalhe, ou o detalhe à coleção? | Alinhar **a coleção ao detalhe** (remover `user_name`, `category_name`, `task_count`): elimina o N+1 de F-012 no mesmo movimento. | Alinhar **o detalhe à coleção** (acrescentar os campos derivados a `GET /tasks/<id>` e `GET /users/<id>`): preserva o que os clientes de `GET /tasks` já consomem, mas mantém o custo por item. |
| **ND-5** | **Tamanho de página default** (BC-4). | `limit=50`, máximo `200`, array na raiz preservado (sem envelope) — mantém o `shape` do baseline como array. | Envelope `{"items": [...], "total": n}` — mais informativo, porém muda o `shape` de 4 endpoints de array para objeto, ampliando a superfície de breaking change. |
| **ND-6** | **Política de senha.** Hoje o mínimo é 4 caracteres (`routes/user_routes.py:64,115`). | **Não alterar nesta refatoração.** É decisão de produto, explicitamente fora do escopo da skill; TR-03 troca a derivação sem tocar na política. | Elevar para 8+ com requisitos de composição — melhora real, mas invalida as senhas dos 3 usuários semeados e é mudança de produto, não de arquitetura. |

---

## Fora do escopo desta skill

Observado, real, e **não** corrigido pela Fase 3:

- **Infraestrutura de qualidade (F-023).** Suíte de testes, linter, CI e `.python-version`. A
  skill declara "escrita da suíte de testes do projeto" fora do escopo. TR-01 e TR-12 produzem
  cobertura parcial (`.env.example` e uma regra de lint) como consequência, não como escopo.
- **Política de senha (ND-6)** e qualquer decisão de retenção de dados pessoais.
- **Rotação efetiva dos segredos** expostos em `app.py:13` e `services/notification_service.py:10`
  (ND-3): a skill os remove do código, mas a rotação acontece fora do repositório.
- **Troca de framework, ORM, banco ou runtime.** SQLite, Flask e SQLAlchemy permanecem.
- **Enforcement de FK no SQLite** exige ligar `PRAGMA foreign_keys` por conexão; TR-16 declara a
  constraint no schema, mas a decisão de ligar o pragma em runtime altera comportamento de
  escritas existentes e fica registrada como consequência a validar.
- **Deploy e CI.**

---

## Próximo passo

Total: **23 findings** (4 CRITICAL · 5 HIGH · 9 MEDIUM · 5 LOW) ·
**8 breaking changes** propostas · plano em **4 ondas com TR** (vazias: nenhuma).

Nenhum arquivo do projeto foi modificado até aqui.

    Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
