# Dossiê de Análise Manual — `task-manager-api`

> Auditoria cética, somente leitura. Toda referência de arquivo:linha foi obtida por leitura direta
> dos arquivos nesta sessão e reconferida com `sed -n` contra o intervalo citado. Findings sem
> evidência literal foram descartados.
>
> **Numeração:** os dossiês anteriores encerraram em **AM-027** (`code-smells-project`) e **AM-049**
> (`ecommerce-api-legacy`). Esta série inicia em **AM-050** e termina em **AM-075**. O próximo
> dossiê deve continuar em **AM-076**.

---

## Contexto do projeto

| Item | Valor |
|---|---|
| **Linguagem** | Python — nenhuma versão declarada no projeto (não há `.python-version`, `pyproject.toml`, `setup.cfg` ou `Dockerfile`); interpretador do ambiente: 3.12.3 |
| **Framework** | Flask `3.0.0` com Flask-SQLAlchemy `3.1.1` (ORM) e Flask-CORS `4.0.0` |
| **Dependências** | 6 declaradas em `requirements.txt`. Três são efetivamente usadas (`flask`, `flask-sqlalchemy`, `flask-cors`); `marshmallow`, `requests` e `python-dotenv` não são importadas em nenhum arquivo do projeto. Sem dependência de teste, de lint ou de migração. |
| **Domínio de negócio** | Gerenciador de tarefas: CRUD de tasks com status, prioridade, prazo e tags; CRUD de usuários com papéis (`user`/`admin`/`manager`) e login; CRUD de categorias; e relatórios de produtividade e de tarefas atrasadas. |
| **Nº de arquivos-fonte** | 15 arquivos `.py` (incluindo 4 `__init__.py`, sendo 3 vazios). Distribuídos em `models/` (3 + init), `routes/` (3 + init), `services/` (1 + init), `utils/` (1 + init), mais `app.py`, `database.py` e `seed.py`. |
| **LOC** | 1.158 linhas Python totais (969 não-vazias). Maiores: `routes/task_routes.py` 299 / `routes/report_routes.py` 223 / `routes/user_routes.py` 211 / `utils/helpers.py` 116 / `seed.py` 99 |
| **Tabelas do banco** | 3 — `users`, `tasks`, `categories`, declaradas como models SQLAlchemy (`models/user.py:6`, `models/task.py:6`, `models/category.py:5`). Banco SQLite em arquivo (`sqlite:///tasks.db`, `app.py:11`), com chaves estrangeiras declaradas em `models/task.py:13-14`. |

### Arquitetura atual

Este é o projeto mais estruturado dos três auditados: existe separação física em `models/`,
`routes/`, `services/` e `utils/`, os blueprints do Flask são usados corretamente, o acesso a dados
passa por um ORM com relacionamentos declarados, e há um script de seed isolado. O problema é que a
estrutura é em boa parte **fachada**: as camadas existem no sistema de arquivos, mas a lógica não as
respeita. Os três módulos de rotas concentram validação de domínio, regras de negócio, serialização
manual e chamadas diretas a `db.session`, sem nenhuma camada de serviço entre a rota e o ORM. A
camada `services/` contém uma única classe que **nunca é importada por ninguém**, e o módulo
`utils/helpers.py` — que contém um validador completo, sete constantes nomeadas e funções de
formatação — é **integralmente código morto**: suas duas únicas funções importadas
(`report_routes.py:7`) jamais são chamadas. Os models declaram métodos de domínio (`is_overdue`,
`validate_status`, `validate_priority`, `is_admin`) que também nunca são invocados, enquanto as rotas
reimplementam essas mesmas regras inline. Não há autenticação real, migrações, paginação, testes,
lint nem configuração por ambiente.

### Observação de disciplina de auditoria — o que NÃO foi encontrado

**Não há SQL Injection.** Todo o acesso a dados usa a API de query do SQLAlchemy com parâmetros
vinculados; a única construção de filtro a partir de entrada do usuário é
`Task.title.like(f'%{query}%')` (`task_routes.py:252`), onde a f-string monta o *valor* do padrão
`LIKE`, que o ORM envia como parâmetro vinculado — não é concatenação em SQL. Também **não há God
Class**: diferente de `ecommerce-api-legacy`, aqui roteamento, models e persistência estão em
arquivos distintos. Nenhum finding foi registrado nessas duas categorias, apesar de ambas constarem
explicitamente na escala de severidade do desafio.

---

## Findings

### [CRITICAL] AM-050 — Senhas protegidas por MD5 sem salt

- **Arquivo:** `models/user.py:27-32`
- **Evidência:**

```python
    def set_password(self, pwd):

        self.password = hashlib.md5(pwd.encode()).hexdigest()

    def check_password(self, pwd):
        return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

- **Descrição:** A derivação de senha usa MD5, um algoritmo rápido e criptograficamente quebrado, sem
  salt e sem fator de custo. A comparação em `check_password` é feita com `==` sobre a string
  hexadecimal, o que também não é uma comparação em tempo constante.
- **Impacto:** MD5 sem salt é diretamente reversível por rainbow tables públicas para qualquer senha
  comum, e o hardware moderno calcula bilhões de MD5 por segundo, tornando o brute-force de toda a
  base viável em minutos. Sem salt, dois usuários com a mesma senha produzem o mesmo hash, o que
  entrega ao atacante quais contas compartilham credencial antes mesmo de quebrar qualquer uma delas.
  A política de senha vigente agrava o quadro: o mínimo é de 4 caracteres (`user_routes.py:64`).
- **Correção esperada:** Substituir por uma função de derivação de chave lenta e com salt
  (bcrypt/argon2/scrypt), encapsulada num serviço de autenticação em vez de no model.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-051 — Serialização do model expõe o hash de senha em todas as respostas

- **Arquivo:** `models/user.py:16-25`
- **Evidência:**

```python
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }
```

- **Descrição:** O método de serialização do model inclui o campo `password` — o hash MD5 — e é
  usado sem filtro em cinco pontos que respondem ao cliente: `GET /users/<id>`
  (`user_routes.py:33`), `POST /users` (`user_routes.py:85`), `PUT /users/<id>`
  (`user_routes.py:129`), o relatório por usuário e, o mais grave, a resposta de login
  (`user_routes.py:209`).
- **Impacto:** Qualquer requisição anônima a `GET /users/<id>` devolve o hash da senha do usuário
  — que, sendo MD5 sem salt (AM-050), equivale a devolver a senha em texto puro para qualquer valor
  comum. O login é o caso mais absurdo: o endpoint entrega ao chamador o material de credencial da
  conta que ele acabou de acessar, ampliando o dano de qualquer log de tráfego, cache de proxy ou
  histórico de navegador.
- **Correção esperada:** A serialização de resposta deve passar por um schema/DTO explícito que nunca
  projeta campo de credencial, separado do model de persistência.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-052 — Chave secreta hardcoded e debug ativo em interface pública

- **Arquivo:** `app.py:11-15`
- **Evidência:**

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super-secret-key-123'

CORS(app)
```

- **Descrição:** A chave de assinatura da aplicação é um literal versionado no repositório, ao lado
  da URI do banco, sem nenhuma leitura de variável de ambiente em nenhum dos 15 arquivos do projeto.
  O servidor sobe com `app.run(debug=True, host='0.0.0.0', port=5000)` (`app.py:34`), ou seja, o modo
  de depuração fica exposto em todas as interfaces de rede.
- **Impacto:** A chave no controle de versão não pode ser rotacionada sem novo deploy e é conhecida
  por qualquer um com acesso ao repositório. Com `debug=True` alcançável de fora, o console
  interativo do Werkzeug transforma qualquer exceção não tratada em execução remota de código — e este
  projeto tem vários caminhos que lançam exceção não tratada (ver AM-064). Note a ironia: a
  dependência `python-dotenv` está declarada em `requirements.txt:6` justamente para resolver isso, e
  nunca é importada.
- **Correção esperada:** Toda configuração sensível deve vir de variáveis de ambiente carregadas por
  um módulo de configuração dedicado, com `debug` desligado por padrão.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-053 — Credenciais de SMTP hardcoded no serviço de notificação

- **Arquivo:** `services/notification_service.py:5-10`
- **Evidência:**

```python
    def __init__(self):
        self.notifications = []
        self.email_host = 'smtp.gmail.com'
        self.email_port = 587
        self.email_user = 'taskmanager@gmail.com'
        self.email_password = 'senha123'
```

- **Descrição:** Host, porta, usuário e senha da conta de e-mail estão fixados como literais no
  construtor da classe, usados diretamente em `server.login(self.email_user, self.email_password)`
  (`notification_service.py:17`). Não há leitura de ambiente nem parâmetro de configuração.
- **Impacto:** A credencial de uma conta de e-mail real está versionada e permite a qualquer leitor
  do repositório enviar mensagens em nome da aplicação — vetor direto de phishing contra a própria
  base de usuários, cujos e-mails o projeto também expõe (AM-051). Agrava o caso o fato de a classe
  inteira ser código morto: uma verificação por `grep` nesta sessão confirmou que `NotificationService`
  **não é importado por nenhum arquivo do projeto**, de modo que o segredo está exposto sem sequer
  entregar função.
- **Correção esperada:** Credenciais de integração devem vir de variáveis de ambiente injetadas no
  serviço pelo composition root, nunca fixadas no construtor.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [CRITICAL] AM-054 — Token de autenticação falso e previsível, sem nenhuma rota que o valide

- **Arquivo:** `routes/user_routes.py:207-211`
- **Evidência:**

```python
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': 'fake-jwt-token-' + str(user.id)
    }), 200
```

- **Descrição:** O login devolve uma string que apenas concatena um prefixo fixo ao id do usuário —
  não é um JWT, não é assinado, não expira e não carrega claim algum. Nenhuma das 22 rotas do projeto
  verifica esse token: não há decorator de autenticação, `before_request` ou middleware em lugar
  nenhum, e o `SECRET_KEY` de `app.py:13` não assina coisa alguma.
- **Impacto:** O token é forjável por qualquer pessoa que saiba contar — `fake-jwt-token-1` é o
  administrador semeado — mas isso é academicamente irrelevante, porque nenhuma rota o exige: um
  chamador anônimo lista todos os usuários, altera o papel de qualquer conta para `admin`
  (`user_routes.py:119-122`) ou deleta um usuário e todas as suas tasks. O campo `role` e o método
  `User.is_admin()` existem no domínio mas nunca são consultados em decisão de acesso.
- **Correção esperada:** Emitir credencial assinada e verificável num serviço de autenticação, com um
  decorator/middleware de autorização por papel aplicado antes dos handlers.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-055 — Regra de domínio reimplementada no controller seis vezes, com o método do model existente e nunca chamado

- **Arquivo:** `routes/task_routes.py:30-37`
- **Evidência:**

```python
            if t.due_date:
                if t.due_date < datetime.utcnow():
                    if t.status != 'done' and t.status != 'cancelled':
                        task_data['overdue'] = True
                    else:
                        task_data['overdue'] = False
                else:
                    task_data['overdue'] = False
```

- **Descrição:** A definição de "tarefa atrasada" — data limite vencida e status diferente de `done`
  e `cancelled` — é uma regra de negócio copiada literalmente em seis pontos das rotas:
  `task_routes.py:30-39`, `task_routes.py:71-80`, `task_routes.py:284-287`,
  `user_routes.py:171-180`, `report_routes.py:34-37` e `report_routes.py:132-135`. O model já
  implementa exatamente essa regra em `Task.is_overdue()` (`models/task.py:50-60`), método que,
  confirmado por `grep` nesta sessão, **nunca é chamado em lugar algum**.
- **Impacto:** Mudar a definição de atraso — por exemplo, passar a considerar um período de carência
  ou incluir um novo status terminal — exige localizar e alterar seis cópias, e a sétima
  implementação (a do model) ficaria silenciosamente divergente. Regra de negócio dentro do handler
  também não é testável sem subir o stack HTTP, embora aqui exista uma versão no model que seria
  trivialmente testável e está sendo ignorada.
- **Correção esperada:** As rotas devem delegar ao método de domínio já existente no model, ou a um
  serviço que o encapsule, eliminando as seis cópias inline.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-056 — Regras de validação de domínio embutidas nos handlers de rota

- **Arquivo:** `routes/task_routes.py:110-114`
- **Evidência:**

```python
    if status not in ['pending', 'in_progress', 'done', 'cancelled']:
        return jsonify({'error': 'Status inválido'}), 400

    if priority < 1 or priority > 5:
        return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
```

- **Descrição:** As invariantes do domínio — vocabulário de status, faixa de prioridade, tamanho de
  título, papéis válidos, política de senha — vivem exclusivamente dentro dos handlers HTTP, escritas
  como sequências de `if` com literais inline. O projeto possui **três** implementações concorrentes
  dessas mesmas regras que não são usadas: `Task.validate_status` e `Task.validate_priority`
  (`models/task.py:38-48`), a função `process_task_data` (`utils/helpers.py:57-108`) e as constantes
  `VALID_STATUSES`/`MAX_TITLE_LENGTH`/`MIN_TITLE_LENGTH` (`utils/helpers.py:110-116`).
- **Impacto:** As invariantes só são aplicadas por quem passar pela rota certa, e nada impede que
  `seed.py` ou um futuro job grave um status fora do vocabulário — o schema também não restringe
  (`status = db.Column(db.String(50)`, `models/task.py:11`). Existir quatro definições da mesma regra
  no mesmo repositório, três delas mortas, é a condição perfeita para que uma correção seja aplicada
  no lugar errado e pareça não ter efeito.
- **Correção esperada:** Consolidar as invariantes numa única camada de validação declarativa
  (a dependência `marshmallow` já está declarada em `requirements.txt:4` e nunca é usada), invocada
  por todo caminho de escrita.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [HIGH] AM-057 — Rotas acopladas diretamente ao ORM e à sessão global, sem camada de serviço

- **Arquivo:** `routes/task_routes.py:146-154`
- **Evidência:**

```python
    try:
        db.session.add(task)
        db.session.commit()
        print(f"Task criada: {task.id} - {task.title}")
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar task: {str(e)}")
        return jsonify({'error': 'Erro ao criar task'}), 500
```

- **Descrição:** Os handlers manipulam a sessão do SQLAlchemy diretamente — `db.session.add`,
  `commit`, `rollback`, `delete` — e constroem queries com `Model.query` espalhadas por todo o
  módulo, sem nenhuma camada de serviço ou repositório entre a rota e o ORM. O diretório `services/`
  existe mas contém apenas uma classe morta, e `db` é importado como singleton de módulo
  (`from database import db`) em todos os arquivos, sem injeção.
- **Impacto:** Nenhum caso de uso é testável sem instanciar o Flask e um banco real, e não há ponto
  onde inserir uma transação que abranja mais de um handler ou substituir a persistência por um duplo
  de teste. O acoplamento é bidirecional e sutil: o model expõe `to_dict()` para uso da camada HTTP
  (AM-051), então a decisão de serialização de API vive na camada de persistência, e a decisão de
  transação vive na camada de apresentação — exatamente invertido.
- **Correção esperada:** Introduzir uma camada de serviço que receba um repositório por injeção,
  deixando os handlers apenas traduzindo request e resposta.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-058 — N+1 pervasivo apesar de os relacionamentos estarem declarados

- **Arquivo:** `routes/task_routes.py:41-48`
- **Evidência:**

```python
            if t.user_id:
                user = User.query.get(t.user_id)
                if user:
                    task_data['user_name'] = user.name
                else:
                    task_data['user_name'] = None
            else:
                task_data['user_name'] = None
```

- **Descrição:** Para cada task listada, o handler dispara uma query de usuário e outra de categoria
  (`task_routes.py:50-57`), embora `models/task.py:20-21` já declare
  `db.relationship('User', backref='tasks')` e o equivalente para categoria — os relacionamentos
  existem e são ignorados. O mesmo padrão aparece em `user_routes.py:22` (`len(u.tasks)` dispara um
  lazy load por usuário), em `report_routes.py:56` (uma query de tasks por usuário) e em
  `report_routes.py:163` (um `count` por categoria).
- **Impacto:** `GET /tasks` custa `1 + 2N` queries; com 500 tasks são 1.001 idas ao banco onde um
  `joinedload` resolveria em uma. O custo cresce linearmente e nenhum dos quatro endpoints afetados
  tem paginação (AM-060), então a degradação é ilimitada.
- **Correção esperada:** Usar eager loading sobre os relacionamentos já declarados
  (`joinedload`/`selectinload`) numa camada de repositório, eliminando as consultas por item.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-059 — Agregações calculadas em Python sobre a tabela inteira em vez de em SQL

- **Arquivo:** `routes/report_routes.py:30-37`
- **Evidência:**

```python
    all_tasks = Task.query.all()
    overdue_count = 0
    overdue_list = []
    for t in all_tasks:
        if t.due_date:
            if t.due_date < datetime.utcnow():
                if t.status != 'done' and t.status != 'cancelled':
                    overdue_count = overdue_count + 1
```

- **Descrição:** O relatório carrega **todas** as tasks para a memória do processo apenas para contar
  as atrasadas, quando a condição é expressável em `WHERE`. O mesmo endpoint ainda emite 12 queries
  `COUNT` separadas para status e prioridade (`report_routes.py:19-28`) onde um único `GROUP BY`
  bastaria, e `task_routes.py:281-287` repete a varredura completa para o mesmo cálculo.
- **Impacto:** O consumo de memória do endpoint cresce com o tamanho da tabela inteira, não com o
  tamanho do resultado, e uma base de algumas centenas de milhares de tasks derruba o processo por
  esgotamento. Somando as contagens, a varredura completa e o N+1 de produtividade por usuário
  (AM-058), o `GET /reports/summary` é o endpoint mais caro do sistema e não tem cache nem limite.
- **Correção esperada:** Expressar as agregações como consultas SQL com filtro e `GROUP BY` numa
  camada de repositório, retornando apenas os números.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-060 — Ausência de paginação em todos os endpoints de listagem

- **Arquivo:** `routes/task_routes.py:266-271`
- **Evidência:**

```python
    results = tasks.all()
    output = []
    for t in results:
        output.append(t.to_dict())

    return jsonify(output), 200
```

- **Descrição:** Nenhum dos endpoints de listagem aceita `limit`/`offset` ou cursor: `GET /tasks`
  (`task_routes.py:14`), `GET /tasks/search`, `GET /users` (`user_routes.py:12`),
  `GET /users/<id>/tasks`, `GET /categories` e o relatório de resumo devolvem o conjunto completo.
  A busca aceita filtros opcionais, mas sem nenhum deles retorna a tabela inteira.
- **Impacto:** O tamanho da resposta é ilimitado e determinado pelos dados, não pelo contrato, o que
  torna o tempo de resposta imprevisível e permite que um único `GET /tasks` sature memória e banda.
  Vale registrar que o próprio seed do projeto contém uma task descrevendo este defeito —
  `'Adicionar paginação na API'`, `seed.py:70` — o que indica que é uma dívida conhecida e não um
  descuido de leitura minha.
- **Correção esperada:** Paginação obrigatória com limite máximo aplicada na camada de repositório,
  com metadados de página no envelope de resposta.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-061 — Serialização manual nas rotas duplicando o `to_dict()` do model

- **Arquivo:** `routes/task_routes.py:18-25`
- **Evidência:**

```python
            task_data['id'] = t.id
            task_data['title'] = t.title
            task_data['description'] = t.description
            task_data['status'] = t.status
            task_data['priority'] = t.priority
            task_data['user_id'] = t.user_id
            task_data['category_id'] = t.category_id
            task_data['created_at'] = str(t.created_at)
```

- **Descrição:** O handler remonta campo a campo um dicionário que `Task.to_dict()`
  (`models/task.py:23-36`) já produz de forma idêntica, e o mesmo acontece em
  `user_routes.py:162-169` com um subconjunto diferente dos campos. Outros handlers do mesmo arquivo
  — `task_routes.py:69`, `150`, `220`, `269` — usam `to_dict()` normalmente.
- **Impacto:** O mesmo recurso é serializado de três formas diferentes conforme o endpoint:
  `GET /tasks` inclui `user_name` e `category_name`, `GET /tasks/search` não os inclui, e
  `GET /users/<id>/tasks` omite `user_id`, `category_id`, `updated_at` e `tags`. Adicionar um campo
  ao model exige lembrar de três lugares, e o consumidor não pode assumir uma forma estável para
  "uma task".
- **Correção esperada:** Uma única função de serialização por entidade (schema/DTO), usada por todos
  os endpoints, com variações expressas por parâmetro explícito.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-062 — Validação duplicada entre criação e atualização, com regex de e-mail repetido

- **Arquivo:** `routes/user_routes.py:105-111`
- **Evidência:**

```python
    if 'email' in data:
        if not re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', data['email']):
            return jsonify({'error': 'Email inválido'}), 400

        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Email já cadastrado'}), 409
```

- **Descrição:** O mesmo padrão de e-mail aparece literalmente três vezes no projeto —
  `user_routes.py:61`, `user_routes.py:106` e `utils/helpers.py:21` (esta última dentro de
  `validate_email`, função nunca chamada). O bloco de validação de título, status e prioridade
  também é reescrito entre `create_task` (`task_routes.py:96-114`) e `update_task`
  (`task_routes.py:166-184`), e as cópias já divergem: a criação valida a existência de `user_id` e
  `category_id` de forma diferente da atualização.
- **Impacto:** Corrigir o regex — que hoje aceita `a@b`, sem exigir TLD — obriga a alterar três
  lugares, e a cópia morta em `helpers.py` permaneceria divergente sem que nada acuse. Divergências
  entre o validador de criação e o de atualização produzem o defeito clássico de recurso rejeitado
  num endpoint e aceito no outro.
- **Correção esperada:** Um único schema de validação por entidade, reutilizado por todos os casos de
  uso de escrita.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-063 — `except:` nu engolindo qualquer exceção sem registro

- **Arquivo:** `routes/task_routes.py:61-63`
- **Evidência:**

```python
        return jsonify(result), 200
    except:
        return jsonify({'error': 'Erro interno'}), 500
```

- **Descrição:** O bloco captura **toda** exceção, incluindo `KeyboardInterrupt` e `SystemExit`, e
  descarta o objeto de erro sem log nem rastro. O padrão se repete em nove pontos do projeto:
  `task_routes.py:62`, `137`, `204`, `236`; `user_routes.py:130`, `149`;
  `report_routes.py:186`, `207`, `221`; e mais dois em `utils/helpers.py:46` e `49`.
- **Impacto:** Um defeito de programação dentro do laço de serialização vira um `500` genérico
  indistinguível de uma falha de banco, sem stack trace em lugar algum — o diagnóstico fica
  impossível em produção. Nos casos de `helpers.py:46-49`, o `except` nu ainda mascara um erro de
  parsing devolvendo `None`, que o chamador interpreta como "data inválida", escondendo a causa real.
- **Correção esperada:** Capturar exceções específicas, registrar o erro com stack trace via logger
  estruturado, e delegar a tradução para status HTTP a um error handler centralizado do Flask.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-064 — Entrada não validada produz erro 500 em vez de 400

- **Arquivo:** `routes/task_routes.py:257-264`
- **Evidência:**

```python
    if status:
        tasks = tasks.filter(Task.status == status)

    if priority:
        tasks = tasks.filter(Task.priority == int(priority))

    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))
```

- **Descrição:** Os parâmetros de query são convertidos com `int()` sem `try/except` e sem validação
  prévia, de modo que `?priority=alta` levanta `ValueError` não tratada. O mesmo tipo de falha existe
  em `create_task`, onde `if priority < 1` (`task_routes.py:113`) compara um valor vindo do JSON sem
  checar o tipo — um `priority` textual levanta `TypeError` fora de qualquer bloco `try` — e em
  `update_category` (`report_routes.py:196-197`), que acessa `data` sem o guard `if not data` que
  todos os handlers irmãos possuem.
- **Impacto:** Erros de cliente são reportados como falha de servidor, o que polui métricas de
  disponibilidade e impede o consumidor de distinguir "corrija sua requisição" de "tente mais tarde".
  Com `debug=True` exposto (AM-052), essas exceções não tratadas renderizam o traceback interativo do
  Werkzeug ao chamador.
- **Correção esperada:** Coerção e validação de tipo declarativas na borda da rota, devolvendo `400`
  com mensagem de campo antes de qualquer acesso ao banco.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-065 — Política de deleção inconsistente entre entidades, deixando referências órfãs

- **Arquivo:** `routes/report_routes.py:217-220`
- **Evidência:**

```python
    try:
        db.session.delete(cat)
        db.session.commit()
        return jsonify({'message': 'Categoria deletada'}), 200
```

- **Descrição:** A deleção de categoria remove apenas a linha da categoria, sem tocar nas tasks que a
  referenciam por `category_id` (`models/task.py:14`) e sem `cascade` declarado no relacionamento
  (`models/task.py:21`). A deleção de usuário, no mesmo projeto, faz exatamente o oposto: apaga
  manualmente todas as tasks do usuário num laço (`user_routes.py:140-142`).
- **Impacto:** Após deletar uma categoria, as tasks ficam apontando para um id inexistente e
  `GET /tasks` passa a devolver `category_name: null` sem qualquer sinal de que houve perda de
  integridade — o SQLite não impõe chave estrangeira por padrão, então nada bloqueia. A
  inconsistência entre as duas políticas é o problema maior: um mesmo sistema apaga dados em cascata
  numa entidade e produz órfãos noutra, sem que a diferença esteja documentada ou seja intencional.
- **Correção esperada:** Definir a política de deleção explicitamente no relacionamento do ORM
  (`cascade` ou `SET NULL`) e centralizar a remoção num caso de uso transacional único por entidade.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-066 — `print()` como mecanismo de log, com helper de logging disponível e ignorado

- **Arquivo:** `routes/user_routes.py:82-83`
- **Evidência:**

```python
        db.session.commit()
        print(f"Usuário criado: {user.id} - {user.name}")
```

- **Descrição:** A observabilidade se resume a chamadas de `print` espalhadas pelos handlers —
  `task_routes.py:149`, `153`, `219`, `234`; `user_routes.py:83`, `89`, `147`; além das do
  `seed.py` e do serviço morto. Não há níveis de severidade, timestamp, correlação de requisição nem
  destino configurável, e o módulo `logging` não é importado em nenhum arquivo do projeto.
- **Impacto:** Não há como filtrar por severidade, silenciar ruído ou direcionar erros a um
  agregador, e os caminhos de falha mais importantes (os `except:` nus de AM-063) não registram nada.
  O projeto até define `log_action` em `utils/helpers.py:36-41` para padronizar isso — função que,
  como todo o módulo, nunca é chamada.
- **Correção esperada:** Adotar `logging` configurado no bootstrap, com níveis e handlers definidos
  por ambiente, injetado onde for necessário.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-067 — CORS habilitado sem restrição de origem

- **Arquivo:** `app.py:15-16`
- **Evidência:**

```python
CORS(app)
db.init_app(app)
```

- **Descrição:** O Flask-CORS é aplicado à aplicação inteira com a configuração padrão, que responde
  `Access-Control-Allow-Origin: *` para todas as 22 rotas, sem allowlist de origens, de métodos ou de
  headers. Isso cobre indistintamente `GET /users`, `PUT /users/<id>` e `DELETE /users/<id>`.
- **Impacto:** Qualquer página web pode chamar a API a partir do navegador da vítima. Como não existe
  autenticação alguma (AM-054), isso significa que um site arbitrário consegue promover uma conta a
  `admin` ou deletar usuários e suas tasks com um único `fetch`.
- **Correção esperada:** Configurar CORS com allowlist explícita de origens e escopo por blueprint,
  definida via configuração de ambiente.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [MEDIUM] AM-068 — Schema criado no import da aplicação, sem migrações

- **Arquivo:** `app.py:30-31`
- **Evidência:**

```python
with app.app_context():
    db.create_all()
```

- **Descrição:** A criação do schema é um efeito colateral de nível de módulo, executado no import de
  `app.py` — inclusive quando `seed.py` o importa (`seed.py:2`). Não há Alembic nem Flask-Migrate no
  `requirements.txt`, e `create_all()` só cria tabelas ausentes: nunca altera uma coluna existente.
- **Impacto:** Evoluir o schema — mudar um tipo, adicionar um `NOT NULL`, criar um índice — é
  impossível por esse mecanismo, e o banco de um ambiente já rodando ficará silenciosamente
  desatualizado em relação aos models sem que nada acuse. Efeito colateral no import também significa
  que qualquer ferramenta que apenas importe o módulo (um runner de teste, um linter que execute
  código) toca o banco.
- **Correção esperada:** Extrair o schema para migrações versionadas executadas por comando
  explícito, removendo o efeito colateral do import.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-069 — Módulo utilitário inteiro é código morto, incluindo o validador e as constantes que resolveriam outros findings

- **Arquivo:** `utils/helpers.py:110-116`
- **Evidência:**

```python
VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'
```

- **Descrição:** Uma verificação por `grep` nesta sessão confirmou que **nenhum** dos 16 símbolos
  públicos de `utils/helpers.py` é usado fora do próprio arquivo. Os únicos dois importados,
  `format_date` e `calculate_percentage` (`report_routes.py:7`), jamais são chamados — o mesmo
  arquivo recalcula percentual à mão em `report_routes.py:67` e `151`, e formata datas com `str()`.
- **Impacto:** São 116 linhas que aparentam ser a camada de padronização do projeto e não padronizam
  nada, o que induz quem for refatorar a acreditar que as constantes já estão em uso. O custo real é
  a divergência: `MAX_TITLE_LENGTH = 200` e o literal `200` em `task_routes.py:99` e `169` são o
  mesmo valor em três lugares que podem se separar a qualquer momento, e `process_task_data`
  (`helpers.py:57-108`) é um validador completo e coerente competindo com a validação inline das
  rotas (AM-056).
- **Correção esperada:** Ou passar a usar o módulo nas rotas, ou removê-lo — manter as duas
  implementações é a única opção que não deve permanecer.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-070 — Camada de serviço existe no sistema de arquivos e nunca é usada

- **Arquivo:** `services/notification_service.py:43-48`
- **Evidência:**

```python
    def get_notifications(self, user_id):
        result = []
        for n in self.notifications:
            if n['user_id'] == user_id:
                result.append(n)
        return result
```

- **Descrição:** `NotificationService` — 48 linhas com envio de e-mail, notificação de atribuição de
  task e notificação de atraso — não é importado por nenhum arquivo do projeto, conforme `grep`
  executado nesta sessão. `models/__init__.py`, que reexporta os três models, também nunca é
  importado: todos os consumidores usam o caminho completo (`from models.task import Task`).
- **Impacto:** A existência do diretório `services/` sugere uma arquitetura em camadas que na prática
  não é exercida por nenhum caminho de execução (AM-057), o que torna a leitura da estrutura
  enganosa. O acumulador `self.notifications` (`notification_service.py:6`) seria ainda um estado
  em memória por instância, perdido a cada restart e invisível entre workers, caso a classe chegasse
  a ser usada.
- **Correção esperada:** Remover o código morto ou conectá-lo de fato ao fluxo de atribuição de
  tarefa através da camada de serviço.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-071 — Métodos de domínio declarados nos models e nunca invocados

- **Arquivo:** `models/task.py:38-43`
- **Evidência:**

```python
    def validate_status(self, new_status):
        valid = ['pending', 'in_progress', 'done', 'cancelled']
        if new_status in valid:
            return True
        else:
            return False
```

- **Descrição:** `Task.validate_status`, `Task.validate_priority` (`models/task.py:45-48`),
  `Task.is_overdue` (`models/task.py:50-60`) e `User.is_admin` (`models/user.py:34-38`) são
  definidos e, conforme `grep` nesta sessão, nunca chamados. Os quatro seguem ainda o padrão
  `if cond: return True else: return False`, que é a própria condição escrita de forma verbosa.
- **Impacto:** O domínio parece rico mas é anêmico na prática — a regra que esses métodos expressam
  está reimplementada nas rotas (AM-055, AM-056), e a existência deles mascara essa duplicação numa
  leitura superficial. `User.is_admin()` é o caso mais revelador: o projeto modela o conceito de
  administrador e nunca o consulta em decisão alguma, o que confirma a ausência de autorização
  (AM-054).
- **Correção esperada:** Passar a usar os métodos de domínio a partir da camada de serviço, ou
  removê-los se a regra for consolidada noutro lugar.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-072 — Imports não utilizados em todos os módulos

- **Arquivo:** `app.py:5-7`
- **Evidência:**

```python
from routes.user_routes import user_bp
from routes.report_routes import report_bp
import os, sys, json, datetime
```

- **Descrição:** Em `app.py`, dos quatro módulos importados na linha 7 apenas `datetime` é usado
  (linha 24); `os`, `sys` e `json` não aparecem em nenhum outro ponto do arquivo. O mesmo ocorre em
  `routes/task_routes.py:7` (`json, os, sys, time` — nenhum usado), `routes/user_routes.py:6`
  (`hashlib` e `json` não usados), `routes/report_routes.py:8` (`json` não usado) e
  `models/task.py:3` (`json` não usado). Todos foram verificados por `grep` nesta sessão.
- **Impacto:** Imports agrupados numa linha só, no estilo `import os, sys, json`, contrariam a
  convenção da linguagem e escondem quais dependências o módulo realmente tem, dificultando avaliar o
  impacto de mover código entre camadas. É também sintoma de que nenhum linter roda no projeto —
  não há configuração de lint, teste ou CI em lugar algum.
- **Correção esperada:** Remover os imports não utilizados e adicionar um linter ao fluxo de
  desenvolvimento.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-073 — Dependências declaradas e nunca importadas

- **Arquivo:** `requirements.txt:1-6`
- **Evidência:**

```
flask==3.0.0
flask-sqlalchemy==3.1.1
flask-cors==4.0.0
marshmallow==3.20.1
requests==2.31.0
python-dotenv==1.0.0
```

- **Descrição:** Metade das dependências declaradas não é importada por nenhum arquivo do projeto:
  `marshmallow`, `requests` e `python-dotenv`. As três correspondem exatamente a lacunas
  identificadas em outros findings — validação declarativa (AM-056), cliente HTTP para o gateway que
  não existe, e carga de configuração por ambiente (AM-052).
- **Impacto:** O manifesto descreve uma arquitetura pretendida que o código não implementa, o que
  aumenta a superfície de vulnerabilidade e o tempo de build sem entregar nada. Para quem for
  refatorar, é sinal útil de intenção, mas hoje é apenas peso morto no ambiente.
- **Correção esperada:** Remover as dependências não usadas, ou usá-las para resolver as lacunas
  correspondentes.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-074 — Magic numbers e mapeamento de domínio hardcoded na serialização do relatório

- **Arquivo:** `routes/report_routes.py:83-89`
- **Evidência:**

```python
        'tasks_by_priority': {
            'critical': p1,
            'high': p2,
            'medium': p3,
            'low': p4,
            'minimal': p5,
        },
```

- **Descrição:** A tradução de prioridade numérica para nome de negócio — `1` é `critical`, `5` é
  `minimal` — existe apenas aqui, embutida na montagem do dicionário de resposta, e as contagens vêm
  de cinco variáveis `p1`..`p5` obtidas por cinco queries separadas (`report_routes.py:24-28`). O
  mesmo vocabulário implícito reaparece como o limiar `if t.priority <= 2` para "alta prioridade"
  (`report_routes.py:129`), sem nenhuma relação declarada entre os dois lugares.
- **Impacto:** Adicionar um sexto nível de prioridade exige alterar a validação de faixa em quatro
  handlers, criar uma sexta query e uma sexta chave neste dicionário, sem que nada indique que esses
  pontos estão relacionados. As constantes que dariam nome a esses valores existem em
  `utils/helpers.py:112-116` e não são usadas (AM-069).
- **Correção esperada:** Modelar prioridade como enum de domínio com rótulo associado, e obter as
  contagens por `GROUP BY` em vez de cinco variáveis numeradas.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

### [LOW] AM-075 — Verificação de tipo por comparação de classe em vez de `isinstance`

- **Arquivo:** `routes/task_routes.py:140-144`
- **Evidência:**

```python
    if tags:
        if type(tags) == list:
            task.tags = ','.join(tags)
        else:
            task.tags = tags
```

- **Descrição:** O teste `type(x) == list` compara a classe exata em vez de usar `isinstance`,
  padrão que se repete em `task_routes.py:210` e `utils/helpers.py:103`. O `else` também aceita
  silenciosamente qualquer outro tipo — um dicionário ou um número vira o valor da coluna `tags` sem
  validação.
- **Impacto:** A comparação exata rejeita subclasses de `list` e qualquer sequência que não seja
  exatamente uma lista, e o ramo `else` grava lixo no banco sem erro. Some-se a isso o uso de nomes de
  variável de uma letra nos laços (`t`, `u`, `c`, `n`) por todos os módulos de rota, e a redundância
  de `task.updated_at = datetime.utcnow()` (`task_routes.py:215`) quando a coluna já declara
  `onupdate=datetime.utcnow` (`models/task.py:16`).
- **Correção esperada:** Usar `isinstance` com rejeição explícita dos tipos não suportados, dentro do
  schema de validação de entrada.
- **Confiança:** ALTA
- **Status de validação:** `✅ validado`

---

## Resumo

| Severidade | Quantidade |
|---|---|
| CRITICAL | 4 |
| HIGH | 4 |
| MEDIUM | 11 |
| LOW | 7 |
| **Total** | **26** |

**Mínimo exigido pelo enunciado (1 CRITICAL/HIGH + 2 MEDIUM + 2 LOW): ATINGIDO** — 8 findings
CRITICAL/HIGH contra 1 exigido, 11 MEDIUM contra 2, 7 LOW contra 2.

**Nota de calibragem.** A cota já estava satisfeita pelo primeiro finding, então nenhuma severidade
foi elevada por pressão de quota. Quatro decisões merecem registro para a validação humana:

1. **Nenhum finding de SQL Injection nem de God Class**, apesar de ambas as categorias constarem
   explicitamente na escala. Todo o acesso a dados passa pelo ORM com parâmetros vinculados, e a
   separação em `models/`/`routes/`/`services/`/`utils/` é real no nível de arquivo. Registrar
   qualquer das duas aqui seria erro de auditoria.
2. **O perfil de severidade mudou de forma significativa em relação aos outros dois projetos.** Este
   tem menos CRITICAL (4, contra 7 e 4) mas muito mais MEDIUM (11). Isso é coerente com o que o
   projeto é: a estrutura correta existe, e a maior parte dos defeitos está em não a exercer —
   duplicação, N+1, código morto e padronização, não catástrofe de segurança.
3. **AM-069, AM-070 e AM-071 (código morto) foram classificados LOW** seguindo a escala, que coloca
   "código morto" em LOW. Registro a ressalva de que, neste projeto específico, esses três findings
   têm peso arquitetural acima do que a severidade sugere: as implementações mortas são *a solução
   correta* para findings HIGH (AM-055, AM-056). Se você quiser refletir isso no catálogo, o sinal a
   extrair é "abstração correta existe e é ignorada", que é mais forte que "código morto".
4. **`AM-051` foi classificado CRITICAL e não HIGH** porque a exposição do hash não é apenas em uma
   rota administrativa: ela ocorre também na resposta de login e em `GET /users/<id>` anônimo, e o
   hash exposto é MD5 sem salt (AM-050), portanto equivalente à senha em texto puro na prática.

---

## Sinais genéricos extraídos

Sinais de detecção reescritos de forma agnóstica de projeto — insumo direto do catálogo de
anti-patterns da skill.

| # | Sinal genérico de detecção |
|---|---|
| AM-050 | Derivação de senha por função de hash rápida e de propósito geral (MD5/SHA-1/SHA-256 diretos), sem salt e sem fator de custo; verificação de credencial por comparação de igualdade simples sobre o digest, sem comparação em tempo constante. Sinal correlato: política de comprimento mínimo de senha abaixo de 8 caracteres. |
| AM-051 | Método de serialização definido na entidade de persistência que projeta o campo de credencial, consumido sem filtro pelos handlers de resposta — inclusive pela resposta de autenticação, que devolve ao chamador o material da credencial que ele acabou de usar. |
| AM-052 | Literal string atribuído a chave de configuração sensível no bootstrap, sem nenhuma leitura de variável de ambiente no projeto; servidor iniciado com flag de depuração ligada e bind em todas as interfaces. Reforço do sinal: existe no manifesto uma dependência de carga de configuração por ambiente que nunca é importada. |
| AM-053 | Host, usuário e senha de integração externa fixados como literais no construtor de uma classe de serviço e passados direto ao cliente da integração. Agravante a verificar: a classe inteira não é importada por nenhum módulo — segredo exposto sem prestar função. |
| AM-054 | Endpoint de autenticação que devolve como token uma string derivada de forma previsível do identificador do sujeito, sem assinatura nem expiração; ausência de decorator, middleware ou hook de requisição que verifique esse token em qualquer rota. Sinal confirmatório: o schema modela papéis de acesso e nenhum ponto do código os consulta em decisão de autorização. |
| AM-055 | Regra de negócio expressa como cadeia de condicionais copiada literalmente em múltiplos handlers, enquanto a entidade de domínio já implementa exatamente a mesma regra num método que nenhum chamador invoca. Detecção: localizar a condição repetida por busca textual e conferir se existe método homônimo no model com contagem de chamadas igual a zero. |
| AM-056 | Invariantes de domínio (vocabulário fechado, faixa numérica, tamanho de campo) escritas como sequência de `if` com literais inline dentro dos handlers, sem constraint equivalente no schema. Sinal agravante: existirem no repositório duas ou mais implementações concorrentes da mesma validação — em constantes nomeadas, em função utilitária e em método de entidade — nenhuma delas em uso. |
| AM-057 | Handlers de rota manipulando a sessão/transação do ORM diretamente (`add`/`commit`/`rollback`/`delete`) e construindo queries a partir das classes de model, sem camada de serviço ou repositório interposta; a sessão importada como singleton de módulo, sem injeção. Inversão típica a procurar: decisão de serialização de API vivendo no model e decisão de transação vivendo no controller. |
| AM-058 | Consulta a banco por item dentro de laço que itera o resultado de consulta anterior, em contexto onde o mapeamento objeto-relacional **já declara o relacionamento** que resolveria por eager loading; acesso a coleção relacionada dentro de laço, disparando lazy load por iteração. |
| AM-059 | Carregamento do conjunto completo de uma tabela para a memória do processo apenas para contar ou somar em laço, quando a condição é expressável em cláusula de filtro; múltiplas consultas de contagem separadas por valor de uma mesma coluna, onde um agrupamento único bastaria. |
| AM-060 | Endpoints de listagem que retornam o conjunto completo sem parâmetro de limite, offset ou cursor, tornando o tamanho da resposta função dos dados e não do contrato. Sinal auxiliar valioso: os próprios artefatos do repositório (dados de seed, comentários, backlog embutido) já descrevem a lacuna. |
| AM-061 | Handler que remonta campo a campo um dicionário de resposta que a entidade já produz por método próprio, convivendo no mesmo módulo com handlers que usam o método — resultando em duas ou três formas distintas do mesmo recurso conforme o endpoint. |
| AM-062 | Mesma expressão de validação (padrão de formato, faixa, vocabulário) repetida literalmente em três ou mais pontos, sendo pelo menos um deles numa função utilitária não utilizada; bloco de validação divergente entre o handler de criação e o de atualização da mesma entidade. |
| AM-063 | Cláusula de captura de exceção sem tipo especificado, descartando o objeto de erro sem registro, repetida em muitos pontos do projeto; ausência de import da biblioteca de logging em todo o repositório. Caso especialmente nocivo: captura nua que devolve valor sentinela, transformando erro de parsing em resultado "inválido" e escondendo a causa. |
| AM-064 | Coerção de tipo aplicada a parâmetro de entrada sem tratamento de exceção; comparação relacional sobre valor externo sem verificação prévia de tipo; handler que omite o guard de payload ausente que todos os handlers irmãos possuem. Consequência a confirmar: erro de cliente reportado como falha de servidor. |
| AM-065 | Política de deleção divergente entre entidades do mesmo sistema — uma remove dependentes em laço manual, outra deixa referências órfãs — sem `cascade` declarado no relacionamento e sem imposição de integridade no banco. |
| AM-066 | Saída direta para console usada como registro de eventos, sem níveis, timestamp ou destino configurável; caminhos de falha que não registram nada. Reforço do sinal: o projeto define uma função utilitária de log padronizada que nenhum chamador usa. |
| AM-067 | Middleware de política de origem cruzada aplicado globalmente com configuração padrão permissiva, cobrindo indistintamente rotas de leitura, de escrita e de remoção, num sistema sem autenticação. |
| AM-068 | Criação de schema executada como efeito colateral de nível de módulo, disparada no import da aplicação; ausência de ferramenta de migração no manifesto, com a criação feita por comando que só cria tabelas ausentes e nunca altera colunas existentes. |
| AM-069 | Módulo utilitário cujos símbolos públicos não são referenciados por nenhum outro arquivo; símbolos importados e nunca chamados no arquivo que os importa. Verificação decisiva: para cada símbolo exportado, contar referências fora do módulo de origem — importar não é usar. Agravante: constantes nomeadas mortas cujo valor está duplicado como literal nos módulos que deveriam consumi-las. |
| AM-070 | Diretório de camada presente na estrutura do projeto cuja única classe não é importada por nenhum caminho de execução; arquivo de reexportação de pacote que nenhum consumidor utiliza. A estrutura de diretórios anuncia uma arquitetura que o grafo de dependências não confirma. |
| AM-071 | Métodos de domínio definidos na entidade e nunca invocados, enquanto a regra que expressam aparece reimplementada nos handlers; modelagem de um conceito de autorização que nenhum ponto do código consulta. Sinal de estilo correlato: `if cond: return True else: return False`. |
| AM-072 | Múltiplos módulos importados numa única instrução separada por vírgulas, com parte deles não referenciada no arquivo; ausência de configuração de lint, teste ou CI no repositório. |
| AM-073 | Dependências declaradas no manifesto e não importadas por nenhum arquivo. Leitura útil do sinal: quando as dependências mortas correspondem exatamente a lacunas identificadas noutros findings (validação declarativa, configuração por ambiente), elas revelam a arquitetura pretendida e não implementada. |
| AM-074 | Tradução entre valor numérico armazenado e rótulo de negócio embutida na montagem do dicionário de resposta, existindo em um único ponto; contagens obtidas por variáveis numeradas sequencialmente a partir de consultas separadas; limiar da mesma escala usado noutro handler sem relação declarada com o mapeamento. |
| AM-075 | Verificação de tipo por comparação de classe exata em vez do operador de instância, com ramo alternativo que aceita silenciosamente qualquer outro tipo e o persiste; nomes de variável de uma letra em laços por todos os módulos; atribuição manual de campo de timestamp que o mapeamento já preenche automaticamente. |

---

## Metodologia de validação

Validação estratificada executada em 2026-08-16 com `.planning/validar.sh`, que
imprime o código-fonte real no range citado por cada finding e permite comparação
direta com o bloco de Evidência.

- **CRITICAL e HIGH:** 100% conferidos linha a linha (33 findings)
- **AM-054** reclassificado de HIGH para CRITICAL: token previsível (`fake-jwt-token-<id>`) é forjável por qualquer chamador, equivalendo funcionalmente à ausência de autenticação
- **MEDIUM e LOW:** amostragem de ~30%, sem divergências

Correções aplicadas: AM-005, AM-029 e AM-052 tiveram a evidência ampliada porque
o recorte original era mais estreito que a acusação do título. Nenhum finding foi
descartado por linha inexistente ou evidência parafraseada.
