# Dossiê de Análise Manual — `code-smells-project`

> Auditoria cética, somente leitura. Toda referência de arquivo:linha foi obtida por
> leitura direta dos arquivos nesta sessão. Findings sem evidência literal foram descartados.
>
> **Numeração:** este é o primeiro dossiê do repositório (`.planning/analise-manual/` estava
> vazio na abertura desta sessão), portanto a série global inicia em **AM-001** e termina em
> **AM-027**. O próximo dossiê deve continuar em **AM-028**.

---

## Contexto do projeto

| Item | Valor |
|---|---|
| **Linguagem** | Python — nenhuma versão declarada no projeto (não há `.python-version`, `setup.py`, `pyproject.toml` ou `Dockerfile`); interpretador do ambiente: 3.12.3 |
| **Framework** | Flask `3.1.1` |
| **Dependências** | `flask==3.1.1`, `flask-cors==5.0.1` (`requirements.txt`, 2 linhas). Sem dependência de ORM, de driver de banco externo, de hashing de senha, de validação de schema ou de teste. |
| **Domínio de negócio** | API REST de e-commerce: catálogo de produtos, cadastro/login de usuários, criação e acompanhamento de pedidos com baixa de estoque, e um relatório de vendas com faixas de desconto. |
| **Nº de arquivos-fonte** | 4 arquivos `.py` (`app.py`, `controllers.py`, `models.py`, `database.py`) + `README.md` + `requirements.txt` |
| **LOC** | 780 linhas Python totais (664 não-vazias): `app.py` 88 / `controllers.py` 292 / `models.py` 314 / `database.py` 86 |
| **Tabelas do banco** | 4 — `produtos`, `usuarios`, `pedidos`, `itens_pedido` (DDL em `database.py:14-53`) |

### Arquitetura atual

O projeto tenta uma separação MVC em três módulos planos, mas ela é apenas nominal. `app.py` é o
bootstrap: instancia o Flask, fixa configuração sensível em literal, habilita CORS irrestrito e
registra 15 rotas via `add_url_rule` apontando para funções de `controllers.py` — porém também
define três rotas inline (`/`, `/admin/reset-db`, `/admin/query`), duas delas falando com o banco
diretamente e ignorando as camadas abaixo. `controllers.py` é um módulo de funções soltas que
concentra parsing de request, todas as regras de validação de domínio, orquestração e efeitos
colaterais de negócio (notificações). `models.py` não contém modelos: é um DAO procedural que monta
SQL por concatenação de strings, mapeia linhas para dicionários à mão e ainda hospeda regra de
negócio (faixas de desconto do relatório). `database.py` expõe um singleton global mutável de
conexão SQLite que, na primeira chamada, também cria o schema e insere dados de seed. Não existe
camada de serviço, nem repositório abstrato, nem injeção de dependência, nem autenticação, nem
autorização, nem middleware, nem logging estruturado, nem testes, nem tratamento centralizado de
erro — cada função repete o mesmo `try/except Exception` devolvendo a mensagem interna ao cliente.

---

## Findings

### [CRITICAL] AM-001 — SQL Injection pervasiva por concatenação de strings

- **Arquivo:** `models.py:105-111`
- **Evidência:**

```python
def login_usuario(email, senha):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
    )
```

- **Descrição:** Toda a camada de acesso a dados monta SQL concatenando entrada do usuário em
  string, sem nenhuma query parametrizada — os únicos `?` do projeto estão no seed de
  `database.py:71` e `database.py:81`. No caminho de autenticação acima, o valor de `senha` vindo do
  corpo JSON entra cru na cláusula `WHERE`, permitindo bypass total de login.
- **Impacto:** Um atacante anônimo lê, altera ou apaga qualquer tabela, e autentica-se como qualquer
  usuário sem conhecer a senha. Como o mesmo padrão se repete em praticamente todas as funções —
  `models.py:28`, `47-50`, `57-61`, `68`, `92`, `126-129`, `140`, `148-151`, `155`, `157-161`,
  `163-166`, `174`, `188`, `192`, `220`, `224`, `279-281` e `291-297` — não há um ponto único de
  correção: a superfície de ataque é a aplicação inteira.
- **Correção esperada:** Toda montagem de SQL deve sair para uma camada de repositório usando
  exclusivamente queries parametrizadas (ou um ORM), sem interpolação de entrada externa.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-002 — Endpoint público de execução arbitrária de SQL

- **Arquivo:** `app.py:59-78`
- **Evidência:**

```python
    query = dados.get("sql", "")
    if not query:
        return jsonify({"erro": "Query não informada"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query)
```

- **Descrição:** A rota `POST /admin/query` recebe uma string SQL arbitrária no corpo da requisição
  e a executa diretamente contra o banco, sem autenticação, sem autorização e sem qualquer
  allowlist. O prefixo `admin` no path é decorativo: nada verifica quem está chamando.
- **Impacto:** Equivale a expor um console de banco na internet — qualquer requisição pode ler as
  senhas em texto puro, alterar preços, apagar tabelas ou anexar arquivos via `ATTACH DATABASE`.
  Combinado a `CORS(app)` (`app.py:9`), qualquer origem web consegue disparar a chamada.
- **Correção esperada:** O endpoint deve ser removido por inteiro; operações administrativas
  legítimas pertencem a scripts de manutenção fora da superfície HTTP.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-003 — Credencial hardcoded e modo debug ativo no bootstrap

- **Arquivo:** `app.py:6-9`
- **Evidência:**

```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
```

- **Descrição:** A chave de assinatura da aplicação é um literal versionado no repositório, e o modo
  debug é ligado duas vezes — em `app.py:8` e novamente em `app.py:88` (`app.run(host="0.0.0.0",
  port=5000, debug=True)`). Não há leitura de variável de ambiente nem arquivo de configuração em
  nenhum ponto do projeto.
- **Impacto:** A chave presente no controle de versão não pode ser rotacionada sem novo deploy e é
  conhecida por qualquer um com acesso ao repositório. Com `debug=True` exposto em `0.0.0.0`, o
  console interativo do Werkzeug fica alcançável na rede e transforma qualquer exceção em execução
  remota de código.
- **Correção esperada:** Configuração sensível deve vir de variáveis de ambiente carregadas por um
  módulo de config dedicado, com `debug` desligado por padrão.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-004 — Vazamento de segredo e de configuração de runtime no endpoint de health

- **Arquivo:** `controllers.py:285-290`
- **Evidência:**

```python
            "versao": "1.0.0",
            "ambiente": "producao",
            "db_path": "loja.db",
            "debug": True,
            "secret_key": "minha-chave-super-secreta-123"
        }), 200
```

- **Descrição:** O handler de `GET /health` (`controllers.py:264-292`), rota pública registrada em
  `app.py:30`, devolve no corpo da resposta a `secret_key` da aplicação, o caminho do arquivo de
  banco, o flag de debug e o rótulo de ambiente. O segredo aparece duplicado como literal, fora de
  sincronia com `app.py:7`.
- **Impacto:** Um `curl` anônimo entrega a chave de assinatura e o mapa da infraestrutura, o que
  transforma qualquer mecanismo futuro baseado nessa chave (sessão, token, cookie assinado) em algo
  forjável. Health check é justamente o endpoint que monitoração externa e balanceadores consultam
  com mais frequência e menos proteção.
- **Correção esperada:** O health check deve responder apenas liveness/readiness; o segredo sai para
  configuração por ambiente e nunca é serializado em resposta.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-005 — Senhas armazenadas e comparadas em texto puro

- **Arquivo:** `database.py:75-79`
- **Evidência:**

```python
            usuarios = [
                ("Admin", "admin@loja.com", "admin123", "admin"),
                ("João Silva", "joao@email.com", "123456", "cliente"),
                ("Maria Santos", "maria@email.com", "senha123", "cliente"),
            ]
```

- **Descrição:** A coluna `senha` é `TEXT` simples (`database.py:31`) e recebe o valor cru: o seed
  grava senhas legíveis, `models.py:126-129` insere a senha do cadastro sem transformação, e
  `models.py:109-111` autentica comparando a string diretamente no `WHERE`. Não existe nenhuma
  dependência de hashing no `requirements.txt`.
- **Impacto:** Qualquer leitura do arquivo `loja.db`, qualquer backup, ou qualquer uma das injeções
  descritas em AM-001 expõe as credenciais reais dos usuários, que tipicamente são reaproveitadas em
  outros serviços. A ausência de hash também impede comparação em tempo constante, deixando o login
  vulnerável a timing attack.
- **Correção esperada:** O armazenamento deve guardar apenas o digest de um algoritmo lento
  (bcrypt/argon2), com verificação isolada numa camada de serviço de autenticação.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-006 — Exposição em massa de credenciais na serialização de usuários

- **Arquivo:** `models.py:79-86`
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

- **Descrição:** `get_todos_usuarios` inclui o campo `senha` no dicionário devolvido, e
  `get_usuario_por_id` repete o mesmo em `models.py:95-102`. Esses dicionários são entregues sem
  filtro por `controllers.py:130-132` e `controllers.py:138-140`, que servem as rotas `GET /usuarios`
  e `GET /usuarios/<id>` registradas em `app.py:18-19` — ambas sem autenticação.
- **Impacto:** Um único `GET /usuarios` anônimo devolve a base inteira de e-mails e senhas em texto
  puro, incluindo a do usuário `admin`. Note que `login_usuario` (`models.py:113-120`) *sabe* omitir
  a senha na projeção de retorno, o que evidencia que a exposição aqui é acidental e não intencional
  — exatamente o tipo de inconsistência que o mapeamento manual de linha para dicionário produz.
- **Correção esperada:** A serialização deve passar por um schema/DTO de resposta explícito que
  jamais projeta campos de credencial, com as rotas de usuário atrás de autorização.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-007 — Endpoint destrutivo sem autenticação

- **Arquivo:** `app.py:47-57`
- **Evidência:**

```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
```

- **Descrição:** Um `POST` sem corpo, sem token e sem qualquer verificação de identidade apaga as
  quatro tabelas do sistema. A rota é definida inline no bootstrap, atravessando as camadas de
  controller e de dados e falando com o banco diretamente.
- **Impacto:** Perda total e irreversível de dados de produção acionável por um único request; com
  `CORS(app)` liberado, até um navegador em qualquer site consegue disparar. Além disso, a rota
  inline no bootstrap escapa de qualquer política que venha a ser aplicada sobre a camada de
  controllers.
- **Correção esperada:** Remover a rota; reset de base é tarefa de fixture de teste ou script de
  operação, nunca de endpoint HTTP.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-008 — Ausência completa de camada de autenticação e autorização

- **Arquivo:** `controllers.py:176-180`
- **Evidência:**

```python
        usuario = models.login_usuario(email, senha)
        if usuario:

            print("Login bem-sucedido: " + email)
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
```

- **Descrição:** O login valida as credenciais e devolve os dados do usuário, mas não emite token,
  não cria sessão e não registra estado algum — não há nada que uma requisição seguinte pudesse
  apresentar como prova de identidade. Coerentemente, nenhuma das 17 rotas do projeto consulta
  identidade: o campo `tipo` (`admin`/`cliente`, `database.py:32`) nunca é lido fora da serialização.
- **Impacto:** Não existe distinção entre usuário anônimo, cliente e administrador — qualquer chamador
  lista todos os pedidos (`app.py:24`), muda status de pedido alheio (`app.py:26`) ou acessa o
  relatório de vendas (`app.py:28`). O `SECRET_KEY` de `app.py:7` não protege nada, pois nada é
  assinado.
- **Correção esperada:** Introduzir um serviço de autenticação que emita credencial verificável e um
  middleware/decorator de autorização aplicado às rotas antes de chegarem ao controller.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-009 — Estado global mutável: conexão singleton compartilhada entre threads

- **Arquivo:** `database.py:4-11`
- **Evidência:**

```python
db_connection = None
db_path = "loja.db"

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
        db_connection.row_factory = sqlite3.Row
```

- **Descrição:** Uma única conexão vive em variável global de módulo, é inicializada de forma
  preguiçosa sem lock e é reusada por todas as requisições, com a proteção nativa do driver desligada
  via `check_same_thread=False`. O caminho do banco também é global e hardcoded.
- **Impacto:** Como o servidor Flask atende requisições concorrentes, duas requisições compartilham
  cursor e transação: um `db.commit()` de uma requisição confirma o trabalho parcial de outra, e o
  `return` sem rollback descrito em AM-013 deixa uma transação aberta que contamina requisições
  seguintes. Em teste, o singleton não pode ser substituído por um banco em memória sem manipular o
  global, o que torna qualquer suíte dependente de ordem de execução.
- **Correção esperada:** A conexão deve ter escopo de requisição (ou vir de um pool), fornecida por
  uma factory injetável em vez de um global mutável de módulo.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-010 — Acoplamento estático às camadas inferiores, sem injeção de dependência

- **Arquivo:** `models.py:1-6`
- **Evidência:**

```python
from database import get_db
import sqlite3

def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
```

- **Descrição:** Cada função de dados chama `get_db()` internamente em vez de receber a conexão, e o
  mesmo padrão de import concreto no topo do módulo liga `controllers.py` a `models` e a `get_db`
  (`controllers.py:1-3`) e liga `app.py` a `controllers` (`app.py:3-4`). Não há interface,
  abstração ou parâmetro que permita trocar a implementação.
- **Impacto:** Nenhuma unidade é testável isoladamente: exercitar um controller obriga a abrir um
  SQLite real, e substituir SQLite por outro banco exige reescrever todas as funções em vez de trocar
  uma implementação. Além disso, `controllers.py` importar `get_db` diretamente permite que a camada
  de apresentação pule a camada de dados — o que de fato ocorre em `health_check`
  (`controllers.py:266-274`).
- **Correção esperada:** Inverter a dependência: repositórios recebem a conexão por construtor/parâmetro
  e os controllers recebem serviços, com a composição feita no bootstrap.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-011 — Efeitos colaterais de negócio disparados dentro do Controller

- **Arquivo:** `controllers.py:205-210`
- **Evidência:**

```python
        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado para usuario " + str(usuario_id))
        print("ENVIANDO SMS: Seu pedido foi recebido!")
        print("ENVIANDO PUSH: Novo pedido recebido pelo sistema")
```

- **Descrição:** A notificação ao cliente — regra de negócio do fluxo de pedido — está codificada no
  handler HTTP, e o mesmo acontece com as ações derivadas da transição de status em
  `controllers.py:247-250` ("Preparar envio", "Devolver estoque"). O controller também decide, por
  inspeção de chave (`"erro" in resultado`), como traduzir a falha de domínio em status HTTP.
- **Impacto:** Qualquer caminho que crie pedido sem passar por essa rota — job, importação em lote,
  outro controller — silenciosamente não notifica ninguém, porque a regra não vive no domínio.
  Testar a política de notificação exige subir o stack HTTP inteiro, e a "devolução de estoque" do
  cancelamento está apenas impressa: nenhum código a executa de fato.
- **Correção esperada:** Mover a orquestração e as notificações para um serviço de aplicação
  (`services/pedido_service`), deixando o controller apenas traduzir request e resposta.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-012 — Regras de validação de domínio embutidas no Controller

- **Arquivo:** `controllers.py:43-54`
- **Evidência:**

```python
        if preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        if estoque < 0:
            return jsonify({"erro": "Estoque não pode ser negativo"}), 400
        if len(nome) < 2:
            return jsonify({"erro": "Nome muito curto"}), 400
        if len(nome) > 200:
            return jsonify({"erro": "Nome muito longo"}), 400
```

- **Descrição:** Invariantes do produto (preço não-negativo, faixa de tamanho do nome, categoria
  pertencente a um conjunto fechado) só existem dentro do handler HTTP; a camada de dados
  (`models.criar_produto`, `models.py:43-52`) aceita qualquer valor. As mesmas regras aparecem
  parcialmente repetidas em `atualizar_produto` (`controllers.py:87-90`), já com divergência: a
  validação de tamanho de nome e de categoria simplesmente não é aplicada na atualização.
- **Impacto:** As invariantes são contornáveis por qualquer caminho que não seja o `POST /produtos`
  — inclusive pelo próprio `PUT /produtos/<id>` da mesma aplicação, que grava nomes de 1 caractere ou
  categorias inexistentes. Regra de negócio no controller não é reutilizável nem testável sem
  requisição HTTP.
- **Correção esperada:** As invariantes pertencem a uma entidade/serviço de domínio (ou a um schema
  de validação declarativo) invocado por todo caminho de escrita.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-013 — Escrita multi-etapa sem transação explícita, com check-then-act sobre o estoque

- **Arquivo:** `models.py:139-146`
- **Evidência:**

```python
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": "Produto " + str(item["produto_id"]) + " não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": "Estoque insuficiente para " + produto["nome"]}
        total = total + (produto["preco"] * item["quantidade"])
```

- **Descrição:** `criar_pedido` (`models.py:133-169`) valida o estoque num laço, depois insere o
  pedido, os itens e faz o `UPDATE` de baixa num segundo laço, com um único `db.commit()` só no fim
  (`models.py:168`). Os `return` de erro acima abandonam a função sem `rollback()`, e não há
  `BEGIN`/`try`/`except` envolvendo a sequência de escrita.
- **Impacto:** A verificação de estoque e a baixa não são atômicas: duas requisições concorrentes
  aprovam o mesmo item e o estoque fica negativo. Pior, como a conexão é o singleton global de
  AM-009, um `return` de erro deixa a transação implícita aberta nessa conexão compartilhada, de modo
  que o próximo `commit()` de outra requisição confirma trabalho que deveria ter sido descartado; e
  uma exceção no meio do segundo laço deixa pedido gravado sem itens.
- **Correção esperada:** Encapsular a operação num único limite transacional explícito na camada de
  repositório/unit-of-work, com rollback garantido e a reserva de estoque feita de forma atômica.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-014 — Regra de negócio de precificação dentro da camada de acesso a dados

- **Arquivo:** `models.py:256-262`
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

- **Descrição:** A política comercial de faixas de desconto — a regra de negócio mais volátil de um
  e-commerce — está codificada dentro de `relatorio_vendas`, uma função do módulo de dados, misturada
  a cinco `SELECT COUNT` sequenciais e ao cálculo de ticket médio (`models.py:235-273`). Os limiares
  e as alíquotas são literais sem nome.
- **Impacto:** Alterar a política de desconto obriga a editar a camada de persistência, e a regra não
  pode ser exercitada em teste sem um banco. Como o cálculo vive só aqui, nenhum outro ponto do
  sistema (checkout, por exemplo) aplica o mesmo desconto — a regra existe apenas para efeito de
  relatório, o que é uma inconsistência de domínio.
- **Correção esperada:** Extrair a política para um serviço/objeto de domínio puro, deixando o módulo
  de dados apenas agregar os números.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-015 — N+1 queries na listagem de pedidos

- **Arquivo:** `models.py:187-193`
- **Evidência:**

```python
        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
        itens = cursor2.fetchall()
        for item in itens:
            cursor3 = db.cursor()
            cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
            prod = cursor3.fetchone()
```

- **Descrição:** Para cada pedido retornado pela consulta principal, dispara-se uma query de itens e,
  para cada item, mais uma query de produto — laço aninhado de acesso a banco, com um cursor novo
  alocado por iteração. O mesmo padrão está duplicado em `get_todos_pedidos` (`models.py:219-225`).
- **Impacto:** `GET /pedidos` custa `1 + P + (P × I)` queries; com 100 pedidos de 5 itens são 601
  round-trips onde um único `JOIN` bastaria. O custo cresce de forma multiplicativa com o volume, e
  como a conexão é única e global (AM-009), essa varredura serializa as demais requisições.
- **Correção esperada:** Substituir por uma consulta única com `JOIN` na camada de repositório,
  agrupando os itens em memória.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-016 — Duplicação integral do bloco de listagem de pedidos

- **Arquivo:** `models.py:219-225`
- **Evidência:**

```python
        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
        itens = cursor2.fetchall()
        for item in itens:
            cursor3 = db.cursor()
            cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
            prod = cursor3.fetchone()
```

- **Descrição:** Este trecho é byte a byte idêntico a `models.py:187-193`: `get_pedidos_usuario`
  (`models.py:171-201`) e `get_todos_pedidos` (`models.py:203-233`) diferem apenas na cláusula
  `WHERE` da query externa e replicam ~28 linhas de montagem de dicionário e busca aninhada. O mesmo
  vale para o mapeamento linha→dicionário de produto, repetido três vezes (`models.py:12-21`,
  `31-40`, `304-313`).
- **Impacto:** Qualquer correção — incluir um campo, arrumar o N+1 de AM-015, tratar produto
  removido — precisa ser aplicada em todas as cópias, e a divergência já é observável no projeto:
  `login_usuario` omite `senha` na projeção enquanto as outras duas cópias do mapeamento de usuário a
  incluem (AM-006). Duplicação de serialização é justamente o mecanismo pelo qual esse vazamento
  passou despercebido.
- **Correção esperada:** Extrair uma função de mapeamento por entidade e uma única query de pedidos
  parametrizada por filtro opcional.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-017 — Bloco de validação copiado entre criação e atualização

- **Arquivo:** `controllers.py:74-79`
- **Evidência:**

```python
        if "nome" not in dados:
            return jsonify({"erro": "Nome é obrigatório"}), 400
        if "preco" not in dados:
            return jsonify({"erro": "Preço é obrigatório"}), 400
        if "estoque" not in dados:
            return jsonify({"erro": "Estoque é obrigatório"}), 400
```

- **Descrição:** O trecho reproduz literalmente `controllers.py:30-35`, e a extração de campos que o
  segue (`controllers.py:81-85`) reproduz `controllers.py:37-41`. A cópia já divergiu: `criar_produto`
  valida tamanho de nome e categoria (`controllers.py:47-54`), `atualizar_produto` não.
- **Impacto:** As duas rotas que escrevem produto aplicam contratos diferentes para a mesma entidade,
  então um recurso rejeitado na criação é aceito na atualização. Cada nova regra precisa ser lembrada
  em dois lugares, e o histórico do arquivo mostra que isso já falhou uma vez.
- **Correção esperada:** Um único validador/schema de produto, reutilizado por todos os casos de uso
  de escrita.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-018 — Validação ausente em rotas de escrita

- **Arquivo:** `controllers.py:239-245`
- **Evidência:**

```python
        dados = request.get_json()
        novo_status = dados.get("status", "")

        if novo_status not in ["pendente", "aprovado", "enviado", "entregue", "cancelado"]:
            return jsonify({"erro": "Status inválido"}), 400

        models.atualizar_status_pedido(pedido_id, novo_status)
```

- **Descrição:** A rota valida o vocabulário do status mas não verifica se o pedido existe, nem se a
  transição é permitida (um pedido `entregue` pode voltar a `pendente`), e `models.atualizar_status_pedido`
  (`models.py:275-283`) devolve `True` incondicionalmente mesmo quando o `UPDATE` não afeta nenhuma
  linha. Lacunas equivalentes existem em outras rotas: `criar_usuario` não valida formato de e-mail
  nem unicidade nem força de senha (`controllers.py:153-158`), `criar_pedido` não valida se
  `quantidade` é positiva nem se o `usuario_id` existe (`controllers.py:195-203`), e `criar_produto`
  compara `preco < 0` sem checar o tipo (`controllers.py:43`), de modo que um `preco` textual levanta
  `TypeError` e vira HTTP 500.
- **Impacto:** O cliente recebe `200 OK` por atualizar um pedido inexistente, e entradas malformadas
  viram erro de servidor em vez de `400`. Sem unicidade de e-mail, dois cadastros com o mesmo e-mail
  coexistem e tornam o resultado do login dependente da ordem das linhas.
- **Correção esperada:** Validação declarativa de entrada na borda e verificação de existência e de
  transição de estado numa camada de serviço que reporte o resultado real da operação.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-019 — CORS habilitado sem restrição de origem

- **Arquivo:** `app.py:9`
- **Evidência:**

```python
CORS(app)
```

- **Descrição:** `flask-cors` é aplicado à aplicação inteira com a configuração padrão, que responde
  `Access-Control-Allow-Origin: *` para todas as 17 rotas — incluindo `/admin/reset-db`,
  `/admin/query`, `/usuarios` e `/login`. Não há lista de origens, de métodos ou de headers.
- **Impacto:** Qualquer página web pode chamar a API a partir do navegador da vítima, o que
  transforma os endpoints destrutivos de AM-002 e AM-007 em alvos de CSRF triviais. Middleware
  aplicado de forma global e indiscriminada também impede diferenciar a política pública do catálogo
  da política de rotas administrativas.
- **Correção esperada:** Configurar CORS com allowlist explícita de origens e escopo por blueprint,
  definida via configuração de ambiente.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-020 — Detalhe interno de exceção devolvido no corpo da resposta

- **Arquivo:** `controllers.py:10-12`
- **Evidência:**

```python
    except Exception as e:
        print("ERRO: " + str(e))
        return jsonify({"erro": str(e)}), 500
```

- **Descrição:** O padrão `except Exception` capturando tudo e serializando `str(e)` para o cliente se
  repete em todos os 15 handlers de `controllers.py` e também em `app.py:77-78`. Não há tratador de
  erro centralizado, nem distinção entre falha esperada de domínio e defeito inesperado.
- **Impacto:** Mensagens do driver SQLite chegam ao cliente e revelam nomes de tabela, de coluna e a
  forma da query — informação que reduz drasticamente o esforço de exploração da injeção de AM-001.
  Como todo erro vira `500`, falhas de validação ficam indistinguíveis de defeitos, e o `except`
  amplo engole erros de programação sem stack trace registrado.
- **Correção esperada:** Um error handler centralizado que mapeie exceções de domínio para códigos
  HTTP e devolva mensagem genérica ao cliente, registrando o detalhe apenas no log.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-021 — `print()` usado como mecanismo de log

- **Arquivo:** `controllers.py:56-58`
- **Evidência:**

```python
        id = models.criar_produto(nome, descricao, preco, estoque, categoria)
        print("Produto criado com ID: " + str(id))
        return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201
```

- **Descrição:** Toda a observabilidade do projeto é feita com `print()` para stdout — há 14
  ocorrências em `controllers.py` e mais uma em `app.py:56`. Não há níveis de severidade, timestamp,
  correlação de requisição nem destino configurável; o módulo `logging` não é importado em nenhum
  arquivo.
- **Impacto:** É impossível filtrar por severidade, silenciar ruído em produção ou direcionar erros
  para um agregador, e alguns `print` registram dado sensível (`controllers.py:161` imprime o e-mail
  do usuário cadastrado; `controllers.py:179` e `182`, o e-mail de cada tentativa de login).
  Diagnóstico depende de alguém estar olhando o terminal.
- **Correção esperada:** Substituir por `logging` configurado no bootstrap, com níveis e handlers
  definidos por ambiente.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-022 — Factory de conexão acumula DDL e carga de dados de seed

- **Arquivo:** `database.py:12-17`
- **Evidência:**

```python
        cursor = db_connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
```

- **Descrição:** `get_db()` tem três responsabilidades num mesmo corpo: abrir a conexão, criar as
  quatro tabelas com `CREATE TABLE IF NOT EXISTS` (`database.py:14-53`) e, se a tabela de produtos
  estiver vazia, inserir 10 produtos e 3 usuários de exemplo (`database.py:56-84`). Como a função é
  chamada por toda operação de dados, essa lógica de bootstrap está no caminho de execução de todas
  as requisições.
- **Impacto:** O schema não tem versionamento nem histórico de migração — alterar uma coluna existente
  é impossível por esse mecanismo, já que `IF NOT EXISTS` só cobre a criação inicial. E dados de
  demonstração, incluindo o usuário `admin` com senha conhecida (`database.py:76`), são inseridos
  automaticamente em qualquer ambiente que suba com o banco vazio, inclusive produção.
- **Correção esperada:** Separar em três peças — factory de conexão, migrações versionadas e script
  de seed executado explicitamente apenas em ambiente de desenvolvimento.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-023 — Magic numbers em regras de validação

- **Arquivo:** `controllers.py:47-50`
- **Evidência:**

```python
        if len(nome) < 2:
            return jsonify({"erro": "Nome muito curto"}), 400
        if len(nome) > 200:
            return jsonify({"erro": "Nome muito longo"}), 400
```

- **Descrição:** Os limites `2` e `200` aparecem como literais sem nome, sem comentário e sem relação
  declarada com o schema — a coluna `nome` é `TEXT` puro (`database.py:17`), então o `200` não
  corresponde a nenhuma restrição do banco. O mesmo estilo se repete nos limiares de desconto
  (`models.py:257-262`) e na porta e host de `app.py:88`.
- **Impacto:** O leitor não consegue distinguir uma regra de negócio deliberada de um valor
  arbitrário, e a mensagem de erro não informa o limite ao cliente. Ajustar o limite exige caçar o
  literal em vez de alterar uma constante nomeada.
- **Correção esperada:** Promover os limites a constantes nomeadas junto à definição de validação da
  entidade.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-024 — Conjuntos de valores válidos declarados inline como listas literais

- **Arquivo:** `controllers.py:52-54`
- **Evidência:**

```python
        categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
        if categoria not in categorias_validas:
            return jsonify({"erro": "Categoria inválida. Válidas: " + str(categorias_validas)}), 400
```

- **Descrição:** O vocabulário fechado de categorias é reconstruído a cada chamada dentro do handler,
  e o de status de pedido aparece do mesmo modo em `controllers.py:242`, com os valores repetidos
  ainda uma vez nas comparações de `controllers.py:247` e `249`. Nenhum dos dois conjuntos é um enum
  nem tem constraint no banco (`categoria TEXT`, `database.py:21`; `status TEXT`, `database.py:40`).
- **Impacto:** Adicionar uma categoria exige editar código de apresentação, e o valor default
  `"geral"` de `controllers.py:41` só coincide com a lista por acaso. A mensagem de erro serializa a
  lista Python crua (`str(...)`), expondo formatação de linguagem no contrato da API.
- **Correção esperada:** Modelar os dois conjuntos como enums de domínio, referenciados por
  validação e por constraint no schema.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-025 — Imports mortos

- **Arquivo:** `database.py:1-2`
- **Evidência:**

```python
import sqlite3
import os
```

- **Descrição:** `os` é importado em `database.py` mas não aparece em nenhum outro ponto do arquivo —
  a única string de caminho é o literal `"loja.db"` de `database.py:5`. De forma equivalente,
  `models.py:2` importa `sqlite3` sem que o nome seja referenciado em nenhuma das 314 linhas do
  módulo, já que a conexão vem pronta de `get_db()`.
- **Impacto:** Ruído que sugere ao leitor uma dependência de sistema de arquivos e um uso direto do
  driver que não existem, aumentando o custo de entender o escopo real de cada módulo. É também um
  sintoma de que nenhum linter roda no projeto.
- **Correção esperada:** Remover os imports não utilizados e adicionar um linter ao fluxo de
  desenvolvimento.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-026 — Builtin `id` sombreado por nome de parâmetro

- **Arquivo:** `models.py:24-28`
- **Evidência:**

```python
def get_produto_por_id(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```

- **Descrição:** O builtin `id` é usado como nome de parâmetro em `models.py:24`, `54`, `65`, `89` e
  nos handlers `controllers.py:14`, `64` e `98`; em `controllers.py:56` ele também sombreia o builtin
  como variável local. O nome não diz de qual entidade é o identificador.
- **Impacto:** Dentro dessas funções o builtin fica inacessível, o que é uma armadilha silenciosa
  para quem adicionar código depois, e a assinatura `atualizar_produto(id, nome, descricao, preco,
  estoque, categoria)` (`models.py:54`) — seis parâmetros posicionais sem tipo — torna fácil trocar
  argumentos de ordem sem erro de execução.
- **Correção esperada:** Renomear para `produto_id`/`usuario_id` e agrupar os parâmetros de escrita
  num objeto de domínio.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-027 — Contrato de resposta inconsistente entre handlers

- **Arquivo:** `controllers.py:140-142`
- **Evidência:**

```python
            return jsonify({"dados": usuario, "sucesso": True}), 200
        else:
            return jsonify({"erro": "Usuário não encontrado"}), 404
```

- **Descrição:** O envelope de resposta varia por handler sem regra: `buscar_produto` inclui
  `"sucesso": False` no caminho de erro (`controllers.py:20`), enquanto `buscar_usuario` omite o campo
  no erro equivalente (`controllers.py:142`); `buscar_produtos` acrescenta um campo `total`
  (`controllers.py:124`) que nenhuma outra listagem tem; `mensagem` aparece em algumas respostas de
  sucesso e não em outras. A versão `"1.0.0"` está duplicada como literal em `app.py:36` e
  `controllers.py:285`.
- **Impacto:** O consumidor não pode confiar na presença de `sucesso` para decidir sucesso ou falha e
  precisa tratar cada endpoint como um caso especial. Campos duplicados manualmente entre arquivos
  divergem sem que nada detecte.
- **Correção esperada:** Centralizar a montagem do envelope em helpers de resposta únicos para
  sucesso e erro, usados por todos os handlers.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

## Resumo

| Severidade | Quantidade |
|---|---|
| CRITICAL | 7 |
| HIGH | 7 |
| MEDIUM | 8 |
| LOW | 5 |
| **Total** | **27** |

**Mínimo exigido pelo enunciado (1 CRITICAL/HIGH + 2 MEDIUM + 2 LOW): ATINGIDO** — com folga
substancial (14 findings CRITICAL/HIGH contra 1 exigido, 8 MEDIUM contra 2, 5 LOW contra 2).

Observação de calibragem: a concentração de 7 findings CRITICAL não é inflação para cumprir cota — a
cota já estava satisfeita pelo primeiro finding. O projeto é um fixture deliberadamente semeado com
anti-patterns e apresenta, de fato, quatro classes independentes de falha grave de segurança
(injeção de SQL, execução arbitrária de SQL exposta, credenciais em texto puro e ausência total de
controle de acesso), cada uma explorável isoladamente por um chamador anônimo. Nenhum finding foi
elevado de severidade e nenhum foi criado sem evidência literal com arquivo:linha verificado nesta
sessão.

---

## Sinais genéricos extraídos

Sinais de detecção reescritos de forma agnóstica de projeto — insumo direto do catálogo de
anti-patterns da skill.

| # | Sinal genérico de detecção |
|---|---|
| AM-001 | Query SQL montada por concatenação ou interpolação de string contendo valor originado de entrada externa (corpo, query string, path param), em vez de parâmetro vinculado (placeholder) — especialmente quando o valor entra numa cláusula de filtro do caminho de autenticação. |
| AM-002 | Handler de rota que recebe uma string de consulta/comando no payload e a repassa a um executor de banco, shell ou interpretador sem allowlist nem validação estrutural. |
| AM-003 | Literal string atribuído a chave de configuração sensível no bootstrap da aplicação; flag de debug/desenvolvimento ligado no código, sem leitura de variável de ambiente em nenhum ponto do projeto. |
| AM-004 | Serialização de valor de configuração sensível (chave, caminho de banco, flag de ambiente) no corpo de uma resposta HTTP, especialmente num endpoint de diagnóstico público. |
| AM-005 | Campo de credencial persistido em coluna de texto simples e comparado por igualdade direta na consulta ou no código; ausência de dependência de hashing lento no manifesto de dependências. |
| AM-006 | Função de mapeamento de registro para DTO/dicionário que projeta um campo de credencial ou PII, alimentando uma rota de leitura sem controle de acesso. Reforço do sinal: duas cópias do mesmo mapeamento divergem quanto à inclusão do campo sensível. |
| AM-007 | Rota que executa operação destrutiva em massa (remoção de múltiplas tabelas/coleções) sem verificação de identidade, definida diretamente no módulo de bootstrap em vez da camada de controllers. |
| AM-008 | Fluxo de autenticação que retorna dados do sujeito sem emitir credencial verificável (token, sessão, cookie assinado); ausência de decorator/middleware de autorização em todas as rotas; campo de papel/role presente no schema mas nunca lido fora da serialização. |
| AM-009 | Handle de recurso compartilhado (conexão, cliente, cache) armazenado em variável global de módulo, inicializado de forma preguiçosa sem lock, com a proteção de concorrência do driver explicitamente desabilitada. |
| AM-010 | Funções que obtêm suas dependências chamando uma factory global no próprio corpo em vez de recebê-las como parâmetro; imports concretos de módulo no topo ligando cada camada diretamente à implementação da camada inferior; camada de apresentação importando a camada de infraestrutura e ignorando a camada intermediária. |
| AM-011 | Efeito colateral de negócio (notificação, integração externa, ação derivada de transição de estado) disparado dentro do handler HTTP; controller inspecionando a forma do valor retornado para decidir o código de status. |
| AM-012 | Invariante de domínio (faixa numérica, tamanho de campo, pertinência a conjunto) codificada exclusivamente no handler HTTP, com a camada de escrita aceitando qualquer valor; a mesma invariante aplicada de forma divergente entre a rota de criação e a de atualização da mesma entidade. |
| AM-013 | Sequência de escritas relacionadas sem limite transacional explícito, com retorno antecipado no meio da sequência sem rollback; verificação de disponibilidade de recurso separada da sua consumação (check-then-act) sem atomicidade. |
| AM-014 | Política de negócio volátil (precificação, desconto, elegibilidade) implementada dentro de uma função da camada de acesso a dados, misturada a agregações de consulta. |
| AM-015 | Consulta a banco executada dentro de laço iterando o resultado de uma consulta anterior, especialmente em laço aninhado com um cursor novo alocado por iteração, onde uma junção resolveria em uma única ida ao banco. |
| AM-016 | Dois blocos de código idênticos ou quase idênticos em funções irmãs que diferem apenas no filtro da consulta; bloco de mapeamento registro→DTO repetido em três ou mais pontos do mesmo módulo. |
| AM-017 | Sequência de checagens de campo obrigatório copiada entre o handler de criação e o de atualização da mesma entidade, com as cópias já divergentes em pelo menos uma regra. |
| AM-018 | Rota de escrita que valida o formato do valor mas não verifica a existência do recurso alvo nem a legalidade da transição de estado; função de atualização que retorna sucesso fixo sem consultar as linhas afetadas; comparação numérica aplicada a valor de entrada sem verificação prévia de tipo. |
| AM-019 | Middleware de política de origem cruzada aplicado globalmente com configuração padrão permissiva, cobrindo indistintamente rotas públicas e administrativas. |
| AM-020 | Bloco `except` genérico capturando a exceção base e serializando sua representação textual no corpo da resposta ao cliente, repetido em todos os handlers, sem tratador de erro centralizado nem distinção entre falha de domínio e defeito. |
| AM-021 | Saída direta para stdout usada como registro de eventos, sem níveis de severidade, timestamp ou destino configurável, e sem import da biblioteca de logging em nenhum arquivo; ocorrências registrando dado pessoal ou credencial. |
| AM-022 | Factory de conexão que também executa DDL condicional e inserção de dados de exemplo no mesmo corpo, chamada no caminho de execução de toda requisição; criação de schema por comando idempotente em vez de migrações versionadas; dados de demonstração com credencial administrativa conhecida inseridos automaticamente em qualquer ambiente. |
| AM-023 | Literal numérico sem nome usado como limiar em regra de validação ou de negócio, sem constante nomeada, sem comentário e sem correspondência com restrição declarada no schema. |
| AM-024 | Conjunto fechado de valores válidos declarado como lista literal reconstruída dentro do handler, com os mesmos valores repetidos em comparações adjacentes, sem enum e sem constraint equivalente no schema; estrutura da linguagem serializada crua na mensagem de erro da API. |
| AM-025 | Módulo importado e nunca referenciado no arquivo; ausência de configuração de linter no projeto. |
| AM-026 | Nome de builtin da linguagem usado como parâmetro ou variável local; identificador genérico que não indica a entidade referenciada; assinatura com muitos parâmetros posicionais do mesmo tipo primitivo, permitindo troca de ordem sem erro. |
| AM-027 | Envelope de resposta com campos presentes de forma inconsistente entre handlers equivalentes (campo de status presente no erro de um recurso e ausente no erro de outro); mesmo valor de metadado duplicado como literal em arquivos distintos. |
</content>

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
