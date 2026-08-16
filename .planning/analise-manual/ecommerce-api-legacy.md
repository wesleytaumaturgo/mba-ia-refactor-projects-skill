# Dossiê de Análise Manual — `ecommerce-api-legacy`

> Auditoria cética, somente leitura. Toda referência de arquivo:linha foi obtida por leitura direta
> dos arquivos nesta sessão e reconferida com `sed -n` contra o intervalo citado. Findings sem
> evidência literal foram descartados.
>
> **Numeração:** o dossiê anterior (`code-smells-project.md`) encerrou em **AM-027**. Esta série
> inicia em **AM-028** e termina em **AM-049**. O próximo dossiê deve continuar em **AM-050**.

---

## Contexto do projeto

| Item | Valor |
|---|---|
| **Linguagem** | JavaScript (CommonJS) — nenhuma versão de runtime declarada no projeto (não há campo `engines` em `package.json`, nem `.nvmrc`, nem `Dockerfile`); interpretador do ambiente: Node v24.12.0 |
| **Framework** | Express — declarado `^4.18.2` (`package.json:10`), resolvido para `4.22.1` no `package-lock.json` |
| **Dependências** | Apenas duas: `express ^4.18.2` e `sqlite3 ^5.1.6` (resolvido para `5.1.7`). Sem dependência de validação de schema, de hashing, de logging, de teste ou de lint. `node_modules/` não está instalado no diretório. |
| **Domínio de negócio** | LMS/e-commerce de cursos online: catálogo de cursos, cadastro implícito de aluno durante o checkout, processamento de pagamento por cartão, matrícula, trilha de auditoria e relatório financeiro administrativo. |
| **Nº de arquivos-fonte** | 3 arquivos `.js` em `src/` (`app.js`, `AppManager.js`, `utils.js`). Acompanham `package.json`, `package-lock.json`, `README.md` e `api.http`. |
| **LOC** | 180 linhas JavaScript totais (140 não-vazias): `app.js` 14 / `AppManager.js` 141 / `utils.js` 25 |
| **Tabelas do banco** | 5 — `users`, `courses`, `enrollments`, `payments`, `audit_logs` (DDL em `AppManager.js:12-16`). Banco SQLite **em memória** (`:memory:`, `AppManager.js:7`), sem chaves estrangeiras. |

### Arquitetura atual

Não há arquitetura em camadas: o projeto tem um bootstrap (`app.js`) e uma única classe que é a
aplicação inteira. `app.js` cria o servidor Express, instancia `AppManager` sem argumentos, chama
`initDb()` e `setupRoutes(app)`, e sobe o listener — é apenas um composition root de seis linhas que
não compõe nada, porque a classe resolve todas as próprias dependências internamente. `AppManager`
acumula, num só arquivo de 141 linhas, a abertura da conexão SQLite, o DDL das cinco tabelas, a carga
de seed, o registro das três rotas HTTP, o parsing dos payloads, a autorização de pagamento, a
persistência de matrícula/pagamento/auditoria e a agregação do relatório financeiro — sem controller,
sem service, sem repository, sem model e sem middleware próprio. `utils.js` é um módulo-gaveta que
mistura um objeto de configuração com segredos literais, duas variáveis globais mutáveis de módulo e
uma função de derivação de senha caseira. Todo o fluxo assíncrono é escrito em callbacks aninhados do
driver, com a coordenação de paralelismo feita à mão por contadores decrementados. Não existem testes,
lint, migrações, tratamento centralizado de erro, autenticação, autorização nem logging estruturado.

### Observação de disciplina de auditoria — o que NÃO foi encontrado

Diferente do dossiê anterior, **este projeto não tem SQL Injection**. Todas as consultas do runtime
usam placeholders `?` com bind de parâmetros (`AppManager.js:37`, `40`, `50`, `54`, `57`, `69`, `83`,
`92`, `104`, `106`, `133`). O único template literal presente numa chamada de query
(`AppManager.js:57`) está no *array de parâmetros vinculados*, não concatenado à string SQL — o que
foi confirmado por `grep` sobre todas as chamadas `db.run/get/all` procurando concatenação ou
interpolação dentro da string de query, com zero ocorrências. As únicas queries montadas com valores
embutidos são os `INSERT` de seed (`AppManager.js:18-21`), cujos dados são literais fixos do próprio
código e não entrada externa. Nenhum finding de injeção foi registrado, apesar de a categoria estar
explicitamente na escala de severidade do desafio.

---

## Findings

### [CRITICAL] AM-028 — Credenciais de produção e chave de gateway de pagamento hardcoded

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

- **Descrição:** Senha de banco, chave de gateway de pagamento e usuário de SMTP são literais
  versionados no código-fonte, sem nenhuma leitura de variável de ambiente em nenhum dos três arquivos
  do projeto. O prefixo `pk_live_` identifica explicitamente uma chave de ambiente de **produção**, e
  o próprio nome `dbPass: "senha_super_secreta_prod_123"` declara a intenção.
- **Impacto:** Qualquer pessoa com acesso de leitura ao repositório — incluindo todo o histórico do
  Git, forks e artefatos de build — obtém as credenciais, que não podem ser rotacionadas sem um novo
  deploy. Agrava o quadro o fato de `dbUser`, `dbPass` e `smtpUser` não serem referenciados em lugar
  algum do código (o banco real é `:memory:` em `AppManager.js:7`): são segredos expostos sem sequer
  entregar função, o pior custo-benefício possível.
- **Correção esperada:** Toda configuração sensível deve vir de variáveis de ambiente carregadas por
  um módulo de configuração dedicado, com o objeto literal removido do controle de versão.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-029 — God Class: uma única classe concentra conexão, schema, roteamento e regra de negócio

- **Arquivo:** `src/AppManager.js:4-11`
- **Evidência:**

```javascript
class AppManager {
    constructor() {

        this.db = new sqlite3.Database(':memory:');
    }

    initDb() {
        this.db.serialize(() => {
```

- **Descrição:** `AppManager` é dono da conexão de banco (`constructor`), do DDL e do seed
  (`initDb`, linhas 10-23) e das três rotas HTTP com toda a sua lógica (`setupRoutes`, linhas 25-138)
  — as 141 linhas do arquivo são um único objeto responsável por infraestrutura, apresentação,
  domínio e persistência. O próprio nome, um substantivo genérico terminado em "Manager", não
  descreve nenhuma responsabilidade delimitada.
- **Impacto:** Não existe fronteira onde inserir um controller, um service ou um repository: qualquer
  mudança de regra de negócio, de contrato HTTP ou de banco toca o mesmo arquivo, e nenhuma dessas
  camadas pode ser testada sem instanciar todas as outras. É exatamente o cenário de God Class que a
  escala de severidade do desafio nomeia — DB + regra de negócio + roteamento no mesmo lugar.
- **Correção esperada:** Decompor em `routes` → `controllers` → `services` (domínio) →
  `repositories` (persistência), com a conexão e o schema saindo para a camada de infraestrutura.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-030 — Número de cartão e chave do gateway emitidos em log

- **Arquivo:** `src/AppManager.js:43-45`
- **Evidência:**

```javascript
                    let processPaymentAndEnroll = (userId) => {

                        console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

- **Descrição:** A cada checkout, o número completo do cartão recebido em `req.body.card` e a chave
  de produção do gateway de pagamento são escritos em texto puro no stdout do processo. Não há
  mascaramento, truncamento nem qualquer filtro de dado sensível.
- **Impacto:** Dados de portador de cartão passam a existir fora do escopo da transação — em arquivos
  de log, em coletores centralizados e em ferramentas de observabilidade de terceiros — o que é uma
  violação direta de PCI-DSS e transforma o log num alvo de valor equivalente ao do banco de dados.
  Como a chave `pk_live_` é impressa junto, um único vazamento de log entrega ao mesmo tempo o meio de
  pagamento e a credencial para usá-lo.
- **Correção esperada:** Dado de cartão nunca deve ser logado nem trafegar pela aplicação; a
  integração pertence a um gateway/adapter que recebe um token de pagamento, com logging estruturado
  e redação de campos sensíveis.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-031 — Função de derivação de senha criptograficamente inútil

- **Arquivo:** `src/utils.js:17-23`
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

- **Descrição:** A função não é um hash: ela concatena 10.000 vezes os **mesmos** dois primeiros
  caracteres do Base64 da senha e devolve os 10 primeiros caracteres do resultado — ou seja, esses
  dois caracteres repetidos cinco vezes. Não há salt, não há função criptográfica, o resultado é
  determinístico e depende apenas dos ~12 primeiros bits da senha, limitando todo o espaço de saída a
  no máximo 4.096 valores distintos.
- **Impacto:** Verificado por execução nesta sessão: `"123456"` e `"123"` produzem ambos
  `MTMTMTMTMT`, e `"senhaforte"` e `"senhafraca"` produzem ambos `c2c2c2c2c2` — qualquer senha que
  compartilhe o começo com outra colide, então uma senha arbitrária autentica a conta de outro
  usuário. A saída é ainda trivialmente reversível por Base64, e o seed em `AppManager.js:18` grava a
  senha `'123'` sem passar sequer por essa função, em texto puro. Como bônus negativo, o laço executa
  10.000 concatenações e alocações de `Buffer` no caminho síncrono do checkout para produzir 10
  caracteres, desperdiçando CPU no request path.
- **Correção esperada:** Substituir por uma função de derivação de chave padrão e com salt
  (bcrypt/argon2/scrypt), isolada num serviço de autenticação.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-032 — Regra de autorização de pagamento embutida no handler de rota

- **Arquivo:** `src/AppManager.js:46-48`
- **Evidência:**

```javascript
                        let status = cc.startsWith("4") ? "PAID" : "DENIED";

                        if (status === "DENIED") return res.status(400).send("Pagamento recusado");
```

- **Descrição:** A decisão de aprovar ou recusar um pagamento — a regra de negócio mais crítica do
  domínio — é um ternário sobre o primeiro caractere do número do cartão, escrito dentro do callback
  da rota Express. Não há chamada a gateway, não há validação de cartão e o literal `"4"` (prefixo de
  bandeira) aparece sem nome nem explicação.
- **Impacto:** A política de pagamento não é reutilizável, não é testável sem subir o servidor HTTP e
  não pode ser trocada por uma integração real sem reescrever o handler. Como toda a autorização se
  resume ao primeiro dígito, qualquer número começando com `4` é aprovado, e a matrícula e o registro
  de pagamento são gravados como `PAID` sem que dinheiro algum tenha sido movimentado.
- **Correção esperada:** Mover a autorização para um serviço de domínio de pagamento com um adapter
  de gateway injetado, deixando o handler apenas traduzir request e resposta.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-033 — Acoplamento forte às dependências concretas, sem injeção

- **Arquivo:** `src/app.js:5-10`
- **Evidência:**

```javascript
const app = express();
app.use(express.json());

const manager = new AppManager();
manager.initDb();
manager.setupRoutes(app);
```

- **Descrição:** O composition root instancia `AppManager` sem passar nenhuma dependência, porque a
  classe resolve tudo internamente: abre a própria conexão com `new sqlite3.Database(':memory:')`
  (`AppManager.js:7`) e importa configuração, cache e função de hash por `require` concreto
  (`AppManager.js:2`). Os parâmetros de infraestrutura estão fixados em código — o driver é carregado
  em modo `verbose()` incondicionalmente (`AppManager.js:1`), o banco é sempre `:memory:` e a porta é
  o literal de `utils.js:6`.
- **Impacto:** Nenhuma unidade é testável em isolamento: exercitar uma rota obriga a subir o Express e
  um SQLite real, e não há como injetar um duplo de teste para o gateway de pagamento ou para o
  repositório. Trocar SQLite por outro banco, ou apontar para um arquivo persistente em vez de
  memória, exige editar a classe de aplicação em vez de mudar configuração — e hoje todo dado é
  perdido a cada restart, inclusive matrículas e pagamentos "confirmados".
- **Correção esperada:** Inverter a dependência — a conexão, o logger e o gateway entram por
  construtor a partir do composition root, com a seleção da implementação vinda de configuração.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-034 — Estado global mutável exportado por módulo

- **Arquivo:** `src/utils.js:9-15`
- **Evidência:**

```javascript
let globalCache = {};
let totalRevenue = 0;

function logAndCache(key, data) {
    console.log(`[LOG] Salvando no cache: ${key}`);
    globalCache[key] = data;
}
```

- **Descrição:** Duas variáveis mutáveis vivem no escopo do módulo e são exportadas
  (`utils.js:25`). `globalCache` é escrito a cada checkout via `logAndCache`
  (`AppManager.js:59`) e cresce sem limite, sem TTL, sem invalidação e sem que nenhum ponto do
  projeto jamais o leia de volta — é um vazamento de memória que acumula títulos de curso indexados
  por usuário enquanto o processo viver.
- **Impacto:** Estado compartilhado fora de qualquer fronteira de módulo torna o comportamento
  dependente da ordem das requisições e impede paralelizar testes, já que cada teste contamina o
  próximo. `totalRevenue` expõe um segundo problema, estrutural: por ser um primitivo exportado em
  CommonJS, ele é copiado por valor no `require`, de modo que nenhuma reatribuição dentro de
  `utils.js` jamais seria vista pelos consumidores — um "acumulador global" que não pode funcionar
  nem se alguém tentasse usá-lo.
- **Correção esperada:** Eliminar o estado de módulo; cache deve ser um serviço com ciclo de vida
  explícito e injetado, e agregados de negócio devem ser derivados de consulta, não de contador em
  memória.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-035 — Rotas administrativa e destrutiva sem autenticação ou autorização

- **Arquivo:** `src/AppManager.js:80-84`
- **Evidência:**

```javascript
        app.get('/api/admin/financial-report', (req, res) => {
            let report = [];

            this.db.all("SELECT * FROM courses", [], (err, courses) => {
                if (err) return res.status(500).send("Erro DB");
```

- **Descrição:** O handler vai direto do registro da rota para a consulta ao banco, sem middleware de
  autenticação, sem verificação de identidade e sem checagem de papel — o segmento `admin` no path é
  puramente decorativo. O mesmo vale para `DELETE /api/users/:id` (`AppManager.js:131`), e o projeto
  inteiro não possui nenhuma rota de login, emissão de token ou verificação de sessão.
- **Impacto:** Um `GET` anônimo devolve o faturamento consolidado por curso e a lista nominal de todos
  os alunos com os valores que cada um pagou (`AppManager.js:112-115`) — exposição simultânea de dado
  financeiro do negócio e de PII dos clientes. Um `DELETE` anônimo remove qualquer usuário pelo id, o
  que torna a base destrutível por qualquer chamador que consiga alcançar a porta.
- **Correção esperada:** Introduzir middleware de autenticação e autorização por papel aplicado antes
  dos handlers, com as rotas administrativas exigindo verificação explícita de privilégio.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-036 — Escrita multi-etapa de checkout sem transação nem rollback

- **Arquivo:** `src/AppManager.js:50-57`
- **Evidência:**

```javascript
                        this.db.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, cid], function(err) {
                            if (err) return res.status(500).send("Erro Matrícula");
                            let enrId = this.lastID;

                            self.db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrId, course.price, status], function(err) {
                                if (err) return res.status(500).send("Erro Pagamento");

                                self.db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [`Checkout curso ${cid} por ${userId}`], (err) => {
```

- **Descrição:** O checkout grava usuário (linha 69), matrícula, pagamento e log de auditoria em
  quatro `INSERT` independentes e aninhados, sem `BEGIN`/`COMMIT` e sem nenhum caminho de compensação.
  Cada `if (err) return res.status(500)` aborta a sequência deixando intacto tudo o que já foi
  gravado.
- **Impacto:** Uma falha no `INSERT` de pagamento deixa a matrícula persistida sem pagamento
  correspondente — o aluno fica matriculado de graça e o relatório financeiro o contabiliza com
  `paid: 0` (`AppManager.js:114`). Uma falha na criação da matrícula, por sua vez, deixa o usuário
  já criado, e o log de auditoria (linha 57) só é escrito no caminho feliz, de modo que exatamente as
  execuções que falham são as que não deixam rastro.
- **Correção esperada:** Encapsular a operação num único limite transacional na camada de
  repositório/unit-of-work, com rollback garantido em qualquer falha intermediária.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-037 — Coordenação manual de concorrência por contador, com erros ignorados e requisições que nunca respondem

- **Arquivo:** `src/AppManager.js:92-99`
- **Evidência:**

```javascript
                    this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
                        let enrPending = enrollments.length;
                        
                        if (enrPending === 0) {
                            report.push(courseData);
                            coursesPending--;
                            if (coursesPending === 0) res.json(report);
                            return;
```

- **Descrição:** O relatório dispara consultas em paralelo dentro de `forEach` e tenta descobrir
  quando terminou decrementando à mão dois contadores (`coursesPending`, `enrPending`), enviando a
  resposta no ponto em que ambos zeram. O parâmetro `err` é recebido na linha 92 e **nunca
  verificado** antes de `enrollments.length`, e o mesmo acontece nos callbacks das linhas 104 e 106.
- **Impacto:** Se a consulta falhar, `enrollments` vem `undefined` e a leitura de `.length` lança
  `TypeError` dentro de um callback assíncrono, derrubando o processo Node inteiro — não há
  `try/catch` nem handler de erro que o contenha. Se um erro impedir o decremento de qualquer
  contador, a condição `=== 0` nunca é satisfeita, `res.json` nunca é chamado e a requisição fica
  pendurada até o timeout do cliente, segurando a conexão. A ordem de `report.push` também depende de
  qual callback retorna primeiro, então a resposta não é determinística entre execuções.
- **Correção esperada:** Substituir a orquestração manual por composição assíncrona explícita
  (`Promise.all` sobre um driver promissificado) numa camada de serviço, com propagação de erro para
  um error handler centralizado.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-038 — Credencial default silenciosa para usuários criados no checkout

- **Arquivo:** `src/AppManager.js:66-69`
- **Evidência:**

```javascript
                    if (!user) {

                        let hash = badCrypto(p || "123456");
                        this.db.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [u, e, hash], function(err) {
```

- **Descrição:** A validação de entrada da rota (`AppManager.js:35`) exige `usr`, `eml`, `c_id` e
  `card`, mas deliberadamente **não** exige `pwd`. Quando a senha não vem no payload, o código atribui
  em silêncio a senha literal `"123456"` à conta recém-criada, sem informar o usuário e sem marcar a
  credencial para troca obrigatória.
- **Impacto:** Contas são criadas com uma senha universalmente conhecida, e o titular sequer sabe que
  possui uma conta — o cadastro é um efeito colateral implícito do checkout. Combinado com AM-031,
  onde todas as senhas que começam igual colidem, isso significa que qualquer conta criada sem senha é
  acessível por qualquer pessoa que tente `123456` ou qualquer string iniciada por `12`.
- **Correção esperada:** O caso de uso deve tratar criação de conta como fluxo explícito, exigindo
  senha válida ou emitindo um convite de definição de senha, nunca preenchendo credencial por default.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-039 — N+1 em cascata de três níveis no relatório financeiro

- **Arquivo:** `src/AppManager.js:102-107`
- **Evidência:**

```javascript
                        enrollments.forEach(enr => {

                            this.db.get("SELECT name, email FROM users WHERE id = ?", [enr.user_id], (err, user) => {
                                
                                this.db.get("SELECT amount, status FROM payments WHERE enrollment_id = ?", [enr.id], (err, payment) => {
                                    
```

- **Descrição:** O relatório faz uma consulta de cursos, depois uma consulta de matrículas por curso
  (linha 92) e, dentro dela, **duas** consultas por matrícula — uma de usuário e outra de pagamento —
  aninhadas uma na outra. O custo total é `1 + C + (C × E × 2)` idas ao banco, onde uma única consulta
  com `JOIN` entre as quatro tabelas resolveria tudo.
- **Impacto:** Com 20 cursos de 50 matrículas cada, são 2.021 queries para montar um relatório que
  caberia em uma. A agregação de receita (`courseData.revenue += payment.amount`, linha 109) também é
  feita em JavaScript, linha a linha, quando `SUM` com filtro por status faria o trabalho no banco.
- **Correção esperada:** Uma consulta agregada única na camada de repositório, com o mapeamento para
  o DTO de relatório feito sobre o resultado já consolidado.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-040 — Validação de entrada ausente e incompleta nas rotas

- **Arquivo:** `src/AppManager.js:29-35`
- **Evidência:**

```javascript
            let u = req.body.usr;
            let e = req.body.eml;
            let p = req.body.pwd;
            let cid = req.body.c_id;
            let cc = req.body.card;

            if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");
```

- **Descrição:** A única validação é um teste de presença por falsy sobre quatro dos cinco campos:
  não há verificação de tipo, de formato de e-mail, de formato de cartão nem de `c_id` ser numérico, e
  `pwd` fica de fora (ver AM-038). O teste por falsy também rejeita valores legítimos como `c_id: 0`,
  e `req.params.id` na rota de deleção (`AppManager.js:132`) é usado sem qualquer validação.
- **Impacto:** Um `card` não-string faz `cc.startsWith` lançar `TypeError` dentro de um callback,
  derrubando o processo, e um e-mail malformado cria um usuário permanente com identificador inválido
  — sem constraint `UNIQUE` na coluna (`AppManager.js:12`), dois cadastros com o mesmo e-mail
  coexistem e tornam o resultado da busca da linha 40 dependente da ordem das linhas. Erros de
  validação e defeitos internos ficam indistinguíveis para o cliente.
- **Correção esperada:** Validação declarativa de schema num middleware na borda da rota, antes de
  qualquer acesso ao handler.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-041 — Deleção que produz registros órfãos, com erro ignorado e sucesso sempre retornado

- **Arquivo:** `src/AppManager.js:131-136`
- **Evidência:**

```javascript
        app.delete('/api/users/:id', (req, res) => {
            let id = req.params.id;
            this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {

                res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
            });
```

- **Descrição:** O handler remove apenas a linha de `users` e não toca em `enrollments` nem em
  `payments`, deixando registros apontando para um usuário inexistente — o próprio texto da resposta
  admite o defeito. O parâmetro `err` é recebido e nunca verificado, e o schema não declara nenhuma
  `FOREIGN KEY` (`AppManager.js:12-16`) que pudesse impor `ON DELETE` no banco.
- **Impacto:** A base perde integridade referencial de forma permanente, e o relatório financeiro
  passa a listar esses registros como `student: 'Unknown'` (`AppManager.js:113`) enquanto continua
  somando a receita deles. Como o `err` é ignorado, a rota responde `200` com mensagem de sucesso
  mesmo quando a deleção falha, e responde `200` também quando o id não existe.
- **Correção esperada:** A remoção deve ser um caso de uso transacional que trate os agregados
  dependentes (ou anonimize em vez de deletar), com `FOREIGN KEY` declarada no schema e o resultado
  real da operação refletido no status HTTP.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-042 — Schema criado pela aplicação no boot, sem migrações e sem constraints

- **Arquivo:** `src/AppManager.js:12-16`
- **Evidência:**

```javascript
            this.db.run("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)");
            this.db.run("CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)");
            this.db.run("CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)");
            this.db.run("CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)");
            this.db.run("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)");
```

- **Descrição:** O DDL das cinco tabelas é executado pela classe de aplicação a cada boot, sem
  versionamento e sem ferramenta de migração. As definições não têm `NOT NULL`, `UNIQUE`, `DEFAULT`,
  `CHECK` nem `FOREIGN KEY`: `user_id`, `course_id` e `enrollment_id` são inteiros soltos sem relação
  declarada, e `status` é texto livre sem domínio restrito.
- **Impacto:** Nenhuma invariante é garantida pelo banco — toda a integridade depende de código de
  aplicação que, como mostram AM-036 e AM-041, não a garante. Sem histórico de migração, evoluir uma
  coluna existente é impossível por esse mecanismo, e o schema não pode ser reproduzido nem revisado
  fora do código da classe.
- **Correção esperada:** Extrair o schema para migrações versionadas na camada de infraestrutura, com
  constraints de integridade declaradas no próprio banco.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-043 — `console.log` como mecanismo de observabilidade

- **Arquivo:** `src/utils.js:12-15`
- **Evidência:**

```javascript
function logAndCache(key, data) {
    console.log(`[LOG] Salvando no cache: ${key}`);
    globalCache[key] = data;
}
```

- **Descrição:** Toda a observabilidade do projeto se resume a três `console.log` — este,
  `AppManager.js:45` e `app.js:13` — sem níveis de severidade, sem timestamp, sem correlação de
  requisição e sem destino configurável. A função também viola separação de responsabilidades já no
  nome: `logAndCache` faz duas coisas não relacionadas, e nenhum dos chamadores pode escolher só uma.
- **Impacto:** Não há como filtrar por severidade, silenciar ruído em produção ou direcionar erros a
  um agregador, e nenhum dos caminhos de falha do projeto registra qualquer coisa — os `if (err)`
  respondem ao cliente e descartam o erro sem deixar rastro para diagnóstico. Um dos três logs
  existentes, aliás, é justamente o que vaza dado de cartão (AM-030).
- **Correção esperada:** Adotar um logger estruturado injetado por dependência, com níveis e handlers
  definidos por ambiente, e separar cache de logging.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-044 — Contrato de resposta inconsistente entre handlers

- **Arquivo:** `src/AppManager.js:38-41`
- **Evidência:**

```javascript
                if (err || !course) return res.status(404).send("Curso não encontrado");

                this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
                    if (err) return res.status(500).send("Erro DB");
```

- **Descrição:** Erros são devolvidos como texto puro (`send`) enquanto sucessos são JSON
  (`res.json`, linhas 60 e 98), de modo que o cliente precisa inspecionar o status para saber como
  desserializar. As mensagens misturam idiomas — `"Bad Request"` (linha 35) convive com
  `"Curso não encontrado"` (linha 38) e `"Erro Matrícula"` (linha 51) — e não há código de erro
  estável, apenas prosa. A linha 38 ainda colapsa dois casos distintos, falha de banco e curso
  inexistente, num mesmo `404`.
- **Impacto:** Nenhum consumidor consegue tratar erros programaticamente sem casar strings, e a
  mudança de uma mensagem quebra clientes silenciosamente. Colapsar erro de infraestrutura em `404`
  esconde indisponibilidade real do banco como se fosse ausência de recurso, atrapalhando diagnóstico
  e monitoração.
- **Correção esperada:** Centralizar a montagem de respostas num error handler do Express, com
  envelope JSON único, código de erro estável e mapeamento explícito de exceção de domínio para status
  HTTP.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-045 — Import morto e primitivo exportado por valor que nunca propaga

- **Arquivo:** `src/AppManager.js:1-2`
- **Evidência:**

```javascript
const sqlite3 = require('sqlite3').verbose();
const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');
```

- **Descrição:** `totalRevenue` é desestruturado aqui e não aparece em nenhuma outra linha das 141 do
  arquivo — confirmado por `grep`, que encontra o nome apenas na declaração (`utils.js:10`), na
  exportação (`utils.js:25`) e neste import. `globalCache` também é exportado e nunca lido por
  ninguém. A mesma linha 1 carrega o driver em modo `verbose()` de forma incondicional, um flag de
  depuração ativo em qualquer ambiente.
- **Impacto:** O import sugere ao leitor que existe um acumulador de receita compartilhado no
  domínio, quando não existe — e, por ser um primitivo em CommonJS, ele nunca poderia funcionar como
  tal (ver AM-034). Código morto desse tipo desorienta quem for refatorar e é sintoma de que nenhum
  linter roda no projeto.
- **Correção esperada:** Remover o import e a exportação não utilizados, e mover o flag de verbosidade
  do driver para configuração por ambiente.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-046 — Nomenclatura críptica no código e no contrato público da API

- **Arquivo:** `src/AppManager.js:29-33`
- **Evidência:**

```javascript
            let u = req.body.usr;
            let e = req.body.eml;
            let p = req.body.pwd;
            let cid = req.body.c_id;
            let cc = req.body.card;
```

- **Descrição:** Cinco variáveis de uma ou três letras (`u`, `e`, `p`, `cid`, `cc`) recebem campos de
  payload igualmente abreviados e sem padrão de convenção — `usr`, `eml`, `pwd` e `card` sem
  separador, ao lado de `c_id` em snake_case. A variável `e`, em particular, guarda um e-mail no mesmo
  escopo em que `err` é o nome convencional de erro, e `cc` não indica que carrega dado de cartão.
- **Impacto:** A abreviação atravessa a fronteira do sistema e vira contrato público: todo consumidor
  da API precisa aprender um vocabulário que não corresponde a nenhum termo do domínio, e renomear
  depois quebra clientes. Internamente, nomes de uma letra num handler de 50 linhas com quatro níveis
  de aninhamento tornam a leitura dependente de rolagem constante até a declaração.
- **Correção esperada:** Nomes de domínio explícitos em um DTO de entrada validado, com o contrato da
  API expresso em campos legíveis e consistentes.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-047 — Dados de seed embutidos no código de aplicação

- **Arquivo:** `src/AppManager.js:18-21`
- **Evidência:**

```javascript
            this.db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
            this.db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
            this.db.run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)");
            this.db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
```

- **Descrição:** Dados de demonstração — um usuário nomeado com e-mail real, dois cursos com preços e
  uma matrícula paga — são inseridos incondicionalmente pela classe de aplicação a cada boot, dentro
  do mesmo método que cria o schema. As linhas 20 e 21 dependem de ids auto-incrementados presumidos
  (`1`, `1`) em vez de referenciar as chaves efetivamente geradas.
- **Impacto:** Não há como subir a aplicação sem os dados fictícios, o que impede qualquer uso que não
  seja demonstração e mistura fixture de teste com código de produção. A senha `'123'` do usuário de
  seed é gravada em texto puro, sem passar sequer pela função de hash do próprio projeto, e os ids
  presumidos quebram silenciosamente se a ordem dos inserts mudar.
- **Correção esperada:** Extrair o seed para um script separado, executado explicitamente apenas em
  ambiente de desenvolvimento.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-048 — Alias `self` convivendo com arrow functions no mesmo escopo

- **Arquivo:** `src/AppManager.js:25-26`
- **Evidência:**

```javascript
    setupRoutes(app) {
        const self = this;
```

- **Descrição:** O método captura `this` num alias `self` no topo, embora quase todos os callbacks
  sejam arrow functions que já preservam o `this` léxico. O alias só é necessário porque três
  callbacks do driver são declarados como `function(err)` (linhas 50, 54 e 69) para acessar
  `this.lastID`, o que rebinda `this` para o objeto de statement do sqlite3.
- **Impacto:** No mesmo bloco de 50 linhas, `this.db` (linha 50) e `self.db` (linhas 54 e 57)
  referem-se ao mesmo objeto por caminhos diferentes, e `this.lastID` (linhas 52 e 71) refere-se a
  outro objeto inteiramente — três significados de `this` sem nada que sinalize a troca. É uma
  armadilha silenciosa: converter qualquer um desses `function` em arrow function quebra
  `this.lastID` sem erro de sintaxe.
- **Correção esperada:** Promissificar o driver numa camada de repositório, eliminando tanto os
  callbacks com `this` rebindado quanto a necessidade do alias.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-049 — Ausência de qualquer infraestrutura de qualidade

- **Arquivo:** `package.json:6-12`
- **Evidência:**

```json
  "scripts": {
    "start": "node src/app.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "sqlite3": "^5.1.6"
  }
```

- **Descrição:** O manifesto declara um único script (`start`), nenhuma `devDependency` e nenhum
  campo `engines`. Uma varredura do diretório nesta sessão não encontrou arquivo de teste, config de
  lint, `.env`/`.env.example` nem pipeline de CI — os únicos artefatos além do código são
  `README.md`, `api.http` e o lockfile.
- **Impacto:** Não há rede de segurança alguma para a refatoração: nenhuma suíte que comprove que o
  comportamento foi preservado, e nenhum linter que teria apontado sozinho o import morto de AM-045.
  Sem `engines`, a versão de Node usada em produção é indefinida, e o `^` nas duas dependências
  permite que um `npm install` futuro resolva versões diferentes das do lockfile.
- **Correção esperada:** Adicionar test runner, linter e scripts correspondentes ao manifesto antes de
  iniciar a refatoração, junto de um `.env.example` documentando a configuração esperada.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

## Resumo

| Severidade | Quantidade |
|---|---|
| CRITICAL | 4 |
| HIGH | 7 |
| MEDIUM | 6 |
| LOW | 5 |
| **Total** | **22** |

**Mínimo exigido pelo enunciado (1 CRITICAL/HIGH + 2 MEDIUM + 2 LOW): ATINGIDO** — 11 findings
CRITICAL/HIGH contra 1 exigido, 6 MEDIUM contra 2, 5 LOW contra 2.

**Nota de calibragem.** A cota já estava satisfeita pelo primeiro finding, então não houve pressão de
quota atuando sobre a severidade. Três decisões merecem registro para a validação humana:

1. **Nenhum finding de SQL Injection foi criado**, apesar de a categoria estar explicitamente na
   escala do desafio e de o dossiê anterior ter registrado um. Este projeto usa bind de parâmetros em
   todas as queries de runtime, o que foi verificado por inspeção linha a linha e por `grep` buscando
   concatenação dentro das strings SQL. Registrar injeção aqui seria erro de auditoria.
2. **Apenas 4 CRITICAL**, contra 7 no projeto anterior, embora este seja igualmente um fixture
   semeado. A diferença é real e não estilística: `ecommerce-api-legacy` acerta a parametrização de
   queries e não expõe endpoint de SQL arbitrário nem de reset total da base.
3. **AM-031 (`badCrypto`) foi classificado CRITICAL e não HIGH** com base em execução verificada
   nesta sessão, não em leitura: a função colide `"123456"` com `"123"` e `"senhaforte"` com
   `"senhafraca"`, reduzindo todo o espaço de senhas a no máximo 4.096 valores. É falha grave de
   segurança pelo critério da escala, ainda que não conste entre os exemplos nomeados.

---

## Sinais genéricos extraídos

Sinais de detecção reescritos de forma agnóstica de projeto — insumo direto do catálogo de
anti-patterns da skill.

| # | Sinal genérico de detecção |
|---|---|
| AM-028 | Objeto de configuração literal no código-fonte contendo senha, chave de API ou credencial de serviço externo, sem nenhuma leitura de variável de ambiente no projeto. Reforço do sinal: o valor carrega marcador explícito de ambiente produtivo no próprio conteúdo, e/ou a chave declarada nunca é referenciada em lugar algum — segredo exposto sem sequer prestar função. |
| AM-029 | Uma única classe ou módulo que reúne, no mesmo arquivo, abertura de conexão de banco, definição de schema, registro de rotas e regra de negócio. Sinal de nome: substantivo genérico com sufixo do tipo "Manager"/"Handler"/"Util" que não delimita responsabilidade. |
| AM-030 | Chamada de log cujo template interpola dado de portador de cartão, credencial, token ou segredo de configuração, sem mascaramento ou redação. |
| AM-031 | Função caseira de derivação de senha que não invoca primitiva criptográfica da plataforma: laço construindo string por concatenação, ausência de salt, saída determinística e truncada a poucos caracteres. Verificação decisiva: executar a função sobre entradas distintas e observar colisão — se dois valores diferentes produzem a mesma saída, o finding está confirmado empiricamente, não por leitura. |
| AM-032 | Decisão de negócio de alto valor (autorização de pagamento, cálculo de elegibilidade, aprovação) implementada como expressão inline dentro do callback ou corpo do handler de rota, tipicamente sobre um literal mágico não nomeado. |
| AM-033 | Classe que instancia suas próprias dependências de infraestrutura no construtor e as importa por referência concreta no topo do módulo, enquanto o composition root a constrói sem passar argumento algum; parâmetros de infraestrutura (destino do banco, flag de verbosidade do driver, porta) fixados em literal. |
| AM-034 | Variável mutável declarada no escopo de módulo e exportada, escrita pelo caminho de requisição e sem política de expiração ou invalidação. Sinal adicional específico de módulos CommonJS: primitivo exportado por valor, de modo que reatribuições no módulo de origem nunca chegam aos consumidores — acumulador global estruturalmente incapaz de funcionar. |
| AM-035 | Handler de rota que vai direto do registro para o acesso a dados, sem middleware de autenticação ou verificação de papel, em endpoint cujo path sugere privilégio administrativo ou cuja operação é destrutiva; ausência de qualquer rota de autenticação no projeto inteiro. |
| AM-036 | Sequência de escritas relacionadas em tabelas distintas, encadeadas em callbacks aninhados, sem delimitação transacional e com retorno antecipado de erro no meio da cadeia sem compensação; registro de auditoria gravado apenas no caminho de sucesso, de modo que execuções falhas não deixam rastro. |
| AM-037 | Coordenação de operações assíncronas paralelas por contador decrementado à mão, com a resposta emitida quando o contador zera; parâmetro de erro recebido no callback e nunca verificado antes de desreferenciar o resultado. Consequências a procurar: desreferência de valor indefinido derrubando o processo, e caminhos de erro em que o contador nunca zera e a resposta nunca é enviada. |
| AM-038 | Valor de credencial atribuído por operador de fallback quando o campo não vem no payload, combinado a uma validação de entrada que deliberadamente não exige esse campo — criação silenciosa de conta com senha default conhecida. |
| AM-039 | Consulta a banco disparada dentro de laço que itera o resultado de consulta anterior, em mais de dois níveis de aninhamento; agregação numérica (soma, contagem) calculada em laço na camada de aplicação quando poderia ser expressa na própria consulta. |
| AM-040 | Validação de entrada resumida a teste de presença por coerção booleana, sem verificação de tipo nem de formato, e cobrindo apenas parte dos campos consumidos adiante. Sinais correlatos: teste por falsy rejeitando zero legítimo, parâmetro de rota usado sem validação, ausência de constraint de unicidade na coluna usada como identificador de negócio. |
| AM-041 | Rota de deleção que remove o registro principal sem tratar os dependentes, num schema sem chave estrangeira declarada; parâmetro de erro ignorado no callback, fazendo o handler responder sucesso incondicionalmente, inclusive quando nada foi afetado. Sinal auxiliar forte: a própria mensagem de resposta ou um comentário admite o defeito. |
| AM-042 | DDL executado pela classe de aplicação no boot, sem ferramenta de migração nem versionamento; definições de tabela sem `NOT NULL`, `UNIQUE`, `DEFAULT`, `CHECK` ou `FOREIGN KEY`, com colunas de relacionamento declaradas como inteiros soltos e colunas de estado como texto livre. |
| AM-043 | Saída direta para console usada como registro de eventos, sem níveis, timestamp ou destino configurável; caminhos de erro que respondem ao cliente e descartam o erro sem registrá-lo. Sinal de coesão: função cujo nome enumera duas responsabilidades não relacionadas, sem permitir ao chamador escolher uma. |
| AM-044 | Respostas de erro emitidas como texto puro enquanto as de sucesso são JSON, sem código de erro estável; mensagens misturando idiomas dentro do mesmo handler; condição que colapsa falha de infraestrutura e recurso inexistente no mesmo status HTTP. |
| AM-045 | Símbolo importado por desestruturação e nunca referenciado no arquivo; símbolo exportado e nunca consumido por nenhum módulo; flag de verbosidade ou depuração do driver ativado incondicionalmente no import. |
| AM-046 | Variáveis de uma a três letras recebendo campos de payload em handler extenso e aninhado; nomes de campo abreviados e com convenções misturadas no contrato público da API, sem correspondência com o vocabulário do domínio. |
| AM-047 | Dados de demonstração inseridos incondicionalmente pela aplicação no boot, no mesmo método que cria o schema; inserts que referenciam chaves auto-incrementadas por valor presumido em vez do id efetivamente gerado; credencial de usuário de exemplo gravada sem passar pela função de hash do próprio projeto. |
| AM-048 | Alias de `this` capturado em variável no topo de um método que também usa arrow functions, convivendo no mesmo bloco com callbacks em `function` cujo `this` é rebindado pela biblioteca — três referentes distintos sem sinalização, onde converter um callback em arrow quebra o código silenciosamente. |
| AM-049 | Manifesto de dependências sem devDependencies, sem script além do de execução e sem declaração de versão de runtime; ausência de arquivo de teste, de configuração de lint, de exemplo de variáveis de ambiente e de pipeline de CI no repositório; faixas de versão abertas convivendo com lockfile. |

---

## Metodologia de validação

Validação estratificada executada em 2026-08-16 com `.planning/validar.sh`, que
imprime o código-fonte real no range citado por cada finding e permite comparação
direta com o bloco de Evidência.

- **CRITICAL e HIGH:** 100% conferidos linha a linha (33 findings)
- **MEDIUM e LOW:** amostragem de ~30%, sem divergências

Correções aplicadas: AM-005, AM-029 e AM-052 tiveram a evidência ampliada porque
o recorte original era mais estreito que a acusação do título. Nenhum finding foi
descartado por linha inexistente ou evidência parafraseada.
