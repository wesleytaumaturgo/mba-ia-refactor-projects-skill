# run-2 · Fase 3 — Refatoração · `ecommerce-api-legacy`

**Commit de baseline:** `5d02287` · **Data:** 2026-08-17
**Boot usado em toda a fase:** `npm start` → `node --env-file-if-exists=.env src/app.js`

---

## Gate

Reapresentado após ND-5 gerar BC-9, e respondido:

```console
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
y
```

Decisões NEEDS-DECISION registradas antes de qualquer escrita: ND-1 checkout público ·
ND-2 token administrativo via ambiente · ND-3 `scrypt` do `node:crypto` · ND-4 seed atrás de
guarda de desenvolvimento · **ND-5 `ON DELETE RESTRICT` + 409 (gerou BC-9)** · ND-6 renomear com
compatibilidade.

---

## Onda 1 — CRITICAL · TR-01, TR-06, TR-03, TR-05, TR-14

### Boot após cada TR

| # | TR | Boot | Evidência |
|---|---|---|---|
| 1 | TR-01 | ✓ | porta `127.0.0.1:3000` · processo vivo após 3 s · probe `404` |
| 2 | TR-06 | ✓ (após falso vermelho, ver abaixo) | as 4 respostas idênticas ao baseline |
| 3 | TR-03 | ✓ | checkout com criação de usuário exercitou o `scrypt` no caminho quente |
| 4 | TR-05 | ✓ | `401` sem credencial, `200` com credencial |
| 5 | TR-14 | ✓ | log estruturado, zero dado sensível |

### Falso vermelho em TR-06 — diagnóstico e recuperação (1 de 2 tentativas)

```console
Error: listen EADDRINUSE: address already in use 127.0.0.1:3000
    at Server.setupListenHandle [as _listen2] (node:net:1940:16)
```

Consultado `validation-protocol.md` §8 antes de declarar a onda vermelha: *"Porta ocupada /
conexão recusada → processo de um boot anterior ainda vivo."* Confirmado:

```console
$ ps -eo pid,args | grep 'src/app\.js'
 728741 node --env-file-if-exists=.env src/app.js
```

Era o processo do boot de TR-01, que o teardown não derrubou. Derrubado, boot repetido, verde.
**Causa na validação, não no código** — nenhuma linha do projeto foi alterada para recuperar.

### Verificações que os TRs exigem

**TR-01** — fail-fast nomeando a chave:

```console
$ node -e "delete process.env.ADMIN_TOKEN; require('./src/config').loadConfig();"
ConfigError: Variável de ambiente obrigatória ausente: ADMIN_TOKEN. Veja .env.example para a lista completa.
```

Nenhum literal sensível sobrevive à busca (`pk_live`, `senha_super_secreta`, `admin_master`,
`no-reply@`): zero ocorrências. `.env.example` publicado sem valores; `.env` confirmado ignorado
pelo VCS (`git check-ignore -v .env` → `.gitignore:29`). O bind de rede passou de `*:3000`
(todas as interfaces) para `127.0.0.1:3000`, vindo de `HOST`, e a verbosidade do driver deixou de
ser incondicional — **passo 3 de TR-01, que cobre o que a Fase 2 não detectou (FN-3)**.

**TR-03** — verificação decisiva reexecutada:

```console
conta A: scrypt$16384$9bb5bc1e530bc39fa4bf8327d0444fd6$be2d104809bfa4...
conta B: scrypt$16384$2b65cdc32cad70dda6f8182398b4731f$857fa9da02b4fa...
iguais? false

=== as tres colisoes de badCrypto ainda colidem? ===
distintos: 3 de 3

senha certa : {"valid":true,"needsRehash":false}
senha errada: {"valid":false,"needsRehash":false}
formato legado (badCrypto): {"valid":false,"needsRehash":true,"reason":"legacy-format"}
```

Duas contas com a mesma senha produzem valores diferentes; as três senhas que colidiam em
`badCrypto` agora produzem três valores distintos; o formato legado é reconhecido e marcado para
reidratação.

**TR-05** — negar por padrão:

```console
--- sem credencial
Credencial ausente ou inválida            [401]
--- com credencial inválida
Credencial ausente ou inválida            [401]
--- com credencial válida
[{"course":"Clean Architecture",...}]     [200]
--- rota pública continua pública
{"msg":"Sucesso","enrollment_id":2}       [200]
```

**TR-14** — busca por dado sensível no log de um fluxo completo:

```console
{"timestamp":"2026-08-17T19:03:40.422Z","level":"info","event":"server_started","port":3000,"host":"127.0.0.1","environment":"development"}
{"timestamp":"2026-08-17T19:03:42.439Z","level":"info","event":"payment_authorization_requested","cardLast4":"4444","amount":497}
{"timestamp":"2026-08-17T19:03:42.439Z","level":"info","event":"payment_authorization_settled","status":"PAID","amount":497}
{"timestamp":"2026-08-17T19:03:42.439Z","level":"info","event":"checkout_completed","userId":2,"courseId":2,"enrollmentId":2,"amount":497,"status":"PAID"}

$ grep -c "4111222233334444|5111222233334444|pk_test_local_dev_only|pk_live|senhaforte|dev-admin-token"
0
```

Zero ocorrências. Redação por **allowlist** de campos emitíveis, não por denylist de nomes.

### Smoke test da Onda 1

```console
--- 1. POST /api/checkout  (sucesso)
{"msg":"Sucesso","enrollment_id":2}
    status=200  media=application/json; charset=utf-8
--- 2. POST /api/checkout  (pagamento recusado)
Pagamento recusado
    status=400  media=text/html; charset=utf-8
--- 3. GET /api/admin/financial-report
[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},{"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]
    status=200  media=application/json; charset=utf-8
--- 4. DELETE /api/users/1  (destrutivo)
Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
    status=200  media=text/html; charset=utf-8
```

**4/4 conformes.** Divergências: BC-1 e BC-2 (401 anônimo), ambas declaradas. → commit `4701894`.

---

## Onda 2 — HIGH · TR-09, TR-16, TR-10, TR-07

Ordem escolhida dentro da onda: TR-09 antes de TR-16 porque a inversão de dependências é
pré-requisito do `unitOfWork` de TR-10; TR-07 por último porque a regra de remoção que ele
introduz só é imponível depois da constraint de TR-16.

### Boot após cada TR

| # | TR | Boot | Evidência |
|---|---|---|---|
| 1 | TR-09 | ✓ | repositório construído em isolamento com banco falso |
| 2 | TR-16 | ✓ | migração aplicada, seed aplicado, FK imposta pelo banco |
| 3 | TR-10 | ✓ | recusa não deixa registro parcial |
| 4 | TR-07 | ✓ | `409` tipado, `404` para inexistente |

### Verificações

**TR-09** — nenhum módulo abaixo do composition root instancia infraestrutura, e a camada é
construível em teste com implementação alternativa:

```console
$ grep -rn "new sqlite3|require('sqlite3')" src/ | grep -v src/db/connection.js
OK: so src/db/connection.js conhece o driver

$ grep -rn "^let |^var " src/
OK: nenhum

$ node -e "makeCourseRepository({ get: async (sql,p) => ({id:p[0],title:'FAKE',...}) }).findActiveById(7)"
sem SQLite, sem env, sem servidor -> {"id":7,"title":"FAKE","price":1,"active":1}
```

**TR-16** — o boot deixa de executar DDL; a integridade passa a ser imposta pelo banco:

```console
{"timestamp":"2026-08-17T19:07:04.492Z","level":"warn","event":"ephemeral_database","code":"in-memory-bootstrap"}
{"timestamp":"2026-08-17T19:07:04.495Z","level":"info","event":"migration_applied","code":"0001_initial.sql"}
{"timestamp":"2026-08-17T19:07:04.530Z","level":"info","event":"seed_applied","environment":"development"}

Error: SQLITE_CONSTRAINT: FOREIGN KEY constraint failed
    at Object.deleteById (.../src/repositories/userRepository.js:17:38)
```

A FK passou a valer de fato — o que exigiu `PRAGMA foreign_keys = ON` **por conexão**, sem o qual
o SQLite ignora silenciosamente as constraints declaradas no schema.

> **Desvio declarado.** TR-16 manda o boot apenas *verificar* a versão de schema. Com
> `DATABASE_FILE=':memory:'` isso é impossível: o banco deixa de existir quando o processo morre,
> então não há o que pré-migrar por script. A implementação verifica
> (`assertSchemaUpToDate`) para bancos persistentes e, **só em desenvolvimento e só para
> `:memory:`**, aplica migração e seed no boot emitindo `ephemeral_database` — o boot diz o que
> está fazendo. `npm run migrate` e `npm run seed` existem e são o caminho normal.

**TR-10** — um erro no meio da sequência não deixa registro parcial:

```console
=== checkout recusado ===
Pagamento recusado [400]
=== a recusa criou o usuario? (UNIQUE(email) delataria) ===
{"msg":"Sucesso","enrollment_id":3} [200]
```

O segundo checkout com o **mesmo e-mail** sucede, provando que a recusa anterior não deixou o
usuário gravado. A transação foi mantida curta e **fora** da chamada ao gateway, para não segurar
lock durante uma chamada externa.

**TR-07** — nenhum service importa símbolo de protocolo; a regra sinaliza por tipo:

```console
$ grep -rn "require('express')|req\.|res\." src/services/ src/repositories/
OK: services e repositories nao conhecem HTTP

=== BC-9: DELETE usuario 1 (TEM matricula) ===
Usuário possui matrículas e não pode ser removido   [409]
=== DELETE usuario inexistente ===
Usuário não encontrado                              [404]
```

### Observação de escopo — TR-06 absorveu a maior parte de TR-07

Como no run-1: TR-06 já move a regra de negócio para os services (é o passo 2 do próprio TR-06),
então o que sobrou para TR-07 foi a parte que TR-06 não cobre — a regra de remoção de usuário
como erro de domínio tipado, e a confirmação de que nenhum service importa protocolo. Registrado
para que a contagem de TRs não sugira mais trabalho do que houve.

### Smoke test da Onda 2

```console
--- 1. POST /api/checkout  (sucesso)
{"msg":"Sucesso","enrollment_id":2}                          status=200  application/json
--- 2. POST /api/checkout  (pagamento recusado)
Pagamento recusado                                           status=400  text/html
--- 3. GET /api/admin/financial-report
[{"course":"Clean Architecture","revenue":997,...}]          status=200  application/json
--- 4. DELETE /api/users/1  (destrutivo)
Usuário possui matrículas e não pode ser removido            status=409  text/html
```

**4/4 conformes.** Divergência nova: BC-9. → commit `fb19464`.

---

## Onda 3 — MEDIUM · TR-13, TR-11, TR-17

### Boot após cada TR

| # | TR | Boot | Evidência |
|---|---|---|---|
| 1 | TR-13 | ✓ | envelope único, `correlationId` batendo entre resposta e log |
| 2 | TR-11 | ✓ | corpo igual ao baseline item a item, ordem estável |
| 3 | TR-17 | ✓ | default 50, teto 200, página aplicada na consulta |

### Verificações

**TR-13** — nenhuma captura genérica nos handlers, um envelope, um idioma:

```console
--- erro de cliente (recusa)
{"error":{"code":"PAYMENT_DECLINED","message":"Pagamento recusado","correlationId":"7b6e21e6-..."}}   [400]
--- recurso inexistente
{"error":{"code":"COURSE_NOT_FOUND","message":"Curso não encontrado","correlationId":"320252a6-..."}} [404]
--- sem credencial
{"error":{"code":"UNAUTHORIZED",...}}                                                                [401]
--- 409
{"error":{"code":"USER_HAS_ENROLLMENTS",...}}                                                        [409]
--- rota inexistente
{"error":{"code":"ROUTE_NOT_FOUND",...}}                                                             [404]
--- defeito
{"error":{"code":"INTERNAL_ERROR","message":"Erro interno","correlationId":"5dd098e0-..."}}          [500]
```

O defeito aparece no log com o **mesmo** identificador de correlação da resposta:

```console
{"timestamp":"2026-08-17T19:10:02.487Z","level":"error","event":"unhandled_error","code":"TypeError","correlationId":"5dd098e0-be97-4dfc-9b9b-94602d98b392","method":"POST","path":"/api/checkout","statusCode":500}
```

Nenhuma resposta contém texto de exceção nem caminho de arquivo. O colapso original — falha de
driver devolvida como `404` em `AppManager.js:38` — desapareceu: inexistente é `404`, defeito é
`500`.

**TR-11** — a cascata `1 + C + 2·E` virou **uma** consulta, e a ordem deixou de ser
não-determinística:

```console
=== corpo do relatorio ===
[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},{"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]

=== ordem estavel entre 3 execucoes (BC-6)? ===
['Clean Architecture', 'Docker']
['Clean Architecture', 'Docker']
['Clean Architecture', 'Docker']
```

A soma de receita saiu do laço em JavaScript e passou para a cláusula da consulta.

**TR-17** — defaults explícitos, teto que vence, página aplicada na consulta:

```console
--- sem parametros (default) ---
{"items":[...2 cursos...],"total":2,"limit":50,"offset":0}
--- limit=1 ---
{"items":[{"course":"Clean Architecture",...}],"total":2,"limit":1,"offset":0}
--- limit=1&offset=1 ---
{"items":[{"course":"Docker",...}],"total":2,"limit":1,"offset":1}
--- limit=999999 -> o TETO vence ---
limit aplicado = 200 | total = 2
```

A **forma do item** é a do baseline; o que mudou é o envoltório (BC-6).

### Smoke test da Onda 3

```console
--- 1. POST /api/checkout  (sucesso)
{"msg":"Sucesso","enrollment_id":2}                                        status=200  application/json
--- 2. POST /api/checkout  (pagamento recusado)
{"error":{"code":"PAYMENT_DECLINED",...}}                                  status=400  application/json
--- 3. GET /api/admin/financial-report
{"items":[...],"total":2,"limit":50,"offset":0}                            status=200  application/json
--- 4. DELETE /api/users/1  (destrutivo)
{"error":{"code":"USER_HAS_ENROLLMENTS",...}}                              status=409  application/json
```

**4/4 conformes.** Divergências: BC-3, BC-5, BC-6, BC-7 (+ BC-9 herdada). → commit `0d1eacc`.

---

## Onda 4 — LOW · TR-15, TR-18

### Boot após cada TR

| # | TR | Boot | Evidência |
|---|---|---|---|
| 1 | TR-15 | ✓ | `src/utils.js` removido, aplicação sobe |
| 2 | TR-18 | ✓ | nomes antigos e novos do payload aceitos |

### Verificações

**TR-15** — alcançabilidade confirmada pelo grafo de resolução **e** por busca no repositório
inteiro, **antes** de apagar:

```console
logAndCache  -> referencias fora de src/utils.js: 0
badCrypto    -> referencias fora de src/utils.js: 1
globalCache  -> referencias fora de src/utils.js: 1
totalRevenue -> referencias fora de src/utils.js: 0

$ grep -rn "\bbadCrypto\b|\bglobalCache\b" src/ scripts/ | grep -v ^src/utils.js
src/services/passwordService.js:13:// ... Substitui a função caseira `badCrypto`,
src/lib/cache.js:3:// Substitui o `globalCache` de escopo de módulo por uma instância ...
```

As duas ocorrências são **menções em comentário**, não chamadas. Nenhuma dependência do manifesto
ficou órfã: `express` e `sqlite3` seguem importados.

**TR-18** — literais nomeados com valor idêntico, e o contrato público sem quebra:

```console
$ grep -rn "'PAID'|'DENIED'|startsWith('4')" src/ | grep -v models/paymentStatus.js
OK: nenhum — o vocabulario vive em src/models/paymentStatus.js

$ grep -rnE "let (u|e|p|cc|cid) =" src/
OK: nenhum

=== BC-8: nomes ANTIGOS continuam aceitos (payload literal do baseline) ===
{"msg":"Sucesso","enrollment_id":2} [200]
=== BC-8: nomes NOVOS tambem aceitos ===
{"msg":"Sucesso","enrollment_id":3} [200]
```

### Smoke test da Onda 4

```console
--- 1. POST /api/checkout  (sucesso)
{"msg":"Sucesso","enrollment_id":2}                                        status=200  application/json
--- 2. POST /api/checkout  (pagamento recusado)
{"error":{"code":"PAYMENT_DECLINED",...}}                                  status=400  application/json
--- 3. GET /api/admin/financial-report
{"items":[...],"total":2,"limit":50,"offset":0}                            status=200  application/json
--- 4. DELETE /api/users/1  (destrutivo)
{"error":{"code":"USER_HAS_ENROLLMENTS",...}}                              status=409  application/json
```

**4/4 conformes.** Divergência nova: BC-8 (aditiva). → commit `cc8d8a5`.

---

## Registro de ondas (§6.1) — completo

```console
| stage    | sha       | smoke  | status |
|----------|-----------|--------|--------|
| baseline | 5d02287   | —      | green  |
| onda-1   | 4701894   | 4/4    | green  |
| onda-2   | fb19464   | 4/4    | green  |
| onda-3   | 0d1eacc   | 4/4    | green  |
| onda-4   | cc8d8a5   | 4/4    | green  |
```

Nenhuma onda vazia, nenhuma onda vermelha, nenhum rollback. O único vermelho da fase foi o
`EADDRINUSE` em TR-06, identificado como falso vermelho conhecido antes de qualquer decisão de
rollback.
