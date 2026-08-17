# Baseline funcional — code-smells-project

Snapshot pré-refatoração capturado manualmente, **independente** do que a skill
`refactor-arch` venha a capturar. Serve como referência para o cruzamento posterior
com o `BASELINE_PATH` gerado pela skill.

- **Data da captura:** 2026-08-17
- **Projeto:** `code-smells-project/`
- **Operador:** captura manual (Passo 1 do protocolo de auditoria)
- **Idioma do relatório:** PT-BR · **saídas de console preservadas literalmente**

---

## 1. Estado do repositório no momento da captura

### `git status --porcelain`

```
(saída vazia — working tree limpo)
```

### `git log --oneline -3`

```
fd95af0 fix(skill): declare label convention as ceiling and renumber TR-14, TR-18
9284e32 fix(skill): close wave-assignment contradiction and add final validation procedure
081411c feat(skill): add refactor-arch skill v1
```

---

## 2. Ambiente de execução

O interpretador do sistema **não** tinha Flask instalado:

```
Python 3.12.3
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'flask'
```

Foi criado um virtualenv isolado (fora da árvore do projeto, no scratchpad da sessão)
com as dependências declaradas em `requirements.txt`:

```
Flask        3.1.1
flask-cors   5.0.1
```

### Inventário de fontes (`wc -l *.py`)

```
   88 app.py
  292 controllers.py
   86 database.py
  314 models.py
  780 total
```

4 arquivos-fonte Python, 780 LOC. Além deles, apenas `README.md` e `requirements.txt`.

---

## 3. Boot da aplicação

### Comando exato

```bash
cd code-smells-project
rm -f loja.db
nohup <scratchpad>/venv/bin/python -u app.py > boot.log 2>&1 &
```

> `loja.db` foi removido antes do boot para que o baseline partisse de um banco
> recriado do zero pelo seed automático de `database.py`.
> A flag `-u` (unbuffered) foi necessária: na primeira tentativa, sem ela, todas as
> linhas de `print()` da aplicação ficaram retidas no buffer de bloco do stdout
> redirecionado e se perderam ao encerrar o processo — apenas o log do Werkzeug
> (que vai para stderr) sobrevivia. Os status codes dos 21 chamados foram idênticos
> nas duas execuções; a segunda é a registrada aqui por ser a completa.

### Saída LITERAL do boot (antes de qualquer requisição)

```
==================================================
SERVIDOR INICIADO
Rodando em http://localhost:5000
==================================================
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.100.120:5000
Press CTRL+C to quit
 * Restarting with stat
==================================================
SERVIDOR INICIADO
Rodando em http://localhost:5000
==================================================
 * Debugger is active!
 * Debugger PIN: 268-305-094
```

> Sequências de escape ANSI de cor foram removidas do bloco acima para legibilidade;
> o texto é literal quanto ao conteúdo.
>
> **Observação de comportamento:** o banner `SERVIDOR INICIADO` é impresso **duas vezes**.
> Causa: `debug=True` ativa o reloader do Werkzeug, que reexecuta o processo; o bloco
> `if __name__ == "__main__":` — incluindo a chamada a `get_db()` — roda no processo pai
> e de novo no processo filho.

---

## 4. Endpoints levantados por leitura do código

Levantamento feito lendo `app.py` (registro de rotas via `add_url_rule` + decoradores
`@app.route`). **19 endpoints** no total.

| # | Método | Rota | Handler | Origem |
|---|--------|------|---------|--------|
| 1 | GET | `/` | `index` | `app.py:32` (`@app.route`) |
| 2 | GET | `/produtos` | `controllers.listar_produtos` | `app.py:11` |
| 3 | GET | `/produtos/busca` | `controllers.buscar_produtos` | `app.py:12` |
| 4 | GET | `/produtos/<int:id>` | `controllers.buscar_produto` | `app.py:13` |
| 5 | POST | `/produtos` | `controllers.criar_produto` | `app.py:14` |
| 6 | PUT | `/produtos/<int:id>` | `controllers.atualizar_produto` | `app.py:15` |
| 7 | DELETE | `/produtos/<int:id>` | `controllers.deletar_produto` | `app.py:16` |
| 8 | GET | `/usuarios` | `controllers.listar_usuarios` | `app.py:18` |
| 9 | GET | `/usuarios/<int:id>` | `controllers.buscar_usuario` | `app.py:19` |
| 10 | POST | `/usuarios` | `controllers.criar_usuario` | `app.py:20` |
| 11 | POST | `/login` | `controllers.login` | `app.py:21` |
| 12 | POST | `/pedidos` | `controllers.criar_pedido` | `app.py:23` |
| 13 | GET | `/pedidos` | `controllers.listar_todos_pedidos` | `app.py:24` |
| 14 | GET | `/pedidos/usuario/<int:usuario_id>` | `controllers.listar_pedidos_usuario` | `app.py:25` |
| 15 | PUT | `/pedidos/<int:pedido_id>/status` | `controllers.atualizar_status_pedido` | `app.py:26` |
| 16 | GET | `/relatorios/vendas` | `controllers.relatorio_vendas` | `app.py:28` |
| 17 | GET | `/health` | `controllers.health_check` | `app.py:30` |
| 18 | POST | `/admin/reset-db` | `reset_database` (inline em `app.py`) | `app.py:47` |
| 19 | POST | `/admin/query` | `executar_query` (inline em `app.py`) | `app.py:59` |

**Ordem de execução do smoke:** os endpoints destrutivos foram deixados por último
(`DELETE /produtos/11` → `POST /admin/query` → `POST /admin/reset-db`) para não
contaminar as respostas anteriores. Um `GET /health` extra foi executado depois do
reset para registrar o efeito.

---

## 5. Chamadas curl — requisição e resposta

21 chamadas cobrindo os 19 endpoints (o `GET /produtos/<id>` foi exercitado nos
caminhos 200 e 404; o `GET /health` foi chamado antes e depois do reset).

```
==============================================================
### GET /
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "endpoints": {
    "health": "/health",
    "login": "/login",
    "pedidos": "/pedidos",
    "produtos": "/produtos",
    "relatorios": "/relatorios/vendas",
    "usuarios": "/usuarios"
  },
  "mensagem": "Bem-vindo \u00e0 API da Loja",
  "versao": "1.0.0"
}

==============================================================
### GET /health
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "ambiente": "producao",
  "counts": {
    "pedidos": 0,
    "produtos": 10,
    "usuarios": 3
  },
  "database": "connected",
  "db_path": "loja.db",
  "debug": true,
  "secret_key": "minha-chave-super-secreta-123",
  "status": "ok",
  "versao": "1.0.0"
}

==============================================================
### GET /produtos
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "dados": [
    {
      "ativo": 1,
      "categoria": "informatica",
      "criado_em": "2026-08-17 14:38:04",
      "descricao": "Notebook potente para jogos",
      "estoque": 10,
      "id": 1,
      "nome": "Notebook Gamer",
      "preco": 5999.99
    },
    {
      "ativo": 1,
      "categoria": "informatica",
      "criado_em": "2026-08-17 14:38:04",
      "descricao": "Mouse sem fio ergon\u00f4mico",
      "estoque": 50,
      "id": 2,
      "nome": "Mouse Wireless",
      "preco": 89

==============================================================
### GET /produtos/1
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "dados": {
    "ativo": 1,
    "categoria": "informatica",
    "criado_em": "2026-08-17 14:38:04",
    "descricao": "Notebook potente para jogos",
    "estoque": 10,
    "id": 1,
    "nome": "Notebook Gamer",
    "preco": 5999.99
  },
  "sucesso": true
}

==============================================================
### GET /produtos/9999
--- RESPONSE ---
STATUS: 404
BODY(<=500): {
  "erro": "Produto n\u00e3o encontrado",
  "sucesso": false
}

==============================================================
### GET /produtos/busca?q=mouse
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "dados": [
    {
      "ativo": 1,
      "categoria": "informatica",
      "criado_em": "2026-08-17 14:38:04",
      "descricao": "Mouse sem fio ergon\u00f4mico",
      "estoque": 50,
      "id": 2,
      "nome": "Mouse Wireless",
      "preco": 89.9
    }
  ],
  "sucesso": true,
  "total": 1
}

==============================================================
### POST /produtos
--- REQUEST BODY ---
{"nome":"Produto Baseline","descricao":"item de smoke test","preco":10.5,"estoque":3,"categoria":"geral"}
--- RESPONSE ---
STATUS: 201
BODY(<=500): {
  "dados": {
    "id": 11
  },
  "mensagem": "Produto criado",
  "sucesso": true
}

==============================================================
### PUT /produtos/11
--- REQUEST BODY ---
{"nome":"Produto Baseline Editado","descricao":"item editado","preco":12.0,"estoque":4,"categoria":"geral"}
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "mensagem": "Produto atualizado",
  "sucesso": true
}

==============================================================
### GET /usuarios
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "dados": [
    {
      "criado_em": "2026-08-17 14:38:04",
      "email": "admin@loja.com",
      "id": 1,
      "nome": "Admin",
      "senha": "admin123",
      "tipo": "admin"
    },
    {
      "criado_em": "2026-08-17 14:38:04",
      "email": "joao@email.com",
      "id": 2,
      "nome": "Jo\u00e3o Silva",
      "senha": "123456",
      "tipo": "cliente"
    },
    {
      "criado_em": "2026-08-17 14:38:04",
      "email": "maria@email.com",
      "id": 3,
      "nome": "Maria Santos"

==============================================================
### GET /usuarios/1
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "dados": {
    "criado_em": "2026-08-17 14:38:04",
    "email": "admin@loja.com",
    "id": 1,
    "nome": "Admin",
    "senha": "admin123",
    "tipo": "admin"
  },
  "sucesso": true
}

==============================================================
### POST /usuarios
--- REQUEST BODY ---
{"nome":"Baseline User","email":"baseline@teste.com","senha":"senha123"}
--- RESPONSE ---
STATUS: 201
BODY(<=500): {
  "dados": {
    "id": 4
  },
  "sucesso": true
}

==============================================================
### POST /login
--- REQUEST BODY ---
{"email":"joao@email.com","senha":"123456"}
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "dados": {
    "email": "joao@email.com",
    "id": 2,
    "nome": "Jo\u00e3o Silva",
    "tipo": "cliente"
  },
  "mensagem": "Login OK",
  "sucesso": true
}

==============================================================
### POST /pedidos
--- REQUEST BODY ---
{"usuario_id":2,"itens":[{"produto_id":2,"quantidade":1}]}
--- RESPONSE ---
STATUS: 201
BODY(<=500): {
  "dados": {
    "pedido_id": 1,
    "total": 89.9
  },
  "mensagem": "Pedido criado com sucesso",
  "sucesso": true
}

==============================================================
### GET /pedidos
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "dados": [
    {
      "criado_em": "2026-08-17 14:38:15",
      "id": 1,
      "itens": [
        {
          "preco_unitario": 89.9,
          "produto_id": 2,
          "produto_nome": "Mouse Wireless",
          "quantidade": 1
        }
      ],
      "status": "pendente",
      "total": 89.9,
      "usuario_id": 2
    }
  ],
  "sucesso": true
}

==============================================================
### GET /pedidos/usuario/2
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "dados": [
    {
      "criado_em": "2026-08-17 14:38:15",
      "id": 1,
      "itens": [
        {
          "preco_unitario": 89.9,
          "produto_id": 2,
          "produto_nome": "Mouse Wireless",
          "quantidade": 1
        }
      ],
      "status": "pendente",
      "total": 89.9,
      "usuario_id": 2
    }
  ],
  "sucesso": true
}

==============================================================
### PUT /pedidos/1/status
--- REQUEST BODY ---
{"status":"aprovado"}
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "mensagem": "Status atualizado",
  "sucesso": true
}

==============================================================
### GET /relatorios/vendas
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "dados": {
    "desconto_aplicavel": 0,
    "faturamento_bruto": 89.9,
    "faturamento_liquido": 89.9,
    "pedidos_aprovados": 1,
    "pedidos_cancelados": 0,
    "pedidos_pendentes": 0,
    "ticket_medio": 89.9,
    "total_pedidos": 1
  },
  "sucesso": true
}

==============================================================
### DELETE /produtos/11
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "mensagem": "Produto deletado",
  "sucesso": true
}

==============================================================
### POST /admin/query
--- REQUEST BODY ---
{"sql":"SELECT COUNT(*) AS total FROM produtos"}
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "dados": [
    {
      "total": 10
    }
  ],
  "sucesso": true
}

==============================================================
### POST /admin/reset-db
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "mensagem": "Banco de dados resetado",
  "sucesso": true
}

==============================================================
### GET /health
--- RESPONSE ---
STATUS: 200
BODY(<=500): {
  "ambiente": "producao",
  "counts": {
    "pedidos": 0,
    "produtos": 0,
    "usuarios": 0
  },
  "database": "connected",
  "db_path": "loja.db",
  "debug": true,
  "secret_key": "minha-chave-super-secreta-123",
  "status": "ok",
  "versao": "1.0.0"
}

```

---

## 6. Log do servidor durante o smoke (LITERAL)

```
==================================================
SERVIDOR INICIADO
Rodando em http://localhost:5000
==================================================
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.100.120:5000
Press CTRL+C to quit
 * Restarting with stat
==================================================
SERVIDOR INICIADO
Rodando em http://localhost:5000
==================================================
 * Debugger is active!
 * Debugger PIN: 268-305-094
127.0.0.1 - - [17/Aug/2026 11:38:08] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /health HTTP/1.1" 200 -
Listando 10 produtos
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /produtos HTTP/1.1" 200 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /produtos/1 HTTP/1.1" 200 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /produtos/9999 HTTP/1.1" 404 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /produtos/busca?q=mouse HTTP/1.1" 200 -
Produto criado com ID: 11
127.0.0.1 - - [17/Aug/2026 11:38:15] "POST /produtos HTTP/1.1" 201 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "PUT /produtos/11 HTTP/1.1" 200 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /usuarios HTTP/1.1" 200 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /usuarios/1 HTTP/1.1" 200 -
Usuário criado: baseline@teste.com
127.0.0.1 - - [17/Aug/2026 11:38:15] "POST /usuarios HTTP/1.1" 201 -
Login bem-sucedido: joao@email.com
127.0.0.1 - - [17/Aug/2026 11:38:15] "POST /login HTTP/1.1" 200 -
ENVIANDO EMAIL: Pedido 1 criado para usuario 2
ENVIANDO SMS: Seu pedido foi recebido!
ENVIANDO PUSH: Novo pedido recebido pelo sistema
127.0.0.1 - - [17/Aug/2026 11:38:15] "POST /pedidos HTTP/1.1" 201 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /pedidos HTTP/1.1" 200 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /pedidos/usuario/2 HTTP/1.1" 200 -
NOTIFICAÇÃO: Pedido 1 foi aprovado! Preparar envio.
127.0.0.1 - - [17/Aug/2026 11:38:15] "PUT /pedidos/1/status HTTP/1.1" 200 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /relatorios/vendas HTTP/1.1" 200 -
Produto 11 deletado
127.0.0.1 - - [17/Aug/2026 11:38:15] "DELETE /produtos/11 HTTP/1.1" 200 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "POST /admin/query HTTP/1.1" 200 -
!!! BANCO DE DADOS RESETADO !!!
127.0.0.1 - - [17/Aug/2026 11:38:15] "POST /admin/reset-db HTTP/1.1" 200 -
127.0.0.1 - - [17/Aug/2026 11:38:15] "GET /health HTTP/1.1" 200 -
```

> Códigos ANSI de cor removidos; conteúdo literal preservado.

---

## 7. Resumo dos status codes

| # | Método | Rota chamada | Status |
|---|--------|--------------|--------|
| 1 | GET | `/` | 200 |
| 2 | GET | `/health` | 200 |
| 3 | GET | `/produtos` | 200 |
| 4 | GET | `/produtos/1` | 200 |
| 5 | GET | `/produtos/9999` | 404 |
| 6 | GET | `/produtos/busca?q=mouse` | 200 |
| 7 | POST | `/produtos` | 201 |
| 8 | PUT | `/produtos/11` | 200 |
| 9 | GET | `/usuarios` | 200 |
| 10 | GET | `/usuarios/1` | 200 |
| 11 | POST | `/usuarios` | 201 |
| 12 | POST | `/login` | 200 |
| 13 | POST | `/pedidos` | 201 |
| 14 | GET | `/pedidos` | 200 |
| 15 | GET | `/pedidos/usuario/2` | 200 |
| 16 | PUT | `/pedidos/1/status` | 200 |
| 17 | GET | `/relatorios/vendas` | 200 |
| 18 | DELETE | `/produtos/11` | 200 |
| 19 | POST | `/admin/query` | 200 |
| 20 | POST | `/admin/reset-db` | 200 |
| 21 | GET | `/health` (pós-reset) | 200 |

**Falhas pré-existentes: nenhuma.** Os 19 endpoints responderam. O único não-2xx
(`404` em `/produtos/9999`) é o comportamento esperado do caminho de erro.

### Efeitos colaterais observáveis registrados no log

Comportamentos que o baseline precisa preservar após a refatoração, porque são
observáveis via stdout (não via HTTP):

- `Listando 10 produtos` — em `GET /produtos`
- `Produto criado com ID: 11` — em `POST /produtos`
- `Usuário criado: baseline@teste.com` — em `POST /usuarios`
- `Login bem-sucedido: joao@email.com` — em `POST /login`
- `ENVIANDO EMAIL / SMS / PUSH` (3 linhas) — em `POST /pedidos`
- `NOTIFICAÇÃO: Pedido 1 foi aprovado! Preparar envio.` — em `PUT /pedidos/1/status`
- `Produto 11 deletado` — em `DELETE /produtos/11`
- `!!! BANCO DE DADOS RESETADO !!!` — em `POST /admin/reset-db`

### Estado do banco ao longo do smoke

| Momento | produtos | usuarios | pedidos |
|---------|----------|----------|---------|
| Após o boot (seed automático) | 10 | 3 | 0 |
| Após `POST /admin/reset-db` | 0 | 0 | 0 |

---

## 8. Encerramento

Aplicação derrubada ao final da captura. Verificação:

```
pgrep_exit=1
http_code=000
curl_exit=7
```

`pgrep` sem processos `app.py` remanescentes; `curl` com exit 7 (connection refused)
confirma a porta 5000 fechada.

Working tree permaneceu limpo após a captura — `loja.db` e `__pycache__/` são
cobertos pelo `.gitignore` do repositório.
