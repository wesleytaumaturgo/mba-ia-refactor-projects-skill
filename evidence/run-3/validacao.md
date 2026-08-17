# run-3 · Validação da refatoração · `task-manager-api`

Validação final da Fase 3, conforme `SKILL.md` §Validação final: as três verificações que **não**
são herdadas das ondas verdes, porque nenhuma delas foi testada por onda alguma. Mais as duas
confirmações específicas pedidas no gate.

Estado validado: commit `e86217f`. Baseline: `f580ee5`, `M = 22`.

---

## 1. Boot pós-refatoração

### Comando exato

O fluxo mudou: a DDL saiu do caminho de boot (TR-16), então a criação de schema virou passo
explícito. O README foi atualizado para refletir isso.

```console
$ python -m infra.migrator upgrade
$ python seed.py
$ python app.py
```

### Saída LITERAL

```console
$ python -m infra.migrator upgrade
Migrações aplicadas: 0001_initial.sql

$ python seed.py
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks

$ python app.py
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 505-623-803
127.0.0.1 - - [17/Aug/2026 17:32:23] "GET /health HTTP/1.1" 200 -
```

Duas diferenças em relação ao baseline, ambas consequência de TR-01 e **não** regressão:

- **`Running on http://127.0.0.1:5000`**, e não mais `Running on all addresses (0.0.0.0)`. O bind
  passou a vir de `HOST`, cujo default é `127.0.0.1`. No baseline o servidor escutava em todas as
  interfaces com o debugger ligado — que era metade de F-001.
- O aviso de servidor de desenvolvimento continua porque `APP_ENV=development` no `.env` local.
  Em `APP_ENV=production` o boot **recusa** subir com `DEBUG` ligado (verificado em `fase3.md` §2).

Boot verde pelos três critérios observáveis da `validation-protocol.md` §3 — porta escutando,
processo vivo depois de alguns segundos, primeira requisição respondida:

```console
BOOT VERDE (porta escutando · processo vivo · primeira requisicao HTTP 200)
```

### Instalação limpa a partir do manifesto

```console
$ python -m venv venv-check && venv-check/bin/pip install -r requirements.txt
$ venv-check/bin/pip freeze
blinker==1.9.0 click==8.4.2 Flask==3.0.0 Flask-Cors==4.0.0 Flask-SQLAlchemy==3.1.1
greenlet==3.5.5 itsdangerous==2.2.0 Jinja2==3.1.6 MarkupSafe==3.0.3 python-dotenv==1.0.0
SQLAlchemy==2.0.52 typing_extensions==4.16.0 Werkzeug==3.1.8

$ venv-check/bin/python -m infra.migrator upgrade
Migrações aplicadas: 0001_initial.sql
$ venv-check/bin/python seed.py
  10 tasks
$ venv-check/bin/python -c "import app; print('IMPORT OK')"
IMPORT OK
```

---

## 2. As 22 requisições do baseline

```console
$ python smoke.py reports/baseline-task-manager-api.json --wave 3 --auth
Smoke test: 22/22 endpoints conformes ao baseline
VERDE
```

Comparação nos cinco critérios da §4, na ordem: endpoint existe · método e path idênticos ·
status idêntico · media type **e** forma do corpo no mesmo termo em que o baseline registrou
(`shape` contra `shape`) · valores não-voláteis coerentes.

| Método | Endpoints | Status | Resultado |
|---|---|---|---|
| GET | 12 | 200 ×12 | 12/12 conformes |
| POST | 4 | 200 ×1 · 201 ×3 | 4/4 conformes |
| PUT | 3 | 200 ×3 | 3/3 conformes |
| DELETE | 3 | 200 ×3 | 3/3 conformes |
| **Total** | **22** | — | **22/22** |

Path, verbo e status de sucesso **preservados nos 22**. Nenhum endpoint removido, nenhum
adicionado.

### Verificação 3 do protocolo — diff de forma e media type contra a seção Breaking changes aprovada

```console
  GET /users
    media    : application/json -> application/json  OK
    removidos: ['task_count']   declarado em BC-6: ['task_count']
    acrescidos NAO declarados: nenhum
    veredito : CONFORME a BC aprovada

  GET /users/1
    media    : application/json -> application/json  OK
    removidos: ['password']   declarado em BC-1: ['password']
    acrescidos NAO declarados: nenhum
    veredito : CONFORME a BC aprovada

  GET /tasks
    media    : application/json -> application/json  OK
    removidos: ['category_name', 'user_name']   declarado em BC-5: ['category_name', 'user_name']
    acrescidos NAO declarados: nenhum
    veredito : CONFORME a BC aprovada

  POST /login
    media    : application/json -> application/json  OK
    removidos: ['password']   declarado em BC-1+BC-2: ['password']
    acrescidos NAO declarados: nenhum
    veredito : CONFORME a BC aprovada
```

**Zero divergências não declaradas.** As 8 breaking changes aprovadas, uma a uma:

| # | Declarada | Aplicada | Evidência |
|---|---|---|---|
| BC-1 | `password` sai de 4 respostas de User | ✅ | acima; `GET /users`, `GET /users/1`, `POST /users`, `PUT /users/<id>`, `POST /login` sem o campo |
| BC-2 | `token` vira credencial assinada com expiração | ✅ | `eyJzdWIiOjEsInJvbGUiOiJhZG1pbiIsImlhdCI6…`; `fake-jwt-token-1` agora responde 401 |
| BC-3 | rotas passam a responder 401 sem credencial | ✅ | **12 rotas**, conferidas uma a uma (ver §5 sobre a contagem) |
| BC-4 | paginação, default 50 / teto 200, array na raiz | ✅ | `GET /tasks` → 50 de 130; `?limit=999` → teto; raiz continua `list` |
| BC-5 | `user_name`/`category_name` saem do item de `GET /tasks` | ✅ | diff acima |
| BC-6 | `task_count` sai do item de `GET /users` | ✅ | diff acima |
| BC-7 | envelope de erro uniformizado com `code`/`message` | ✅ | 7 caminhos de erro conferidos em `fase3.md` §4; acrescentou `correlation_id` |
| BC-8 | 500 → 400 em entrada de tipo inválido | ✅ | os 3 caminhos que davam 500 agora dão 400 |

> **BC-7 entregou a mais do que declarou:** o envelope aprovado era
> `{"error": {"code", "message"}}` e o implementado é
> `{"error": {"code", "message", "correlation_id"}}`, com `field` opcional. O campo extra vem do
> passo 1 do TR-13 (*"código estável, mensagem para humano, identificador de correlação"*).
> Registro como **acréscimo além do declarado**, não como divergência: os caminhos de erro não
> constam do baseline capturado (§4 do protocolo compara o que a §2 capturou, e a captura usou
> requisições representativas válidas), então não afeta `M`. Mas quem aprovou BC-7 aprovou dois
> campos e recebeu três.

### Mudanças de comportamento fora do contrato HTTP capturado, declaradas aqui

Nenhuma delas aparece no smoke test — todas são cenários que o baseline não capturou. Declaro-as
explicitamente porque são mudanças reais que um consumidor pode notar:

1. **`PUT /tasks/<id>` com título vazio ou curto passa de 200 para 400.** É a resolução da
   divergência que F-011 apontava como agravante decisivo: o `POST` exigia título válido e o
   `PUT` aceitava `{"title": ""}` e gravava. TR-08 passo 2 obriga a escolher **explicitamente**
   qual regra vence — venceu a do `POST`. Consequência inerente à correção aprovada em F-011.
2. **`PUT /users/<id>` com nome vazio passa de 200 para 400**, pela mesma razão.
3. **Campos desconhecidos no payload passam a ser descartados em vez de ignorados.** Antes já não
   eram gravados (não havia bind em massa — AP-14 não era finding); agora a allowlist é explícita
   e o comportamento é o mesmo. Sem efeito observável.
4. **`POST /users` passa a exigir credencial** (BC-3). Isso significa que **não há auto-cadastro**:
   o primeiro usuário nasce do `seed.py`. Está dentro do que ND-1 aprovou, mas vale dizer em voz
   alta porque muda o desenho do produto, não só a segurança.
5. **`DELETE /categories/<id>` passou a desassociar as tasks** (`category_id → NULL`) em vez de
   deixá-las apontando para uma linha inexistente. O corpo da resposta é idêntico; o efeito
   colateral no banco mudou — para o que F-008 descrevia como correto.
6. **O bind de rede mudou de `0.0.0.0` para `127.0.0.1`** por default. Quem dependia de acessar a
   API de outra máquina precisa definir `HOST=0.0.0.0` no ambiente.

---

## 3. Árvore de diretórios resultante

```text
task-manager-api/
├── app.py                        composition root: lê config, monta o grafo, sobe
├── database.py                   instancia o objeto SQLAlchemy
├── seed.py                       dados de demonstração, execução manual, recusa produção
├── .env.example                  chaves sem valores reais
├── .python-version               3.12
├── requirements.txt              4 dependências, todas importadas
├── requirements-dev.txt          ruff
├── ruff.toml                     regra que barra a regressão de TR-12
├── config/                       ler ambiente, validar obrigatórios, expor tipado
│   └── settings.py
├── models/                       forma dos dados e invariantes que valem sempre
│   ├── task.py  user.py  category.py
├── repositories/                 único lugar que conhece o ORM
│   ├── task_repository.py  user_repository.py  category_repository.py
│   └── unit_of_work.py           fronteira transacional
├── services/                     regra de negócio: decide O QUE acontece
│   ├── task_service.py  user_service.py  category_service.py  report_service.py
│   └── errors.py                 tipos de erro de domínio
├── controllers/                  tradução protocolo ↔ domínio
│   ├── task_controller.py  user_controller.py  category_controller.py  report_controller.py
├── routes/                       método + path → handler + middlewares. Sem lógica
│   ├── task_routes.py  user_routes.py  category_routes.py  report_routes.py
├── middlewares/                  transversais
│   ├── auth.py                   negar por padrão + autorização por papel
│   ├── error_handler.py          envelope único, mapa tipo→status
│   └── rate_limit.py             limite de taxa no login
├── dto/                          projeção de saída com allowlist
│   ├── task_dto.py  user_dto.py  category_dto.py
├── validators/                   invariantes de entrada + allowlist de bind
│   ├── base.py  task_validator.py  user_validator.py  category_validator.py
│   └── pagination.py
├── security/                     derivação de senha e credencial assinada
│   ├── passwords.py  tokens.py
├── infra/                        migração versionada
│   └── migrator.py
├── observability/                logger com níveis e redação
│   └── logger.py
├── migrations/
│   └── 0001_initial.sql          schema com FK, CHECK, UNIQUE, NOT NULL e índices
└── utils/                        RELIGADO — utilitários com chamador real
    └── helpers.py
```

**Antes → depois:** 15 arquivos `.py` / 1158 LOC → 53 arquivos `.py` / 2286 LOC.
Maior arquivo: `routes/task_routes.py` com **299 LOC** → `app.py` com **126 LOC** (o composition
root). Os três módulos de rota, que somavam 733 LOC (63,3% do projeto), somam agora **85 LOC**.

| Camada | LOC | Camada | LOC |
|---|---|---|---|
| services | 406 | security | 133 |
| validators | 276 | app.py | 126 |
| middlewares | 229 | infra | 118 |
| repositories | 199 | dto | 115 |
| controllers | 185 | models | 105 |
| seed.py | 116 | config | 101 |
| routes | 85 | observability | 56 |
| utils | 33 | database.py | 3 |

### Verificação 2 do protocolo — responsabilidade a responsabilidade

Cada responsabilidade de `mvc-guidelines.md` §2 tem **um** lugar identificável, e esse lugar é
**alcançável pelo mecanismo de resolução da stack** (import explícito, §6):

```console
  === alcancabilidade a partir do entry point (import de app.py) ===
  pacote           carregado?   modulos efetivamente resolvidos
  config           SIM          settings
  models           SIM          category, task, user
  repositories     SIM          category_repository, task_repository, unit_of_work, user_repository
  services         SIM          category_service, errors, report_service, task_service, user_service
  controllers      SIM          category_controller, report_controller, task_controller, user_controller
  routes           SIM          category_routes, report_routes, task_routes, user_routes
  middlewares      SIM          auth, error_handler, rate_limit
  dto              SIM          category_dto, task_dto, user_dto
  validators       SIM          base, category_validator, pagination, task_validator, user_validator
  security         SIM          passwords, tokens
  infra            SIM          migrator
  observability    SIM          logger
  utils            SIM          helpers
  database         SIM          (modulo raiz)

  TODAS as camadas sao alcancaveis: True
```

Direção de dependência (§3) verificada por leitura de imports:

```console
  controllers/ e routes/ limpos de persistencia   (nenhum db.session, nenhum .query.)
  nenhum service importa protocolo                (nenhum request/jsonify/flask)
  instanciacao de infraestrutura: so em app.py    (composition root)
```

Nenhuma responsabilidade ficou sem lugar, e nenhuma ficou espalhada por vários. Nenhuma árvore
paralela foi erguida: `models/`, `routes/` e `utils/` mantiveram nome e posição, como a
precedência 1 da §4 determina.

---

## 4. Verificação 1 do protocolo — reexecução do sinal de detecção de cada CRITICAL e HIGH

Sinal do AP correspondente rodado contra o **código atual**, finding a finding.

| Finding | AP | Sinal ainda dispara? | Evidência |
|---|---|---|---|
| F-001 | AP-02 | **não** | `grep` por literal sensível e `debug=True` → vazio; leitura de ambiente existe em `config/settings.py`; fail-fast comprovado |
| F-002 | AP-03 | **não** | nenhum DTO/model projeta `password`; as 4 respostas conferidas retornam 0 ocorrências |
| F-003 | AP-04 | **não** | MD5 só no caminho de compatibilidade (`security/passwords.py:40`); mesma senha → valores diferentes |
| F-004 | AP-05 | **não** | 12 rotas → 401 sem credencial; token antigo → 401; `role` lido em 5 pontos de decisão |
| F-005 | AP-13 | **não** | zero `db.session`/`.query.` em `controllers/` e `routes/`; camada de repositório interposta |
| F-006 | AP-08 | **não** | zero regra de negócio em `controllers/`/`routes/`; status vem do tipo do erro |
| F-007 | AP-21 | **não** | zero `create_all`; `PRAGMA foreign_keys=1` (era 0); 4 índices (era 0); 3 CHECKs (era 0) |
| F-008 | AP-11 | **não** | 10 blocos transacionais nos services; zero escritas fora de unidade de trabalho |
| F-009 | AP-09 | **não** | instanciação só no composition root; repositório construível com duplo de banco |

**9/9 CRITICAL e HIGH corrigidos.** Nenhum sinal volta a disparar.

### Findings MEDIUM e LOW

Não exigido pela verificação 1, mas conferido para fechar o quadro:

| Finding | AP | Corrigido? | Evidência |
|---|---|---|---|
| F-010 | AP-17 | ✅ | `is_overdue` e `completion_rate` com 3 chamadores cada (eram 0) |
| F-011 | AP-12 | ✅ | 0 invariantes inline em `controllers/`/`routes/`; POST e PUT rejeitam igual |
| F-012 | AP-15 | ✅ | queries constantes (1/2/2/11) com 11 e com 51 tasks |
| F-013 | AP-18 | ✅ | 0 `except:` pelados (eram 12) |
| F-014 | AP-23 | ✅ | `GET /tasks` e `GET /tasks/1` têm a mesma forma |
| F-015 | AP-22 | ✅ | `GET /tasks` sem parâmetros → máx. 50; teto 200; 400 em `limit` inválido |
| F-016 | AP-16 | ✅ | 0 `utcnow` + 0 `Query.get` (eram 18 + 16); `-W error` limpo; linter barra a volta |
| F-017 | AP-20 | ✅ | `origins=settings.cors_origins`; origem não listada recusada |
| F-019 | AP-19 | ✅ | 0 `print` no caminho de requisição; logger com nível, timestamp e allowlist |
| F-020 | AP-26 | ✅ | camada morta removida; 0 dependências declaradas-e-não-importadas (ver abaixo) |
| F-021 | AP-25 | ✅ | `PRIORITY_LABELS` e `HIGH_PRIORITY_THRESHOLD` nomeados |
| F-022 | AP-27 | ✅ | blueprint de Category = `categories` (era `reports`) |

### O residual que esta validação encontrou

**F-020 estava PARCIALMENTE corrigido ao fim da Onda 4.** A camada morta e os símbolos mortos
saíram na Onda 3, mas duas das três dependências declaradas-e-não-importadas continuavam no
manifesto:

```console
  marshmallow        importado? NAO  <-- ainda morta
  requests           importado? NAO  <-- ainda morta
  python-dotenv      importado? SIM
```

`python-dotenv` passou a ser usada por TR-01, como o relatório previa. `marshmallow` não: a
validação declarativa foi implementada em `validators/` com a biblioteca padrão, então a
dependência permaneceu morta em vez de virar viva. `requests` nunca teve correspondente.

Corrigido com um commit próprio, com smoke test verde (`e86217f`), e a instalação limpa a partir
do manifesto reduzido foi verificada (§1). **Registro aqui em vez de silenciar** porque a
verificação 1 existe justamente para pegar o que a onda declarou resolvido e não resolveu por
inteiro.

### Não resolvidos

| Finding | AP | Razão |
|---|---|---|
| **F-023** | AP-28 | **Fora do escopo declarado da skill.** O catálogo é explícito: AP-28 é reportado e não corrigido, e o plano do gate deliberadamente **não** o incluiu. Continua sem suíte de testes e sem CI. |

Coberturas parciais que outros TRs produziram como **consequência**, não como escopo — as duas
que o próprio catálogo prevê: TR-01 publicou `.env.example`; TR-12 instalou `ruff.toml`,
`.python-version` e `requirements-dev.txt`. O que falta de F-023 é a suíte de testes e o pipeline.

**Findings corrigidos: 22/23.**

---

## 5. Correção de contagem em BC-3

A seção Breaking changes aprovada no gate diz *"As **10** rotas de escrita e destrutivas … e as
**3** de leitura de terceiros"*, e o rodapé do relatório soma **13**.

A **enumeração** aprovada está correta e foi cumprida à risca: POST/PUT/DELETE sobre `/tasks`,
`/users` e `/categories` (3 verbos × 3 recursos = **9**), mais `GET /users`, `GET /users/<id>` e
`GET /users/<id>/tasks` (**3**). Total: **12**, não 13.

Conferido rota a rota contra o código atual:

```console
    DELETE /users/2        -> 401       POST /categories      -> 401
    POST /tasks            -> 401       PUT /categories/1     -> 401
    PUT /tasks/1           -> 401       DELETE /categories/1  -> 401
    DELETE /tasks/1        -> 401       GET /users            -> 401
    GET /users/1           -> 401       GET /users/1/tasks    -> 401
    POST /users            -> 401       PUT /users/1          -> 401
```

12 rotas exigem credencial; 10 permanecem públicas (`/`, `/health`, `POST /login`, as 4 leituras
de task, `GET /categories`, e os 2 relatórios). 12 + 10 = 22. ✅

O erro era de **rótulo numérico no relatório da Fase 2**, não de plano nem de execução. Registrado
porque um número errado num artefato de aceite é exatamente o tipo de coisa que a checagem existe
para pegar — inclusive contra o próprio relatório.

---

## 6. As duas confirmações pedidas no gate

### 6.1 O conteúdo de `services/` foi registrado como finding ANTES da remoção — **CONFIRMADO**

`mvc-guidelines.md` §6 exige: *"registre na Fase 2, como finding, tudo o que a camada inalcançável
contém … **antes** de propor a remoção"*.

Provado pelo histórico, não por afirmação:

```console
   commit que ADICIONOU o relatorio com F-020 : 10cc682
   commit que REMOVEU notification_service.py : 3235b4b
   o relatorio e ANCESTRAL do commit de remocao? SIM
```

O relatório aprovado no gate inventariava, textualmente, tudo o que sairia: a classe
`NotificationService`, os métodos `send_email`, `notify_task_assigned`, `notify_task_overdue`,
`get_notifications`, o acumulador `self.notifications`, e — o que mais importa — **a credencial
SMTP versionada** (`notification_service.py:9-10`), com a observação de que apagar o arquivo
**não** a remove do histórico do git.

Essa observação virou **ND-3** e continua **pendente de ação humana**: o segredo
`taskmanager@gmail.com` / `senha123` está no histórico deste repositório e precisa ser rotacionado
fora dele. A skill removeu o arquivo; a rotação não é coisa que ela possa fazer.

### 6.2 `utils/` foi RELIGADO por TR-15, não removido — **CONFIRMADO**

`mvc-guidelines.md` §6 passo 3: *"Alcançável → adote o diretório, preserve sua nomenclatura e
**ligue** o que estiver solto. A transformação é de ligação (TR-15), não de criação."*

```console
$ git ls-files utils/
     utils/__init__.py
     utils/helpers.py
```

| | baseline `f580ee5` | HEAD `e86217f` |
|---|---|---|
| diretório existe | sim | **sim** |
| importadores | 1 (`report_routes.py:7`) | **13 módulos** |
| símbolos importados | 2 | 2 |
| **sítios de chamada** | **0** | **25** (`utc_now` 16, `format_date` 9) |

```console
quem importa utils/ agora:
  app.py, seed.py, dto/user_dto.py, dto/task_dto.py, dto/category_dto.py,
  repositories/task_repository.py, services/report_service.py, services/task_service.py,
  controllers/user_controller.py, controllers/task_controller.py,
  models/user.py, models/task.py, models/category.py
```

**O contraste com `services/` é o ponto da regra.** As duas pastas tinham nome de camada e
conteúdo não exercido. Mas `utils/` **era alcançável** (import explícito em
`report_routes.py:7`, o mecanismo real desta stack) e `services/` **não era** (zero importadores).
A regra de alcançabilidade levou uma a ser **ligada** e a outra a ser **substituída** — e o
veredito foi tomado na Fase 2, antes de qualquer código mudar.

Os símbolos de `utils/` que não tinham chamador nem podiam ganhar um foram **consolidados na
camada que os governa**, não recriados nem simplesmente apagados:

| Símbolo morto no baseline | Para onde foi |
|---|---|
| `calculate_percentage` | `TaskService.completion_rate` — 3 chamadores |
| `process_task_data` (52 LOC) | `validators/task_validator.py` — allowlist + invariantes |
| `parse_date` | `validators/base.py` |
| `validate_email` | `validators/user_validator.py:is_valid_email` |
| `is_valid_color` | `validators/category_validator.py:is_valid_color` |
| `sanitize_string` | `validators/base.py:require_text` (faz `strip` no caminho de escrita) |
| `log_action` | `observability/logger.py` — com nível, timestamp e redação |
| `VALID_STATUSES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH` | `models/task.py` |
| `VALID_ROLES`, `MIN_PASSWORD_LENGTH` | `models/user.py` |
| `DEFAULT_COLOR` | `models/category.py` |
| `DEFAULT_PRIORITY` | `validators/task_validator.py:DEFAULTS` |
| `generate_id` | removido — sem correspondente no domínio |
| `format_date` | **permaneceu em `utils/helpers.py`** — 9 chamadores nos DTOs |

---

## 7. Checklist MVC do enunciado, item a item

| Exigência | Estado | Onde |
|---|---|---|
| Separação de responsabilidades em camadas | ✅ | 13 pacotes, cada um com uma responsabilidade, todos alcançáveis |
| Model isolado da apresentação | ✅ | `models/` só define forma e invariantes; serialização em `dto/` |
| Controller sem acesso direto a dados | ✅ | zero `db.session`/`.query.` em `controllers/` |
| Rotas sem lógica | ✅ | `routes/` = 85 LOC, só tabelas de rota |
| Camada de serviço com a regra de negócio | ✅ | `services/`, 406 LOC, sem importar protocolo |
| Acesso a dados isolado | ✅ | `repositories/`, único lugar com ORM |
| Configuração fora do código | ✅ | `config/settings.py` + `.env.example`, fail-fast |
| Tratamento de erro centralizado | ✅ | `middlewares/error_handler.py`, envelope único |
| Autenticação/autorização | ✅ | negar por padrão + papel lido do schema |
| Contrato de endpoints preservado | ✅ | 22/22 path, verbo e status de sucesso |

---

## 8. Veredito

```console
PHASE 3: REFACTORING COMPLETE
─────────────────────────────────────────────
Waves         : 1 CRITICAL ✓ · 2 HIGH ✓ · 3 MEDIUM ✓ · 4 LOW ✓
Smoke test    : 22/22 endpoints conform to baseline
Breaking chg  : 8 applied, all declared in the approved report
Findings fixed: 22/23 (23 reported, not fixed: F-023)
History       : f580ee5 → 7fd2012 → 9e81e4d → 3235b4b → 303c1f9 → e86217f
─────────────────────────────────────────────
```

| Critério de aceite do enunciado | Resultado |
|---|---|
| CA-1 — Fase 1 detecta a stack | ✅ 15/15 campos |
| CA-2 — Fase 2 encontra ≥ 5 findings | ✅ **23** |
| CA-3 — ≥ 1 CRITICAL ou HIGH | ✅ **9** |
| **CA-4 — aplicação funciona após a refatoração** | ✅ **sobe e responde 22/22 conforme o baseline** |

**Ressalvas honestas, para não declarar mais do que foi feito:**

- **F-023 não foi corrigido** e não deveria ter sido: sem suíte de testes, a única rede de
  proteção desta refatoração é o smoke test de 22 endpoints. É pouco para 2286 LOC.
- **BC-7 entregou um campo a mais** do que o gate aprovou (`correlation_id`).
- **F-020 precisou de um commit extra** depois da Onda 4 — a onda declarou o finding resolvido e
  ele estava resolvido pela metade.
- **ND-3 continua pendente:** a credencial SMTP está no histórico do git e só uma pessoa pode
  rotacioná-la.
- **A contagem de BC-3 no relatório da Fase 2 estava errada** (13 declarado, 12 real). A
  enumeração, que é o que foi aprovado, estava certa.
