# Auditoria de Arquitetura — `code-smells-project`

> Fase 2 de `/refactor-arch`. Auditoria somente leitura. Nenhum arquivo do projeto foi
> modificado. Todo `arquivo:linha` foi obtido por leitura direta nesta execução.

## Contexto

| Item | Valor |
|---|---|
| Linguagem | Python (runtime do ambiente: 3.12.3) |
| Framework | Flask 3.1.1 · flask-cors 5.0.1 |
| Persistência | `sqlite3` (driver da stdlib, SQLite lib 3.45.1), arquivo `loja.db`, 4 tabelas |
| Domínio | E-commerce: catálogo de produtos, cadastro de usuários, pedidos com itens e relatório de vendas |
| Arquivos-fonte / LOC | 4 arquivos, 780 linhas |
| Endpoints | 19 — baseline capturado em 19 respostas |
| Commit de baseline | `ec6d1d4` |

### Arquitetura efetiva

O mecanismo de resolução da stack é **import explícito**: Flask com rotas registradas
nominalmente, sem autoload por convenção, sem varredura de pacote e sem container. O grafo parte
do único entry point `app.py` e alcança os quatro arquivos do projeto — `app.py → controllers →
models → database`, com `app.py` e `controllers.py` também importando `database` diretamente
(`app.py:4`, `controllers.py:3`). **Não há camada inalcançável**: nada aqui é código morto de
diretório, e nenhum diretório de camada preexistente precisa ser adotado ou descartado.

Responsabilidade acumulada por módulo alcançável:

- `app.py` (88 linhas) — composition root degenerado (não constrói nada, apenas importa),
  tabela de rotas, **e** dois handlers inline que executam SQL diretamente contra a conexão
  (`app.py:47-57`, `app.py:59-78`). Acumula três responsabilidades.
- `controllers.py` (292 linhas) — tradução de protocolo, **e** validação de domínio, **e**
  regra de negócio com efeitos colaterais de notificação, **e** acesso direto ao driver em
  `health_check` (`controllers.py:266-274`). Acumula quatro responsabilidades.
- `models.py` (314 linhas) — acesso a dados por SQL montado à mão, **e** regra de negócio
  (checagem de estoque, cálculo de total, faixas de desconto). Acumula duas responsabilidades.
- `database.py` (86 linhas) — fábrica de conexão global, **e** DDL, **e** seed de dados.
  Acumula três responsabilidades.

A árvore de arquivos sugere três camadas (`controllers`, `models`, `database`); o grafo de
resolução mostra que **nenhuma delas tem responsabilidade única** e que a direção de dependência
de `mvc-guidelines.md` §3 é violada em duas arestas: `routes → driver` (`app.py:4`, usado em
`app.py:50` e `app.py:67`) e `controllers → driver` (`controllers.py:3`, usado em
`controllers.py:266`). Não existe camada de service em ponto algum do projeto — a regra de
negócio está distribuída entre `controllers.py` e `models.py`.

### Baseline de comportamento

| Método | Endpoints | Status codes observados |
|---|---|---|
| GET | 10 | 200 ×10 |
| POST | 6 | 201 ×3 · 200 ×3 |
| PUT | 2 | 200 ×2 |
| DELETE | 1 | 200 ×1 |
| **Total (`M`)** | **19** | — |

Todos os 19 responderam `application/json`; nenhum exigiu `selector`.

Baseline completo, com media type e forma do corpo por endpoint, em
`/home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/baseline-code-smells-project.json`.
Pré-existentes quebrados: **nenhum**.
Não enumeráveis, fora de `M`: **nenhum** — as 19 rotas são registradas estaticamente
(16 via `add_url_rule`, 3 via decorador), sem montagem dinâmica.

`M` é o denominador de toda onda da Fase 3: onda verde exige `19/19` conformes.

## Sumário

| Severidade | Findings | Ocorrências |
|---|---|---|
| CRITICAL | 8 | 43 |
| HIGH | 6 | 39 |
| MEDIUM | 7 | 33 |
| LOW | 5 | 34 |
| **Total** | **26** | **149** |

---

## Findings

### [CRITICAL] F-001 — SQL montado por concatenação de entrada externa em toda a camada de dados

- **Anti-pattern:** AP-01 · **Transformação:** TR-02 · **Onda:** 1
- **Arquivo:** `models.py:109-111` (representativo de 16 pontos)
- **Evidência:**

```python
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
    )
```

- **Descrição:** `models.py` monta **toda** consulta por concatenação de string, sem um único
  parâmetro vinculado, apesar de o driver `sqlite3` suportar placeholders — que o próprio
  projeto usa em `database.py:70-73` e `database.py:80-83`, no seed. Os 16 pontos que
  concatenam valor de **entrada externa**: `models.py:28` (path param), `47-50` (corpo),
  `57-61` (corpo + path), `68` (path), `92` (path), `109-111` (corpo), `126-129` (corpo),
  `140` (corpo), `148-151` (corpo), `155` (corpo), `157-161` (corpo), `163-166` (corpo),
  `174` (path), `279-281` (corpo + path), `289-297` (query string). Outros 4 pontos concatenam
  apenas valores internos (`models.py:188`, `192`, `220`, `224`) — não são finding por si sós
  pelo contra-exemplo do AP, mas a mesma transformação os cobre.
- **Impacto:** verificado por execução nesta auditoria, não inferido. Dois caminhos anônimos:
  **(a)** `POST /login` com `{"email":"admin@loja.com","senha":"x' OR '1'='1"}` retornou
  `200` e `{"tipo":"admin"}` — autenticação como administrador sem conhecer a senha;
  **(b)** `GET /produtos/busca?categoria=informatica' OR '1'='1` retornou os 10 produtos,
  incluindo os das categorias `moveis` e `vestuario`, derrotando o filtro. Os mesmos caminhos
  aceitam `UPDATE`/`DELETE` encadeados.
- **Correção esperada:** toda consulta passa a usar parâmetros vinculados do driver; nenhum
  valor de entrada externa aparece na string da consulta.
- **Confiança:** ALTA

### [CRITICAL] F-002 — Onze rotas privilegiadas ou destrutivas sem nenhum ponto de verificação de identidade

- **Anti-pattern:** AP-05 · **Transformação:** TR-05 · **Onda:** 1
- **Arquivo:** `app.py:14-30`, `app.py:47`, `app.py:59`
- **Evidência:**

```python
app.add_url_rule("/usuarios", "listar_usuarios", controllers.listar_usuarios, methods=["GET"])
...
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
```

- **Descrição:** não existe middleware, decorador, `before_request`, leitura de header
  `Authorization` ou verificação inline em **nenhum** arquivo do projeto — confirmado por
  varredura. As onze rotas afetadas: `POST /admin/reset-db` (`app.py:47`, destrutiva em massa),
  `POST /admin/query` (`app.py:59`, SQL arbitrário), `GET /usuarios` (`app.py:18`, dados de
  terceiros **com senhas**), `GET /usuarios/<id>` (`app.py:19`), `GET /pedidos` (`app.py:24`,
  pedidos de todos os usuários), `GET /pedidos/usuario/<id>` (`app.py:25`, pedidos de
  terceiros), `PUT /pedidos/<id>/status` (`app.py:26`), `POST /produtos` (`app.py:14`),
  `PUT /produtos/<id>` (`app.py:15`), `DELETE /produtos/<id>` (`app.py:16`),
  `GET /relatorios/vendas` (`app.py:28`, faturamento).
  Além disso, `POST /login` **não emite credencial alguma** — nem assinada, nem previsível:
  devolve o registro do usuário (`controllers.py:180`) e o chamador não recebe nada que possa
  apresentar na requisição seguinte. Não há sessão a sequestrar porque não há sessão.
- **Sinal correlato confirmado:** o schema modela papel (`database.py:32`, `tipo TEXT DEFAULT
  'cliente'`) e o seed cria um `admin` (`database.py:76`), mas o campo é **apenas projetado em
  resposta** (`models.py:84`, `100`, `118`) e nunca lido por decisão alguma. A autorização foi
  projetada e não implementada.
- **Impacto:** um chamador anônimo apaga as quatro tabelas com um `POST /admin/reset-db`, ou lê
  o cadastro completo com as senhas em texto simples com um `GET /usuarios`. Ambos foram
  executados nesta auditoria e retornaram `200`.
- **Correção esperada:** login emite credencial assinada com expiração; rotas privilegiadas
  negam por padrão e verificam identidade e papel antes de alcançar a camada de dados.
- **Confiança:** ALTA

### [CRITICAL] F-003 — Segredo de assinatura em literal e debug ligado com bind em todas as interfaces

- **Anti-pattern:** AP-02 · **Transformação:** TR-01 · **Onda:** 1
- **Arquivo:** `app.py:7-8`, `app.py:88`
- **Evidência:**

```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
...
    app.run(host="0.0.0.0", port=5000, debug=True)
```

- **Descrição:** o segredo é literal versionado; **nenhum arquivo do projeto lê o ambiente**
  para essa ou qualquer outra chave — confirmado por varredura de `os.environ`, `getenv` e
  `dotenv` nos quatro arquivos, com zero ocorrências. O debug aparece ligado em dois pontos
  (`app.py:8` e `app.py:88`), no segundo junto do bind em `0.0.0.0`. Uma quarta ocorrência
  reexpõe ambos via HTTP (`controllers.py:288-289`) — reportada em F-007.
- **Impacto:** o console interativo do debugger do Werkzeug fica exposto em todas as interfaces
  de rede; o PIN aparece no stdout do boot (`Debugger PIN: 268-305-094`, capturado no baseline)
  e o segredo, estando no repositório, não é rotacionável apagando a linha — o histórico
  precisa ser rotacionado.
- **Correção esperada:** módulo de configuração que lê o ambiente e falha no boot se faltar
  valor obrigatório; nenhum segredo em literal; debug e bind derivados do ambiente.
- **Confiança:** ALTA

### [CRITICAL] F-004 — Senha persistida em texto simples e verificada por igualdade dentro da consulta

- **Anti-pattern:** AP-04 · **Transformação:** TR-03 · **Onda:** 1
- **Arquivo:** `models.py:109-111`, `models.py:126-129`, `database.py:75-79`
- **Evidência:**

```python
            usuarios = [
                ("Admin", "admin@loja.com", "admin123", "admin"),
                ("João Silva", "joao@email.com", "123456", "cliente"),
                ("Maria Santos", "maria@email.com", "senha123", "cliente"),
            ]
```

- **Descrição:** não há derivação em ponto algum — nem hash rápido, nem função caseira: a senha
  é gravada como veio (`models.py:126-129`) e verificada por igualdade **dentro da cláusula
  `WHERE`** (`models.py:109-111`), o que é simultaneamente a causa de F-001 no caminho de
  autenticação. O manifesto não declara nenhuma dependência de hashing
  (`requirements.txt` tem 2 linhas: `flask` e `flask-cors`), portanto não há aqui a
  "arquitetura pretendida e não implementada" que AP-26 às vezes revela — a derivação nunca foi
  planejada.
- **Impacto:** o `GET /usuarios`, público (F-002), devolve todas as senhas em texto simples —
  confirmado no baseline, que registra o campo `senha` na forma do corpo. Um vazamento do
  arquivo `loja.db` ou uma única chamada anônima entrega as credenciais reutilizáveis em outros
  serviços.
- **Correção esperada:** senha derivada por primitiva lenta com salt e fator de custo,
  verificada por comparação da derivação, nunca em SQL; contas existentes migradas por
  reidratação no próximo login bem-sucedido.
- **Confiança:** ALTA

### [CRITICAL] F-005 — Endereço de e-mail de usuário emitido em log, inclusive em falha de autenticação

- **Anti-pattern:** AP-07 · **Transformação:** TR-14 · **Onda:** 1
- **Arquivo:** `controllers.py:161`, `controllers.py:179`, `controllers.py:182`
- **Evidência:**

```python
        usuario = models.login_usuario(email, senha)
        if usuario:

            print("Login bem-sucedido: " + email)
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
        else:
            print("Login falhou: " + email)
```

- **Descrição:** o e-mail — identificador pessoal direto — é emitido integralmente, sem
  mascaramento nem truncamento, em três pontos: criação de conta (`controllers.py:161`) e nos
  dois ramos do login (`179`, `182`). O contra-exemplo do AP não se aplica: o valor não é
  derivado irreversível nem truncado, e não é público.
- **Impacto:** o stdout do processo passa a conter a lista de e-mails cadastrados e, pela
  distinção entre as duas mensagens de login, o par (e-mail, tentativa falha) — que é
  enumeração de contas persistida em log. Como não há destino configurável (F-022), esse
  conteúdo vai para onde quer que o stdout do processo seja coletado.
- **Correção esperada:** logger com níveis e timestamp, e redação dos campos sensíveis; o
  identificador do usuário substitui o e-mail nas mensagens.
- **Confiança:** ALTA

### [CRITICAL] F-006 — Senha projetada na resposta de duas rotas de leitura sem controle de acesso

- **Anti-pattern:** AP-03 · **Transformação:** TR-04 · **Onda:** 1
- **Arquivo:** `models.py:79-86`, `models.py:95-102`
- **Evidência:**

```python
        result.append({
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "senha": row["senha"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"]
        })
```

- **Descrição:** as duas funções de mapeamento registro→DTO de usuário projetam o campo
  `senha`: `get_todos_usuarios` (`models.py:79-86`) e `get_usuario_por_id` (`models.py:95-102`).
  Alimentam `GET /usuarios` (`app.py:18`) e `GET /usuarios/<id>` (`app.py:19`), ambas sem
  controle de acesso (F-002).
- **Reforço decisivo:** a **terceira** cópia do mesmo mapeamento, em `login_usuario`
  (`models.py:114-119`), **omite** `senha` e `criado_em`. A projeção do campo nas outras duas é
  portanto exposição acidental, não decisão de contrato — o projeto já demonstra saber qual é a
  projeção correta.
- **Impacto:** confirmado no baseline: `GET /usuarios` retorna `senha` para chamador anônimo, e
  as senhas são texto simples (F-004). Uma requisição entrega todas as credenciais do sistema.
- **Correção esperada:** DTO de usuário com allowlist explícita de projeção; `senha` não
  atravessa a fronteira de saída em nenhuma rota.
- **Confiança:** ALTA

### [CRITICAL] F-007 — Endpoint de diagnóstico serializa o segredo de assinatura e a configuração interna

- **Anti-pattern:** AP-03 · **Transformação:** TR-04 · **Onda:** 1
- **Arquivo:** `controllers.py:276-290`
- **Evidência:**

```python
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": { ... },

            "versao": "1.0.0",
            "ambiente": "producao",
            "db_path": "loja.db",
            "debug": True,
            "secret_key": "minha-chave-super-secreta-123"
        }), 200
```

- **Descrição:** `GET /health` (`app.py:30`), rota pública e não autenticada, devolve o segredo
  de assinatura, o caminho do arquivo de banco, o flag de debug e um rótulo de ambiente
  `"producao"` fixo em literal. Reportado separadamente de F-006 porque a causa é outra — não é
  o mapeamento de entidade, é um payload de diagnóstico montado à mão — e a correção é outra.
- **Impacto:** o segredo que F-003 mantém no repositório também é servido por HTTP a qualquer
  chamador anônimo, sem sequer exigir acesso ao código. Confirmado no baseline: o campo
  `secret_key` consta da forma do corpo registrada para `GET /health`.
- **Correção esperada:** o health check reporta apenas liveness e readiness; nenhum valor de
  configuração atravessa a fronteira de saída.
- **Confiança:** ALTA

### [CRITICAL] F-008 — Endpoint que executa SQL arbitrário recebido no corpo da requisição

- **Anti-pattern:** AP-01 · **Transformação:** TR-02 · **Onda:** 1
- **Arquivo:** `app.py:59-78`
- **Evidência:**

```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    dados = request.get_json()
    query = dados.get("sql", "")
    ...
    cursor.execute(query)
```

- **Descrição:** handler que recebe uma string de consulta no payload e a repassa ao executor
  do driver **sem allowlist alguma**. O único ramo condicional (`app.py:70`) apenas escolhe
  entre devolver linhas e comitar — ou seja, `INSERT`, `UPDATE`, `DELETE` e `DROP` são
  explicitamente suportados pelo caminho `else` (`app.py:74-76`). Reportado separadamente de
  F-001 porque a causa é distinta: F-001 é ausência de vinculação de parâmetros, corrigível
  sem mudar a superfície; aqui a execução arbitrária **é a funcionalidade**, e a correção é
  remover o endpoint.
- **Impacto:** um `POST /admin/query` anônimo com `{"sql":"DROP TABLE usuarios"}` destrói o
  schema. Nesta auditoria o endpoint foi exercido apenas com `SELECT` (retornou `200`), o que
  já comprova o caminho de execução sem tocar nos dados.
- **Correção esperada:** endpoint removido. Não há forma de fechá-lo preservando a superfície,
  porque a superfície **é** o defeito.
- **Confiança:** ALTA

---

### [HIGH] F-009 — Dependências obtidas por fábrica global no corpo de cada função, sem injeção

- **Anti-pattern:** AP-09 · **Transformação:** TR-09 · **Onda:** 2
- **Arquivo:** `models.py:4-6` (representativo de 19 chamadas), `database.py:5`
- **Evidência:**

```python
def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
```

- **Descrição:** as 19 funções que tocam persistência chamam `get_db()` no próprio corpo — 18
  em `models.py` e uma em `controllers.py:266` — em vez de receber a conexão como parâmetro. O
  destino do banco está fixado em literal (`database.py:5`, `db_path = "loja.db"`). O
  composition root (`app.py`) **não constrói nada**: importa `controllers` e `get_db` e
  registra rotas, sem passar dependência alguma — item 10 do checklist de conformidade de
  camada. Não há container na stack detectada, portanto o contra-exemplo do AP não se aplica.
- **Impacto:** nenhuma função da camada de dados é executável sem o singleton global e sem
  criar o arquivo `loja.db` no diretório de trabalho. Isso torna qualquer teste da regra de
  negócio dependente de banco real, o que é a causa estrutural de F-026 (ausência de testes):
  não há como escrever o primeiro teste sem antes desfazer este acoplamento.
- **Correção esperada:** composition root constrói conexão, repositórios e serviços e os
  injeta; nenhuma camada abaixo chama fábrica global.
- **Confiança:** ALTA

### [HIGH] F-010 — Regra de negócio e efeito colateral distribuídos entre o handler e a camada de dados

- **Anti-pattern:** AP-08 · **Transformação:** TR-07 · **Onda:** 2
- **Arquivo:** `controllers.py:205-216`, `models.py:256-262`
- **Evidência:**

```python
        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado para usuario " + str(usuario_id))
        print("ENVIANDO SMS: Seu pedido foi recebido!")
        print("ENVIANDO PUSH: Novo pedido recebido pelo sistema")
```

```python
    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
```

- **Descrição:** não existe camada de service no projeto, e a regra de domínio se acomodou nas
  duas camadas erradas simultaneamente. **No handler:** efeitos colaterais de notificação
  (`controllers.py:208-210`, `248`, `250`), vocabulário fechado de transição de estado
  (`controllers.py:242`), e regra de precificação/elegibilidade (`controllers.py:43-54`).
  **Na camada de dados:** faixas de desconto sobre faturamento (`models.py:256-262`) e
  checagem de estoque com cálculo de total (`models.py:144-146`) — misturadas a agregações de
  consulta, exatamente a direção inversa que o sinal do AP descreve.
- **Sinal correlato confirmado (o mais decisivo):** o controller inspeciona a **forma** do
  valor retornado para escolher o status code em quatro pontos — `if produto:`
  (`controllers.py:17`), `if usuario:` (`controllers.py:139`), `if usuario:`
  (`controllers.py:177`) e `if "erro" in resultado:` (`controllers.py:205`). Regra de domínio
  codificada como formato de retorno é o sintoma mais confiável de que não existe service.
- **Impacto:** a regra "pedido criado dispara notificação" só existe sob HTTP: nenhum outro
  gatilho (fila, job, importação em lote) a executa, e nenhum teste a verifica sem subir
  servidor. A regra de desconto, por estar em `models.py`, é invisível para quem lê o
  controller do relatório.
- **Correção esperada:** camada de service que decide *o quê* acontece e orquestra efeitos;
  controller traduz protocolo e mapeia erro de domínio tipado para status.
- **Confiança:** ALTA

### [HIGH] F-011 — Três handlers alcançam o driver diretamente, saltando a camada de dados existente

- **Anti-pattern:** AP-13 · **Transformação:** TR-06 · **Onda:** 2
- **Arquivo:** `app.py:47-57`, `app.py:59-78`, `controllers.py:264-274`
- **Evidência:**

```python
def health_check():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.execute("SELECT COUNT(*) FROM produtos")
```

- **Descrição:** três handlers importam a fábrica de conexão (`app.py:4`, `controllers.py:3`) e
  montam consulta e controlam commit dentro do próprio corpo: `reset_database` (`app.py:50-55`,
  quatro `DELETE` e um `commit`), `executar_query` (`app.py:66-76`, `execute` e `commit`) e
  `health_check` (`controllers.py:266-274`, quatro `SELECT`). O contra-exemplo do AP **não se
  aplica**: existe camada intermediária alcançável (`models.py`), e estes três handlers a
  saltam — não é o idioma da stack, é salto de camada. As duas arestas proibidas por
  `mvc-guidelines.md` §3 são `routes → driver` e `controllers → driver`.
- **Nota de onda:** o teto de TR-06 é a Onda 1 por AP-06, que **não virou finding** nesta
  auditoria (ver "O que não foi encontrado"). Pela regra de que a onda é propriedade do
  finding, TR-06 **desce para a Onda 2**, que é a severidade deste AP.
- **Impacto:** três caminhos de acesso a dados escapam de qualquer política que a camada de
  dados venha a aplicar — vinculação de parâmetros, limite de resultado, auditoria. A correção
  de F-001 em `models.py` não os alcança.
- **Correção esperada:** os três handlers passam a chamar service/repositório; nenhum módulo de
  rota ou de controller importa a fábrica de conexão.
- **Confiança:** ALTA

### [HIGH] F-012 — Escritas relacionadas sem fronteira transacional e deleção que produz órfãos

- **Anti-pattern:** AP-11 · **Transformação:** TR-10 · **Onda:** 2
- **Arquivo:** `models.py:139-168`, `models.py:65-70`
- **Evidência:**

```python
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": "Produto " + str(item["produto_id"]) + " não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": "Estoque insuficiente para " + produto["nome"]}
```

- **Descrição:** duas manifestações. **(a) Check-then-act sem atomicidade:** a verificação de
  disponibilidade (`models.py:144-146`) está separada da consumação
  (`models.py:163-166`, `UPDATE produtos SET estoque = estoque - …`) por dez linhas e por dois
  `INSERT`, sem bloqueio nem constraint que torne a corrida impossível — o schema não declara
  `CHECK (estoque >= 0)` (`database.py:14-25`). **(b) Deleção com órfãos:** `deletar_produto`
  (`models.py:65-70`) remove a linha de `produtos` e deixa as linhas de `itens_pedido` que a
  referenciam, num schema **sem nenhuma chave estrangeira declarada**.
- **Cenário concreto (a):** dois pedidos concorrentes do último item em estoque. Ambos leem
  `estoque = 1` na linha 144, ambos passam na verificação, ambos executam o `UPDATE` relativo
  da linha 163-166, e o estoque termina em `-1`. Nenhuma constraint impede o valor negativo.
- **Cenário concreto (b), verificado por execução:** criado um pedido do produto `3`, depois
  `DELETE /produtos/3` (retornou `200`); o `GET /pedidos` seguinte devolveu o item com
  `"produto_nome": "Desconhecido"`. O próprio código já tem o fallback que denuncia o estado
  órfão (`models.py:196`, `prod["nome"] if prod else "Desconhecido"`) — o defeito é conhecido
  pelo projeto e não tratado.
- **Correção esperada:** as escritas relacionadas do pedido passam a compor uma unidade de
  trabalho única, com a consumação de estoque condicional e atômica; a deleção respeita a
  integridade referencial que TR-16 declara.
- **Confiança:** ALTA

### [HIGH] F-013 — DDL e seed executados no boot, em schema sem nenhuma restrição de integridade

- **Anti-pattern:** AP-21 · **Transformação:** TR-16 · **Onda:** 2
- **Arquivo:** `database.py:12-54` (DDL), `database.py:56-84` (seed)
- **Evidência:**

```python
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT,
                senha TEXT,
                tipo TEXT DEFAULT 'cliente',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
```

- **Descrição:** as quatro tabelas são criadas dentro de `get_db()` (`database.py:12-54`), que
  é chamada no caminho de boot (`app.py:82`) e em toda requisição. O manifesto não declara
  ferramenta de migração. O seed roda **sem guarda de ambiente**, condicionado apenas a a
  tabela estar vazia (`database.py:56-57`), e insere uma credencial administrativa conhecida
  (`database.py:76`, `admin@loja.com` / `admin123`).
- **Sinal estrutural adicional, verificado:** nenhuma das quatro tabelas declara `FOREIGN KEY`,
  `UNIQUE` ou `NOT NULL` — busca no `sqlite_master` retornou zero ocorrências dos três. A
  consequência foi confirmada por execução: dois `POST /usuarios` com o **mesmo e-mail**
  retornaram `201` e `201`, criando contas duplicadas sobre o identificador que o login usa
  (`models.py:110`).
- **Consequência a nomear:** como o comando só cria o que falta, **nenhuma evolução de coluna é
  possível** — alterar um tipo ou adicionar uma constraint exige apagar `loja.db`. O projeto
  não tem caminho de evolução de schema, e esse é o dano maior que o incômodo do boot.
- **Correção esperada:** migração versionada fora do boot, seed separado e guardado por
  ambiente, e as restrições de integridade declaradas — em particular `UNIQUE` em
  `usuarios.email` e as chaves estrangeiras de `itens_pedido` e `pedidos`.
- **Confiança:** ALTA

### [HIGH] F-014 — Conexão de banco em variável global mutável, com a proteção de concorrência do driver desligada

- **Anti-pattern:** AP-10 · **Transformação:** TR-09 · **Onda:** 2
- **Arquivo:** `database.py:4-11`
- **Evidência:**

```python
db_connection = None
db_path = "loja.db"

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
```

- **Descrição:** `db_connection` é declarada em escopo de módulo (`database.py:4`) e escrita a
  partir do caminho de requisição (`database.py:9-10`), sem lock e sem política de invalidação
  — o `if` de inicialização preguiçosa não é atômico. O contra-exemplo do AP não se aplica: não
  é global imutável pós-inicialização nem pool com contrato de compartilhamento.
- **Agravante:** `check_same_thread=False` (`database.py:10`) desabilita explicitamente a
  proteção de concorrência do driver, entregando a mesma conexão a todas as threads do servidor.
- **Impacto:** todas as requisições compartilham uma conexão e, portanto, a mesma transação
  implícita. Um `commit` disparado por uma requisição confirma escritas parciais de outra em
  andamento — o que é a via mais provável pela qual o estado parcial de F-012 se materializa.
  A conexão também nunca é reaberta se cair.
- **Correção esperada:** a conexão deixa de ser global e passa a ser construída pelo composition
  root com escopo por requisição, injetada adiante.
- **Confiança:** ALTA

---

### [MEDIUM] F-015 — Captura genérica em todos os handlers, devolvendo a mensagem da exceção ao cliente

- **Anti-pattern:** AP-18 · **Transformação:** TR-13 · **Onda:** 3
- **Arquivo:** `controllers.py:10-12` (representativo de 17 ocorrências)
- **Evidência:**

```python
    except Exception as e:
        print("ERRO: " + str(e))
        return jsonify({"erro": str(e)}), 500
```

- **Descrição:** o mesmo bloco se repete **17 vezes** — 16 em `controllers.py` (linhas 10, 21,
  60, 95, 108, 125, 133, 143, 164, 185, 218, 226, 234, 254, 261, 291) e 1 em `app.py:77`. Não
  há tratador centralizado, não há distinção entre falha de domínio e defeito, e a
  representação textual da exceção é serializada no corpo da resposta. Onze das 17 ocorrências
  descartam o erro sem registrá-lo em lugar algum.
- **Consequência confirmada por execução:** entrada inválida que deveria virar 4xx vira 5xx com
  detalhe interno vazado. Três caminhos verificados nesta auditoria:
  `POST /produtos` com `"preco":"abc"` → `500` e
  `{"erro":"'<' not supported between instances of 'str' and 'int'"}`;
  `POST /login` com corpo `null` → `500` e
  `{"erro":"'NoneType' object has no attribute 'get'"}`;
  `GET /produtos/busca?preco_min=abc` → `500` e
  `{"erro":"could not convert string to float: 'abc'"}`.
- **Impacto:** o cliente recebe mensagens de exceção do interpretador, que revelam tipos
  internos e estrutura do código; e um monitor que alerta por taxa de 5xx dispara para erro do
  chamador, mascarando defeitos reais no ruído.
- **Correção esperada:** tratador centralizado na fronteira do processo, com envelope único,
  erro completo registrado e apenas identificador de correlação emitido ao cliente; erro de
  domínio tipado mapeado para 4xx.
- **Confiança:** ALTA

### [MEDIUM] F-016 — Cinco endpoints de listagem sem limite, offset ou cursor

- **Anti-pattern:** AP-22 · **Transformação:** TR-17 · **Onda:** 3
- **Arquivo:** `models.py:7`, `models.py:75`, `models.py:174`, `models.py:206`, `models.py:289-299`
- **Evidência:**

```python
def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    rows = cursor.fetchall()
```

- **Descrição:** nenhuma das cinco consultas de listagem tem cláusula de limite, e nenhum dos
  handlers correspondentes lê parâmetro de paginação: `GET /produtos` (`models.py:7`),
  `GET /usuarios` (`models.py:75`), `GET /pedidos/usuario/<id>` (`models.py:174`),
  `GET /pedidos` (`models.py:206`) e `GET /produtos/busca` (`models.py:289-299`, que monta
  filtros mas nunca limite). O contra-exemplo não se aplica: nenhuma das quatro tabelas tem
  cardinalidade fechada pelo domínio — todas crescem com o uso.
- **Impacto:** o tamanho da resposta é função dos dados e não do contrato. As duas listagens de
  pedido são as piores: combinadas com o N+1 de F-019, o custo cresce com o produto do número
  de pedidos pelo número de itens.
- **Correção esperada:** paginação com defaults explícitos e limite máximo em todos os cinco.
- **Confiança:** ALTA

### [MEDIUM] F-017 — Envelopes de resposta divergentes entre handlers equivalentes

- **Anti-pattern:** AP-23 · **Transformação:** TR-13 · **Onda:** 3
- **Arquivo:** `controllers.py:20` vs `controllers.py:142`
- **Evidência:**

```python
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
```

```python
            return jsonify({"erro": "Usuário não encontrado"}), 404
```

- **Descrição:** os dois handlers são equivalentes — busca por id, recurso ausente, 404 — e
  emitem envelopes diferentes: o de produto traz `sucesso`, o de usuário não. Mais quatro
  divergências no mesmo projeto: `criar_produto` devolve `{"dados","sucesso","mensagem"}`
  (`controllers.py:58`) enquanto o equivalente `criar_usuario` devolve `{"dados","sucesso"}`
  (`controllers.py:162`); `buscar_produtos` acrescenta `total` (`controllers.py:124`) enquanto
  `listar_produtos` não (`controllers.py:9`); `health_check` usa uma **terceira** chave de erro,
  `{"status","detalhes"}` (`controllers.py:292`); e os 17 blocos de F-015 devolvem
  `{"erro"}` sem `sucesso`. Não há código de erro estável em nenhum deles.
- **Impacto:** um cliente que trate `sucesso` como campo confiável quebra ao chamar
  `/usuarios/<id>` inexistente, porque o campo simplesmente não vem. Não há como escrever um
  tratamento de erro único do lado do consumidor.
- **Correção esperada:** envelope único de erro com código estável, aplicado por tratador
  centralizado; envelope de sucesso uniforme entre recursos equivalentes.
- **Confiança:** ALTA

### [MEDIUM] F-018 — Invariantes de domínio como condicionais literais no handler, divergentes entre criar e atualizar

- **Anti-pattern:** AP-12 · **Transformação:** TR-08 · **Onda:** 3
- **Arquivo:** `controllers.py:43-54` vs `controllers.py:87-90`
- **Evidência (criar — `controllers.py:43-54`):**

```python
        if preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        if estoque < 0:
            return jsonify({"erro": "Estoque não pode ser negativo"}), 400
        if len(nome) < 2:
            return jsonify({"erro": "Nome muito curto"}), 400
        if len(nome) > 200:
            return jsonify({"erro": "Nome muito longo"}), 400

        categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
        if categoria not in categorias_validas:
            return jsonify({"erro": "Categoria inválida. Válidas: " + str(categorias_validas)}), 400
```

- **Evidência (atualizar — `controllers.py:87-90`):**

```python
        if preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        if estoque < 0:
            return jsonify({"erro": "Estoque não pode ser negativo"}), 400
```

- **Agravante decisivo:** a mesma entidade, as mesmas invariantes, e a regra **já discordou de
  si mesma**. `POST /produtos` rejeita nome com menos de 2 caracteres, nome com mais de 200 e
  categoria fora do vocabulário; `PUT /produtos/<id>` aceita todos os três. Um produto criado
  válido pode ser atualizado para um estado que a criação proíbe.
- **Descrição:** as invariantes são de domínio, não de protocolo, e nenhuma tem constraint
  equivalente no schema — `database.py:14-25` declara `nome TEXT`, `preco REAL`, `estoque
  INTEGER`, `categoria TEXT`, todos nuláveis e sem `CHECK`. Uma terceira ocorrência do mesmo
  padrão está em `atualizar_status_pedido` (`controllers.py:242`), com o vocabulário fechado de
  status reconstruído inline. As verificações de campo obrigatório ausente
  (`controllers.py:30-35`, `74-79`) **não** entram neste finding: são de protocolo, e pertencem
  à borda.
- **Impacto:** a regra existe em dois lugares e já divergiu; qualquer terceira porta de entrada
  (importação, job) nasceria com uma terceira versão.
- **Correção esperada:** validador declarativo por entidade, compartilhado entre criação e
  atualização, com as constraints correspondentes declaradas no schema por TR-16.
- **Confiança:** ALTA

### [MEDIUM] F-019 — N+1 em três níveis nas duas listagens de pedido, com cursor novo por iteração

- **Anti-pattern:** AP-15 · **Transformação:** TR-11 · **Onda:** 3
- **Arquivo:** `models.py:171-201`, `models.py:203-233`
- **Evidência:**

```python
    for row in rows:
        pedido = { ... }

        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
        itens = cursor2.fetchall()
        for item in itens:
            cursor3 = db.cursor()
            cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

- **Descrição:** três níveis de aninhamento em `get_pedidos_usuario` (`models.py:174` externa,
  `188` intermediária, `192` interna) e o bloco **duplicado quase literalmente** em
  `get_todos_pedidos` (`models.py:206`, `220`, `224`). Uma junção de três tabelas resolveria em
  uma ida. **Agravante:** um cursor novo é alocado por iteração em ambos os níveis
  (`models.py:187`, `191`, `219`, `223`), somando custo de recurso ao custo de rede.
- **Estimativa de idas ao banco:** `1 + P + Σ(itens de cada pedido)`, onde `P` é o número de
  pedidos. Para 100 pedidos de 3 itens: 401 consultas onde 1 bastaria. Como não há paginação
  (F-016), `P` é a tabela inteira.
- **Variante correlata:** `relatorio_vendas` (`models.py:239-254`) dispara **cinco** consultas
  de agregação separadas (`COUNT`, `SUM`, e três `COUNT` com filtro de status) sobre a mesma
  tabela, todas exprimíveis numa consulta só.
- **Correção esperada:** as duas listagens colapsam numa única consulta com junção; as cinco
  agregações do relatório viram uma.
- **Confiança:** ALTA

### [MEDIUM] F-020 — Política de origem cruzada permissiva aplicada globalmente

- **Anti-pattern:** AP-20 · **Transformação:** TR-18 · **Onda:** 3
- **Arquivo:** `app.py:9`
- **Evidência:**

```python
CORS(app)
```

- **Descrição:** o middleware é registrado sem nenhum argumento de restrição, o que na
  configuração padrão de `flask-cors` libera qualquer origem. Aplicado globalmente, cobre
  indistintamente as rotas públicas de leitura e as 11 rotas de escrita e remoção que F-002
  mostra não terem autenticação — incluindo `POST /admin/reset-db` e `POST /admin/query`.
- **Impacto:** qualquer página web aberta pela vítima pode disparar as rotas destrutivas contra
  uma instância alcançável e ler a resposta. Sem F-002 a exposição seria só de leitura; com ele,
  é de escrita.
- **Nota de composição / severidade:** mantida em MEDIUM conforme a escala. Não foi elevada
  porque **não há autenticação por cookie** a ser explorada — não há credencial alguma
  (F-002), então a política permissiva amplia o alcance mas não escala privilégio.
- **Correção esperada:** allowlist de origens configurável por ambiente, lida pelo módulo de
  configuração de TR-01.
- **Confiança:** ALTA

### [MEDIUM] F-021 — Endpoint de autenticação sem contador, backoff ou bloqueio

- **Anti-pattern:** AP-24 · **Transformação:** TR-05 · **Onda:** 3
- **Arquivo:** `app.py:21`, `controllers.py:167-186`
- **Evidência:**

```python
app.add_url_rule("/login", "login", controllers.login, methods=["POST"])
```

- **Descrição:** a rota é registrada sem middleware de limite de taxa; o handler
  (`controllers.py:167-186`) não mantém contador de tentativas por sujeito nem atraso
  progressivo; e o manifesto não declara dependência correspondente. O contra-exemplo não se
  aplica: não há gateway nem proxy verificável no repositório — o único entry point é
  `app.run` (`app.py:88`).
- **Sinal correlato registrado:** hoje a força bruta é **desnecessária**, porque F-001 permite
  o bypass por injeção e F-006 entrega as senhas por `GET /usuarios`. Assim que TR-02, TR-03 e
  TR-04 fecharem esses caminhos, a força bruta passa a ser o caminho mais barato — e é por isso
  que este finding é registrado agora e não depois.
- **Impacto:** tentativas ilimitadas contra as três contas de seed com senhas fracas
  (`admin123`, `123456`, `senha123`, `database.py:76-78`).
- **Correção esperada:** limite de taxa por sujeito e por origem no endpoint de autenticação,
  entregue junto de TR-05.
- **Confiança:** ALTA

---

### [LOW] F-022 — Saída de console como único mecanismo de registro de eventos

- **Anti-pattern:** AP-19 · **Transformação:** TR-14 · **Onda:** 4
- **Arquivo:** `controllers.py` (14 ocorrências), `app.py` (5 ocorrências)
- **Evidência:**

```python
        print("Listando " + str(len(produtos)) + " produtos")
```

- **Descrição:** 19 chamadas de `print` no código servidor — `controllers.py:8, 11, 57, 61,
  106, 161, 179, 182, 208, 209, 210, 219, 248, 250` e `app.py:56, 83, 84, 85, 86` — sem nível
  de severidade, sem timestamp e sem destino configurável. **Nenhum arquivo do projeto importa
  biblioteca de logging** — confirmado por varredura de `import logging`, `getLogger` e
  `logger`, com zero ocorrências. O contra-exemplo não se aplica: não é ferramenta de linha de
  comando, e 14 das 19 estão no caminho de requisição.
- **Reforço:** os caminhos de erro respondem ao cliente e **descartam** o erro sem registrá-lo
  em 11 dos 17 blocos de F-015, tornando o defeito invisível fora do momento da chamada.
- **Impacto:** não há como filtrar por severidade, correlacionar uma requisição ou desligar o
  volume em produção; e F-005 mostra que esse fluxo não-filtrável carrega PII.
- **Correção esperada:** logger com níveis, timestamp, destino configurável e redação de campos
  sensíveis, substituindo as 19 chamadas.
- **Confiança:** ALTA

### [LOW] F-023 — Builtin `id` sombreado como parâmetro e variável, e assinaturas com muitos posicionais do mesmo tipo

- **Anti-pattern:** AP-27 · **Transformação:** TR-18 · **Onda:** 4
- **Arquivo:** `models.py:24, 54, 65, 89`, `controllers.py:14, 56, 64, 98, 160`
- **Evidência:**

```python
def atualizar_produto(id, nome, descricao, preco, estoque, categoria):
```

- **Descrição:** o builtin `id` da linguagem detectada é usado como nome de parâmetro em sete
  funções (`models.py:24, 54, 65, 89`; `controllers.py:14, 64, 98`) e como variável local que
  recebe o retorno de criação em duas (`controllers.py:56`, `160`). Nesses corpos, `id()` deixa
  de estar acessível. O contra-exemplo não se aplica: não é índice de laço nem variável de
  compreensão de uma linha — `atualizar_produto` tem 33 linhas.
- **Risco de troca de ordem:** `atualizar_produto(id, nome, descricao, preco, estoque,
  categoria)` (`models.py:54`) tem seis parâmetros posicionais, dos quais **três são strings
  adjacentes** (`nome`, `descricao`) e (`categoria`); `criar_produto(nome, descricao, preco,
  estoque, categoria)` (`models.py:43`) tem cinco com o mesmo problema. Inverter `nome` e
  `descricao` na chamada não produz erro algum — grava e segue.
- **Impacto:** custo de leitura e uma classe de defeito silencioso na chamada. Sem efeito
  observável em produção hoje, o que sustenta a severidade LOW.
- **Correção esperada:** renomear para o vocabulário do domínio (`produto_id`, `usuario_id`) e
  tornar os parâmetros de mesmo tipo nomeados na assinatura.
- **Confiança:** ALTA

### [LOW] F-024 — Limiares de negócio como literais sem nome na camada de dados

- **Anti-pattern:** AP-25 · **Transformação:** TR-18 · **Onda:** 4
- **Arquivo:** `models.py:256-262`, `models.py:150`, `controllers.py:286`
- **Evidência:**

```python
    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02
```

- **Descrição:** seis literais (`10000`, `0.1`, `5000`, `0.05`, `1000`, `0.02`) carregam a
  política comercial de desconto por faixa de faturamento, sem constante nomeada e sem
  correspondência com restrição no schema. Duas outras ocorrências: o status inicial
  `'pendente'` embutido na consulta de criação de pedido (`models.py:150`) e o rótulo de
  ambiente `"producao"` fixo na resposta de diagnóstico (`controllers.py:286`) — este último
  factualmente errado, já que `debug` está ligado no mesmo payload.
- **Exclusão aplicada:** os literais de `controllers.py:47-54` (tamanhos de nome, vocabulário
  de categorias) e de `controllers.py:242` (vocabulário de status) **não** entram aqui: vivem
  dentro do bloco que já é F-018 (AP-12), e o catálogo determina que sejam citados como
  ocorrência daquele finding, não como finding LOW separado.
- **Impacto:** mudar a política de desconto exige editar a camada de dados, e a faixa aplicada
  não é auditável a partir do relatório que a expõe.
- **Correção esperada:** constantes nomeadas no lugar da responsabilidade correspondente, com a
  política de desconto migrando para o service que TR-07 cria.
- **Confiança:** ALTA

### [LOW] F-025 — Imports declarados e nunca referenciados

- **Anti-pattern:** AP-26 · **Transformação:** TR-15 · **Onda:** 4
- **Arquivo:** `database.py:2`, `models.py:2`
- **Evidência:**

```python
import sqlite3
import os
```

- **Descrição:** `os` é importado em `database.py:2` e tem **zero** referências no arquivo —
  confirmado por varredura de `os.` com zero ocorrências. `sqlite3` é importado em `models.py:2`
  e tem **uma** ocorrência, que é a própria linha do import: `models.py` nunca usa o driver
  diretamente, porque recebe a conexão de `get_db()`. As duas dependências do manifesto
  (`flask`, `flask-cors`) **são** importadas e usadas — não há dependência morta no manifesto.
  Não há diretório de camada inalcançável: os quatro arquivos são alcançáveis a partir de
  `app.py` por import explícito.
- **Leitura de alto valor do sinal:** o `os` importado e não usado em `database.py`
  corresponde **exatamente** à lacuna que F-003 aponta — a leitura do ambiente foi cogitada no
  arquivo que fixa `db_path = "loja.db"` em literal (`database.py:5`) e nunca implementada. Não
  é ruído: é a arquitetura pretendida e abandonada, e indica que TR-01 tem menos atrito do que
  parece.
- **Impacto:** custo de leitura. O `import os` sugere ao leitor que existe configuração por
  ambiente, quando não existe em ponto algum do projeto.
- **Correção esperada:** os dois imports removidos — o de `os` **depois** de TR-01, que é quem
  vai de fato usar o ambiente.
- **Confiança:** ALTA

### [LOW] F-026 — Ausência completa de infraestrutura de qualidade

- **Anti-pattern:** AP-28 · **Transformação:** nenhuma — reportado, não corrigido · **Onda:** —
- **Arquivo:** `requirements.txt` (íntegro, 2 linhas)
- **Evidência:**

```text
flask==3.1.1
flask-cors==5.0.1
```

- **Descrição:** o manifesto declara apenas as duas dependências de execução: nenhuma
  dependência de desenvolvimento, nenhum comando reproduzível além de `python app.py`, e
  nenhuma versão de runtime fixada. O repositório não tem arquivo de teste, configuração de
  lint, exemplo de variáveis de ambiente nem pipeline de CI — verificado **no projeto e um
  nível acima**, na raiz do repositório, para descartar a hipótese de monorepo com configuração
  centralizada: nenhum dos dois níveis tem `.github/`, `pyproject.toml`, `setup.cfg`, `tox.ini`,
  `pytest.ini`, configuração de linter ou `Makefile`. As versões são fixadas exatamente, e não
  há lockfile — o que é coerente, não contraditório.
- **Impacto:** nenhuma das 25 correções acima tem rede de proteção automatizada; a validação da
  Fase 3 depende inteiramente do smoke test contra o baseline desta skill. Sem runtime fixado,
  a verificação de AP-16 vale para 3.12.3 e não é reprodutível em outra máquina.
- **Este AP não tem TR** e **não entra no plano de refatoração** — instalar test runner, linter
  e CI está fora do escopo declarado da skill. Coberturas parciais que outras transformações
  produzem: TR-01 publica o exemplo de variáveis de ambiente.
- **Confiança:** ALTA

---

## O que não foi encontrado

Os 4 APs do catálogo que não produziram finding, com o estado de cada um. Somados aos 24 APs
representados nos 26 findings acima, cobrem as 28 entradas do catálogo.

- **God class / god module (AP-06) — não encontrado.** O sinal exige um único arquivo ou classe
  que reúna, **no mesmo corpo**, abertura de conexão, definição de schema, registro de rotas e
  regra de negócio, de modo que não exista fronteira onde inserir uma camada. Nenhum dos quatro
  arquivos satisfaz isso: `app.py` registra rotas e alcança o driver mas não define schema nem
  concentra regra; `database.py` abre conexão, define schema e faz seed, mas não registra rota
  nem decide regra; `controllers.py` mistura protocolo, validação e regra, mas não define schema
  nem registra rota; `models.py` é acesso a dados com regra, sem schema nem rota. As fronteiras
  **existem** — estão nos lugares errados, o que é AP-08 (F-010), AP-13 (F-011) e AP-09 (F-009),
  não AP-06. **Consequência para o plano:** TR-06 tinha teto na Onda 1 por este AP; como ele não
  virou finding, TR-06 desce para a Onda 2, a severidade de AP-13 (F-011).
- **Mass assignment / bind não filtrado (AP-14) — não encontrado.** Todos os caminhos de escrita
  extraem campo a campo, com allowlist implícita pela assinatura: `criar_produto` lê cinco
  campos nomeados (`controllers.py:37-41`), `criar_usuario` lê três (`controllers.py:153-155`),
  `atualizar_status_pedido` lê um (`controllers.py:240`). Nenhum espalhamento de payload
  (`**dados` ou equivalente) existe no projeto. Verificação decisiva: a coluna privilegiada
  `usuarios.tipo` **não** é gravável pelo chamador — `models.criar_usuario` a recebe como
  parâmetro com default (`models.py:122`) e o controller nunca a passa (`controllers.py:160`),
  então `POST /usuarios` não consegue criar um administrador.
- **Duplicação com a abstração correta morta (AP-17) — não encontrado.** Existe duplicação
  substancial e verificada: o mapeamento registro→dicionário de produto aparece em três cópias
  (`models.py:12-21`, `31-40`, `304-313`), o de usuário em duas (`models.py:79-86`, `95-102`) e
  o bloco de montagem de pedido com itens em duas quase idênticas de ~20 linhas
  (`models.py:178-199`, `211-231`). Mas o sinal deste AP exige **as duas metades**: a
  duplicação **e** a abstração correta já presente no repositório que ninguém invoca. A segunda
  metade não existe — não há função, método ou constante morta que resolveria essas cópias, e a
  contagem de referências externas confirmou que todo símbolo exportado por `models.py` é
  chamado por `controllers.py`. Sem a abstração morta, a Fase 3 seria "criar camadas" e não
  "ligar as que já existem", que é a distinção que este AP mede. A duplicação em si é
  consequência da ausência de camada de DTO e de repositório, e é endereçada por TR-04 (F-006) e
  TR-06 (F-011); não abre finding próprio.
- **Deprecated API usage (AP-16) — não encontrado.** Verificado contra o runtime **3.12.3**,
  obtido executando o interpretador do ambiente (não lido do manifesto, que aliás não declara
  versão alguma). Procedimento: a aplicação foi executada com `-W always::DeprecationWarning
  -W always::PendingDeprecationWarning` e todos os endpoints do baseline foram exercidos;
  **zero** avisos foram emitidos, de dependências ou de arquivos do projeto. Cruzamento manual
  das APIs efetivamente chamadas — `sqlite3.connect`, `Connection.cursor`, `Cursor.execute`,
  `executemany`, `fetchone`, `fetchall`, `lastrowid`, `commit`, `sqlite3.Row`, `flask.Flask`,
  `add_url_rule`, `route`, `jsonify`, `request.get_json`, `request.args.get`, `app.run`,
  `flask_cors.CORS` — contra as notas de depreciação de 3.12: nenhuma está depreciada nessa
  versão. As duas depreciações de 3.12 que atingiriam esta stack não são acionadas: os
  adaptadores default de data do `sqlite3` exigem `detect_types`, que o projeto não usa
  (`database.py:10`), e `datetime.utcnow()` não é chamado em lugar algum — os timestamps vêm de
  `CURRENT_TIMESTAMP` no SQL. **Consequência para o plano:** TR-12 não é acionado por finding
  algum e **não é agendado em onda alguma**.

## Breaking changes propostas

Previstas na Fase 2 a partir do efeito de cada TR do plano sobre o contrato de resposta. Path,
verbo e status code de sucesso são preservados por regra; o que consta abaixo é mudança de forma
do corpo, mudança de status para o mesmo cenário, e remoção de endpoint.

| # | Endpoint | Mudança | Motivo | TR |
|---|---|---|---|---|
| BC-1 | `GET /usuarios`, `GET /usuarios/<id>` | O campo `senha` deixa de constar da resposta | Credencial não atravessa a fronteira de saída (F-006) | TR-04 |
| BC-2 | `GET /health` | Os campos `secret_key`, `debug`, `db_path` e `ambiente` deixam de constar | Segredo e configuração interna não atravessam a fronteira de saída (F-007) | TR-04 |
| BC-3 | `POST /admin/query` | **Endpoint removido** | Executa SQL arbitrário do corpo contra o banco; a superfície é o defeito (F-008) | TR-02 |
| BC-4 | `POST /admin/reset-db`, `GET /usuarios`, `GET /usuarios/<id>`, `GET /pedidos`, `GET /pedidos/usuario/<id>`, `PUT /pedidos/<id>/status`, `POST /produtos`, `PUT /produtos/<id>`, `DELETE /produtos/<id>`, `GET /relatorios/vendas` | Passam a responder `401` sem credencial válida | Rotas privilegiadas ou destrutivas sem verificação de identidade (F-002) | TR-05 |
| BC-5 | `POST /login` | A resposta deixa de trazer o registro do usuário e passa a trazer credencial assinada com expiração | Login precisa emitir algo apresentável na requisição seguinte (F-002) | TR-05 |
| BC-6 | `POST /login` | As senhas de seed em texto simples deixam de autenticar até serem reidratadas | Derivação lenta substitui a comparação por igualdade (F-004) | TR-03 |
| BC-7 | todos os 19 endpoints, no caminho de erro | Envelope de erro uniformizado, com código estável e sem a mensagem da exceção | Contrato de erro divergente entre handlers e vazamento de detalhe interno (F-015, F-017) | TR-13 |
| BC-8 | `POST /produtos`, `POST /login`, `GET /produtos/busca` | Entrada inválida passa a responder `4xx` onde hoje responde `500` | Erro de cliente deixa de ser reportado como falha de servidor (F-015) | TR-13 |
| BC-9 | `GET /produtos`, `GET /usuarios`, `GET /pedidos`, `GET /pedidos/usuario/<id>`, `GET /produtos/busca` | A resposta passa a trazer no máximo `N` itens, com envelope de paginação | Tamanho da resposta deixa de ser função dos dados (F-016) | TR-17 |
| BC-10 | `PUT /produtos/<id>` | Passa a rejeitar com `400` nome fora de 2–200 caracteres e categoria fora do vocabulário | A invariante passa a ser a mesma da criação, que hoje diverge (F-018) | TR-08 |
| BC-11 | `POST /usuarios` | Passa a rejeitar com `409` e-mail já cadastrado | `UNIQUE` declarado em `usuarios.email` (F-013) | TR-16 |

**Atenção para o smoke test.** BC-3 remove um endpoint do baseline e BC-4 altera o status de dez
outros; BC-6 quebra a chamada de login que o baseline registra com `joao@email.com`/`123456`.
São **doze dos 19 registros** do baseline afetados por mudança declarada. O critério de onda
verde (`M/M` com as divergências declaradas contando como conformes) continua valendo, mas o
roteiro de smoke precisará autenticar antes das rotas protegidas a partir da Onda 1 — este é
o falso vermelho mais provável desta execução.

## Plano de refatoração

### Onda 1 — CRITICAL

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-01 | F-003 | `config/`, `.env.example` | `app.py`, `database.py` | — |
| TR-02 | F-001, F-008 | — | `models.py`, `app.py` | — |
| TR-03 | F-004 | `security/` (derivação de senha) | `models.py`, `database.py`, `controllers.py` | — |
| TR-04 | F-006, F-007 | `dto/` (allowlist de projeção) | `models.py`, `controllers.py` | — |
| TR-05 | F-002, **F-021** | `middlewares/` (autenticação, limite de taxa) | `app.py`, `controllers.py` | — |
| TR-14 | F-005, **F-022** | `logging/` (logger com níveis e redação) | `controllers.py`, `app.py` | — |

TR-01 primeiro na onda, por criar a estrutura de que TR-03 e TR-05 dependem.
Critério de aceite: **smoke test 19/19 endpoints conformes → commit**.

### Onda 2 — HIGH

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-06 | F-011 | `repositories/`, `services/`, `controllers/`, `routes/` | todos | — |
| TR-09 | F-009, F-014 | — | `app.py` (composition root), `database.py`, `repositories/` | — |
| TR-07 | F-010 | `services/` (regra e efeitos) | `controllers/`, `repositories/` | — |
| TR-10 | F-012 | — | `services/`, `repositories/` | — |
| TR-16 | F-013 | `migrations/`, `seeds/` | `database.py` | — |

TR-06 primeiro na onda, por criar a estrutura de que TR-07, TR-09 e TR-10 dependem.
Critério de aceite: **smoke test 19/19 endpoints conformes → commit**.

### Onda 3 — MEDIUM

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-13 | F-015, F-017 | `middlewares/error_handler` | `controllers/`, `app.py` | — |
| TR-17 | F-016 | — | `controllers/`, `repositories/` | — |
| TR-08 | F-018 | `validators/` | `controllers/` | — |
| TR-11 | F-019 | — | `repositories/` | — |
| TR-18 | F-020, **F-024**, **F-023** | `constants/` | `app.py`, `services/`, `repositories/` | — |

Critério de aceite: **smoke test 19/19 endpoints conformes → commit**.

### Onda 4 — LOW

| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-15 | F-025 | — | `database.py`, `models.py` (ou seus sucessores após TR-06) | imports mortos |

Critério de aceite: **smoke test 19/19 endpoints conformes → commit**.

### Ondas vazias

**Nenhuma.** As quatro ondas receberam TR.

### TRs não agendados

- **TR-12** (substituir chamada deprecated) — AP-16 não produziu finding; nenhum TR é agendado
  sem finding que o acione.
- **AP-28 / F-026** não tem TR e não entra no plano, conforme o catálogo.

### Ajustes de onda aplicados, com justificativa

| TR | Teto (playbook) | Onda atribuída | Motivo |
|---|---|---|---|
| TR-06 | 1 | **2** | Teto fixado por AP-06, que não virou finding. O finding que aciona TR-06 é F-011 (AP-13, HIGH). Descida. |
| TR-08 | 2 | **3** | Teto fixado por AP-14, que não virou finding. O finding que aciona TR-08 é F-018 (AP-12, MEDIUM). Descida. |
| TR-14 | 1 | **1** | Teto fixado por AP-07, que **é** finding (F-005, CRITICAL). Permanece no teto; F-022 (AP-19, LOW) é resolvido de carona. |
| TR-05 | 1 | **1** | Teto fixado por AP-05, que **é** finding (F-002, CRITICAL). F-021 (AP-24, MEDIUM) é resolvido de carona. |
| TR-15 | 3 | **4** | Teto fixado por AP-17, que não virou finding. O finding que aciona TR-15 é F-025 (AP-26, LOW). Descida. |
| TR-18 | 3 | **3** | Teto fixado por AP-20, que **é** finding (F-020, MEDIUM). Permanece; F-023 e F-024 (LOW) de carona. |

### Risco conhecido do plano, para decisão no gate

O playbook adverte que aplicar TR-04 antes de existirem camadas obriga a refazê-lo. Neste plano
TR-04 está na Onda 1 (por F-006/F-007 serem CRITICAL) e TR-06 está na Onda 2 (por AP-06 não ter
virado finding). A regra de que a onda é propriedade do finding produz, portanto, **retrabalho
previsto** em TR-04: a allowlist de projeção criada na Onda 1 terá de ser realocada para a
camada de DTO que TR-06 cria na Onda 2. O plano mantém a ordem por severidade, que é a regra;
o retrabalho é o custo aceito e está sendo declarado aqui em vez de descoberto na Fase 3.

### Itens NEEDS-DECISION

Exigem decisão de produto que a skill não toma sozinha. Cada um traz a recomendação e a
alternativa, para que um único `y` continue sendo suficiente.

1. **Migração das senhas existentes (F-004).** *Recomendado:* reidratação no próximo login
   bem-sucedido — as contas de seed continuam funcionando até o primeiro login, quando a senha
   é derivada e regravada. *Alternativa:* invalidar todas as senhas e exigir redefinição, o que
   quebra as três contas de seed imediatamente.
2. **Destino de `POST /admin/reset-db` (F-002).** *Recomendado:* manter o endpoint atrás de
   autenticação de administrador (preserva a superfície, conforme BC-4). *Alternativa:* remover,
   como será feito com `/admin/query` — mas remoção não é exigida por nenhum finding aqui, já
   que o defeito é a ausência de verificação e não a funcionalidade.
3. **Visibilidade de `GET /usuarios` (F-002, F-006).** *Recomendado:* restringir a
   administradores. *Alternativa:* manter público apenas com `id` e `nome` projetados. A opção
   recomendada é mais restritiva e já está refletida em BC-4.
4. **Allowlist de origens do CORS (F-020).** *Recomendado:* lista vazia por default, populada
   por variável de ambiente — a aplicação sobe sem origem liberada. *Alternativa:* liberar
   `localhost` por default em ambiente de desenvolvimento.
5. **Tamanho de página default e máximo (F-016).** *Recomendado:* default 20, máximo 100.
   *Alternativa:* default 50, máximo 200.

## Fora do escopo desta skill

Observado, real, e a Fase 3 **não** vai corrigir:

- **Instalar test runner, linter e CI (F-026).** Fora do escopo declarado; reportado e não
  corrigido.
- **Rotação do segredo `minha-chave-super-secreta-123` no histórico do repositório (F-003).**
  Remover a linha não o remove dos commits anteriores; a rotação é operação de infraestrutura.
- **Política de retenção dos e-mails já emitidos em log (F-005).** Decisão de produto sobre
  dados pessoais já coletados.
- **Substituir SQLite por outro banco, ou `sqlite3` por um ORM.** Troca de banco e de mecanismo
  de persistência está fora do escopo declarado.
- **As três senhas fracas do seed (`admin123`, `123456`, `senha123`).** TR-16 separa o seed e
  TR-03 as deriva, mas a política de força de senha é decisão de produto.

## Próximo passo

Total: **26 findings** (8 CRITICAL · 6 HIGH · 7 MEDIUM · 5 LOW) ·
**11 breaking changes** propostas · plano em **4 ondas com TR** (vazias: nenhuma).

Nenhum arquivo do projeto foi modificado até aqui.

    Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
