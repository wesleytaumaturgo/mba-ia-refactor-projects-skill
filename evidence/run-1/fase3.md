# Run 1 — Fase 3 (refactor-arch)

Execução da Fase 3 da skill `refactor-arch` sobre `code-smells-project/`, após resposta `y`
ao gate da Fase 2. Protocolo de onda seguido à risca: boot após cada TR, smoke test completo
ao fim de cada onda, commit só com a contagem `M/M` na mensagem.

- **Data:** 2026-08-17 · **Baseline:** `ec6d1d4` · **`M` = 19 endpoints**
- **Console preservado literalmente**; texto em PT-BR.

## Gate

```console
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
y
```

---

## Onda 1 — CRITICAL · TR-01, TR-02, TR-03, TR-04, TR-05, TR-14

TR-01 primeiro na onda, por criar a estrutura de que TR-03 e TR-05 dependem.

### Boot após cada TR

```console
TR-01  BOOT: VERDE - porta escutando, processo vivo (pid 675658), primeira requisicao respondeu 200
TR-02  BOOT: VERDE - porta escutando, processo vivo (pid 675920), primeira requisicao respondeu 200
TR-03  BOOT: VERMELHO - processo morreu apos subir
TR-03  BOOT: VERDE - porta escutando, processo vivo (pid 676258), primeira requisicao respondeu 200
TR-04  BOOT: VERDE - porta escutando, processo vivo (pid 676381), primeira requisicao respondeu 200
TR-05  BOOT: VERDE - porta escutando, processo vivo (pid 676627), primeira requisicao respondeu 200
TR-14  BOOT: VERDE - porta escutando, processo vivo (pid 676880), primeira requisicao respondeu 200
```

### Boot vermelho em TR-03 — diagnóstico e recuperação (1 de 2 tentativas)

Consultados os falsos vermelhos da §8 primeiro: **não era** nenhum deles. Defeito real do
próprio TR-03.

```console
Traceback (most recent call last):
  File "/home/wesley/.../code-smells-project/app.py", line 73, in <module>
    get_db()
  File "/home/wesley/.../code-smells-project/database.py", line 91, in get_db
    [(nome, email, hash_password(senha), tipo) for nome, email, senha, tipo in usuarios]
                   ^^^^^^^^^^^^^^^^^^^^
  File "/home/wesley/.../code-smells-project/security/password.py", line 55, in hash_password
    dk = _derivar(senha, salt, custo, _R, _P)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/wesley/.../code-smells-project/security/password.py", line 40, in _derivar
    return hashlib.scrypt(
           ^^^^^^^^^^^^^^^
ValueError: [digital envelope routines] memory limit exceeded
```

**Causa:** o `maxmem` que passei ao `scrypt` era `2**(custo+7)` = 2 MB, menor que os
`128·n·r` = 16 MB que o algoritmo exige com `n=2^14, r=8`.
**Correção:** `maxmem = 128 * n * r * p * 2`. Boot verde na tentativa seguinte; nenhum TR
foi aplicado sobre boot vermelho.

### Verificações que os TRs exigem

```console
TR-01  ConfigError: Variável de ambiente obrigatória ausente: LOJA_SECRET_KEY. Copie .env.example para .env e preencha os valores.
TR-01  .gitignore:29:.env	code-smells-project/.env   -> .env ESTA ignorado pelo VCS

TR-02  busca com injecao -> total = 0        (antes: 10 produtos, filtro derrotado)
TR-02  busca legitima    -> total = 8
TR-02  login com injecao -> HTTP 401         (antes: 200 + {"tipo":"admin"})
TR-02  login legitimo    -> HTTP 200
TR-02  POST /admin/query -> HTTP 404         (rota removida, BC-3)

TR-03  admin@loja.com  -> scrypt$14$8$1$92V7hex5Gx7iJc9iJjvCKg$if1YUCz...
TR-03  duas contas com a MESMA senha: iguais? False
TR-03  login legado: HTTP 200 -> valor regravado como scrypt$... (reidratacao)
TR-03  senha errada apos reidratacao: HTTP 401 | senha certa: HTTP 200

TR-04  GET /health -> {"counts":{...},"database":"connected","status":"ok","versao":"1.0.0"}
TR-04  varredura de senha/secret_key/db_path/debug/ambiente em 8 GETs -> todos limpos

TR-05  GET /usuarios sem credencial            -> HTTP 401
TR-05  GET /usuarios com credencial de cliente -> HTTP 403
TR-05  GET /usuarios com credencial de admin   -> HTTP 200
TR-05  token invalido / payload forjado        -> HTTP 401
TR-05  login: tentativas 1..5 -> 401 | tentativa 6 e 7 -> 429
TR-05  endpoints registrados 18 | com politica declarada 18 | sem politica: nenhum

TR-14  busca por PII/credencial no log de um fluxo completo:
       logtest@sensivel.com -> 0 | segredo123 -> 0 | admin@loja.com -> 0
       admin123 -> 0 | joao@email.com -> 0 | scrypt -> 0
TR-14  registros com nivel+timestamp: 9 | prints remanescentes no codigo servidor: nenhum
```

### Smoke test da Onda 1

```console
SMOKE TEST: 19/19 endpoints conformes ao baseline
ONDA VERDE
```

Commit `5e0591b`.

---

## Onda 2 — HIGH · TR-06, TR-09, TR-07, TR-10, TR-16

TR-06 primeiro na onda, por criar a estrutura de que TR-07, TR-09 e TR-10 dependem.
TR-06 desceu da Onda 1 para a Onda 2 porque AP-06 não virou finding — ajuste já declarado
no plano aprovado.

```console
TR-06  BOOT: VERDE - porta escutando, processo vivo (pid 677644), primeira requisicao respondeu 200
TR-09  BOOT: VERDE - porta escutando, processo vivo (pid 678192), primeira requisicao respondeu 200
TR-07  BOOT: VERDE - porta escutando, processo vivo (pid 678354), primeira requisicao respondeu 200
TR-10  BOOT: VERDE - porta escutando, processo vivo (pid 678455), primeira requisicao respondeu 200
TR-16  BOOT: VERDE - porta escutando, processo vivo (pid 678695), primeira requisicao respondeu 200
```

### Verificações

```console
TR-06  nenhum arquivo importa driver E framework web ao mesmo tempo: nenhuma violacao
TR-06  controllers/ e routes/ mencionando cursor/SQL: nenhuma (so docstring)
TR-06  services/ importando simbolo de protocolo: nenhuma (so docstring)
TR-06  rotas registradas: 18, mesmos metodos e paths do baseline (19 menos a removida por BC-3)

TR-09  service construido com banco alternativo, sem singleton e sem variavel de ambiente:
       listar() vazio: [] | criar() -> id 1 | listar() apos: ['Isolado']
TR-09  conexao fechada apos o bloco: ProgrammingError -> como esperado
TR-09  politica de desconto exercitavel sem banco:
       faturamento    500 -> desconto 0.00
       faturamento   1500 -> desconto 30.00
       faturamento   6000 -> desconto 300.00
       faturamento  20000 -> desconto 2000.00

TR-10  erro no meio da sequencia: estoque antes 8 -> HTTP 400 -> estoque depois 8
       pedidos gravados: 0 | itens_pedido orfaos: 0
TR-10  4 pedidos concorrentes do estoque inteiro (8 un) -> [201, 400, 400, 400]
       aceitos: 1 | recusados: 3 | estoque final = 0 (nao negativo)

TR-16  boot contra banco nao migrado:
       infra.migrator.SchemaDesatualizado: Schema do banco na versão 0, esperada 1.
       Rode `python -m scripts.migrate` antes de subir a aplicação.
TR-16  CREATE TABLE no log do boot: 0
TR-16  estoque negativo                  -> recusado (CHECK constraint failed: estoque >= 0)
TR-16  categoria fora do vocabulario     -> recusado (CHECK constraint failed: categoria IN ...)
TR-16  nome com 1 caractere              -> recusado (CHECK constraint failed: length(nome) BETWEE)
TR-16  pedido de usuario inexistente     -> recusado (FOREIGN KEY constraint failed)
TR-16  item de produto inexistente       -> recusado (FOREIGN KEY constraint failed)
TR-16  quantidade zero                   -> recusado (CHECK constraint failed: quantidade > 0)
TR-16  restricoes: NOT NULL 20 | UNIQUE 1 | REFERENCES 3 | CHECK 9
```

### Observação de escopo — TR-06 absorveu a maior parte de TR-07

Ao decompor as camadas, o passo 2 de TR-06 ("mova as decisões de negócio para services") já
realocou as notificações, a política de desconto e a validação. Restaram para TR-07 apenas
o default de domínio de `categoria`, que ainda era decidido no controller, e um import tardio
dentro de um método do service. **Isto é sobreposição real entre os dois TRs do playbook**
quando o projeto não tem camada de service alguma — está registrado aqui em vez de fingir que
TR-07 fez trabalho que TR-06 já tinha feito.

### Smoke test da Onda 2

```console
SMOKE TEST: 19/19 endpoints conformes ao baseline
ONDA VERDE
```

Commit `dc0e74c`.

---

## Onda 3 — MEDIUM · TR-13, TR-08, TR-17, TR-11, TR-18

**Ajuste de ordem dentro da onda:** TR-08 foi antecipado a TR-17 porque o passo 4 de TR-17
exige o validador de TR-08 para os parâmetros de página. A onda é a mesma; só a ordem interna
mudou.

```console
TR-13  BOOT: VERDE - porta escutando, processo vivo (pid 679042), primeira requisicao respondeu 200
TR-08  BOOT: VERDE - porta escutando, processo vivo (pid 679230), primeira requisicao respondeu 200
TR-17  BOOT: VERDE - porta escutando, processo vivo (pid 680295), primeira requisicao respondeu 200
TR-11  BOOT: VERDE - porta escutando, processo vivo (pid 680501), primeira requisicao respondeu 200
TR-18  BOOT: VERDE - porta escutando, processo vivo (pid 681087), primeira requisicao respondeu 200
```

### Verificações

```console
TR-13  GET /produtos/9999 (inexistente)     -> HTTP 404  {"error":{"code":"nao_encontrado",...}}
TR-13  GET /rota/que/nao/existe             -> HTTP 404  {"error":{"code":"rota_inexistente",...}}
TR-13  POST /produtos sem credencial        -> HTTP 401  {"error":{"code":"credencial_ausente",...}}
TR-13  POST /produtos campo ausente         -> HTTP 400  {"error":{"code":"entrada_invalida",...}}
TR-13  POST /login corpo null               -> HTTP 400  (antes: 500)
TR-13  nenhuma resposta contem texto de excecao ou caminho de arquivo

TR-08  a MESMA entrada invalida em criar e atualizar:
       POST=400 PUT=400  {"nome":"x",...}                    (antes: PUT aceitava)
       POST=400 PUT=400  {"categoria":"inexistente",...}     (antes: PUT aceitava)
       POST=400 PUT=400  {"preco":-1,...}
TR-08  entrada de tipo errado -> 400 nos tres casos (fecha BC-8)
TR-08  payload com campo extra: id gravado 11 (payload tentou 999) | ativo 1 (tentou 0)

TR-17  sem parametros: itens = 10 | paginacao = {'limite': 20, 'offset': 0, 'total': 10}
TR-17  ?limite=9999: paginacao = {'limite': 100, ...}   (teto vence)
TR-17  ?limite=3&offset=0 -> [1, 2, 3] | ?limite=3&offset=3 -> [4, 5, 6]
TR-17  forma do item identica ao baseline: True (/produtos e /produtos/busca)
TR-17  ?limite=abc -> HTTP 400 | ?offset=-1 -> HTTP 400

TR-11  pedidos x itens | consultas AGORA | o laco aninhado faria
         5 x 3          | 2               | 21
        20 x 3          | 2               | 81
        50 x 5          | 2               | 301
       200 x 5          | 2               | 1201
TR-11  relatorio de vendas -> 1 consulta (antes eram 5)
TR-11  produto removido ainda cai em "Desconhecido" (LEFT JOIN preservou o fallback)

TR-18  Origin: http://localhost:3000 (listada)    -> Access-Control-Allow-Origin: http://localhost:3000
TR-18  Origin: http://evil.example (nao listada)  -> cabecalho ausente (recusada)
TR-18  versao "1.0.0" declarada uma vez so, em constants.py
TR-18  builtin `id` como parametro ou variavel local: nenhuma ocorrencia
```

### Smoke test da Onda 3

```console
SMOKE TEST: 19/19 endpoints conformes ao baseline
ONDA VERDE
```

Commit `222bb9a`.

---

## Onda 4 — LOW · TR-15

```console
TR-15  BOOT: VERDE - porta escutando, processo vivo (pid 681785), primeira requisicao respondeu 200
```

Os imports mortos que F-025 nomeava (`os` em `database.py`, `sqlite3` em `models.py`)
desapareceram junto com os arquivos planos na Onda 2. TR-15 tratou o que sobrou:

```console
TR-15  passo 1 — ligar chamadores a abstracoes que ja existiam:
       CREDENCIAL     -> 3 referencias (validava nada; agora valida o login)
       PAPEL_ADMIN    -> 3 referencias (middleware duplicava o literal "admin")
       CAMPOS_ITEM    -> 2 referencias (o mapeamento nao usava a constante)
TR-15  passo 3 — removidos: usuario_autenticado_dto, CAMPOS_USUARIO_AUTENTICADO, PAPEIS_VALIDOS
TR-15  imports mortos fora de __init__.py: 0
TR-15  flask==3.1.1      -> importado em 13 arquivo(s)
TR-15  flask-cors==5.0.1 -> importado em 1 arquivo(s)
```

### Smoke test da Onda 4

```console
SMOKE TEST: 19/19 endpoints conformes ao baseline
ONDA VERDE
```

Commit `d1b9b8e`.

---

## Correção pós-validação — passo 4 de TR-13 no caminho da chave estrangeira

A Validação final (verificação 1) encontrou `POST /pedidos` com `usuario_id` inexistente
respondendo **500**: a `IntegrityError` da FK que TR-16 declarou subia sem tipo e caía no
tratador de defeito. Erro de cliente reportado como falha de servidor é exatamente o colapso
que o passo 4 de TR-13 existe para desfazer — **completar um TR do plano aprovado, não
revisá-lo**.

```console
antes  POST /pedidos {"usuario_id":9999,...} -> HTTP 500 {"error":{"code":"erro_interno",...}}
depois POST /pedidos {"usuario_id":9999,...} -> HTTP 404 {"error":{"code":"nao_encontrado",
                                                          "message":"Usuário 9999 não encontrado"}}
depois POST /pedidos {"usuario_id":2,...}    -> HTTP 201  (caminho legitimo preservado)

SMOKE TEST: 19/19 endpoints conformes ao baseline
```

Commit `48b6f7b`. Registrado como **BC-12** no relatório de validação: é mudança de
comportamento em caminho que o baseline não cobre e que a seção Breaking changes não previu.

---

## Registro de ondas (§6.1) — completo

```console
| stage    | sha       | smoke  | status |
|----------|-----------|--------|--------|
| baseline | ec6d1d4   | —      | green  |
| onda-1   | 5e0591b   | 19/19  | green  |
| onda-2   | dc0e74c   | 19/19  | green  |
| onda-3   | 222bb9a   | 19/19  | green  |
| onda-4   | d1b9b8e   | 19/19  | green  |
```

Linha adicional, fora da numeração de ondas: `48b6f7b` — correção do passo 4 de TR-13
encontrada pela Validação final, com smoke test `19/19` próprio.

Nenhuma onda ficou vermelha; nenhum `git reset --hard` foi executado. Nenhuma onda vazia:
o plano aprovado atribuiu TR às quatro.

---

## Saída da Fase 3

```console
PHASE 3: REFACTORING COMPLETE
─────────────────────────────────────────────
Waves         : 1 CRITICAL ✓ · 2 HIGH ✓ · 3 MEDIUM ✓ · 4 LOW ✓
Smoke test    : 19/19 endpoints conform to baseline
Breaking chg  : 12 applied, 11 declared in the approved report + BC-12 undeclared (reported)
Findings fixed: 25/26 (26 reported, not fixed: F-026 — sem TR, reportado e não corrigido por escopo)
History       : ec6d1d4 → 5e0591b → dc0e74c → 222bb9a → d1b9b8e → 48b6f7b
─────────────────────────────────────────────
```

### New structure

```text
code-smells-project/
├── config/                    leitura e validação do ambiente, fail-fast no boot
│   ├── __init__.py
│   └── settings.py
├── models/                    forma dos dados e invariantes que valem sempre
│   ├── __init__.py
│   ├── pedido.py
│   ├── produto.py
│   └── usuario.py
├── repositories/              único lugar que conhece SQL e driver
│   ├── __init__.py
│   ├── admin_repository.py
│   ├── pedido_repository.py
│   ├── produto_repository.py
│   └── usuario_repository.py
├── services/                  regra de negócio e orquestração de efeitos
│   ├── __init__.py
│   ├── admin_service.py
│   ├── auth_service.py
│   ├── errors.py
│   ├── notificacao_service.py
│   ├── paginacao.py
│   ├── pedido_service.py
│   ├── produto_service.py
│   ├── relatorio_service.py
│   └── usuario_service.py
├── controllers/               tradução protocolo ↔ domínio
│   ├── __init__.py
│   ├── admin_controller.py
│   ├── pedido_controller.py
│   ├── produto_controller.py
│   ├── relatorio_controller.py
│   └── usuario_controller.py
├── routes/                    método + path → handler, sem lógica (blueprints)
│   ├── __init__.py
│   ├── pedido_routes.py
│   ├── produto_routes.py
│   ├── relatorio_routes.py
│   ├── sistema_routes.py
│   └── usuario_routes.py
├── middlewares/               autenticação, autorização, limite de taxa, tratamento de erro
│   ├── __init__.py
│   ├── auth.py
│   ├── error_handler.py
│   └── rate_limit.py
├── dto/                       allowlist de projeção na fronteira de saída
│   ├── __init__.py
│   └── serializers.py
├── validators/                invariantes declarativas por entidade
│   ├── __init__.py
│   ├── paginacao_validator.py
│   ├── pedido_validator.py
│   ├── produto_validator.py
│   ├── schema.py
│   └── usuario_validator.py
├── security/                  derivação de credencial e token assinado
│   ├── __init__.py
│   ├── password.py
│   └── tokens.py
├── observability/             logger com níveis, timestamp e redação
│   ├── __init__.py
│   └── logger.py
├── infra/                     conexão e migrações versionadas
│   ├── migrations/
│   │   └── 0001_initial.sql
│   ├── __init__.py
│   ├── connection.py
│   └── migrator.py
├── scripts/                   operações explícitas, fora do boot
│   ├── __init__.py
│   ├── migrate.py
│   └── seed_dev.py
├── .env.example
├── app.py                     composition root: monta o grafo e sobe
├── constants.py
├── README.md
└── requirements.txt
```

| Camada | LOC |
|---|---|
| `services/` | 451 |
| `repositories/` | 268 |
| `middlewares/` | 225 |
| `controllers/` | 202 |
| `validators/` | 157 |
| `security/` | 152 |
| `app.py` | 128 |
| `config/` | 118 |
| `infra/` | 109 |
| `scripts/` | 81 |
| `routes/` | 66 |
| `dto/` | 63 |
| `observability/` | 61 |
| `models/` | 56 |
| `constants.py` | 18 |
| **Total** | **2155 LOC em 58 arquivos** (baseline: 780 em 4) |
