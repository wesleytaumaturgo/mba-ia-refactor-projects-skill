# run-2 · Fase 1 — Análise · `ecommerce-api-legacy`

**Invocação:** `/refactor-arch` **sem argumento** — os caminhos dos artefatos foram resolvidos
pelos defaults da própria skill.
**Data:** 2026-08-17 · **Commit de baseline:** `5d02287`

---

## Pré-condições

```console
$ git rev-parse --show-toplevel
/home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill
$ git status --porcelain
[fim da saida de status]
$ git rev-parse --short HEAD
5d02287
```

Working tree limpo. Caminhos resolvidos pela skill, ancorados na raiz do repositório (não no
diretório de trabalho):

```
REPORT_PATH   : /home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/audit-ecommerce-api-legacy.md
BASELINE_PATH : /home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/baseline-ecommerce-api-legacy.json
```

Declaração emitida: *"auditoria read-only até o gate da Fase 2"*.

---

## Saída de console da Fase 1

```console
PHASE 1: PROJECT ANALYSIS
─────────────────────────────────────────────
Language      : JavaScript / CommonJS (runtime in use: Node.js v24.12.0)
Framework     : Express 4.22.1 (declared ^4.18.2)
Package mgr   : package.json + package-lock.json (npm 11.6.2)
Database      : SQLite in-memory (sqlite3 5.1.7) · 5 tables
Domain        : LMS de cursos pagos — checkout cria usuário, matrícula e pagamento; há relatório financeiro administrativo e remoção de usuário
Entry points  : src/app.js (package.json main + scripts.start)
Resolution    : explicit import (CommonJS require)
Architecture  : monolito de 3 arquivos sem camadas — AppManager acumula persistência, roteamento, regra de negócio, integração de pagamento e apresentação
Source files  : 3 files · 180 LOC
Endpoints     : 3 mapped · baseline captured (4 responses)
Baseline SHA  : 5d02287
Baseline file : /home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/baseline-ecommerce-api-legacy.json
─────────────────────────────────────────────
```

---

## Os oito fatos e como cada um foi obtido

| # | Fato | Valor | Como foi obtido |
|---|---|---|---|
| 1 | Linguagem dominante | JavaScript / CommonJS | Extensões (`3/3` arquivos `.js`) ∩ manifesto `package.json` na raiz; `type` ausente → CommonJS |
| 2 | Framework efetivo | Express 4.22.1 | Declarado (`^4.18.2`) **∩** resolvido por `src/app.js:1`. Nenhuma dependência declarada e não resolvida |
| 3 | **Versão real do runtime** | **Node.js v24.12.0** | `node --version` **executado no ambiente**, não lido do manifesto — que aliás não declara `engines` |
| 4 | Persistência | `sqlite3` 5.1.7, SQLite `:memory:`, 5 tabelas | Driver no manifesto ∩ `require` em `src/AppManager.js:1` ∩ DDL embutida em `:12-16` ∩ conexão em `:7`. **DDL no caminho de boot registrada já aqui** (`project-analysis.md` §4) |
| 5 | Domínio | LMS de cursos pagos | Tabelas (`users`, `courses`, `enrollments`, `payments`, `audit_logs`) → paths (`/api/checkout`, `/api/admin/financial-report`) → entidades. Divergência de vocabulário anotada (`usr`/`eml`/`pwd` vs `name`/`email`/`pass`) |
| 6 | Arquitetura efetiva | monolito sem camadas | Grafo de **resolução**, não árvore de diretórios |
| 7 | Inventário de endpoints | 3 | `grep` de registro de rota + cruzamento com `api.http` |
| 8 | Baseline | 4 respostas | `validation-protocol.md` §2, com o código intocado |

### Versão instalada vs. declarada

```console
$ node -e "console.log('express', require('express/package.json').version); console.log('sqlite3', require('sqlite3/package.json').version)"
express 4.22.1
sqlite3 5.1.7
$ node -e "const p=require('./package.json'); console.log('engines:', JSON.stringify(p.engines||null))"
engines: null
```

Divergência declarado × instalado registrada — insumo de AP-16 e AP-28.

---

## Grafo de resolução

**Mecanismo determinado antes de concluir alcançabilidade:** import explícito (CommonJS
`require`). Não há autoloader, varredura de pacote nem container — portanto import textual **é**
o mecanismo aqui, e a armadilha de tratar como morto o que a stack resolve por convenção não se
aplica.

```console
$ grep -n "require(" src/*.js
src/app.js:1:const express = require('express');
src/app.js:2:const AppManager = require('./AppManager');
src/app.js:3:const { config } = require('./utils');
src/AppManager.js:1:const sqlite3 = require('sqlite3').verbose();
src/AppManager.js:2:const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');
```

```
src/app.js  ──require──> express
            ──require──> ./AppManager ──require──> sqlite3
                                      ──require──> ./utils
            ──require──> ./utils
```

Os 3 arquivos-fonte são alcançáveis. **Nenhum diretório de camada existe** — alcançável ou não.
Não há `controllers/`, `services/`, `repositories/`, `models/`, `middlewares/` nem `config/`, logo
não há camada preexistente a adotar nem código morto de camada a registrar antes de remoção.

### Referências externas por símbolo exportado (evidência de AP-17 / AP-26)

```console
$ for s in config logAndCache badCrypto globalCache totalRevenue; do echo -n "$s: "; grep -c "\b$s\b" src/app.js src/AppManager.js | tr '\n' ' '; echo; done
config: src/app.js:3 src/AppManager.js:2 
logAndCache: src/app.js:0 src/AppManager.js:2 
badCrypto: src/app.js:0 src/AppManager.js:2 
globalCache: src/app.js:0 src/AppManager.js:0 
totalRevenue: src/app.js:0 src/AppManager.js:1 
```

`totalRevenue` → 1 ocorrência, que é a **própria linha de import** (`src/AppManager.js:2`): zero
usos. `globalCache` → zero referências externas. Importar não é usar.

```console
$ grep -n "dbUser\|dbPass\|smtpUser" src/app.js src/AppManager.js
(nenhuma ocorrencia fora de utils.js)
```

Três chaves de configuração **sensíveis** nunca lidas — segredos versionados dentro de código
morto.

---

## Inventário de endpoints

```console
$ grep -n "app\.\(get\|post\|put\|patch\|delete\|all\|use\)" src/*.js
src/app.js:6:app.use(express.json());
src/AppManager.js:28:        app.post('/api/checkout', (req, res) => {
src/AppManager.js:80:        app.get('/api/admin/financial-report', (req, res) => {
src/AppManager.js:131:        app.delete('/api/users/:id', (req, res) => {
```

| Método | Path | Handler | arquivo:linha | Autenticação | Corpo esperado | Efeito |
|---|---|---|---|---|---|---|
| POST | `/api/checkout` | arrow inline | `src/AppManager.js:28` | **nenhuma** | `usr`, `eml`, `pwd`, `c_id`, `card` | escrita (4 tabelas) |
| GET | `/api/admin/financial-report` | arrow inline | `src/AppManager.js:80` | **nenhuma** — rota **privilegiada** | — | leitura |
| DELETE | `/api/users/:id` | arrow inline | `src/AppManager.js:131` | **nenhuma** — rota **destrutiva** | — | destrutivo |

Armadilhas verificadas: nenhuma rota registrada fora de `setupRoutes` (o único `app.use` é
`express.json()` em `src/app.js:6`); nenhuma rota montada dinamicamente por laço ou configuração.

**Cruzamento com `api.http`:** as 4 requisições do arquivo mapeiam para os 3 endpoints do código,
sem rota órfã no arquivo nem rota do código faltando nele. `api.http` está sincronizado. Os dois
blocos de checkout (sucesso e recusa) foram aproveitados como dois casos representativos.

---

## Captura do baseline

Comando de boot descoberto pela precedência de `validation-protocol.md` §1, item 1 — script no
manifesto: `npm start` → `node src/app.js`. Porta 3000, bind `*`, nenhuma variável de ambiente
necessária (o projeto não lê ambiente algum).

Três critérios de "subiu com sucesso", sem depender de string de log de framework:

```console
$ ss -ltn | awk 'NR==1 || $4 ~ /:3000$/'
State  Recv-Q Send-Q               Local Address:Port  Peer Address:PortProcess
LISTEN 0      511                              *:3000             *:*
=== (2) processo vivo apos 3s? ===
VIVO
=== (3) primeira requisicao respondida ===
status=404
```

(1) porta escutando · (2) processo vivo após 3 s · (3) primeira requisição respondida — `404` em
`/__probe__` prova servidor de pé.

Requisições, com a rota destrutiva **por último**:

```console
### POST /api/checkout (caso: sucesso)
{"msg":"Sucesso","enrollment_id":2}
[status=200] [media=application/json; charset=utf-8]

### POST /api/checkout (caso: pagamento recusado)
Pagamento recusado
[status=400] [media=text/html; charset=utf-8]

### GET /api/admin/financial-report
[{"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]},{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]}]
[status=200] [media=application/json; charset=utf-8]

### DELETE /api/users/:id  (destrutivo - por ultimo)
Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
[status=200] [media=text/html; charset=utf-8]
```

`M = 4` (3 endpoints, 4 requisições). Pré-existentes quebrados: nenhum. Não enumeráveis: nenhum.

**Achado do próprio baseline:** a ordem da coleção de `/api/admin/financial-report` **não é
determinística**. Duas execuções do código intocado devolveram ordens diferentes:

```
execução 1: [{"course":"Clean Architecture",...},{"course":"Docker",...}]
execução 2: [{"course":"Docker",...},{"course":"Clean Architecture",...}]
```

Registrado no baseline como `"order_guaranteed": false` — sem isso, a Fase 3 produziria um falso
vermelho por um contrato que o código nunca prometeu (`validation-protocol.md` §8).

Baseline persistido em `BASELINE_PATH` com método, path, status, media type e forma do corpo
(`shape` para corpo estruturado, `selector` para os dois corpos `text/html`). O processo foi
derrubado ao fim, para não segurar a porta.

---

## Estado do repositório ao fim da Fase 1

```console
$ git status --porcelain
?? reports/baseline-ecommerce-api-legacy.json
```

Única escrita: o artefato de baseline. **Nenhum arquivo do projeto tocado.**
