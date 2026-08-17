# Baseline pré-refatoração — ecommerce-api-legacy

**Data:** 2026-08-17
**Commit base:** `f3e4297` (working tree limpo)
**Stack:** Node.js v24.12.0 / npm 11.6.2 / Express ^4.18.2 / sqlite3 ^5.1.6
**Tamanho:** 180 LOC em 3 arquivos (`src/app.js` 14, `src/AppManager.js` 141, `src/utils.js` 25)

Objetivo: registrar o comportamento observável da API **antes** de qualquer refatoração,
para servir de contrato de regressão na Fase 3.

---

## 1. Instalação de dependências

`node_modules` não existia no projeto. Executado `npm install`:

```
added 191 packages, and audited 192 packages in 1s

26 packages are looking for funding
  run `npm fund` for details

13 vulnerabilities (2 low, 3 moderate, 7 high, 1 critical)
```

> Nota: as 13 vulnerabilidades vêm do lockfile congelado do boilerplate. Não foram
> tratadas — corrigi-las alteraria o baseline e está fora do escopo da refatoração
> arquitetural.

---

## 2. Boot

Comando: `npm start` (→ `node src/app.js`)

Saída literal do stdout no boot:

```
> desafio-arquitetura-ia-boilerplate@1.0.0 start
> node src/app.js

Frankenstein LMS rodando na porta 3000...
```

**Resultado: BOOT OK.** Sobe na porta 3000 sem erro. Banco SQLite é inicializado
em memória (`manager.initDb()`) — nenhum arquivo `.db` é criado no working tree,
confirmado por `git status` limpo após a execução.

---

## 3. Lista de endpoints

Fonte primária: registro de rotas no código (`grep` por `app.<verbo>` em `src/*.js`).

```
src/AppManager.js:28:        app.post('/api/checkout', (req, res) => {
src/AppManager.js:80:        app.get('/api/admin/financial-report', (req, res) => {
src/AppManager.js:131:        app.delete('/api/users/:id', (req, res) => {
```

Total: **3 endpoints** registrados. (`src/app.js:6` tem `app.use(express.json())`,
que é middleware, não endpoint.)

### Cruzamento com `api.http`

| # | Endpoint no código | Presente em `api.http`? | Observação |
|---|---|---|---|
| 1 | `POST /api/checkout` | Sim (2 blocos: sucesso e recusa) | `api.http` cobre dois cenários do mesmo endpoint |
| 2 | `GET /api/admin/financial-report` | Sim | — |
| 3 | `DELETE /api/users/:id` | Sim (`/api/users/1`) | — |

**Divergência: nenhuma.** O `api.http` está sincronizado com o código: as 4 requests
do arquivo mapeiam exatamente para os 3 endpoints registrados, sem rota órfã no
arquivo nem rota do código faltando nele. O baseline usa os 4 cenários do `api.http`
para exercitar também o caminho de erro do checkout.

---

## 4. Smoke test — saída literal do `curl`

### 4.1 `POST /api/checkout` — cenário de sucesso

```
$ curl -s -i -X POST http://localhost:3000/api/checkout \
    -H 'Content-Type: application/json' \
    -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'

HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: application/json; charset=utf-8
Content-Length: 35
ETag: W/"23-M21Cm8ianfku3j1jgcW8LNf4kGo"
Date: Mon, 17 Aug 2026 16:42:26 GMT
Connection: keep-alive
Keep-Alive: timeout=5

{"msg":"Sucesso","enrollment_id":2}
```

### 4.2 `POST /api/checkout` — cenário de pagamento recusado

```
$ curl -s -i -X POST http://localhost:3000/api/checkout \
    -H 'Content-Type: application/json' \
    -d '{"usr":"João","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}'

HTTP/1.1 400 Bad Request
X-Powered-By: Express
Content-Type: text/html; charset=utf-8
Content-Length: 18
ETag: W/"12-cCbpbDoP+QR6rY78eoVsId2FZ+s"
Date: Mon, 17 Aug 2026 16:42:26 GMT
Connection: keep-alive
Keep-Alive: timeout=5

Pagamento recusado
```

### 4.3 `GET /api/admin/financial-report`

```
$ curl -s -i http://localhost:3000/api/admin/financial-report

HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: application/json; charset=utf-8
Content-Length: 174
ETag: W/"ae-JuM6jV5S5HzAaA5yixML4Uk6zZA"
Date: Mon, 17 Aug 2026 16:42:26 GMT
Connection: keep-alive
Keep-Alive: timeout=5

[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},{"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]
```

### 4.4 `DELETE /api/users/1`

```
$ curl -s -i -X DELETE http://localhost:3000/api/users/1

HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: text/html; charset=utf-8
Content-Length: 74
ETag: W/"4a-vthBeOP7zzO+HHtdIi6mpA3d8h8"
Date: Mon, 17 Aug 2026 16:42:26 GMT
Connection: keep-alive
Keep-Alive: timeout=5

Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
```

---

## 5. Stdout do servidor durante o smoke test

```
Frankenstein LMS rodando na porta 3000...
Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef
[LOG] Salvando no cache: last_checkout_2
Processando cartão 5111222233334444 na chave pk_live_1234567890abcdef
```

---

## 6. Contrato de regressão

Após a refatoração, estes seis pontos devem se manter **idênticos**:

| # | Verificação | Valor esperado |
|---|---|---|
| B-1 | Boot | `npm start` sobe na porta 3000 e imprime a linha de boot |
| B-2 | `POST /api/checkout` (sucesso) | `200` + `{"msg":"Sucesso","enrollment_id":2}` |
| B-3 | `POST /api/checkout` (recusado) | `400` + corpo `Pagamento recusado` |
| B-4 | `GET /api/admin/financial-report` | `200` + JSON com 2 cursos (`Clean Architecture` R$997 / `Docker` R$497) e seus alunos |
| B-5 | `DELETE /api/users/1` | `200` + a mensagem de texto sobre os registros órfãos |
| B-6 | Efeito colateral | Nenhum arquivo novo no working tree (`git status` limpo) |

> Observação sobre B-5: a mensagem confessa um comportamento defeituoso (deleção sem
> cascata deixa matrículas e pagamentos órfãos). O baseline **registra** esse
> comportamento sem legitimá-lo — se a refatoração corrigir o problema de integridade,
> a divergência em B-5 é intencional e deve ser declarada explicitamente na Fase 3,
> não tratada como regressão silenciosa.

> Observação sobre B-2/B-4: os valores dependem do seed executado em `initDb()` a cada
> boot (banco em memória). O baseline vale para um servidor recém-iniciado; repetir o
> checkout na mesma instância incrementa `enrollment_id`.
