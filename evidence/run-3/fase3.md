# run-3 · Fase 3 — Refatoração · `task-manager-api`

Continuação de [`fase2.md`](fase2.md). Validação final em [`validacao.md`](validacao.md).

Referências carregadas nesta fase, conforme o `SKILL.md`: `mvc-guidelines.md` integral,
`validation-protocol.md`, e do `refactor-playbook.md` **apenas o índice e as seções dos 17 TRs
que a auditoria acionou** (TR-02 não foi acionado e não foi lido).

---

## Gate

```console
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

Resposta explícita, com uma instrução adicional sobre O-3 (ver §1). O plano executado é o
**plano apresentado no gate** — mesmos TRs, mesmas ondas. Nenhuma revisão de escopo no caminho.

`M = 22`. Toda onda exige **22/22** para ser verde.

---

## 1. O-3 — ordenação dentro da Onda 1 para minimizar o retrabalho de TR-04

O gate registrou a tensão: o playbook avisa que *"aplicar TR-04 antes de haver camadas obriga a
refazê-lo"*, mas a regra de onda põe TR-04 na Onda 1 (severidade de F-002, CRITICAL) e TR-06 na
Onda 2 (severidade de F-005, HIGH).

**Ordenação escolhida:** `TR-01 → TR-03 → TR-04 → TR-05`.

- **TR-01 primeiro** é imposição do playbook: TR-05 depende da chave de assinatura que ele traz
  do ambiente.
- **TR-03 antes de TR-04** porque TR-03 mexe em `models/user.py` (derivação) e TR-04 mexe na
  projeção do mesmo model; fazer a derivação primeiro evita tocar o arquivo duas vezes.
- **TR-05 por último** porque consome os dois anteriores: a chave de TR-01 e o DTO de TR-04 (a
  resposta de login).

**A decisão que efetivamente reduziu o retrabalho não foi a ordem, foi o lugar.** O DTO de TR-04
nasceu direto em `dto/user_dto.py` — o caminho **definitivo** que o plano aprovado já previa para
ele (a linha de TR-13 na Onda 3 cria `dto/{task,category}_dto.py` no mesmo diretório). Como
consequência, quando TR-06 rodou na Onda 2, ele **não moveu arquivo nenhum**: apenas trocou o
chamador, de `routes/user_routes.py` para `controllers/user_controller.py`.

**Retrabalho efetivamente pago:** a linha de import do DTO mudou de arquivo, e `User.to_dict()`
— que TR-04 reduziu a um encaminhamento para `user_public()` — foi eliminada em TR-06, quando os
controllers passaram a chamar o DTO diretamente. Custo real: **duas edições de uma linha**.
Nenhum arquivo criado em Onda 1 precisou ser movido, renomeado ou reescrito.

Não houve ordenação que eliminasse o retrabalho por completo, porque a causa não é a ordem
dentro da onda e sim a distância entre as ondas. Registrado como observação de execução, conforme
instruído.

---

## 2. Onda 1 — CRITICAL · TR-01, TR-03, TR-04, TR-05

Resolve F-001, F-002, F-003, F-004 e F-018 (que desceu junto de TR-05).

### Boot após cada TR

| # | TR | Boot | Observação |
|---|---|---|---|
| 1 | TR-01 | ✓ verde | exigiu criar `.env` local antes — falso vermelho previsto pelo próprio TR |
| 2 | TR-03 | ✓ verde | — |
| 3 | TR-04 | ✓ verde | — |
| 4 | TR-05 | ✓ verde | — |

O risco que TR-01 nomeia (*"fail-fast transforma variável esquecida em aplicação que não sobe"*)
se materializou como previsto e foi tratado antes do boot, não depois:

```console
$ cp .env.example .env      # + SECRET_KEY gerada localmente
$ git check-ignore -v .env
.gitignore:29:.env	.env
$ ./boot.sh
BOOT VERDE (porta escutando · processo vivo · primeira requisicao HTTP 200)
```

### Verificações que os TRs exigem

**TR-01 — sobe com as variáveis; falha explícita nomeando a chave quando falta; nenhum literal
sensível sobrevive.**

```console
$ APP_ENV=production DEBUG=false python -c "from config import load_settings; load_settings()"
ConfigError levantada no boot:
  Variável de ambiente obrigatória ausente: SECRET_KEY. Copie .env.example para .env e preencha-a.

$ APP_ENV=production SECRET_KEY=chave-real DEBUG=true python -c "..."
ConfigError levantada no boot:
  DEBUG não pode ficar ligado em produção.

$ APP_ENV=production SECRET_KEY=chave-real DEBUG=false python -c "..."
  <Settings env=production debug=False host=127.0.0.1:5000>

$ grep -rnE "super-secret-key-123|senha123|smtp\.gmail\.com|taskmanager@gmail\.com|debug *= *True" --include='*.py' .
  nenhum literal sensivel encontrado
```

> Escolha registrada: `SECRET_KEY` é **obrigatória em produção** e cai num placeholder
> declaradamente inválido em desenvolvimento. É exatamente o limite superior que o AP-02 admite
> (*"default de desenvolvimento E o valor de produção vem do ambiente com precedência E o nome
> do valor não sugere uso produtivo"*), e mantém o projeto bootável numa clonagem limpa.

**TR-03 — credenciais ilegíveis; mesma senha produz valores diferentes; login antigo funciona e
o valor migra no primeiro sucesso.**

```console
  formato: pbkdf2_sha256$260000$74fea486232a937f269...
  len = 118 | coluna = 255 -> CABE, sem ampliar        (passo 4 do TR: não foi preciso ampliar)

  a = pbkdf2_sha256$260000$3fa0e2adcf05a5ccccb0fc9c210d1110$5...
  b = pbkdf2_sha256$260000$09469404456d594998d88c7ba216a0c4$6...
  iguais? False | ambos verificam? True True
```

Reidratação, exercida contra os hashes MD5 que o seed antigo deixou:

```console
--- antes do login ---
1|81dc9bdb52d04dc20036dbd8313ed055
2|e2fc714c4727ee9395f324cd2e7f331f
3|1a1dc91c907325c69271ddf0c944bc72

$ curl -X POST /login -d '{"email":"joao@email.com","password":"1234"}'   → HTTP 200

--- depois do login ---
  (1, 'joao@email.com',   'pbkdf2_sha256$260000$0c501939e8f64c0ca333fa61')   ← migrado
  (2, 'maria@email.com',  'e2fc714c4727ee9395f324cd2e7f331f')                ← ainda legado
  (3, 'pedro@email.com',  '1a1dc91c907325c69271ddf0c944bc72')                ← ainda legado
```

Só o usuário que autenticou migrou. É o comportamento que ND-2 aprovou: zero impacto no usuário,
sem fluxo de reset.

**TR-04 — nenhuma resposta contém campo de credencial; a de autenticação carrega só a credencial
de sessão e a identificação mínima.**

```console
$ curl -s /login -d '{"email":"joao@email.com","password":"1234"}'
{
    "message": "Login realizado com sucesso",
    "token": "fake-jwt-token-1",
    "user": { "active": true, "created_at": "...", "email": "joao@email.com",
              "id": 1, "name": "João Silva", "role": "admin" }
}
```

> `token` ainda no formato antigo aqui porque TR-05 ainda não tinha rodado. A projeção por
> allowlist já está em vigor: `password` sumiu das 4 respostas.

**TR-05 — 401 sem credencial; 403 com papel insuficiente; como no baseline com credencial válida;
tentativas repetidas de login barradas.**

```console
--- (1) rota privilegiada SEM credencial -> 401 ---
  DELETE /users/2        -> HTTP 401
  POST /tasks            -> HTTP 401
  PUT /categories/1      -> HTTP 401
  GET /users             -> HTTP 401

--- (2) rota publica SEM credencial -> como no baseline ---
  GET /                  -> HTTP 200
  GET /health            -> HTTP 200
  GET /tasks             -> HTTP 200
  GET /tasks/stats       -> HTTP 200
  GET /categories        -> HTTP 200
  GET /reports/summary   -> HTTP 200

--- (3) token forjado -> 401 ---
  token antigo 'fake-jwt-token-1' -> HTTP 401

--- (4) com credencial valida -> como no baseline ---
  token emitido: eyJzdWIiOjEsInJvbGUiOiJhZG1pbiIsImlhdCI6MTc4Njk5...
  GET /users com credencial -> HTTP 200

--- (5) papel insuficiente -> 403 (le o 'role' que o schema modela) ---
  maria (role=user) DELETE /users/3      -> HTTP 403
  maria tenta se promover a admin        -> HTTP 403  {"error":"Permissão insuficiente para alterar o papel"}
  joao (role=admin) mesma operacao       -> HTTP 200

--- (6) limite de taxa (limite=10/300s) ---
  tentativa  1..10 -> 401
  tentativa 11 -> 429
  tentativa 12 -> 429
  HTTP/1.1 429 TOO MANY REQUESTS
  Retry-After: 300
```

> **Negar por padrão implementado como o TR pede:** a rota **declara** que é pública com
> `@public`; a ausência de declaração não libera. Uma rota nova nasce protegida.

### Correção de contagem em BC-3 (a enumeração vale, o número estava errado)

A seção Breaking changes aprovada diz *"As **10** rotas de escrita e destrutivas … e as **3** de
leitura de terceiros"*, totalizando 13. A **enumeração** é o que foi aprovado e foi cumprida à
risca — POST/PUT/DELETE sobre `/tasks`, `/users` e `/categories`, mais `GET /users`,
`GET /users/<id>` e `GET /users/<id>/tasks`. Mas a soma correta dessa enumeração é
**9 + 3 = 12**, não 13: são 3 verbos × 3 recursos, não 10 rotas.

**12 rotas passaram a exigir credencial**, conferido rota a rota acima. O erro estava no rótulo
numérico do relatório, não no plano nem na execução. Registrado aqui e em `validacao.md` porque
"contagem real" é critério, e ele vale contra o meu próprio relatório.

### Smoke test da Onda 1

O limitador de taxa ficou com o orçamento do IP consumido pela verificação (6) — reiniciar o
processo zera o contador em memória. É o falso vermelho *"porta ocupada / processo de um boot
anterior"* na sua variante de estado, e foi tratado antes de declarar qualquer coisa:

```console
$ python seed.py
Seed concluído com sucesso!
  3 usuários · 4 categorias · 10 tasks
$ ./boot.sh
BOOT VERDE (porta escutando · processo vivo · primeira requisicao HTTP 200)

$ python smoke.py baseline-task-manager-api.json --wave 1 --auth
Smoke test: 22/22 endpoints conformes ao baseline
VERDE
```

Commit `7fd2012`.

---

## 3. Onda 2 — HIGH · TR-06, TR-07, TR-09, TR-10, TR-16

Resolve F-005, F-006, F-007, F-008 e F-009.

### Passo 0 de TR-06, decidido antes de criar qualquer diretório

`mvc-guidelines.md` §1 regra 4 **não se aplica**: Flask não declara convenção de camadas
(sem raiz de autoload, sem pacote-base varrido, sem estrutura imposta). Cai na §4 **precedência
1** — convenção já praticada e alcançável dentro do próprio projeto.

**Consequência prática:** `models/`, `routes/` e `utils/` foram **adotados com o nome que já
tinham**; nada de árvore paralela. Criou-se apenas o que algum finding exigiu e a convenção do
projeto não cobria: `repositories/`, `services/` (real), `controllers/`, `validators/`, `infra/`.

### Boot após cada TR

| # | TR | Boot | Observação |
|---|---|---|---|
| 5 | TR-06 | **✗ vermelho → ✓ verde na tentativa 1 de 2** | ver diagnóstico abaixo |
| 6 | TR-07 | ✓ verde | — |
| 7 | TR-09 | ✓ verde | — |
| 8 | TR-10 | ✓ verde | — |
| 9 | TR-16 | ✓ verde | precedido de falha **esperada** contra schema defasado |

### Boot vermelho em TR-06 — diagnóstico e recuperação (1 de 2 tentativas)

```console
BOOT VERMELHO
Traceback (most recent call last):
  File ".../app.py", line 70, in create_app
    app.register_blueprint(register_task_routes(TaskController(task_service)))
  File ".../routes/task_routes.py", line 11, in register_task_routes
    public(controller.list_tasks), methods=['GET'])
  File ".../middlewares/auth.py", line 16, in public
    view.is_public = True
AttributeError: 'method' object has no attribute 'is_public'
```

**Causa isolada no TR, não na onda:** `@public` marcava a rota setando um atributo na função.
Com TR-06, o view deixou de ser função de módulo e passou a ser **método vinculado de
controller**, que não aceita atribuição de atributo. Não estava nos falsos vermelhos conhecidos
da §8 — é defeito real, introduzido pelo próprio TR.

**Conserto (tentativa 1):** `public()` passou a envolver o callable numa função com `@wraps` e
marcar o wrapper. Boot verde na sequência. Nenhum TR foi aplicado sobre boot vermelho.

### Verificações

**TR-06 — todas as rotas do baseline continuam registradas; nenhum arquivo mistura driver e
framework web; nenhum handler menciona sessão.**

```console
  rotas registradas agora : 22
  paths do baseline       : 22
  faltando                : nenhuma

  arquivos que importam persistencia E protocolo: ['./app.py']
  controllers/ e routes/ limpos de persistencia
  nenhum service importa protocolo
```

> `app.py` é o **único** que importa os dois — e é o composition root, cuja responsabilidade
> única é exatamente montar o grafo (`mvc-guidelines.md` §5). Não é violação.

**TR-07 — nenhum handler contém condicional sobre valor de negócio; os status do baseline não
mudaram.** O service passou a sinalizar por **tipo** (`services/errors.py`), e o mapa
tipo → status vive num lugar só:

```console
  GET /tasks/9999 (inexistente)      -> HTTP 404  {"error":"Task não encontrada"}
  GET /users/9999 (inexistente)      -> HTTP 404  {"error":"Usuário não encontrado"}
  GET /reports/user/9999             -> HTTP 404  {"error":"Usuário não encontrado"}
  POST /tasks user_id inexistente    -> HTTP 404  {"error":"Usuário não encontrado"}
  POST /users email duplicado        -> HTTP 409  {"error":"Email já cadastrado"}
  POST /login senha errada           -> HTTP 401  {"error":"Credenciais inválidas"}
  PUT /categories/9999               -> HTTP 404  {"error":"Categoria não encontrada"}

  nenhuma inspecao de forma nos controllers
```

**TR-09 — nenhum módulo abaixo do composition root instancia infraestrutura; um repositório é
construível em isolamento.**

```console
  nenhuma instanciacao de infraestrutura fora do app.py

  TaskRepository construido com duplo de banco : TaskRepository
  TaskService construido sobre ele             : TaskService
  regra exercitada SEM servidor e SEM banco    : NotFound -> Task não encontrada
```

Esta é a propriedade que a §5 diz que a inversão compra, e agora ela existe: a regra roda sem
Flask, sem SQLite e sem variável de ambiente.

**TR-10 — erro forçado no meio da sequência não deixa registro parcial.**

```console
  antes: 3 usuarios, 10 tasks (maria tem 3 tasks)
  erro injetado: falha injetada entre as duas escritas
  depois: 3 usuarios, 10 tasks
  ROLLBACK COMPLETO? True
```

E o cenário concreto que o relatório descrevia em F-008 deixou de produzir órfãos:

```console
  tasks na categoria 3 ANTES: 2
  DELETE /categories/3 -> HTTP 200
  tasks apontando para a categoria 3 inexistente: 0  (esperado 0)
  tasks desassociadas (category_id NULL)        : 2
```

**TR-16 — sobe contra banco migrado sem executar DDL; banco vazio fica utilizável com migração +
seed; violar integridade agora falha no banco.**

O risco que o TR nomeia foi verificado **antes** de declarar as constraints:

```console
  status fora do vocabulario      : 0
  priority fora de 1..5           : 0
  tasks.user_id orfao             : 0
  tasks.category_id orfao         : 0
  users.email duplicado           : 0
  colunas NOT NULL com valor nulo : 0
```

Nenhum dado preexistente violava a regra, então a migração não podia falhar por causa dos dados.

```console
$ python -c "import app"
infra.migrator.PendingMigrations: Schema desatualizado. Migrações pendentes: 0001_initial.sql.
Rode: python -m infra.migrator upgrade

$ python -m infra.migrator upgrade
Migrações aplicadas: 0001_initial.sql
$ python seed.py
Seed concluído com sucesso!  3 usuários · 4 categorias · 10 tasks
$ ./boot.sh
BOOT VERDE
```

```console
  status fora do vocabulario   -> REJEITADO pelo banco: IntegrityError
  priority fora de 1..5        -> REJEITADO pelo banco: IntegrityError
  FK de usuario inexistente    -> REJEITADO pelo banco: IntegrityError
  email duplicado              -> REJEITADO pelo banco: IntegrityError
  titulo curto demais          -> REJEITADO pelo banco: IntegrityError

  PRAGMA foreign_keys = 1                    (era 0)
  indices em tasks: ix_tasks_due_date, ix_tasks_status, ix_tasks_category_id, ix_tasks_user_id
```

> A metade "seed no boot" do sinal do AP-21 **não existia** neste projeto e o relatório já dizia
> isso. TR-16 só acrescentou a guarda de ambiente ao `seed.py`, que agora recusa rodar em
> produção por carregar credencial de demonstração.

### Observação de escopo — TR-06 absorveu parte de TR-07 e de TR-09

Mover a persistência para repositórios e a decisão para services (TR-06) já leva junto a maior
parte de *"mover a regra para o service"* (TR-07) e a montagem do grafo no composition root
(TR-09). O que restou de específico:

- **TR-07:** introduzir os **tipos** de erro de domínio e o mapa tipo → status, para o controller
  parar de inspecionar a forma do retorno. Sem isso, `GET /tasks/9999` teria virado 500.
- **TR-09:** a prova de isolamento — construir repositório e service com um duplo de banco.

Registro porque um leitor que confira TR por TR precisa saber onde cada mudança realmente entrou.

### Smoke test da Onda 2

```console
$ python smoke.py baseline-task-manager-api.json --wave 1 --auth
Smoke test: 22/22 endpoints conformes ao baseline
VERDE
```

Commit `9e81e4d`.

---

## 4. Onda 3 — MEDIUM · TR-08, TR-11, TR-12, TR-13, TR-15, TR-17, TR-18

Resolve F-010, F-011, F-012, F-013, F-014, F-015, F-016, F-017, F-020, F-021 e F-022.

### Boot após cada TR

| # | TR | Boot | Observação |
|---|---|---|---|
| 10 | TR-08 | ✓ verde | validadores já criados em TR-06; aqui foi verificação + escolha da regra vencedora |
| 11 | TR-11 | ✓ verde | — |
| 12 | TR-12 | ✓ verde | `-W error` revelou 5 ocorrências que o `grep` não pegava |
| 13 | TR-13 | ✓ verde | — |
| 14 | TR-15 | ✓ verde | — |
| 15 | TR-17 | ✓ verde | — |
| 16 | TR-18 | ✓ verde | — |

### Verificações

**TR-08 — mesma entrada inválida rejeitada com o mesmo status em criar e atualizar; payload com
campo extra não grava.**

```console
  {"title":"ab"}           POST=400  PUT=400  OK
  {"status":"invalido"}    POST=400  PUT=400  OK
  {"priority":99}          POST=400  PUT=400  OK
  {"title":""}             POST=400  PUT=400
```

Allowlist de bind, com payload hostil:

```console
$ curl -X POST /tasks -d '{"title":"Allowlist de bind","id":9999,
                           "created_at":"1999-01-01","campo_inexistente":"x"}'
{
    "id": 12,                                  ← atribuído pelo banco, não pelo payload
    "created_at": "2026-08-17 20:18:31.177007", ← agora, não 1999
    "title": "Allowlist de bind",
    ...                                         ← `campo_inexistente` não aparece
}
```

> **Passo 2 do TR — a divergência resolvida explicitamente, com a escolha registrada.**
> `POST /tasks` exigia título não-vazio; `PUT /tasks/<id>` aceitava `{"title":""}` e gravava.
> **Venceu a regra do POST** (a mais restritiva): a invariante de domínio vale para toda escrita.
> Consequência: uma entrada que o `PUT` antes aceitava passa a ser rejeitada com 400. O cenário
> **não está no baseline capturado** (o `PUT` do roteiro envia `status` e `priority`), então não
> afeta o smoke test — mas é mudança de comportamento e está declarada em `validacao.md` §4.

**TR-11 — a contagem de consultas deixa de crescer com o número de registros.**

```console
  rota                    tasks  queries
  /tasks                     11        1   HTTP 200
  /users                     11        3   HTTP 200
  /categories                11        2   HTTP 200
  /reports/summary           11       11   HTTP 200

  /tasks                     51        1   HTTP 200
  /users                     51        2   HTTP 200
  /categories                51        2   HTTP 200
  /reports/summary           51       11   HTTP 200
```

Constante de 11 para 51 tasks. Baseline era `/tasks` 17, `/users` 6, `/categories` 5,
`/reports/summary` 21 — e todos cresciam linearmente.

**TR-12 — execução não emite aviso de depreciação; o linter reprova a reintrodução.**

A verificação por execução pegou o que a busca textual não pegava:

```console
$ python -W error::DeprecationWarning seed.py
sqlalchemy.exc.StatementError: (builtins.DeprecationWarning) datetime.datetime.utcnow() is
deprecated ...
```

Causa: os defaults de coluna usam `default=datetime.utcnow` — **referência ao callable, sem
parênteses**. O `grep 'utcnow()'` não os encontrava. Cinco ocorrências em `models/`:

```console
  models/user.py:18     default=datetime.utcnow
  models/task.py:24     default=datetime.utcnow
  models/task.py:25-26  default=datetime.utcnow, onupdate=datetime.utcnow
  models/category.py:13 default=datetime.utcnow
```

Depois de corrigidas:

```console
$ python -W error::DeprecationWarning seed.py
Seed concluído com sucesso!  3 usuários · 4 categorias · 10 tasks

$ python -W error::DeprecationWarning  # 12 leituras
  status: [200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200]
  nenhum DeprecationWarning -> OK
```

**Verificação semântica, não só de assinatura** — o risco que o TR nomeia:

```console
  datetime.utcnow() -> 2026-08-17 20:20:15.643404  tzinfo=None
  utc_now()         -> 2026-08-17 20:20:15.643412  tzinfo=None
  delta             -> 0.0000s
  mesma semantica (naive UTC)? True
  se tivesse usado o aware direto -> TypeError: can't compare offset-naive and offset-aware datetimes
```

O substituto ingênuo (`datetime.now(datetime.UTC)`) teria quebrado **toda** comparação com as
colunas `DATETIME` do schema, que guardam UTC sem fuso. `utc_now()` preserva a semântica de
propósito, e a razão está escrita na docstring dele.

Regra de linter:

```console
$ ruff check _regressao_proposital.py
TID251 `datetime.datetime.utcnow` is banned: Deprecado no Python 3.12. Use utils.helpers.utc_now().
DTZ003 `datetime.datetime.utcnow()` used
```

Âncora de versão registrada: `.python-version` = 3.12, cabeçalho no `requirements.txt`, e
`requirements-dev.txt` com `ruff==0.16.3`.

**TR-13 — envelope único; nenhuma resposta com texto de exceção; nenhum handler com captura
genérica.**

```console
  404 rota inexistente   {"error":{"code":"not_found","correlation_id":"e71cd7881652","message":"The requested URL was not found..."}}
  404 recurso            {"error":{"code":"not_found","correlation_id":"e166135d2c89","message":"Task não encontrada"}}
  400 validacao          {"error":{"code":"validation_error","correlation_id":"af07491fcf48","field":"título","message":"Título deve ter entre..."}}
  401 sem credencial     {"error":{"code":"unauthorized","correlation_id":"83a3a08cc9cf","message":"Credencial ausente"}}
  403 papel              {"error":{"code":"forbidden","correlation_id":"9ecbfc36ad9c","message":"Permissão insuficiente"}}
  409 conflito           {"error":{"code":"conflict","correlation_id":"ad26be40578d","field":"email","message":"Email já cadastrado"}}
  405 metodo             {"error":{"code":"method_not_allowed","correlation_id":"299253fe6241","message":"The method is not allowed..."}}

$ grep -rnE '^\s*except\s*:' --include='*.py' .
  zero 'except:' pelados no projeto inteiro (eram 12)
```

As três capturas `except Exception` que restam são legítimas e não engolem nada:
`repositories/unit_of_work.py` (rollback e **re-raise**) e duas em `services/user_service.py`
(traduzem violação de unicidade para `Conflict` e re-levantam o resto).

**TR-15 — consolidar e remover o morto.** Ver §6, que a instrução do gate pediu explicitamente.

**TR-17 — sem parâmetros a resposta tem no máximo o default; o teto vence; o item tem a forma do
baseline; a consulta traz só a página.**

```console
  total de tasks: 130
  GET /tasks            -> 50 itens          (default)
  GET /tasks?limit=999  -> 130 itens         (teto 200 aplicado; só existem 130)
  GET /tasks?limit=10   -> 10 itens
  GET /tasks?limit=10&offset=5 -> primeiro id 6 (sem offset: 1)

  SQL: ... FROM tasks ORDER BY tasks.id LIMIT 10 OFFSET 5
  tipo da raiz: list                         ← array preservado, sem envelope
  chaves do item: ['category_id','created_at','description','due_date','id','overdue',
                   'priority','status','tags','title','updated_at','user_id']
  GET /tasks?limit=abc -> HTTP 400
```

**TR-18 — origem não listada recusada; vocabulário do contrato corrigido; nenhum literal de
negócio solto.**

```console
  Origin: http://localhost:3000 (listada)    -> Access-Control-Allow-Origin: http://localhost:3000
  Origin: http://evil.example  (nao listada) -> (sem header)

  /categories                      -> categories.get_categories     (era reports.get_categories)
  /categories                      -> categories.create_category
  /categories/<int:cat_id>         -> categories.update_category
  /categories/<int:cat_id>         -> categories.delete_category
  /reports/summary                 -> reports.summary_report
  /reports/user/<int:user_id>      -> reports.user_report
```

> **Desvio do plano, registrado:** o plano previa `constants.py` para TR-18. Não foi criado. As
> constantes foram para a entidade que as governa — `Task.VALID_STATUSES`, `Task.MIN_PRIORITY`,
> `User.VALID_ROLES`, `Category.DEFAULT_COLOR`, `ReportService.PRIORITY_LABELS`. Um
> `constants.py` paralelo duplicaria a invariante em dois lugares, que é o que
> `mvc-guidelines.md` §2 atribui ao model. O efeito prometido (nenhum literal de negócio solto)
> foi entregue; o arquivo específico, não.

### Smoke test da Onda 3

```console
$ ruff check .
All checks passed!
$ python smoke.py baseline-task-manager-api.json --wave 3 --auth
Smoke test: 22/22 endpoints conformes ao baseline
VERDE
```

Commit `3235b4b`.

---

## 5. Onda 4 — LOW · TR-14

Resolve F-019. **Chegou aqui por descida:** o teto de TR-14 é a Onda 1 (resolve AP-07, CRITICAL),
mas AP-07 **não virou finding** nesta auditoria, e o finding mais severo que TR-14 resolve é
F-019 (AP-19, LOW). É o único caminho pelo qual a Onda 4 recebe TR.

### Boot após cada TR

| # | TR | Boot | Observação |
|---|---|---|---|
| 17 | TR-14 | ✓ verde | — |

### Verificações

**Nenhuma saída de console no caminho de requisição; busca por credencial no log de um fluxo
completo não retorna nada; todo registro tem nível e timestamp.**

Os 11 `print()` já haviam saído do caminho de requisição em TR-06, quando as rotas viraram tabela
fina. O que TR-14 fez foi **devolver os eventos que eles carregavam**, agora com nível, timestamp
e redação:

```console
2026-08-17 17:26:33,027 INFO     task_manager.users login_succeeded role=admin user_id=1
2026-08-17 17:26:33,102 WARNING  task_manager.users login_failed code=invalid_credentials
2026-08-17 17:26:33,103 WARNING  task_manager.errors domain_error code=invalid_credentials status=401 path=/login cid=61fe84e0ddbf
2026-08-17 17:26:33,186 INFO     task_manager.users user_created role=user user_id=5
2026-08-17 17:26:33,202 INFO     task_manager.tasks task_created priority=2 status=pending task_id=12 user_id=None
2026-08-17 17:26:33,225 INFO     task_manager.tasks task_updated status=done task_id=12
2026-08-17 17:26:33,243 INFO     task_manager.tasks task_deleted task_id=12
```

Fluxo exercido com senha e token propositalmente distintos, depois buscados no log:

```console
--- busca por credencial/token/e-mail no log do fluxo completo ---
  nenhuma ocorrencia de senha, hash, e-mail ou token no log
```

**Redação por allowlist, não denylist** (passo 3 do TR):

```console
  entrada : {'user_id': 7, 'password': 'segredo', 'email': 'a@b.c', 'token': 'xyz', 'status': 'done'}
  emitido : {'user_id': 7, 'status': 'done'}
```

Os `print()` de `seed.py` e `infra/migrator.py` permanecem: são a **interface de scripts de linha
de comando**, fora do caminho de requisição — isenção explícita do AP-19.

### Smoke test da Onda 4

```console
$ ruff check .
All checks passed!
$ python smoke.py baseline-task-manager-api.json --wave 3 --auth
Smoke test: 22/22 endpoints conformes ao baseline
VERDE
```

Commit `303c1f9`.

---

## 6. As duas confirmações pedidas no gate

### 6.1 O conteúdo de `services/` foi registrado como finding ANTES da remoção

Exigência de `mvc-guidelines.md` §6: *"registre na Fase 2, como finding, tudo o que a camada
inalcançável contém … **antes** de propor a remoção. Nada desaparece sem constar do relatório que
o humano aprova no gate."*

Provado pelo próprio histórico do git:

```console
   commit que ADICIONOU o relatorio com F-020:
     10cc682 docs(evidence): run-3 fases 1-2 e checagem do task-manager-api
   commit que REMOVEU services/notification_service.py:
     3235b4b refactor(onda-3): MEDIUM — TR-08, TR-11, TR-12, TR-13, TR-15, TR-17, TR-18

   o relatorio e ANCESTRAL do commit de remocao?
     SIM — o registro precede a remocao
```

O inventário, textual, como constava do relatório aprovado no gate:

> **Conteúdo de `services/notification_service.py`** (a camada inalcançável): a classe
> `NotificationService`, com `send_email` (SMTP via `smtplib`), `notify_task_assigned`,
> `notify_task_overdue`, `get_notifications`, e um acumulador `self.notifications` em memória.
> Carrega **uma credencial SMTP versionada** — `email_user = 'taskmanager@gmail.com'`,
> `email_password = 'senha123'` (`notification_service.py:9-10`), já reportada como parte de
> F-001. **Apagar o arquivo não remove o segredo do histórico do repositório**, e é o histórico
> que precisa ser rotacionado; a rotação é item NEEDS-DECISION do plano.

O relatório menciona o arquivo 21 vezes. A credencial foi promovida a **ND-3**, aprovado no gate.
Apagar o arquivo **não** a removeu do histórico — e a decisão registrada é **não removê-la de lá**:
é credencial de fixture de um repositório de exercício, sem valor real, e reescrever o histórico
invalidaria os SHAs que esta própria evidência usa como prova. Ver `.planning/04-achados-execucao.md`
(AE-07).

### 6.2 `utils/` foi RELIGADO por TR-15, não removido

`mvc-guidelines.md` §6 passo 3: *"Alcançável → adote o diretório, preserve sua nomenclatura e
**ligue** o que estiver solto. A transformação é de ligação (TR-15), não de criação."*

**O diretório existe no HEAD:**

```console
$ git ls-files utils/
     utils/__init__.py
     utils/helpers.py
```

**Antes** (baseline `f580ee5`) — 2 símbolos importados, **zero** chamadas:

```console
report_routes.py:7:from utils.helpers import format_date, calculate_percentage
sitios de CHAMADA de format_date/calculate_percentage no baseline:
  (nenhum)
```

**Depois** (HEAD) — chamadores reais:

```console
     utc_now      -> 16 chamadas em 8 arquivos
     format_date  ->  9 chamadas em 4 arquivos

quem importa utils/ agora:
     app.py, seed.py, dto/user_dto.py, dto/task_dto.py, dto/category_dto.py,
     repositories/task_repository.py, services/report_service.py, services/task_service.py,
     controllers/user_controller.py, controllers/task_controller.py,
     models/user.py, models/task.py, models/category.py
```

**13 módulos** importam `utils/`, com **25 sítios de chamada**. Eram 1 importador e 0 chamadas.

O contraste com `services/` é o ponto: as duas pastas tinham nome de camada e conteúdo não
exercido, mas **`utils/` era alcançável e `services/` não era** — e a regra de alcançabilidade
levou uma a ser ligada e a outra a ser substituída. Os símbolos de `utils/` que não tinham
chamador nem podiam ganhar um (`calculate_percentage`, `process_task_data`, `VALID_STATUSES`, …)
foram consolidados na camada que os governa, não recriados: `completion_rate` no
`TaskService`, `parse_date`/`normalize_tags`/`is_valid_email`/`is_valid_color` em `validators/`,
o vocabulário nas entidades.

---

## 7. Registro de ondas (§6.1) — completo

```console
| stage    | sha       | smoke  | status |
|----------|-----------|--------|--------|
| baseline | f580ee5   | —      | green  |
| onda-1   | 7fd2012   | 22/22  | green  |
| onda-2   | 9e81e4d   | 22/22  | green  |
| onda-3   | 3235b4b   | 22/22  | green  |
| onda-4   | 303c1f9   | 22/22  | green  |
```

Nenhuma onda vazia, nenhuma onda vermelha, nenhum `git reset --hard` executado.

**Boots realizados:** 17 (um por TR) + 1 recuperação após o vermelho de TR-06 = 18.
**Ondas vermelhas:** 0. **Boots vermelhos:** 1, recuperado na primeira tentativa das duas.

```console
$ git log --oneline --grep '^refactor(onda-'
303c1f9 refactor(onda-4): LOW — TR-14
3235b4b refactor(onda-3): MEDIUM — TR-08, TR-11, TR-12, TR-13, TR-15, TR-17, TR-18
9e81e4d refactor(onda-2): HIGH — TR-06, TR-07, TR-09, TR-10, TR-16
7fd2012 refactor(onda-1): CRITICAL — TR-01, TR-03, TR-04, TR-05
```
