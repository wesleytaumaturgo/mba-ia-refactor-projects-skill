# run-2 · Validação da refatoração · `ecommerce-api-legacy`

Herdada das quatro ondas verdes, mais as três verificações que a skill exige executar **agora** —
nenhuma delas foi testada por onda alguma — e mais **uma quarta**, específica desta execução:
a reexecução do caso FN-1.

---

## 1. Boot pós-refatoração

### Comando exato

```console
$ npm start
```

que resolve para `node --env-file-if-exists=.env src/app.js`.

### Saída LITERAL

```console
> desafio-arquitetura-ia-boilerplate@1.0.0 start
> node --env-file-if-exists=.env src/app.js

{"timestamp":"2026-08-17T19:14:23.776Z","level":"warn","event":"ephemeral_database","code":"in-memory-bootstrap"}
{"timestamp":"2026-08-17T19:14:23.778Z","level":"info","event":"migration_applied","code":"0001_initial.sql"}
{"timestamp":"2026-08-17T19:14:23.814Z","level":"info","event":"seed_applied","environment":"development"}
{"timestamp":"2026-08-17T19:14:23.820Z","level":"info","event":"server_started","port":3000,"host":"127.0.0.1","environment":"development"}
```

Os três critérios de "subiu com sucesso" (`validation-protocol.md` §3), sem depender de string de
log de framework:

```console
(1) porta escutando:
State  Recv-Q Send-Q               Local Address:Port  Peer Address:PortProcess
LISTEN 0      511                      127.0.0.1:3000       0.0.0.0:*

(2) processo vivo apos 3s: VIVO
(3) primeira requisicao respondida: 404
```

Mudança de bind registrada: de `*:3000` (todas as interfaces) para `127.0.0.1:3000`, vindo de
`HOST`. É consequência do passo 3 de TR-01 e **é** uma mudança de comportamento — não observável
no contrato HTTP, mas real, e por isso declarada aqui.

---

## 2. As 4 requisições do baseline

`M = 4` (3 endpoints; `POST /api/checkout` com dois casos representativos).

| # | Requisição | ANTES (baseline) | DEPOIS | Conforme? | BC declarada? |
|---|---|---|---|---|---|
| 1 | `POST /api/checkout` sucesso | `200` `application/json`<br>`{"msg":"Sucesso","enrollment_id":2}` | `200` `application/json`<br>`{"msg":"Sucesso","enrollment_id":2}` | ✅ **idêntico** | — (BC-8 é aditiva) |
| 2 | `POST /api/checkout` recusado | `400` `text/html`<br>`Pagamento recusado` | `400` `application/json`<br>`{"error":{"code":"PAYMENT_DECLINED","message":"Pagamento recusado","correlationId":"…"}}` | ✅ conforme | **BC-3** |
| 3 | `GET /api/admin/financial-report` | `200` `application/json`<br>array puro de 2 cursos, anônimo | `200` `application/json`<br>`{"items":[…2 cursos idênticos…],"total":2,"limit":50,"offset":0}`, exige credencial | ✅ conforme | **BC-1** (401 anônimo), **BC-6** (envelope) |
| 4 | `DELETE /api/users/1` | `200` `text/html`<br>`Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.` | `409` `application/json`<br>`{"error":{"code":"USER_HAS_ENROLLMENTS",…}}`, exige credencial | ✅ conforme | **BC-2** (401 anônimo), **BC-9** (409), **BC-7** (JSON) |

**Smoke test final: 4/4 conformes.** Path e verbo preservados nos três endpoints; o status de
**sucesso** preservado onde há sucesso.

### Verificação 3 do protocolo — diff de forma e media type contra a seção Breaking changes aprovada

| Divergência observada | Declarada? | Onde |
|---|---|---|
| `GET /financial-report` → 401 sem credencial | ✅ | BC-1 |
| `DELETE /users/:id` → 401 sem credencial | ✅ | BC-2 |
| `POST /checkout` 400 vira JSON | ✅ | BC-3 |
| demais erros de `/checkout` uniformizados; driver deixa de virar 404 | ✅ | BC-4 |
| `GET /financial-report` erro 500 em JSON | ✅ | BC-5 |
| `GET /financial-report` array → envelope paginado, ordem explícita | ✅ | BC-6 |
| `DELETE /users/:id` corpo de sucesso em JSON | ✅ | BC-7 |
| `POST /checkout` aceita `name`/`email`/`password`/`courseId` | ✅ | BC-8 |
| `DELETE /users/1` 200 → 409 | ✅ | **BC-9** |

**Nenhuma divergência não declarada.** Item a item, o conjunto observado é exatamente o conjunto
aprovado no gate — nada a mais, nada a menos.

### Mudanças de comportamento fora do contrato HTTP, declaradas aqui

Reais, não observáveis pelo smoke test, e por isso registradas em vez de silenciadas:

1. **Checkout recusado não cria mais a conta.** No baseline, um pagamento recusado deixava o
   usuário gravado (`AppManager.js:69` rodava antes de `:48`). Com a fronteira transacional de
   TR-10, ou as quatro escritas acontecem, ou nenhuma. É o que F-010 prometeu corrigir; o HTTP é
   idêntico (`400 PAYMENT_DECLINED`) nos dois casos.
2. **Bind restrito a `127.0.0.1`** por default (era `*`).
3. **Verbosidade do driver** deixou de ser incondicional; agora segue `NODE_ENV`.
4. **Boot passa a falhar** sem `PAYMENT_GATEWAY_KEY` e `ADMIN_TOKEN`. É o fail-fast de TR-01 — o
   comportamento desejado, e o que `validation-protocol.md` §1 avisa que parece regressão.

---

## 3. Árvore de diretórios resultante

```text
ecommerce-api-legacy/
├── .env.example                          TR-01 — chaves sem valores
├── api.http
├── package.json                          scripts: start · migrate · seed
├── scripts/
│   ├── migrate.js                        aplica migrações sob demanda
│   └── seed.js                           seed de desenvolvimento sob demanda
└── src/
    ├── app.js                            composition root: único a instanciar infraestrutura
    ├── config/index.js                   lê o ambiente, falha no boot se faltar obrigatória
    ├── models/paymentStatus.js           vocabulário fechado {PAID, DENIED}
    ├── repositories/                     único lugar que conhece SQL
    │   ├── auditLogRepository.js
    │   ├── courseRepository.js
    │   ├── enrollmentRepository.js
    │   ├── paymentRepository.js
    │   ├── reportRepository.js           consulta única do relatório (TR-11)
    │   └── userRepository.js
    ├── services/                         único lugar que decide o quê acontece
    │   ├── checkoutService.js
    │   ├── passwordService.js            scrypt com salt e fator de custo
    │   ├── paymentGateway.js             adapter da integração
    │   ├── reportService.js
    │   └── userService.js
    ├── controllers/                      protocolo ↔ domínio
    │   ├── checkoutController.js
    │   ├── reportController.js
    │   └── userController.js
    ├── routes/index.js                   método + path → middlewares + handler
    ├── middlewares/
    │   ├── auth.js                       TR-05
    │   ├── errorHandler.js               TR-13 — envelope único + correlação
    │   └── rateLimit.js                  TR-05 / AP-24 por composição
    ├── errors/index.js                   erros de domínio tipados
    ├── lib/
    │   ├── cache.js                      TTL e teto, injetado
    │   └── logger.js                     níveis, timestamp, redação por allowlist
    └── db/
        ├── connection.js                 único módulo que conhece o driver
        ├── migrate.js                    migrações versionadas
        ├── migrations/0001_initial.sql   schema com FK, UNIQUE, NOT NULL, CHECK
        └── seed.js                       atrás de guarda de ambiente
```

**Antes:** 180 linhas em 3 arquivos. **Depois:** 1.157 linhas em 33 arquivos.
`src/AppManager.js` e `src/utils.js` deixaram de existir.

### Verificação 2 do protocolo — responsabilidade a responsabilidade

Cada responsabilidade de `mvc-guidelines.md` §2 tem **um** lugar identificável, e esse lugar é
alcançável a partir de `src/app.js` por `require` explícito — o mecanismo determinado na Fase 1.

| Responsabilidade | Lugar único | Alcançável? |
|---|---|---|
| config | `src/config/index.js` | ✅ `app.js:5` |
| models | `src/models/paymentStatus.js` | ✅ via `paymentGateway`, `reportService`, `seed` |
| repositories | `src/repositories/` (6) | ✅ `app.js:9-14` |
| services | `src/services/` (5) | ✅ `app.js:16-20` |
| controllers | `src/controllers/` (3) | ✅ `app.js:22-24` |
| routes | `src/routes/index.js` | ✅ `app.js:25` |
| middlewares | `src/middlewares/` (3) | ✅ `app.js:26-31` |

Nenhuma responsabilidade espalhada por vários lugares; nenhum diretório de camada inalcançável.
Direção de dependência (§3) verificada por leitura de imports: nenhum controller importa driver ou
repositório; nenhum service importa símbolo de protocolo; nenhum repositório importa service.

```console
$ grep -rn "require('express')|req\.|res\." src/services/ src/repositories/
OK: services e repositories nao conhecem HTTP

$ grep -rn "new sqlite3|require('sqlite3')" src/ | grep -v src/db/connection.js
OK: so src/db/connection.js conhece o driver
```

---

## 4. Checklist MVC do enunciado, item a item

| # | Item | Situação | Evidência |
|---|---|---|---|
| 1 | Separação em camadas MVC | ✅ | árvore acima; 7 responsabilidades, 7 lugares |
| 2 | Rotas sem lógica | ✅ | `src/routes/index.js` — só método + path + middlewares + handler |
| 3 | Controllers finos | ✅ | `src/controllers/*.js`, o maior tem 38 linhas e nenhuma decisão de negócio |
| 4 | Regra de negócio isolada | ✅ | `src/services/checkoutService.js:21-58`, `src/services/userService.js:16-27` |
| 5 | Acesso a dados isolado | ✅ | SQL só em `src/repositories/` e `src/db/`; `grep` de `db.run|get|all` em controllers e routes = 0 |
| 6 | Injeção de dependências | ✅ | `src/app.js:36-97` — ordem config → infra → repos → services → controllers → rotas |
| 7 | Configuração externalizada | ✅ | `src/config/index.js` + `.env.example`; zero literais sensíveis |
| 8 | Tratamento de erro centralizado | ✅ | `src/middlewares/errorHandler.js`; nenhuma captura nos handlers |
| 9 | Sem estado global mutável | ✅ | `grep -rnE "^(let\|var) " src/` = 0 |
| 10 | Contrato de resposta consistente | ✅ | envelope `{error:{code,message,correlationId}}` em toda falha |
| 11 | Integridade no banco | ✅ | `0001_initial.sql` — 14 ocorrências de FK/UNIQUE/NOT NULL/CHECK, e `PRAGMA foreign_keys = ON` por conexão |
| 12 | Schema versionado | ✅ | `src/db/migrations/` + tabela `schema_migrations`; `npm run migrate` |

---

## 5. Findings resolvidos vs. reportados

### Verificação 1 do protocolo — reexecução do sinal de detecção de cada CRITICAL e HIGH

| Finding | AP | Sinal ainda dispara? | Evidência |
|---|---|---|---|
| F-001 | AP-02 | **não** | `grep pk_live\|senha_super_secreta\|admin_master\|no-reply@` em `src/` e `scripts/` = 0; `process.env` lido em `src/config/index.js`; verbosidade condicional |
| F-002 | AP-05 | **não** | `routes/index.js:23,26` — `authenticate` antes do handler nas duas rotas privilegiadas |
| F-003 | AP-04 | **não** | `badCrypto` não existe; `scrypt` + `randomBytes` + `timingSafeEqual` |
| F-004 | AP-06 | **não** | `AppManager.js` não existe; nenhum arquivo importa driver **e** framework web |
| F-005 | AP-07 | **não** | nenhum `console.log` em `src/`; log com redação por allowlist |
| F-006 | AP-13 | **não** | `grep db.run\|db.get\|db.all` em `controllers/` e `routes/` = 0 |
| F-007 | AP-21 | **não** | nenhuma DDL de aplicação em JS; 14 constraints declaradas na migração |
| F-008 | AP-08 | **não** | nenhuma condicional sobre valor de negócio nos controllers |
| F-009 | AP-09 | **não** | infraestrutura só em `src/db/connection.js`, instanciada só pelo composition root |
| F-010 | AP-11 | **não** | `unitOfWork.run` em `checkoutService.js:40` e `userService.js:16` |
| F-011 | AP-10 | **não** | zero variáveis mutáveis de escopo de módulo |

> Única ocorrência remanescente de `CREATE TABLE` em JavaScript: `src/db/migrate.js:13`, a tabela
> `schema_migrations` do próprio mecanismo de migração. Não é DDL de aplicação no boot — é o
> registro que permite ao boot **verificar** a versão aplicada, que é o que TR-16 pede.

### Findings MEDIUM e LOW

| Finding | AP | Resolvido | Evidência |
|---|---|---|---|
| F-012 | AP-18 | ✅ | tratador central; `err` nunca descartado; 404/500 separados |
| F-013 | AP-23 | ✅ | envelope único, um idioma, código estável |
| F-014 | AP-15 | ✅ | uma consulta em vez de `1 + C + 2·E`; soma no banco |
| F-015 | AP-22 | ✅ | `limit`/`offset` com default 50 e teto 200, aplicados na consulta |
| F-016 | AP-27 | ✅ | nomes de domínio; `self`/`this` eliminados pela promisificação |
| F-017 | AP-25 | ✅ | `src/models/paymentStatus.js` + `CHECK` no schema |
| F-018 | AP-26 | ✅ | `src/utils.js` removido após confirmação de alcançabilidade |
| F-019 | AP-19 | ✅ | logger com níveis e timestamp; zero `console.*` em `src/` |

### Não resolvidos

**19 de 20 findings resolvidos.**

| Finding | Razão |
|---|---|
| **F-020** (AP-28, LOW) | **Fora do escopo declarado da skill, por decisão do próprio catálogo.** AP-28 não tem TR: "instalar test runner, linter e CI está fora do escopo". Foi reportado, não entrou no plano aprovado no gate, e não foi corrigido. Cobertura parcial entregue como consequência: TR-01 publicou o `.env.example`, e `package.json` ganhou `migrate` e `seed` — mas continua sem `devDependencies`, sem `engines`, sem teste, sem lint e sem CI. |

---

## 6. Verificação adicional — reexecução do caso FN-1

Fora das três verificações obrigatórias. FN-1 é o falso negativo que a checagem do run-2
identificou: **uma requisição anônima com `card` como número JSON derrubava o processo inteiro**,
e como o banco é `:memory:`, apagava todos os dados.

### Antes (baseline, commit `5d02287`)

```console
$ curl -X POST http://localhost:3000/api/checkout -H 'Content-Type: application/json' \
       -d '{"usr":"X","eml":"x@y.z","pwd":"p","c_id":2,"card":4111222233334444}'
[status=000]

$ (processo vivo depois?)
MORTO - processo derrubado

/home/.../src/AppManager.js:46
                        let status = cc.startsWith("4") ? "PAID" : "DENIED";
                                        ^
TypeError: cc.startsWith is not a function
```

### Depois (commit `cc8d8a5`)

```console
$ curl -X POST http://localhost:3000/api/checkout -H 'Content-Type: application/json' \
       -d '{"usr":"X","eml":"fn1@teste.com","pwd":"p","c_id":2,"card":4111222233334444}'
{"error":{"code":"INTERNAL_ERROR","message":"Erro interno","correlationId":"bdbddb8a-e593-4d57-b7ec-9f8bce6bcfa9"}}
    [status=500] [media=application/json; charset=utf-8]
    processo: SOBREVIVEU
    servidor ainda atende requisicoes seguintes? status=200

    --- o defeito foi REGISTRADO no log? ---
{"timestamp":"2026-08-17T19:14:26.866Z","level":"error","event":"unhandled_error","code":"TypeError","correlationId":"bdbddb8a-e593-4d57-b7ec-9f8bce6bcfa9","method":"POST","path":"/api/checkout","statusCode":500}
```

### Leitura honesta do resultado

**O processo sobrevive e responde erro tipado.** Três coisas mudaram, e vale separá-las:

1. **A contenção do crash chegou na Onda 1, não na Onda 3.** O smoke test da Onda 1 já registrou
   `processo SOBREVIVEU`. A causa foi **TR-06**: promissificar o driver e encaminhar a rejeição
   por `asyncHandler` transformou uma exceção que escapava de um callback assíncrono numa promessa
   rejeitada que o Express consegue capturar. Não foi TR-13.
2. **A qualidade da resposta veio de TR-13.** Na Onda 1 o corpo era o HTML padrão do Express, com
   `TypeError: card.startsWith is not a function` e três caminhos absolutos de arquivo expostos ao
   chamador anônimo. Depois de TR-13: envelope JSON, `INTERNAL_ERROR`, zero stack trace, e o
   detalhe completo só no log, correlacionado pelo mesmo identificador.
3. **O defeito em si continua lá.** `src/services/paymentGateway.js:21` ainda faz
   `card.startsWith(...)` sem verificar o tipo. Um `card` não-string continua produzindo `500` em
   vez de `400`. **Não foi corrigido de propósito**: nenhum finding o cobre, logo nenhum TR foi
   agendado para ele, e consertá-lo aqui seria trabalho fora do plano aprovado no gate.

### O ponto que importa: isto não foi detecção

> **Nenhum dos 28 APs do catálogo tem como sinal a ausência de uma fronteira de erro.**

Percorridas as 28 entradas: **AP-12** cobre validação de domínio *escrita inline no handler* — o
defeito de estar no lugar errado, não o de não existir. **AP-18** cobre *bloco de captura
genérico* — e aqui não havia captura nenhuma: nem `try/catch`, nem `.catch`, nem handler de erro
registrado. **AP-14**, **AP-23** e **AP-05** não alcançam o caso.

A melhora observada é **efeito colateral** de TR-06 e TR-13, não consequência de o catálogo ter
encontrado o problema. Se o projeto tivesse apenas findings que não acionassem esses dois TRs, o
crash teria sobrevivido à refatoração inteira com o relatório declarando sucesso.

Registrado como achado de execução em `.planning/04-achados-execucao.md`. **Não corrigido nesta
entrega** — a correção exigiria alterar o catálogo genérico em `code-smells-project`,
re-propagá-lo aos 3 projetos e re-executar o projeto 1 para checar regressão.

---

## 7. Veredito

| Critério | Resultado |
|---|---|
| Boot pós-refatoração | ✅ três critérios satisfeitos |
| Smoke test final | ✅ **4/4** requisições conformes |
| Breaking changes | ✅ **9 aplicadas, 9 declaradas** — nenhuma divergência não declarada |
| Ondas | ✅ 4 verdes, 0 vazias, 0 vermelhas, 0 rollbacks |
| Findings resolvidos | **19/20** — F-020 fora do escopo por decisão do catálogo |
| Verificação 1 (sinais CRITICAL/HIGH) | ✅ nenhum dos 11 sinais volta a disparar |
| Verificação 2 (responsabilidades) | ✅ 7/7 com lugar único e alcançável |
| Verificação 3 (diff contra Breaking changes) | ✅ conjunto observado = conjunto aprovado |
| Verificação adicional (FN-1) | ⚠️ contido, **não corrigido** — e a contenção não veio de detecção |
