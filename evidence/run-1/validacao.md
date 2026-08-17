# Run 1 — Validação da refatoração (CA-4)

Validação final da Fase 3, executada após as quatro ondas ficarem verdes. As três
verificações da seção "Validação final" do `SKILL.md` não são herdadas de ondas verdes —
nenhuma delas foi testada por onda alguma.

- **Data:** 2026-08-17 · **Baseline:** `ec6d1d4` · **`M` = 19 endpoints**
- **Último commit:** `48b6f7b` · **Console preservado literalmente**

---

## 1. Boot pós-refatoração

### Comando exato

Depois de TR-16, criar schema e popular dados deixaram de acontecer no boot. São dois passos
explícitos, e o boot apenas **verifica** a versão aplicada:

```bash
cd code-smells-project
python -m scripts.migrate      # aplica as migrações pendentes
python -m scripts.seed_dev     # carga de demonstração; recusa fora de LOJA_ENV=development
python app.py
```

### Saída LITERAL

```console
$ python -m scripts.migrate
migracoes aplicadas: 0001_initial.sql
versao do schema: 1

$ python -m scripts.seed_dev
seed aplicado: 10 produtos, 3 usuarios

$ python app.py
2026-08-17T12:52:35-0300 INFO     loja servidor_iniciado ambiente=development host=127.0.0.1 port=5000
 * Tip: There are .env files present. Install python-dotenv to use them.
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
127.0.0.1 - - [17/Aug/2026 12:52:35] "GET / HTTP/1.1" 200 -
```

Critério de "subiu com sucesso" (`validation-protocol.md` §3):

```console
processo vivo: sim
primeira requisicao: HTTP 200
```

**Diferenças observáveis contra o boot do baseline**, todas intencionais:

| Antes | Depois | Causa |
|---|---|---|
| Banner `SERVIDOR INICIADO` impresso **duas vezes** | uma linha de log com nível e timestamp | TR-14 (logger) + `debug` desligado desativa o reloader |
| `Debug mode: on` · `Debugger PIN: 268-305-094` | `Debug mode: off` | TR-01 — `debug` vem do ambiente |
| `Running on all addresses (0.0.0.0)` | `Running on http://127.0.0.1:5000` | TR-01 — bind vem do ambiente |
| Schema e seed criados no primeiro `get_db()` | dois comandos explícitos antes do boot | TR-16 |

---

## 2. Os 19 endpoints do baseline

Roteiro de smoke autenticado como `admin@loja.com` nas 10 rotas que BC-4 passou a proteger.
"Status ANTES" vem de `reports/baseline-code-smells-project.json`.

| # | Método | Rota | Status ANTES | Status DEPOIS | Shape conforme? | Breaking change declarada? | Veredito |
|---|---|---|---|---|---|---|---|
| 1 | GET | `/` | 200 | 200 | idêntico | — | ✅ conforme |
| 2 | GET | `/health` | 200 | 200 | divergente | **BC-2** (`secret_key`, `debug`, `db_path`, `ambiente` removidos) | ✅ conforme |
| 3 | GET | `/produtos` | 200 | 200 | divergente | **BC-9** (`+paginacao`) | ✅ conforme |
| 4 | GET | `/produtos/1` | 200 | 200 | idêntico | — | ✅ conforme |
| 5 | GET | `/produtos/busca?q=mouse` | 200 | 200 | divergente | **BC-9** (`+paginacao`) | ✅ conforme |
| 6 | GET | `/usuarios` | 200 | 200 | divergente | **BC-1 + BC-9** (`-senha` no item, `+paginacao`) | ✅ conforme |
| 7 | GET | `/usuarios/1` | 200 | 200 | divergente | **BC-1** (`-senha`) | ✅ conforme |
| 8 | POST | `/usuarios` | 201 | 201 | idêntico | — | ✅ conforme |
| 9 | POST | `/login` | 200 | 200 | divergente | **BC-5** (registro do usuário → credencial assinada) | ✅ conforme |
| 10 | POST | `/produtos` | 201 | 201 | idêntico | BC-4 (401 sem credencial) | ✅ conforme |
| 11 | PUT | `/produtos/11` | 200 | 200 | idêntico | BC-4 · BC-10 (passa a validar nome e categoria) | ✅ conforme |
| 12 | POST | `/pedidos` | 201 | 201 | idêntico | — | ✅ conforme |
| 13 | GET | `/pedidos` | 200 | 200 | divergente | **BC-9** (`+paginacao`) | ✅ conforme |
| 14 | GET | `/pedidos/usuario/2` | 200 | 200 | divergente | **BC-9** (`+paginacao`) | ✅ conforme |
| 15 | PUT | `/pedidos/1/status` | 200 | 200 | idêntico | BC-4 | ✅ conforme |
| 16 | GET | `/relatorios/vendas` | 200 | 200 | idêntico | BC-4 | ✅ conforme |
| 17 | DELETE | `/produtos/11` | 200 | 200 | idêntico | BC-4 | ✅ conforme |
| 18 | POST | `/admin/query` | 200 | **404** | endpoint removido | **BC-3** (removido) | ✅ conforme |
| 19 | POST | `/admin/reset-db` | 200 | 200 | idêntico | BC-4 | ✅ conforme |

```console
SMOKE TEST: 19/19 endpoints conformes ao baseline
ONDA VERDE
```

**Media type:** `application/json` nos 19, antes e depois. Nenhum divergiu.

### Verificação 3 do protocolo — diff de forma contra a seção Breaking changes aprovada

```console
Mudancas de forma NAO declaradas : NENHUMA
Media types divergentes          : NENHUM
```

---

## 3. Árvore de diretórios resultante

```text
code-smells-project/
├── config/          settings.py                      leitura e validação do ambiente
├── models/          produto · usuario · pedido       forma dos dados e invariantes
├── repositories/    produto · usuario · pedido · admin   único lugar com SQL
├── services/        produto · usuario · auth · pedido · relatorio · admin
│                    notificacao · paginacao · errors   regra de negócio
├── controllers/     produto · usuario · pedido · relatorio · admin
├── routes/          produto · usuario · pedido · relatorio · sistema  (blueprints)
├── middlewares/     auth · error_handler · rate_limit
├── dto/             serializers.py                   allowlist de projeção
├── validators/      schema · produto · usuario · pedido · paginacao
├── security/        password.py · tokens.py
├── observability/   logger.py
├── infra/           connection.py · migrator.py · migrations/0001_initial.sql
├── scripts/         migrate.py · seed_dev.py
├── .env.example
├── app.py           composition root
├── constants.py
├── README.md
└── requirements.txt
```

**58 arquivos-fonte · 2155 LOC** (baseline: 4 arquivos · 780 LOC).

Direção de dependência verificada por AST contra `mvc-guidelines.md` §3:

```console
=== alcancabilidade (import explicito, com pacotes pai) ===
  modulos do projeto      : 58
  alcancaveis de app.py   : 55
  NAO alcancaveis (AP-26) : nenhum
  (scripts.* sao entry points de operacao, invocados por `python -m`)

=== direcao de dependencia (mvc-guidelines §3) ===
  violacoes de direcao: 0
```

### Verificação 2 do protocolo — responsabilidade a responsabilidade

```console
CAMADA        RESPONSABILIDADE UNICA                                   LUGAR              ALCANCAVEL
config        Ler o ambiente, validar o obrigatorio, expor tipados     1 (config/)        1/1 sim
models        Forma dos dados e invariantes que valem sempre           1 (models/)        3/3 sim
repositories  Unico lugar que conhece SQL/driver                       1 (repositories/)  4/4 sim
services      Regra de negocio e orquestracao de efeitos               1 (services/)      7/7 sim
controllers   Traduzir protocolo <-> dominio                           1 (controllers/)   5/5 sim
routes        Declarar metodo+path->handler, sem logica                1 (routes/)        5/5 sim
middlewares   Preocupacoes transversais                                1 (middlewares/)   3/3 sim

RESULTADO: todas as 7 responsabilidades tem UM lugar identificavel e alcancavel
```

---

## 4. Checklist MVC do enunciado

| # | Item | Status | Evidência de caminho |
|---|---|---|---|
| 1 | **Estrutura MVC** | ✅ | `models/` (3 mód.) · `controllers/` (5) · `routes/` (5 blueprints), mais `repositories/` (4) e `services/` (7) que a §2 do guia exige. As 7 responsabilidades têm **um** lugar cada, verificado por AST. |
| 2 | **Config sem hardcoded** | ✅ | `config/settings.py:98` `load_settings()` falha no boot sem `LOJA_SECRET_KEY`; `.env.example` publicado, `.env` ignorado (`.gitignore:29`). Busca por `minha-chave-super-secreta-123` no código: **0 ocorrências**. |
| 3 | **Models abstraem dados** | ✅ | `models/produto.py:3 CAMPOS` + `de_registro()` — mapeamento registro→entidade num lugar só (estava copiado 3×). `repositories/*.py` são os únicos com SQL: `grep cursor\|SELECT` em `controllers/` e `routes/` → **0 linhas de código**. |
| 4 | **Views/routes separadas** | ✅ | `routes/produto_routes.py:5` etc. — cada arquivo só declara `bp.add_url_rule(path, endpoint, handler, methods)`. `routes/` tem **66 LOC** no total e nenhuma condicional de negócio. |
| 5 | **Controllers concentram fluxo** | ✅ | `controllers/produto_controller.py:18-59` — parse, chamada ao service, mapeamento. Nenhum `except` genérico (`grep except Exception` em `controllers/` → 0) e nenhuma decisão de negócio. |
| 6 | **Error handling centralizado** | ✅ | `middlewares/error_handler.py:47 registrar(app, logger)` — envelope único `{"error":{"code","message","correlation_id"}}`, mapa erro-de-domínio→status em `STATUS_POR_ERRO`, e o texto da exceção **não** atravessa a fronteira. Os 17 blocos `except Exception` do baseline: **0 restantes**. |
| 7 | **Entry point claro** | ✅ | `app.py:44 build_app(settings)` — único lugar que instancia infraestrutura, na ordem config → infra → repositórios → services → controllers → rotas. `sqlite3.connect` aparece em **1** lugar do projeto: `infra/connection.py:24`. |
| 8 | **Aplicação inicia sem erros** | ✅ | Boot literal na seção 1: processo vivo, porta escutando, `GET /` → 200. |
| 9 | **Endpoints originais respondem** | ✅ | **19/19 conformes ao baseline**, com as 12 breaking changes aplicadas. Path e verbo preservados nos 18 sobreviventes; o 19º foi removido por BC-3, aprovado no gate. |

---

## 5. Findings resolvidos vs. reportados

### Verificação 1 do protocolo — reexecução do sinal de detecção de cada CRITICAL e HIGH

| Finding | AP | Sinal reexecutado | Resultado |
|---|---|---|---|
| F-001 | AP-01 | consulta montada por concatenação de entrada externa | **não dispara** — 0 pontos com valor de requisição |
| F-002 | AP-05 | rota privilegiada alcança dados sem verificar identidade | **não dispara** — 4/4 recusam com 401 |
| F-003 | AP-02 | literal em chave sensível + debug ligado no bootstrap | **não dispara** — 0 literais |
| F-004 | AP-04 | credencial em texto simples / comparação por igualdade no SQL | **não dispara** — 3 credenciais, 0 em texto simples; nenhum `WHERE` compara senha |
| F-005 | AP-07 | log interpola PII ou segredo | **não dispara** — 0 ocorrências num fluxo completo |
| F-006 | AP-03 | mapeamento registro→DTO projeta credencial | **não dispara** — `senha` ausente da resposta |
| F-007 | AP-03 | endpoint de diagnóstico serializa configuração | **não dispara** — 0 campos de config |
| F-008 | AP-01 | handler recebe consulta no payload e repassa ao executor | **não dispara** — rota removida, 404 |
| F-009 | AP-09 | dependência obtida por fábrica global no corpo | **não dispara** — 0 chamadas a `get_db()` |
| F-010 | AP-08 | regra/efeito de negócio dentro do handler de protocolo | **não dispara** — 0 no controller |
| F-011 | AP-13 | handler manipula sessão/cursor/consulta diretamente | **não dispara** — 0 linhas de código |
| F-012 | AP-11 | check-then-act sem atomicidade / deleção com órfãos | **não dispara** — deleção recusada com 409, 0 órfãos |
| F-013 | AP-21 | DDL/seed no boot + schema sem restrições | **não dispara** — 0 DDL no boot, 33 restrições declaradas |
| F-014 | AP-10 | handle de recurso em variável global mutável | **não dispara** — 0 globais de recurso, 0 `check_same_thread` |

> **Nota metodológica.** Quatro sinais dispararam na primeira passada e foram investigados um
> a um: os hits eram `"DELETE FROM " + tabela` (allowlist fechada de classe, contra-exemplo
> literal do AP-01), `SET senha = ? WHERE id = ?` (escrita da reidratação, não comparação),
> e duas linhas de **docstring**. Nenhum sobreviveu à reavaliação. Registro isso porque um
> "não dispara" obtido por grep frouxo não vale nada.

### Findings MEDIUM e LOW

| Finding | AP | TR | Evidência de correção |
|---|---|---|---|
| F-015 | AP-18 | TR-13 | 0 capturas genéricas; entrada inválida → 400; texto de exceção não atravessa. **Ver ressalva BC-12 abaixo.** |
| F-016 | AP-22 | TR-17 | 5 listagens com `LIMIT`/`OFFSET` na consulta; default 20, teto 100 |
| F-017 | AP-23 | TR-13 | envelope único com código estável em todos os caminhos de erro |
| F-018 | AP-12 | TR-08 | mesmo schema em criar e atualizar: `POST=400 PUT=400` nos 3 casos que divergiam |
| F-019 | AP-15 | TR-11 | 2 consultas constantes (200 pedidos × 5 itens: 2 em vez de 1201); relatório 5→1 |
| F-020 | AP-20 | TR-18 | allowlist de origem por ambiente; origem não listada não recebe o cabeçalho |
| F-021 | AP-24 | TR-05 | tentativas 1–5 → 401, 6ª → 429 |
| F-022 | AP-19 | TR-14 | 0 `print` no código servidor; 19 registros com nível e timestamp |
| F-023 | AP-27 | TR-18 | builtin `id` não é mais parâmetro nem variável local |
| F-024 | AP-25 | TR-18 | faixas de desconto em `PoliticaDeDesconto.FAIXAS`; versão só em `constants.py` |
| F-025 | AP-26 | TR-15 | 0 imports mortos; 0 dependências declaradas e não importadas |

### Não resolvidos

| Finding | AP | Razão |
|---|---|---|
| **F-026** | AP-28 | **Sem TR, por decisão do próprio catálogo.** Instalar test runner, linter e CI está fora do escopo declarado da skill; o finding foi reportado e explicitamente mantido fora do plano apresentado no gate. Cobertura parcial entregue: TR-01 publicou o `.env.example`. |

**Total: 25 de 26 findings resolvidos.** O único não resolvido é o que a skill declara,
desde a Fase 2, que não corrigiria.

---

## 6. Ressalvas — o que a Fase 3 encontrou e a Fase 2 não previu

### 6.1 Três mudanças de comportamento não declaradas em Breaking changes

Todas são consequência das constraints que TR-16 declarou — e que F-012 e F-013 pediram
nominalmente. A seção Breaking changes da Fase 2 enumerou mudanças de forma nos caminhos que
o baseline cobre, e **não previu os caminhos de erro que as constraints passariam a rejeitar**.

| # | Cenário (fora do baseline) | Antes | Depois | Causa |
|---|---|---|---|---|
| **BC-12** | `POST /pedidos` com `usuario_id` inexistente | 201 | **404** | FK `pedidos.usuario_id → usuarios.id` |
| **BC-13** | `DELETE /produtos/<id>` referenciado por pedido | 200 (deixando órfãos) | **409** | FK `itens_pedido.produto_id → produtos.id` |
| **BC-14** | `POST /pedidos` com `quantidade = 0` | 201 | **400** | `CHECK (quantidade > 0)` + validador de TR-08 |

BC-13 e BC-14 são o efeito pretendido dos findings F-012 e F-018 — o defeito era aceitá-los.
BC-12 chegou primeiro como **defeito**: a `IntegrityError` subia sem tipo e virava **500**,
que é erro de cliente reportado como falha de servidor. Foi corrigido em `48b6f7b`
completando o passo 4 de TR-13, com smoke test `19/19` próprio.

**Leitura:** o relatório da Fase 2 previu bem as mudanças de forma, e mal as mudanças de
status em caminhos de erro. É a mesma lacuna que a checagem da Fase 2 já tinha apontado — o
baseline não registra nenhum caminho de erro, então a Fase 3 não tinha contra o que comparar.

### 6.2 Residual de estado global de módulo

`security/password.py:27` mantém `global _custo_log2`, escrito uma vez por
`password.configure()` no composition root. **Não é finding de F-014**: não é handle de
recurso, não é escrito pelo caminho de requisição, e cai no contra-exemplo do AP-10
("configuração carregada uma vez"). Mas uma leitura estrita do passo 3 de TR-09 — "converta
estado mutável de módulo em instância com ciclo de vida explícito" — teria transformado o
hasher num objeto injetado, como já são o `Database`, o `LimitadorDeTaxa` e o logger. Fica
registrado como dívida, não como finding aberto.

### 6.3 As duas ressalvas herdadas da Fase 2, deliberadamente não corrigidas

- **F-021 (AP-24) como provável falso positivo.** Seguiu para a Fase 3 como estava e foi
  implementado: o limite de taxa existe e funciona (5 tentativas, 6ª → 429). A ressalva
  permanece registrada em `checagem.md` — o `report-template.md` usa esse caso exato como
  exemplo de linha "não aplicável".
- **Ausência de caminhos de erro no baseline.** O baseline **não foi alterado
  retroativamente**. A consequência se materializou: as três mudanças de 6.1 são
  precisamente o tipo de regressão que um baseline sem caminho de erro não consegue detectar,
  e só apareceram porque a Validação final procurou por elas de propósito.

---

## 7. Veredito CA-4

| Critério | Resultado |
|---|---|
| Boot sem erros | ✅ processo vivo, porta escutando, `GET /` → 200 |
| 19 endpoints respondendo conforme o baseline | ✅ **19/19**, descontadas as breaking changes declaradas |
| Ondas | ✅ 4 verdes, 0 vermelhas, 0 vazias, 0 rollbacks |
| Checklist MVC | ✅ 9 de 9 itens |
| Findings resolvidos | **25/26** — F-026 sem TR por escopo declarado |
| Mudanças de forma não declaradas | **nenhuma** nos 19 endpoints do baseline |
| Mudanças de status não declaradas | **3**, fora do baseline, registradas como BC-12/13/14 |

**CA-4 atendido.**
