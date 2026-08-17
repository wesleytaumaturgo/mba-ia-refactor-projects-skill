# Auditoria de Arquitetura — `ecommerce-api-legacy`

> Fase 2 de `/refactor-arch`. Auditoria somente leitura. Nenhum arquivo do projeto foi
> modificado. Todo `arquivo:linha` foi obtido por leitura direta nesta execução.

## Contexto

| Item | Valor |
|---|---|
| Linguagem | JavaScript / CommonJS (runtime do ambiente: Node.js v24.12.0) |
| Framework | Express 4.22.1 instalado (declarado `^4.18.2`) |
| Persistência | `sqlite3` 5.1.7, SQLite **em memória** (`:memory:`), 5 tabelas |
| Domínio | LMS de cursos pagos: o checkout cria usuário, matrícula e pagamento; há relatório financeiro administrativo e remoção de usuário |
| Arquivos-fonte / LOC | 3 arquivos, 180 linhas (`src/app.js` 14, `src/AppManager.js` 141, `src/utils.js` 25) |
| Endpoints | 3 — baseline capturado em 4 respostas |
| Commit de baseline | `5d02287` |

### Arquitetura efetiva

O mecanismo de resolução da stack é **import explícito** (CommonJS `require`; o manifesto não
declara `type`, e não há autoloader, varredura de pacote nem container de injeção). Partindo do
entry point declarado no manifesto (`package.json` → `main` e `scripts.start` → `src/app.js`), o
grafo alcança exatamente três módulos: `src/app.js` → `src/AppManager.js` → `src/utils.js`, mais
os pacotes `express` e `sqlite3`. **Não existe nenhum diretório de camada, alcançável ou não** —
não há `controllers/`, `services/`, `repositories/`, `models/`, `middlewares/` nem `config/`;
portanto não há camada preexistente a adotar (`mvc-guidelines.md` §1 regra 4 e §6 não se aplicam:
não há convenção declarada pela stack nem árvore de camadas no projeto), e a Fase 3 cai na
precedência 2 da §4.1 — variante idiomática JavaScript, `src/` como raiz das camadas.

Responsabilidade por módulo alcançável:

- **`src/app.js`** — composition root degenerado: instancia `AppManager` sem argumento algum,
  dispara a criação de schema e sobe o servidor. Acumula 2 responsabilidades (montagem do grafo e
  bootstrap de persistência).
- **`src/AppManager.js`** — acumula **cinco** responsabilidades no mesmo corpo: abertura da
  conexão (linha 7), definição de schema e seed (10–23), registro das 3 rotas (28, 80, 131),
  regra de negócio de pagamento e de receita (46, 48, 108–110) e apresentação/serialização
  (35, 38, 41, 48, 60, 84, 98, 121, 135). É o alvo estrutural de AP-06.
- **`src/utils.js`** — acumula 3 responsabilidades: configuração literal com segredos (1–7),
  estado global mutável (9–10) e duas funções heterogêneas (log+cache e derivação de senha).

Símbolos exportados e **não** consumidos fora do módulo de origem: `globalCache` (0 referências),
`totalRevenue` (importado em `AppManager.js:2`, 0 usos). Nenhuma camada inalcançável a registrar
antes de remoção — não existe camada.

Arestas que violam a direção de dependência de `mvc-guidelines.md` §3: **todas**. Não há
camadas entre a rota e o driver; o handler de rota fala SQL diretamente.

### Baseline de comportamento

| Método | Endpoints | Status codes observados |
|---|---|---|
| GET | 1 | 200 ×1 |
| POST | 1 | 200 ×1 · 400 ×1 (dois casos representativos do mesmo endpoint) |
| DELETE | 1 | 200 ×1 |
| **Total (`M`)** | **3 endpoints / 4 requisições** | **`M` = 4** |

Baseline completo, com media type e forma do corpo por endpoint, em
`/home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/baseline-ecommerce-api-legacy.json`.

Pré-existentes quebrados: **nenhum**.
Não enumeráveis, fora de `M`: **nenhum** — não há rota montada dinamicamente nem registrada fora
de `setupRoutes`.

Observação de contrato registrada no baseline: **a ordem dos itens da coleção de
`GET /api/admin/financial-report` não é garantida.** Duas execuções consecutivas do código
intocado devolveram ordens diferentes (`[Clean Architecture, Docker]` e `[Docker, Clean
Architecture]`), consequência direta do finding F-013 (contagem regressiva sobre callbacks
concorrentes). Divergência de ordem na Fase 3 não é vermelha (`validation-protocol.md` §8).

`M` é o denominador de toda onda da Fase 3: onda verde exige `4/4` conformes.

## Sumário

| Severidade | Findings | Ocorrências |
|---|---|---|
| CRITICAL | 5 | 12 |
| HIGH | 6 | 35 |
| MEDIUM | 4 | 24 |
| LOW | 5 | 26 |
| **Total** | **20** | **97** |

---

## Findings

### [CRITICAL] F-001 — Credenciais de produção literais no módulo de configuração, sem nenhuma leitura de ambiente

- **Anti-pattern:** AP-02 · **Transformação:** TR-01 · **Onda:** 1
- **Arquivo:** `src/utils.js:1-7`
- **Evidência:**

```javascript
const config = {
    dbUser: "admin_master",
    dbPass: "senha_super_secreta_prod_123", 
    paymentGatewayKey: "pk_live_1234567890abcdef",
    smtpUser: "no-reply@fullcycle.com.br",
    port: 3000
};
```

- **Descrição:** quatro valores sensíveis atribuídos como literal no módulo carregado pelo
  bootstrap. Ocorrências: `src/utils.js:2` (usuário de banco), `:3` (senha de banco), `:4` (chave
  de gateway de pagamento), `:5` (usuário SMTP). A verificação exigida pelo AP foi executada:
  `grep -rn "process.env\|dotenv" src/ package.json` não retorna **nenhuma** linha — não existe
  leitura de ambiente em ponto algum do projeto, logo nenhum destes literais é default de
  desenvolvimento com precedência de produção. Dois marcadores confirmam intenção produtiva:
  o prefixo `pk_live_` e o sufixo `_prod_` no nome do valor. Três dos quatro (`dbUser`, `dbPass`,
  `smtpUser`) não são referenciados por nenhum outro ponto do código (ver F-018): são segredos
  versionados que não protegem nada, e apagá-los do arquivo não os remove do histórico do
  repositório.
- **Impacto:** qualquer pessoa com acesso de leitura ao repositório — incluindo o histórico do
  Git, forks e mirrors de CI — obtém a chave do gateway de pagamento e a senha de banco. A chave
  ainda é impressa em stdout a cada checkout (F-005), ampliando o vazamento para os logs.
- **Correção esperada:** camada `config` que lê o ambiente, falha no boot se faltar variável
  obrigatória, e um `.env.example` sem valores; os segredos atuais entram na lista de rotação.
- **Confiança:** ALTA

---

### [CRITICAL] F-002 — Rota administrativa e rota destrutiva sem nenhum ponto de verificação de identidade

- **Anti-pattern:** AP-05 · **Transformação:** TR-05 · **Onda:** 1
- **Arquivo:** `src/AppManager.js:80`, `src/AppManager.js:131`, `src/AppManager.js:28`
- **Evidência:**

```javascript
app.get('/api/admin/financial-report', (req, res) => {
    let report = [];
    this.db.all("SELECT * FROM courses", [], (err, courses) => {
```

```javascript
app.delete('/api/users/:id', (req, res) => {
    let id = req.params.id;
    this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
```

- **Descrição:** as três rotas vão do registro ao acesso a dados sem middleware, sem filtro e sem
  verificação inline. `src/app.js:6` registra apenas `express.json()`; não há nenhum outro
  `app.use`. Ocorrências: `:80` (path com prefixo `/api/admin`, expõe dados de terceiros — nome do
  aluno e valor pago por matrícula), `:131` (destrutiva, apaga usuário por id sequencial),
  `:28` (escreve em 4 tabelas e dispara a integração de pagamento). O schema não modela papel
  algum (`src/AppManager.js:12`: `users (id, name, email, pass)`), de modo que não há sequer o
  sinal correlato de autorização projetada e não implementada — ela não foi projetada.
- **Impacto:** caminho concreto e verificado nesta execução —
  `curl -X DELETE http://localhost:3000/api/users/1` de um chamador anônimo devolve `200` e
  remove o usuário; `curl http://localhost:3000/api/admin/financial-report` devolve a receita por
  curso e o nome de cada aluno pagante. Nenhuma condição rara é necessária: basta alcançar a
  porta.
- **Correção esperada:** middleware de autenticação e autorização aplicado às rotas privilegiada
  e destrutiva; `POST /api/checkout` permanece público por decisão de produto (ND-1) e recebe
  limite de taxa.
- **Confiança:** ALTA

---

### [CRITICAL] F-003 — Derivação de senha caseira com colisão demonstrada, e credencial em texto simples no seed

- **Anti-pattern:** AP-04 · **Transformação:** TR-03 · **Onda:** 1
- **Arquivo:** `src/utils.js:17-23`, `src/AppManager.js:68`, `src/AppManager.js:18`
- **Evidência:**

```javascript
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

```javascript
this.db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
```

- **Descrição:** função caseira, sem salt e sem fator de custo real — o laço de 10.000 iterações
  concatena sempre o **mesmo** par de caracteres, gastando CPU sem adicionar entropia alguma. A
  saída é integralmente determinada pelos 2 primeiros caracteres do base64 da senha, repetidos 5
  vezes. Ocorrências: `src/utils.js:17-23` (a função), `src/AppManager.js:68` (único caminho de
  escrita, `badCrypto(p || "123456")` — inclusive com senha default embutida quando o campo vem
  vazio), `src/AppManager.js:18` (seed grava a senha `'123'` em texto simples, sem passar pela
  função). **Verificação decisiva executada nesta auditoria:**

```console
$ node -e "const {badCrypto}=require('./src/utils'); ['senhaforte','senha123','sorvete'].forEach(s=>console.log(s,'->',badCrypto(s)))"
senhaforte -> c2c2c2c2c2
senha123   -> c2c2c2c2c2
sorvete    -> c2c2c2c2c2
```

  Nenhuma dependência de hashing lento é declarada no manifesto (`dependencies`: apenas `express`
  e `sqlite3`) — a arquitetura pretendida não existia sequer como intenção registrada.
- **Impacto:** três senhas distintas produzem o mesmo valor armazenado. Um invasor com acesso à
  tabela `users` recupera a classe de equivalência de qualquer senha em tempo constante — o
  espaço de saída tem no máximo 64² = 4.096 valores. Não há caminho de verificação hoje (não
  existe login), mas o dano é na coluna persistida, que já contém uma credencial em claro.
- **Correção esperada:** derivação com salt por registro e fator de custo (ND-3 escolhe o
  mecanismo); o seed passa a gravar credencial derivada, ou deixa de gravar credencial.
- **Confiança:** ALTA

---

### [CRITICAL] F-004 — God class: conexão, schema, rotas, regra de negócio e apresentação no mesmo corpo

- **Anti-pattern:** AP-06 · **Transformação:** TR-06 · **Onda:** 1
- **Arquivo:** `src/AppManager.js:1-141`
- **Evidência:**

```javascript
const sqlite3 = require('sqlite3').verbose();       // linha 1  — driver de banco
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }   // linha 7  — conexão
    initDb() { this.db.run("CREATE TABLE users (...)"); ... }       // 10–23    — schema + seed
    setupRoutes(app) {
        app.post('/api/checkout', (req, res) => {                   // 28       — rota
            let status = cc.startsWith("4") ? "PAID" : "DENIED";    // 46       — regra de negócio
            res.status(200).json({ msg: "Sucesso", ... });          // 60       — apresentação
```

- **Descrição:** um único arquivo de 141 linhas reúne cinco responsabilidades distintas em faixas
  entrelaçadas: abertura de conexão (`:7`), definição de schema e seed (`:10-23`), registro das
  três rotas (`:28`, `:80`, `:131`), regra de negócio (`:46`, `:48`, `:108-110`) e montagem de
  resposta (`:35`, `:38`, `:41`, `:48`, `:60`, `:84`, `:98`, `:121`, `:135`). O sinal de nome
  também dispara: `AppManager` é substantivo genérico com sufixo "Manager" que não delimita
  responsabilidade — o nome não permite prever o conteúdo. Não é o caso de isenção do AP: o
  arquivo não é monotemático nem é o composition root (esse papel está em `src/app.js`).
  Não existe fronteira onde inserir uma camada.
- **Impacto:** nenhuma responsabilidade é testável isoladamente — verificar a regra de aprovação
  de pagamento exige subir um servidor HTTP e um banco. Toda mudança de qualquer natureza toca o
  mesmo arquivo, e o histórico de versionamento perde a capacidade de indicar o que mudou.
- **Correção esperada:** decomposição em `config`, `models`, `repositories`, `services`,
  `controllers`, `routes` e `middlewares` sob `src/`, com `src/app.js` como composition root
  único; `AppManager` deixa de existir.
- **Confiança:** ALTA

---

### [CRITICAL] F-005 — Número de cartão completo e chave de gateway emitidos em log a cada checkout

- **Anti-pattern:** AP-07 · **Transformação:** TR-14 · **Onda:** 1
- **Arquivo:** `src/AppManager.js:45`
- **Evidência:**

```javascript
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

- **Descrição:** o template interpola dois valores sensíveis sem mascaramento: `cc`, que vem
  diretamente de `req.body.card` (`src/AppManager.js:33`) e é o PAN completo do portador, e
  `config.paymentGatewayKey`, que é a chave `pk_live_...` de F-001. A emissão ocorre **antes** de
  qualquer decisão de aprovação, portanto em todo checkout, aprovado ou recusado. Nenhum
  truncamento, nenhuma redação. Confirmado literalmente no stdout capturado no baseline:

```console
Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef
Processando cartão 5111222233334444 na chave pk_live_1234567890abcdef
```

- **Impacto:** o PAN completo de todo cliente e a chave de produção do gateway ficam em texto
  simples em stdout — e portanto em qualquer coletor de logs, arquivo de journal ou pipeline de
  observabilidade que capture a saída do processo. É vazamento de dado de portador de cartão sem
  nenhuma condição rara.
- **Desvio de severidade:** nenhum. Registro para o executor: o catálogo rotula **TR-14** para a
  Onda 3, mas a onda é propriedade do finding — TR-14 é antecipado para a **Onda 1**, conforme a
  nota de severidade da própria entrada AP-07.
- **Correção esperada:** logger estruturado com níveis e redação dos campos sensíveis; o PAN
  nunca é emitido, a chave nunca é emitida.
- **Confiança:** ALTA

---

### [HIGH] F-006 — Handlers de rota falam SQL diretamente, sem repositório nem serviço interposto

- **Anti-pattern:** AP-13 · **Transformação:** TR-06 · **Onda:** 1 (de carona com F-004)
- **Arquivo:** `src/AppManager.js` — 11 ocorrências
- **Evidência:**

```javascript
app.post('/api/checkout', (req, res) => {
    ...
    this.db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [cid], (err, course) => {
```

- **Descrição:** o handle do driver (`this.db`) é manipulado dentro do corpo dos três callbacks
  de rota, com as consultas montadas ali mesmo. Ocorrências: `:37`, `:40`, `:50`, `:54`, `:57`,
  `:69` (rota de checkout), `:83`, `:92`, `:104`, `:106` (relatório financeiro), `:133` (remoção
  de usuário). Não existe camada intermediária alcançável a ser saltada — ela simplesmente não
  existe, o que é a forma mais forte do sinal. A isenção do AP não se aplica: nenhuma das rotas é
  leitura trivial sem regra, e o handler manipula o mecanismo de persistência ele mesmo em vez de
  usar uma API de domínio do framework.
- **Impacto:** SQL espalhado por três handlers significa que qualquer evolução de schema exige
  varrer os handlers de protocolo; e nenhuma regra de negócio é executável sem um objeto de
  requisição HTTP.
- **Correção esperada:** `repositories/` como único lugar do projeto que conhece SQL; controllers
  chamam services, services chamam repositories.
- **Confiança:** ALTA
- **Nota de onda:** TR-06 resolve simultaneamente F-004 (AP-06, CRITICAL) e este finding. Roda na
  Onda 1 pela severidade de F-004 e fecha este de carona.

---

### [HIGH] F-007 — DDL e seed executados no boot, em banco volátil e sem nenhuma restrição de integridade

- **Anti-pattern:** AP-21 · **Transformação:** TR-16 · **Onda:** 2
- **Arquivo:** `src/AppManager.js:10-23`, `src/app.js:9`
- **Evidência:**

```javascript
initDb() {
    this.db.serialize(() => {
        this.db.run("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)");
        ...
        this.db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
```

```javascript
const manager = new AppManager();
manager.initDb();                 // src/app.js:9 — DDL como efeito colateral do boot
```

- **Descrição:** 5 `CREATE TABLE` e 4 `INSERT` de seed executados incondicionalmente no caminho de
  boot, sem guarda de ambiente e sem ferramenta de migração no manifesto. Ocorrências: `:12`,
  `:13`, `:14`, `:15`, `:16` (DDL); `:18`, `:19`, `:20`, `:21` (seed). O sinal estrutural adicional
  também dispara e foi verificado — `grep -nE "FOREIGN KEY|REFERENCES|UNIQUE|NOT NULL|CHECK"`
  sobre o arquivo não retorna **nenhuma** linha: as 5 tabelas não declaram chave estrangeira,
  unicidade nem não-nulo. `enrollments.user_id` e `enrollments.course_id` não referenciam nada;
  `payments.enrollment_id` não referencia nada; `users.email` não é único.
- **Impacto:** a consequência é maior que o incômodo de criar tabela no boot. O banco é
  `:memory:` (`src/AppManager.js:7`) — **todo dado é perdido a cada reinício**, e o projeto não
  tem caminho de evolução de schema algum: não há migração, e alterar uma coluna significa alterar
  o `CREATE TABLE` e recriar o banco. A ausência de FK é a causa raiz de F-010: sem
  `ON DELETE CASCADE` ou `RESTRICT`, o banco não pode impedir os órfãos que a própria aplicação
  confessa produzir. O seed ainda planta uma credencial conhecida em texto simples em qualquer
  ambiente (cruza com F-003).
- **Correção esperada:** migrações versionadas fora do caminho de boot, com constraints de
  integridade declaradas; seed atrás de guarda de ambiente de desenvolvimento (ND-4).
- **Confiança:** ALTA

---

### [HIGH] F-008 — Regra de negócio, integração de pagamento e efeitos colaterais escritos dentro dos handlers

- **Anti-pattern:** AP-08 · **Transformação:** TR-07 · **Onda:** 2
- **Arquivo:** `src/AppManager.js` — 7 ocorrências
- **Evidência:**

```javascript
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
let status = cc.startsWith("4") ? "PAID" : "DENIED";     // regra de aprovação de pagamento

if (status === "DENIED") return res.status(400).send("Pagamento recusado");
```

```javascript
if (payment && payment.status === 'PAID') {
    courseData.revenue += payment.amount;                 // regra de reconhecimento de receita
}
```

- **Descrição:** decisões de domínio e efeitos colaterais de negócio vivem no corpo dos callbacks
  de protocolo. Ocorrências: `:46` (regra de aprovação de pagamento — a elegibilidade do cartão),
  `:48` (transição de estado do checkout), `:57` (efeito colateral: escrita de trilha de
  auditoria), `:59` (efeito colateral: escrita em cache), `:66-75` (regra de *get-or-create* do
  usuário a partir do e-mail), `:108-110` (regra de reconhecimento de receita: só `PAID` compõe),
  `:113` (regra de exibição de aluno ausente como `'Unknown'`). O **sinal correlato** de alto
  valor também dispara em `:38` — `if (err || !course) return res.status(404)` — o handler
  inspeciona a forma do valor retornado (nulo) para decidir o status code, que é o sintoma mais
  confiável de que não existe service. Nenhuma dessas linhas é tradução de protocolo.
- **Impacto:** a regra de aprovação de pagamento — a decisão de maior valor do domínio — só é
  executável sob HTTP. Não há como testá-la, reusá-la numa fila de mensagens ou auditá-la sem
  subir o servidor. Alterar a regra de receita exige editar um callback aninhado em cinco níveis.
- **Correção esperada:** `services/` como único lugar que decide *o quê* acontece; controllers
  traduzem protocolo e mapeiam erro de domínio para status.
- **Confiança:** ALTA

---

### [HIGH] F-009 — Infraestrutura instanciada no construtor e composition root que não injeta nada

- **Anti-pattern:** AP-09 · **Transformação:** TR-09 · **Onda:** 2
- **Arquivo:** `src/AppManager.js:1`, `src/AppManager.js:7`, `src/app.js:8`, `src/AppManager.js:2`
- **Evidência:**

```javascript
class AppManager {
    constructor() {
        this.db = new sqlite3.Database(':memory:');    // src/AppManager.js:7
    }
```

```javascript
const manager = new AppManager();                      // src/app.js:8 — nenhum argumento
```

- **Descrição:** quatro ocorrências. `:7` instancia o driver de banco dentro do construtor, com o
  destino da conexão fixado em literal (`':memory:'`); `src/app.js:8` constrói o objeto principal
  sem passar dependência alguma — é o item 10 do checklist de `mvc-guidelines.md` §9 respondido
  "sim"; `src/AppManager.js:1` importa o driver no mesmo módulo que registra rotas (salto de
  camada: a apresentação alcança a infraestrutura direto); `src/AppManager.js:2` + `:45` importam
  e consomem o singleton de configuração dentro da lógica, em vez de recebê-lo. Não é o caso de
  isenção: `AppManager` não é o composition root (esse papel está em `src/app.js`), a stack não
  tem container de injeção, e a dependência instanciada tem estado.
- **Impacto:** nenhuma parte do sistema é instanciável em teste com uma implementação
  alternativa de banco — qualquer verificação exige o SQLite real. Trocar `:memory:` por um banco
  persistente exige editar o construtor de uma classe que também registra rotas.
- **Correção esperada:** `src/app.js` como composition root único: lê a config, cria a conexão,
  injeta nos repositories, que são injetados nos services, que são injetados nos controllers.
- **Confiança:** ALTA

---

### [HIGH] F-010 — Escritas relacionadas sem fronteira transacional, e deleção que produz órfãos por construção

- **Anti-pattern:** AP-11 · **Transformação:** TR-10 · **Onda:** 2
- **Arquivo:** `src/AppManager.js:50-63`, `src/AppManager.js:69-72`, `src/AppManager.js:131-137`
- **Evidência:**

```javascript
this.db.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, cid], function(err) {
    if (err) return res.status(500).send("Erro Matrícula");
    let enrId = this.lastID;
    self.db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrId, course.price, status], function(err) {
        if (err) return res.status(500).send("Erro Pagamento");
        self.db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [...], (err) => {
```

```javascript
this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
    res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
});
```

- **Descrição:** duas ocorrências, ambas com interleaving concreto.
  **(a) Checkout** — até quatro escritas relacionadas em sequência (`users` em `:69`,
  `enrollments` em `:50`, `payments` em `:54`, `audit_logs` em `:57`), cada uma com commit
  implícito e com retorno antecipado de erro no meio (`:51`, `:55`) sem nenhuma compensação. O
  bloco `serialize` de `:11` cobre apenas o `initDb`, não este caminho.
  **(b) Deleção** — `:133` remove o registro principal deixando dependentes órfãos, num schema que
  não declara integridade referencial (F-007). O próprio corpo da resposta em `:135` confessa o
  defeito.
- **Impacto:** cenário concreto do checkout — o `INSERT` em `enrollments` sucede, o `INSERT` em
  `payments` falha (disco cheio, violação futura de constraint, processo derrubado entre as duas
  chamadas): o aluno fica **matriculado sem pagamento registrado**, e o cliente recebe `500` como
  se nada tivesse acontecido. Não há como distinguir depois esse estado de uma matrícula
  legítima. Cenário concreto da deleção — apagar o usuário 1 deixa `enrollments.user_id = 1` e a
  linha de `payments` correspondente apontando para um usuário inexistente; o relatório financeiro
  passa a somar receita atribuída a `'Unknown'` (`:113`), corrompendo o número que o negócio usa.
- **Correção esperada:** transação explícita envolvendo as escritas do checkout, com rollback no
  caminho de erro; deleção sob integridade referencial declarada (cascade ou restrict), decidida
  em ND-5.
- **Confiança:** ALTA

---

### [HIGH] F-011 — Estado global mutável de módulo, incluindo um acumulador estruturalmente incapaz de funcionar

- **Anti-pattern:** AP-10 · **Transformação:** TR-09 · **Onda:** 2
- **Arquivo:** `src/utils.js:9`, `src/utils.js:10`
- **Evidência:**

```javascript
let globalCache = {};
let totalRevenue = 0;

function logAndCache(key, data) {
    console.log(`[LOG] Salvando no cache: ${key}`);
    globalCache[key] = data;
}
```

- **Descrição:** duas ocorrências. `:9` — `globalCache` é dicionário em escopo de módulo escrito
  a partir do caminho de requisição (`logAndCache` é chamado em `src/AppManager.js:59`, dentro do
  handler de checkout), sem lock e **sem nenhuma política de invalidação ou expiração**: a chave é
  `last_checkout_${userId}`, então cresce monotonicamente com o número de usuários distintos.
  `:10` — `totalRevenue` é o **sinal correlato** literal do AP: primitivo exportado por valor em
  `:25` e importado em `src/AppManager.js:2`. Em CommonJS, exportar um número por valor faz o
  importador receber uma cópia; nenhuma atribuição futura em `utils.js` seria visível, e de fato
  nunca há atribuição alguma. O código declara uma intenção de acumulador que a linguagem não
  permite cumprir. Não é o caso de isenção: nenhum dos dois é imutável após a inicialização, e
  nenhum é pool thread-safe por contrato.
- **Impacto:** `globalCache` é vazamento de memória sem teto — um processo de vida longa acumula
  uma entrada por usuário que fez checkout, para sempre, e o valor guardado (título do curso)
  nunca é lido por ninguém. `totalRevenue` dá ao leitor a falsa impressão de que existe um
  acumulador de receita; o relatório financeiro recalcula tudo em laço (F-014) porque o
  acumulador nunca funcionou.
- **Correção esperada:** cache com dono explícito e política de expiração, injetado onde é usado;
  `totalRevenue` removido (é também ocorrência de F-018).
- **Confiança:** ALTA

---

### [MEDIUM] F-012 — Erro de driver descartado sem registro, com falha de infraestrutura colapsada em 404 e em 200

- **Anti-pattern:** AP-18 · **Transformação:** TR-13 · **Onda:** 3
- **Arquivo:** `src/AppManager.js` — 11 ocorrências
- **Evidência:**

```javascript
this.db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [cid], (err, course) => {
    if (err || !course) return res.status(404).send("Curso não encontrado");
```

```javascript
this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
    res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
});
```

- **Descrição:** o padrão se repete em todo callback do driver. Ocorrências em que o objeto de
  erro é **descartado sem nenhum registro**: `:41`, `:51`, `:55`, `:70`, `:84`. Ocorrências em que
  o parâmetro `err` é declarado e **inteiramente ignorado**: `:57`, `:93`, `:104`, `:106`, `:133`.
  Ocorrência que **colapsa** falha de infraestrutura e recurso inexistente no mesmo status: `:38`
  — `if (err || !course)` devolve `404` tanto para "curso não existe" quanto para "o banco
  falhou". Não há tratador centralizado; `src/app.js` não registra middleware de erro.
  Não é o caso de isenção: nenhuma dessas capturas está na fronteira do processo, e nenhuma emite
  identificador de correlação.
- **Impacto:** consequência confirmada seguindo o caminho concreto de `:133` — se o `DELETE`
  falhar no banco, o handler responde `200` e o texto de sucesso, porque `err` nunca é lido: o
  cliente é informado de que o usuário foi apagado quando ele não foi. E em `:38`, uma
  indisponibilidade do banco é reportada ao cliente como `404`, levando quem opera a procurar um
  problema de dados onde há um problema de infraestrutura. Como nada é logado, o defeito é
  invisível em produção.
- **Correção esperada:** middleware de tratamento de erro centralizado que distingue erro de
  domínio de defeito, registra o erro completo e emite ao cliente apenas código estável e
  identificador de correlação.
- **Confiança:** ALTA

---

### [MEDIUM] F-013 — Contrato de resposta divergente: sucesso em JSON, erro em texto puro, idiomas misturados no mesmo handler

- **Anti-pattern:** AP-23 · **Transformação:** TR-13 · **Onda:** 3
- **Arquivo:** `src/AppManager.js` — 10 ocorrências
- **Evidência (dois handlers equivalentes lado a lado):**

```javascript
// handler de checkout — src/AppManager.js:35, :38, :60
if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");        // inglês, text/html
    if (err || !course) return res.status(404).send("Curso não encontrado");    // português, text/html
                res.status(200).json({ msg: "Sucesso", enrollment_id: enrId }); // application/json
```

```javascript
// handler de remoção — src/AppManager.js:135
res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");  // sucesso em text/html
```

- **Descrição:** dez ocorrências divergentes. Corpos de erro em texto puro: `:35` (`"Bad
  Request"`), `:38`, `:41`, `:48`, `:51`, `:55`, `:70`, `:84`. Corpos de sucesso: `:60` e `:98`/
  `:121` em `application/json`, mas `:135` em `text/html`. Três divergências independentes: **(a)**
  media type do erro difere do media type do sucesso no mesmo handler; **(b)** o media type de
  sucesso difere entre handlers equivalentes (`POST /api/checkout` devolve JSON, `DELETE
  /api/users/:id` devolve texto); **(c)** idiomas misturados **no mesmo handler** — `"Bad
  Request"` em `:35` e `"Curso não encontrado"` em `:38`, três linhas adiante. Não há código de
  erro estável em nenhuma resposta. A divergência não é deliberada nem documentada — não há
  comentário, nem rota de compatibilidade legada.
- **Impacto:** um cliente que faça `JSON.parse` da resposta funciona no caminho feliz e quebra em
  todo caminho de erro do mesmo endpoint. Não existe campo estável para o cliente distinguir
  "cartão recusado" de "curso inexistente" a não ser comparando strings em dois idiomas.
- **Correção esperada:** envelope de erro uniforme com código estável em toda a API, e sucesso
  sempre em `application/json`. Cada endpoint afetado está enumerado em Breaking changes.
- **Confiança:** ALTA

---

### [MEDIUM] F-014 — N+1 em três níveis no relatório financeiro, com agregação calculada em laço na aplicação

- **Anti-pattern:** AP-15 · **Transformação:** TR-11 · **Onda:** 3
- **Arquivo:** `src/AppManager.js:83-127`
- **Evidência:**

```javascript
this.db.all("SELECT * FROM courses", [], (err, courses) => {          // :83  — 1 consulta
    courses.forEach(c => {
        this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {  // :92 — C consultas
            enrollments.forEach(enr => {
                this.db.get("SELECT name, email FROM users WHERE id = ?", [enr.user_id], (err, user) => {      // :104 — E consultas
                    this.db.get("SELECT amount, status FROM payments WHERE enrollment_id = ?", [enr.id], (err, payment) => {  // :106 — E consultas
                        if (payment && payment.status === 'PAID') {
                            courseData.revenue += payment.amount;      // :109 — agregação em laço
```

- **Descrição:** consulta disparada dentro de laço que itera o resultado da consulta anterior, em
  **três** níveis de aninhamento. Contagem de idas ao banco em função do tamanho do resultado:
  `1 + C + 2·E`, onde `C` é o número de cursos e `E` o total de matrículas. Com 50 cursos e 5.000
  matrículas são **10.051** consultas para montar uma resposta. Uma junção
  `courses ⋈ enrollments ⋈ users ⋈ payments` resolveria numa ida só. A **variante correlata**
  também dispara em `:109`: a soma de receita é calculada em laço na aplicação sobre todos os
  pagamentos, quando é exprimível como `SUM(...) FILTER/WHERE status = 'PAID'` na própria
  consulta. Não é o caso de isenção: a cardinalidade do laço externo (cursos) não é fechada pelo
  domínio — cresce com o catálogo.
- **Impacto:** além do custo, este finding é a causa da **não-determinação de ordem** registrada
  no baseline: `report.push(courseData)` (`:96`, `:119`) ocorre na ordem em que cada cadeia de
  callbacks termina, não na ordem de `courses`. Duas execuções consecutivas do código intocado
  devolveram os cursos em ordens diferentes — o cliente não pode confiar na ordem da coleção.
- **Correção esperada:** consulta única com junção e agregação no banco, com cláusula de
  ordenação explícita.
- **Confiança:** ALTA

---

### [MEDIUM] F-015 — Relatório financeiro sem limite: tamanho da resposta é função dos dados

- **Anti-pattern:** AP-22 · **Transformação:** TR-17 · **Onda:** 3
- **Arquivo:** `src/AppManager.js:83`, `src/AppManager.js:92`
- **Evidência:**

```javascript
this.db.all("SELECT * FROM courses", [], (err, courses) => {
```

```javascript
this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
```

- **Descrição:** duas ocorrências, ambas sem cláusula de limite, offset ou cursor, e o handler
  (`:80`) não lê nenhum parâmetro de query. `GET /api/admin/financial-report` serializa **todos**
  os cursos e, dentro de cada um, **todas** as matrículas com o nome de cada aluno. Não é o caso
  de isenção: nem cursos nem matrículas têm cardinalidade fechada pelo domínio — as duas crescem
  com o uso do produto, e matrículas crescem mais rápido.
- **Impacto:** com 5.000 matrículas a resposta carrega 5.000 objetos de aluno num corpo único,
  montado inteiro em memória (`report` em `:81`, `courseData.students` em `:112`) antes do
  primeiro byte sair. O tempo de resposta e o consumo de memória do processo passam a ser função
  do volume do negócio, não do contrato.
- **Correção esperada:** parâmetros de paginação no contrato, com limite default; forma da
  resposta declarada em Breaking changes (BC-6).
- **Confiança:** ALTA

---

### [LOW] F-016 — Identificadores de uma a três letras recebendo campos de payload, e contrato público divergente do domínio

- **Anti-pattern:** AP-27 · **Transformação:** TR-18 · **Onda:** 4
- **Arquivo:** `src/AppManager.js:26`, `src/AppManager.js:29-33`
- **Evidência:**

```javascript
let u = req.body.usr;
let e = req.body.eml;
let p = req.body.pwd;
let cid = req.body.c_id;
let cc = req.body.card;
```

- **Descrição:** onze ocorrências. Cinco identificadores de 1 a 3 letras (`u`, `e`, `p`, `cid`,
  `cc` em `:29`–`:33`) recebem campos de payload e são usados ao longo de um handler de **50
  linhas** (`:28`–`:78`) — muito além do escopo de três linhas em que nome curto é legível; `e`
  ainda é reutilizado como nome de variável enquanto `err` é o parâmetro de erro nos callbacks
  aninhados. Cinco nomes do contrato público divergem do vocabulário do domínio: `usr`, `eml`,
  `pwd`, `c_id`, `card` contra `name`, `email`, `password`, `courseId` — divergência entre o
  vocabulário da rota e o da tabela (`users(name, email, pass)`), que é o sinal de vocabulário do
  `project-analysis.md` §5. E `:26` (`const self = this;`) mistura dois idiomas de vínculo no
  mesmo método: arrow functions em `:28`/`:37`/`:40` e `function(err)` em `:50`/`:54`/`:69`,
  obrigando o `self` a existir. O nome `AppManager` é ocorrência de F-004, não deste finding.
- **Impacto:** custo de leitura e risco de troca — `e` (email) e `err` (erro) coexistem no mesmo
  escopo aninhado. Sem efeito observável em produção.
- **Correção esperada:** nomes do vocabulário do domínio no código e no contrato público (a
  renomeação de campos de payload é breaking change — BC-7, e é item de decisão ND-6).
- **Confiança:** ALTA

---

### [LOW] F-017 — Vocabulário fechado de status de pagamento como literal inline, sem constante e sem constraint

- **Anti-pattern:** AP-25 · **Transformação:** TR-18 · **Onda:** 4
- **Arquivo:** `src/AppManager.js:46`, `:48`, `:108`, `:21`, `:15`
- **Evidência:**

```javascript
let status = cc.startsWith("4") ? "PAID" : "DENIED";      // :46
if (status === "DENIED") return res.status(400).send("Pagamento recusado");   // :48
if (payment && payment.status === 'PAID') {               // :108
```

- **Descrição:** cinco ocorrências do conjunto fechado `{PAID, DENIED}` reconstruído como literal
  em três pontos do código (`:46` produz os dois, `:48` compara com um, `:108` compara com o
  outro) mais o seed (`:21`), sem enum, sem constante nomeada e sem restrição equivalente no
  schema — `payments.status` é declarado como `TEXT` livre em `:15`, sem `CHECK`. Aspas duplas em
  `:46`/`:48` e simples em `:108`, o que já indica que as cópias não têm dono comum.
  **Limite aplicado:** o literal `"4"` em `:46` (a regra de bandeira do cartão) **não** abre
  finding LOW separado — ele vive dentro do bloco que já é o finding F-008, e é citado lá como
  ocorrência. O mesmo condicional não é dois findings.
- **Impacto:** custo de manutenção — introduzir um terceiro status (`REFUNDED`, `PENDING`) exige
  encontrar as três cópias, e nada no banco impede que uma quarta cópia grave um valor
  divergente. Sem efeito observável em produção hoje.
- **Correção esperada:** vocabulário como constante nomeada única, com `CHECK` equivalente no
  schema (o `CHECK` é entregue por TR-16, na Onda 2).
- **Confiança:** ALTA

---

### [LOW] F-018 — Código morto: dois símbolos exportados sem consumidor e três chaves de configuração sensíveis nunca lidas

- **Anti-pattern:** AP-26 · **Transformação:** TR-15 · **Onda:** 4
- **Arquivo:** `src/utils.js:2`, `:3`, `:5`, `:9`, `:10`, `src/AppManager.js:2`
- **Evidência:**

```javascript
const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');   // AppManager.js:2
```

```javascript
module.exports = { config, logAndCache, badCrypto, globalCache, totalRevenue };  // utils.js:25
```

- **Descrição:** seis ocorrências, todas com contagem de referências verificada nesta execução.
  `totalRevenue` — importado em `src/AppManager.js:2` e **zero** usos (importar não é usar);
  `globalCache` — exportado em `:25` e **zero** referências fora de `src/utils.js`;
  `config.dbUser` (`:2`), `config.dbPass` (`:3`) e `config.smtpUser` (`:5`) — **zero** referências
  em todo o projeto, confirmado por `grep -n "dbUser\|dbPass\|smtpUser" src/app.js
  src/AppManager.js`, que não retorna nada. Nenhuma dependência declarada e não importada: as duas
  do manifesto (`express`, `sqlite3`) são efetivamente usadas. Não há diretório de camada
  inalcançável — não há camada.
- **Impacto (leitura de alto valor do sinal):** as três chaves mortas correspondem exatamente a
  lacunas de arquitetura pretendida e não implementada — `dbUser`/`dbPass` apontam para um banco
  externo que o projeto nunca conecta (usa `:memory:`, F-007), e `smtpUser` aponta para envio de
  e-mail que não existe. E o mais caro: **são segredos versionados dentro de código morto**
  (cruza com F-001). Registrado aqui, antes de qualquer proposta de remoção, conforme
  `mvc-guidelines.md` §6 — apagar as linhas não remove os valores do histórico do repositório, e é
  o histórico que precisa ser rotacionado.
- **Correção esperada:** remoção dos símbolos mortos; as chaves sensíveis saem do código junto com
  TR-01 e entram na lista de rotação de segredos.
- **Confiança:** ALTA

---

### [LOW] F-019 — `console.log` como único mecanismo de registro, sem nível, timestamp ou destino

- **Anti-pattern:** AP-19 · **Transformação:** TR-14 · **Onda:** 1 (de carona com F-005)
- **Arquivo:** `src/app.js:13`, `src/AppManager.js:45`, `src/utils.js:13`
- **Evidência:**

```javascript
console.log(`[LOG] Salvando no cache: ${key}`);        // src/utils.js:13
```

- **Descrição:** três ocorrências de saída direta para stdout usadas como registro de evento, sem
  severidade, sem timestamp e sem destino configurável: `src/app.js:13` (boot),
  `src/AppManager.js:45` (caminho de requisição — é também F-005), `src/utils.js:13` (caminho de
  requisição, com um prefixo `[LOG]` escrito à mão que imita um nível sem ser um). Nenhum arquivo
  do projeto importa biblioteca de logging, e o manifesto não declara nenhuma. Não é o caso de
  isenção: não é ferramenta de linha de comando nem script de uso único — as duas últimas
  ocorrências estão no caminho de requisição de um servidor. **Reforço confirmado:** todos os
  caminhos de erro respondem ao cliente e descartam o erro sem registrá-lo em lugar nenhum
  (F-012), tornando o defeito invisível em produção.
- **Impacto:** não é possível filtrar por severidade, correlacionar uma requisição nem direcionar
  o log para outro destino sem editar o código. Sem efeito observável no contrato da API.
- **Correção esperada:** logger com níveis e saída estruturada, injetado onde é usado.
- **Confiança:** ALTA
- **Nota de onda:** TR-14 é antecipado para a Onda 1 pela severidade de F-005 (AP-07, CRITICAL) e
  fecha este finding de carona.

---

### [LOW] F-020 — Ausência completa de infraestrutura de qualidade

- **Anti-pattern:** AP-28 · **Transformação:** nenhuma — reportado, não corrigido
- **Arquivo:** `package.json:1-13`
- **Evidência:**

```json
{
  "name": "desafio-arquitetura-ia-boilerplate",
  "version": "1.0.0",
  "description": "Boilerplate com código legado para refatoração",
  "main": "src/app.js",
  "scripts": {
    "start": "node src/app.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "sqlite3": "^5.1.6"
  }
}
```

- **Descrição:** o manifesto não declara `devDependencies`, não declara `engines` (nenhuma versão
  de runtime), e o único script é o de execução — não há script de teste nem de lint. A listagem
  do diretório confirma a ausência de arquivo de teste, configuração de lint, `.env.example`,
  `Dockerfile` e pipeline de CI. **Verificação um nível acima executada** (`mvc-guidelines`:
  monorepo com configuração na raiz): a raiz do repositório também não tem nenhum desses
  artefatos, então a isenção não se aplica. Faixas de versão abertas convivem com lockfile, e a
  divergência já é observável: declarado `express ^4.18.2` / `sqlite3 ^5.1.6`, instalado
  **4.22.1** / **5.1.7**.
- **Impacto:** não existe rede de segurança automatizada para a refatoração — a Fase 3 valida por
  boot e smoke test contra o baseline, que é o substituto pontual de uma suíte, não um
  equivalente. `npm install` reporta 13 vulnerabilidades (1 crítica, 7 altas) no lockfile
  congelado, e nada no projeto as observa.
- **Correção esperada:** fora do escopo desta skill. Faltariam: test runner com pelo menos um
  teste por endpoint, linter com regra de erro não tratado, `engines` fixando a major do Node,
  `.env.example` e CI executando os dois. **Coberturas parciais que o plano produz como
  consequência:** TR-01 publica o `.env.example`.
- **Confiança:** ALTA

---

## O que não foi encontrado

- **Injection por concatenação (AP-01) — não encontrado:** as 20 chamadas ao driver foram
  inspecionadas uma a uma. **Todas** as consultas com valor externo usam placeholder `?` com array
  de valores (`src/AppManager.js:37, 40, 50, 54, 57, 69, 92, 104, 106, 133`); as demais são DDL e
  seed com literais do próprio código. O único template literal presente em uma chamada
  (`` `Checkout curso ${cid} por ${userId}` `` em `:57`) está no **array de valores**, não na
  string da consulta — é um parâmetro vinculado, e o próprio AP exclui esse caso.
- **Credencial ou PII na serialização (AP-03) — não encontrado:** a única projeção
  registro→resposta do projeto (`src/AppManager.js:112-115`) é feita campo a campo e **exclui**
  tanto `pass` quanto `email`; não há espalhamento de registro (`{...row}`, `toJSON()`) em ponto
  algum. `src/AppManager.js:104` faz `SELECT name, email` e usa apenas `name` — é over-fetch, não
  exposição. A exposição de dado de terceiro nessa rota existe e está reportada em **F-002**
  (AP-05), que é o AP preciso: o defeito é a ausência de controle de acesso, não a projeção.
- **Validação de domínio inline (AP-12) — não encontrado:** a única verificação anterior à lógica
  (`src/AppManager.js:35`, `if (!u || !e || !cid || !cc)`) é de **protocolo** — campo obrigatório
  ausente no corpo —, que o próprio AP exclui explicitamente. Não há invariante de domínio (faixa
  numérica, tamanho, formato, vocabulário fechado) verificada inline em handler algum. A ausência
  total de invariantes, no handler **e** no schema, está reportada em F-007 como sinal estrutural
  de AP-21.
- **Mass assignment (AP-14) — não encontrado:** os caminhos de escrita leem campo a campo
  (`src/AppManager.js:29-33`) e vinculam colunas nominalmente (`:50`, `:54`, `:57`, `:69`).
  `grep -nE 'Object\.assign|\.\.\.req\.body'` não retorna nenhuma linha — o payload nunca é
  repassado inteiro.
- **Deprecated API (AP-16) — não encontrado:** verificado contra o runtime **Node.js v24.12.0**
  do ambiente, obtido executando `node --version`, não lido do manifesto (que aliás não declara
  `engines`). Procedimento: a aplicação foi executada com
  `node --pending-deprecation --trace-deprecation src/app.js` e os **três** endpoints exercitados;
  nenhuma linha contendo `deprecat` foi emitida, em nenhum caminho, incluindo os pacotes
  transitivos. Em complemento, `grep` por APIs sabidamente depreciadas (`new Buffer(`,
  `util.isArray`, `util._extend`, `url.parse(`, `crypto.createCipher(`, `process.binding`,
  `require.extensions`) não retorna nenhuma ocorrência. `Buffer.from` em `src/utils.js:20` é a
  API moderna, não a construtora depreciada.
- **Duplicação com abstração morta (AP-17) — não encontrado:** o AP exige as **duas** condições
  simultaneamente, e a segunda falha. O bloco de retorno de erro se repete cinco vezes
  (`:41, :51, :55, :70, :84`), acima do limiar de três — mas **não existe no repositório a
  abstração correta que ninguém invoca**: não há tratador de erro, helper de resposta nem
  diretório de camada morto. Essas cinco cópias são reportadas em F-012 (AP-18) e F-013 (AP-23),
  que são os APs cuja causa elas são. Os símbolos mortos do projeto (`totalRevenue`,
  `globalCache`) são valores, não implementações corretas não invocadas: estão em F-018 (AP-26).
- **Política de origem cruzada permissiva (AP-20) — não encontrado:** o sinal exige um middleware
  de origem cruzada **presente** com configuração permissiva. `grep -rn "cors\|Access-Control"`
  sobre `src/` e `package.json` não retorna nenhuma linha, e `src/app.js:6` registra um único
  middleware (`express.json()`). Não há política permissiva porque não há política.
- **Rate limiting em autenticação (AP-24) — não aplicável:** o escopo do AP é "APIs com
  autenticação", e o fato da Fase 1 que o exclui é o inventário de endpoints — as três rotas
  mapeadas não incluem nenhuma de autenticação, e `grep -rniE "login|signin|auth|token|session|
  jwt|passport"` sobre `src/` e `package.json` não retorna nada. Como **não existe finding de
  AP-24, ele não agenda TR algum**: o limite de taxa entra como parte de TR-05, na onda do finding
  que de fato aciona esse TR — aqui, F-002 (AP-05, CRITICAL, Onda 1). Registro do sinal correlato,
  conforme o AP pede: hoje a força bruta é desnecessária porque não há o que forçar; quando TR-05
  introduzir autenticação, ela passa a ser o caminho mais barato, e é por isso que o limite entra
  junto e não depois.

Os 28 APs do catálogo estão cobertos: 20 em findings, 7 como *não encontrado* e 1 como *não
aplicável*. Nenhum ficou *não verificável*.

## Breaking changes propostas

| # | Endpoint | Mudança | Motivo | TR |
|---|---|---|---|---|
| BC-1 | `GET /api/admin/financial-report` | Passa a responder **401** sem credencial (hoje 200 anônimo) | Rota administrativa expõe dados de terceiros sem verificação de identidade (F-002) | TR-05 |
| BC-2 | `DELETE /api/users/:id` | Passa a responder **401** sem credencial (hoje 200 anônimo) | Rota destrutiva sem verificação de identidade (F-002) | TR-05 |
| BC-3 | `POST /api/checkout` | O corpo de erro `400` deixa de ser `text/html` com o texto `Pagamento recusado` e passa a `application/json` no envelope `{"error":{"code","message"}}`. Status `400` preservado. | Contrato de erro divergente do de sucesso no mesmo handler (F-013) | TR-13 |
| BC-4 | `POST /api/checkout` | Mesma uniformização para os demais erros: `400 Bad Request`, `404 Curso não encontrado`, `500 Erro DB`, `500 Erro Matrícula`, `500 Erro Pagamento`, `500 Erro ao criar usuário`. Adicionalmente, falha de driver deixa de ser reportada como `404` e passa a `500` (hoje `:38` colapsa os dois). | Envelope inconsistente (F-013) e colapso de infraestrutura em 404 (F-012) | TR-13 |
| BC-5 | `GET /api/admin/financial-report` | Corpo de erro `500 Erro DB` passa a `application/json` no mesmo envelope | Envelope inconsistente (F-013) | TR-13 |
| BC-6 | `GET /api/admin/financial-report` | Resposta deixa de ser array puro e passa a envelope paginado `{"items":[...],"total","limit","offset"}`, com limite default de 50 e **ordenação explícita** por título de curso | Tamanho da resposta deixa de ser função dos dados (F-015); ordem deixa de ser não-determinística (F-014) | TR-17, TR-11 |
| BC-7 | `DELETE /api/users/:id` | Corpo de sucesso deixa de ser o texto `Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.` e passa a `application/json`. O texto some porque deixa de ser verdadeiro: com integridade referencial declarada, dependentes não ficam órfãos. Status `200` preservado. | Envelope inconsistente (F-013) e integridade referencial (F-007, F-010) | TR-13, TR-16 |
| BC-8 | `POST /api/checkout` | Passa a **aceitar também** `name`/`email`/`password`/`courseId`, mantendo `usr`/`eml`/`pwd`/`c_id` aceitos por compatibilidade (ND-6) | Vocabulário do contrato público divergente do domínio (F-016) | TR-18 |
| **BC-9** | `DELETE /api/users/:id` | **Passa a responder `409` quando o usuário tem matrícula** (hoje `200`). O usuário `1` do seed tem matrícula (`enrollments(1,1)`, `src/AppManager.js:20`), logo `DELETE /api/users/1` — a requisição do baseline — muda de `200` para `409`. | Decisão **ND-5**: `ON DELETE RESTRICT`. Registro de pagamento é dado contábil e não pode ser destruído em cascata por uma chamada de remoção (F-007, F-010) | TR-16, TR-10 |

**Total: 9 breaking changes.** Nenhuma altera path, verbo ou status code de **sucesso** — BC-9
altera o status de um cenário de **erro** recém-criado pela constraint, e está declarada aqui
exatamente para que o smoke test tenha contra o que comparar.

Efeito previsto sobre o smoke test, para que o gate seja uma decisão informada: das 4 requisições
do baseline, **as 4 divergirão** de forma declarada. Por onda:

| Requisição do baseline | Baseline | Após Onda 1 | Após Onda 2 | Após Onda 3 | Após Onda 4 | BC |
|---|---|---|---|---|---|---|
| `POST /api/checkout` (sucesso) | `200` JSON | `200` JSON | `200` JSON | `200` JSON | `200` JSON | — (BC-8 é aditiva) |
| `POST /api/checkout` (recusado) | `400` `text/html` | `400` `text/html` | `400` `text/html` | **`400` JSON** | `400` JSON | BC-3 |
| `GET /api/admin/financial-report` | `200` JSON, sem credencial | **`401` sem credencial / `200` com** | idem | **`200` envelope paginado** | idem | BC-1, BC-5, BC-6 |
| `DELETE /api/users/1` | `200` `text/html` | **`401` sem credencial / `200` com** | **`409`** (tem matrícula) | `409` JSON | idem | BC-2, **BC-9**, BC-7 |

As divergências acima são conformes por serem declaradas (`validation-protocol.md` §4.1);
qualquer outra é vermelha. A partir da Onda 1 o roteiro de smoke test autentica antes de chamar
as duas rotas privilegiadas (`validation-protocol.md` §8, falso vermelho conhecido de TR-05).

## Plano de refatoração

### Onda 1 — CRITICAL

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-01 | F-001 | `src/config/index.js`, `.env.example` | `src/app.js` | — |
| TR-06 | F-004, F-006 | `src/models/`, `src/repositories/`, `src/services/`, `src/controllers/`, `src/routes/`, `src/middlewares/` | `src/app.js` | `src/AppManager.js` |
| TR-03 | F-003 | `src/services/password.service.js` | `src/services/checkout.service.js` | — |
| TR-05 | F-002 (+ AP-24 por composição) | `src/middlewares/auth.js`, `src/middlewares/rateLimit.js` | `src/routes/` | — |
| TR-14 | F-005, F-019 | `src/lib/logger.js` | `src/app.js`, `src/services/`, `src/utils.js` | — |

Aceite: `smoke test 4/4 endpoints conformes ao baseline` (BC-1, BC-2 já aplicadas) → commit.

### Onda 2 — HIGH

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-07 | F-008 | — | `src/services/`, `src/controllers/` | — |
| TR-09 | F-009, F-011 | `src/lib/cache.js` | `src/app.js`, `src/repositories/`, `src/services/`, `src/utils.js` | — |
| TR-10 | F-010 | — | `src/repositories/`, `src/services/checkout.service.js` | — |
| TR-16 | F-007 | `src/db/migrations/`, `src/db/seed.js` | `src/app.js`, `src/repositories/` | — |

Aceite: `smoke test 4/4 endpoints conformes ao baseline` → commit.

### Onda 3 — MEDIUM

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-11 | F-014 | — | `src/repositories/report.repository.js` | — |
| TR-13 | F-012, F-013 | `src/middlewares/errorHandler.js`, `src/errors/` | `src/app.js`, `src/controllers/`, `src/services/` | — |
| TR-17 | F-015 | — | `src/controllers/report.controller.js`, `src/repositories/report.repository.js` | — |

Aceite: `smoke test 4/4 endpoints conformes ao baseline` (BC-3 a BC-7 aplicadas) → commit.

### Onda 4 — LOW

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-15 | F-018 | — | `src/utils.js` (ou sua remoção, se esvaziar) | — |
| TR-18 | F-016, F-017 | `src/models/payment.status.js` | `src/controllers/checkout.controller.js`, `src/services/` | — |

Aceite: `smoke test 4/4 endpoints conformes ao baseline` (BC-8 aplicada) → commit.

**Ondas vazias: nenhuma.** As quatro receberam TR.

**TRs do playbook não agendados**, por não haver finding que os acione: TR-02 (AP-01 não
encontrado), TR-04 (AP-03 não encontrado), TR-08 (AP-12 e AP-14 não encontrados), TR-12 (AP-16 não
encontrado).

### Itens NEEDS-DECISION — **todos decididos pelo humano em 2026-08-17**

| # | Decisão | Escolha registrada | Consequência no plano |
|---|---|---|---|
| ND-1 | `POST /api/checkout` exige autenticação? | **Não — permanece público**, com limite de taxa via TR-05 | Nenhuma BC. O cadastro implícito no checkout é preservado |
| ND-2 | Mecanismo de autenticação das rotas privilegiadas | **Token administrativo lido do ambiente**, comparado em tempo constante | TR-05 sem dependência nova; o token entra na camada `config` de TR-01 e no `.env.example` |
| ND-3 | Derivação de senha | **`scrypt` do `node:crypto`**, salt de 16 bytes por registro | TR-03 sem dependência nova; o manifesto continua com 2 dependências |
| ND-4 | Destino do seed ao sair do boot | **Guarda de ambiente de desenvolvimento**, com a senha do seed derivada em vez de `'123'` | TR-16 preserva os dados que o baseline compara; sem isso o critério 5 do smoke test ficaria sem referente |
| ND-5 | `DELETE /api/users/:id` sob integridade referencial | **`ON DELETE RESTRICT` + `409`** quando houver matrícula | **Gera BC-9.** Registro de pagamento é dado contábil; `CASCADE` deixaria uma requisição anônima destruir histórico financeiro, e a anonimização mudaria a semântica do verbo — decisão de produto, recusada pelo mesmo critério de ND-1 |
| ND-6 | Renomear campos do payload (BC-8) | **Renomear com compatibilidade** — nomes novos e antigos aceitos | BC-8 vira adição, não ruptura; a requisição exata do baseline continua exercitável até a Onda 4 |

> **ND-5 gerou BC-9**, listada na seção Breaking changes acima. Conforme o protocolo do gate
> (`SKILL.md`, "Resposta parcial → replaneje e reapresente o gate"), este plano revisado é um
> **gate novo** e foi reapresentado ao humano antes de qualquer escrita em arquivo do projeto.

## Fora do escopo desta skill

- **Infraestrutura de qualidade (F-020).** Test runner, linter, `engines` e CI são reportados e
  **não** entram no plano acima. `.env.example` sai como consequência de TR-01, não como escopo.
- **13 vulnerabilidades do lockfile** reportadas por `npm install` (1 crítica, 7 altas). Atualizar
  dependências alteraria o baseline e é troca de versão de stack, fora do escopo declarado.
- **Rotação dos segredos de F-001 e F-018.** Remover as linhas não remove os valores do histórico
  do Git; a rotação da chave `pk_live_...` e da senha de banco é ação operacional fora do
  repositório.
- **Troca de `:memory:` por banco persistente.** É troca de mecanismo de persistência. TR-16 torna
  o destino configurável (TR-01) e cria o caminho de migração; escolher e provisionar o banco não.
- **Política de retenção dos dados pessoais** expostos hoje pelo relatório financeiro.

## Próximo passo

Total: **20 findings** (5 CRITICAL · 6 HIGH · 4 MEDIUM · 5 LOW) ·
**9 breaking changes** propostas (BC-9 acrescentada por ND-5) · plano em **4 ondas com TR**
(vazias: nenhuma) · **6 itens NEEDS-DECISION resolvidos**.

Nenhum arquivo do projeto foi modificado até aqui.

    Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
