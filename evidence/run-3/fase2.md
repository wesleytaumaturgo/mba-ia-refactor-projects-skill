# Run-3 · Fase 2 — Auditoria (read-only) · `task-manager-api`

Continuação de [`fase1.md`](fase1.md). Relatório gravado em
`/home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/audit-task-manager-api.md`.

---

## 1. Referências carregadas

Conforme o mapa de conhecimento do `SKILL.md`:

- `references/antipattern-catalog.md` — **integral**, antes de varrer o código.
- `references/mvc-guidelines.md` — integral (o `SKILL.md` pede §9 na Fase 2; li o arquivo inteiro
  porque o passo 6 da fase referencia §6, e §1 regra 4 decide se há convenção a adotar).
- `references/report-template.md` — ao redigir.
- `references/refactor-playbook.md` — **apenas o índice**, para nomear os TRs no plano. As seções
  dos TRs ficam para a Fase 3.

---

## 2. Varredura dos 28 APs na ordem do catálogo

Nenhuma entrada pulada. Para cada AP: sinal respondido, contra-exemplo aplicado, evidência
literal coletada ou finding descartado.

| AP | Nome | Sinal | Resultado |
|---|---|---|---|
| AP-01 | Injection por concatenação | não | **não encontrado** — f-string monta o *valor* do padrão; provado pelo SQL compilado |
| AP-02 | Hardcoded secret + debug | **sim** | **F-001 CRITICAL** |
| AP-03 | Credencial na serialização | **sim** | **F-002 CRITICAL** |
| AP-04 | Derivação de senha quebrada | **sim** | **F-003 CRITICAL** |
| AP-05 | Rota privilegiada sem auth | **sim** | **F-004 CRITICAL** |
| AP-06 | God class / god module | não | **não encontrado** — contra-exemplo aplicado (ver §3) |
| AP-07 | Segredo/PII em log | não | **não encontrado** — nenhum `print` interpola credencial |
| AP-08 | Regra fora do service | **sim** | **F-006 HIGH** |
| AP-09 | Dependência concreta sem injeção | **sim** | **F-009 HIGH** |
| AP-10 | Estado global mutável | não | **não encontrado** — `db` é pool (isento); acumulador está em código morto |
| AP-11 | Escrita multi-etapa sem transação | **sim** | **F-008 HIGH** |
| AP-12 | Validação inline no handler | **sim** | **F-011 MEDIUM** |
| AP-13 | Rota acoplada ao ORM | **sim** | **F-005 HIGH** |
| AP-14 | Mass assignment | não | **não encontrado** — atribuição campo a campo, sem `**payload` |
| AP-15 | N+1 aninhado | **sim** | **F-012 MEDIUM** |
| AP-16 | Deprecated API | **sim** | **F-016 MEDIUM** — verificável (runtime real obtido na Fase 1) |
| AP-17 | Duplicação com abstração morta | **sim** | **F-010 MEDIUM** |
| AP-18 | Captura genérica de exceção | **sim** | **F-013 MEDIUM** |
| AP-19 | Console como log | **sim** | **F-019 LOW** |
| AP-20 | CORS permissivo | **sim** | **F-017 MEDIUM** |
| AP-21 | DDL no boot | **sim** | **F-007 HIGH** |
| AP-22 | Listagem sem paginação | **sim** | **F-015 MEDIUM** |
| AP-23 | Contrato de resposta inconsistente | **sim** | **F-014 MEDIUM** |
| AP-24 | Sem rate limiting no login | **sim** | **F-018 MEDIUM** |
| AP-25 | Magic numbers | **sim** | **F-021 LOW** |
| AP-26 | Código morto e deps não usadas | **sim** | **F-020 LOW** |
| AP-27 | Nomenclatura pobre | **sim** | **F-022 LOW** |
| AP-28 | Sem infra de qualidade | **sim** | **F-023 LOW** — reportado, sem TR |

**23 findings · 5 não encontrados · 23 + 5 = 28.** Cobertura completa.

---

## 3. As três decisões de julgamento que mais afetaram o plano

Registradas aqui porque são o ponto onde a auditoria poderia ter inflado a contagem, e não inflou.

### 3.1 AP-06 (god class) descartado — e o efeito disso na Onda 1

O sinal do AP-06 é específico: *"um único arquivo ou classe que reúne, no mesmo corpo, abertura
de conexão de banco, definição de schema, registro de rotas e regra de negócio — de modo que
não existe fronteira onde inserir uma camada"*.

Aplicando o contra-exemplo:

- `app.py` (34 LOC) faz `db.init_app`, `db.create_all()`, `register_blueprint` ×3 e 2 rotas
  inline. Mas é o **composition root**, e o AP isenta explicitamente: *"nem é finding quando o
  arquivo é o composition root"*. Suas responsabilidades excedentes — config literal e DDL no
  boot — já são F-001 (AP-02) e F-007 (AP-21). Reportá-las aqui de novo violaria "um finding por
  causa".
- `routes/task_routes.py` (299 LOC), `report_routes.py` (223) e `user_routes.py` (211) acumulam
  6–7 responsabilidades cada, mas **nenhum abre conexão nem define schema**, e existe fronteira
  clara onde inserir camada. O AP diz: *"o critério é número de responsabilidades distintas, não
  número de linhas"* — e o sinal exige as quatro responsabilidades juntas. A acumulação foi
  reportada onde pertence: F-005 (AP-13) e F-006 (AP-08).

**Consequência no plano, que é o que torna a decisão verificável:** sem AP-06, o TR-06 perde o
teto da Onda 1 e **desce para a Onda 2**, pela severidade de AP-13 (HIGH). É exatamente o caso
que o `refactor-playbook.md` descreve. A Onda 1 não fica vazia porque quatro findings CRITICAL
independentes (F-001..F-004) a preenchem.

### 3.2 A regra de alcançabilidade, aplicada com rigor às quatro pastas

Este era o ponto crítico do projeto. Mecanismo determinado na Fase 1: **import explícito**.

| Pasta | Símbolo alcançável? | Veredito | Por quê |
|---|---|---|---|
| `models/` | sim | **camada adotada** | importada pelas 3 rotas, que entram pelo `app.py` |
| `routes/` | sim | **camada adotada** | `app.py:4-6` importa e `:18-20` registra |
| `utils/` | **sim** | **camada adotada**, com AP-17 | `report_routes.py:7` importa 2 símbolos nominalmente |
| `services/` | **não** | **AP-26 (F-020)** | zero importadores em todo o projeto |

O caso de `utils/` é o que a regra existe para separar. Ela **é** alcançável — a linha 7 é import
explícito, o mecanismo real desta stack, e o módulo entra na memória no boot. Logo a camada é
**adotada** e **não** vira AP-26. Mas dos 16 símbolos públicos, 2 são importados e **0 invocados**:

```console
$ grep -rn -E 'format_date|calculate_percentage' --include='*.py' . | grep -v '^./.claude'
utils/helpers.py:9:def format_date(date_obj):
utils/helpers.py:14:def calculate_percentage(part, total):
routes/report_routes.py:7:from utils.helpers import format_date, calculate_percentage
```

Duas definições e um import. Zero chamadas. Isso é **AP-17** (duplicação com a abstração correta
morta) + os símbolos não-importados em **AP-26** — categorias diferentes de "camada inalcançável",
e é essa diferença que a regra preserva. Rebaixar `utils/` a AP-26 teria sido o erro simétrico ao
de promover `services/` a camada.

O conteúdo de `services/` foi **inventariado como finding antes de qualquer proposta de remoção**,
conforme `mvc-guidelines.md` §6 — inclusive a credencial SMTP versionada, que virou item
NEEDS-DECISION (ND-3) porque apagar o arquivo não a remove do histórico do git.

### 3.3 `mvc-guidelines.md` §1 regra 4 NÃO se aplica

Tentação natural: "o projeto já tem pastas de camada, logo adote a convenção da stack". Mas a
regra 4 diz explicitamente que **o gatilho não é alcançabilidade** — exige que a stack **declare**
a convenção (raiz de autoload, pacote-base varrido, estrutura imposta). Flask não declara nenhuma.

> *"Um monólito cujos módulos são apenas alcançáveis por import explícito **não tem convenção a
> adotar**, por mais que seus arquivos tenham nome de camada."*

Este projeto é literalmente esse caso. A Fase 3 cai na §4 **precedência 1** (convenção já
praticada e alcançável dentro do próprio projeto), o que significa preservar `models/`, `routes/`,
`utils/` e criar apenas as responsabilidades ausentes — não erguer árvore paralela.

---

## 4. Findings, por severidade

| # | Sev | Título | AP | TR | Onda | Ocorr. |
|---|---|---|---|---|---|---|
| F-001 | CRITICAL | Segredo, credencial SMTP e debug literais no código | AP-02 | TR-01 | 1 | 3 |
| F-002 | CRITICAL | Hash de senha projetado na resposta de 4 endpoints | AP-03 | TR-04 | 1 | 5 |
| F-003 | CRITICAL | Senha por MD5 sem salt, verificada por igualdade | AP-04 | TR-03 | 1 | 8 |
| F-004 | CRITICAL | 22 rotas sem verificação de identidade | AP-05 | TR-05 | 1 | 22 |
| F-005 | HIGH | Rotas manipulam sessão do ORM, sem repositório | AP-13 | TR-06 | 2 | 29 |
| F-006 | HIGH | Regra de domínio dentro dos handlers | AP-08 | TR-07 | 2 | 14 |
| F-007 | HIGH | DDL no boot + schema sem constraints | AP-21 | TR-16 | 2 | 5 |
| F-008 | HIGH | Escritas sem fronteira transacional, órfãos garantidos | AP-11 | TR-10 | 2 | 3 |
| F-009 | HIGH | Singleton global; composition root sem injeção | AP-09 | TR-09 | 2 | 5 |
| F-010 | MEDIUM | Duplicação com a abstração correta morta | AP-17 | TR-15 | 3 | 27 |
| F-011 | MEDIUM | Invariantes inline, divergentes entre criar e atualizar | AP-12 | TR-08 | 3 | 16 |
| F-012 | MEDIUM | N+1 em 4 endpoints, com eager loading já declarado | AP-15 | TR-11 | 3 | 4 |
| F-013 | MEDIUM | 12 `except:` pelados; erro de cliente vira 500 | AP-18 | TR-13 | 3 | 12 |
| F-014 | MEDIUM | Contrato divergente entre handlers do mesmo recurso | AP-23 | TR-13 | 3 | 4 |
| F-015 | MEDIUM | 4 listagens sem paginação | AP-22 | TR-17 | 3 | 4 |
| F-016 | MEDIUM | 34 chamadas deprecated no runtime real | AP-16 | TR-12 | 3 | 34 |
| F-017 | MEDIUM | CORS totalmente permissivo sobre 22 rotas anônimas | AP-20 | TR-18 | 3 | 1 |
| F-018 | MEDIUM | Login sem contador, backoff ou bloqueio | AP-24 | TR-05 | **1** | 1 |
| F-019 | LOW | `print()` como log, helper padronizado morto ao lado | AP-19 | TR-14 | **4** | 11 |
| F-020 | LOW | Camada inalcançável, 14 símbolos e 3 deps mortos | AP-26 | TR-15 | **3** | 28 |
| F-021 | LOW | Tradução valor→rótulo e limiares sem nome | AP-25 | TR-18 | **3** | 6 |
| F-022 | LOW | Nome do contrato público divergente do recurso | AP-27 | TR-18 | **3** | 9 |
| F-023 | LOW | Ausência completa de infra de qualidade | AP-28 | — | — | 1 |

**Total: 23 findings · 252 ocorrências.** Onda em negrito = divergente da onda padrão do AP,
porque a onda é propriedade do **TR** que a executa, e o TR é agendado pela onda do finding **mais
severo** que ele resolve:

- **F-018 (MEDIUM) na Onda 1** — TR-05 é agendado por F-004 (CRITICAL) e fecha F-018 de carona.
- **F-020, F-021, F-022 (LOW) na Onda 3** — TR-15 é agendado por F-010 (MEDIUM), TR-18 por F-017 (MEDIUM).
- **F-019 (LOW) na Onda 4** — TR-14 tem teto na Onda 1 (resolve AP-07), mas AP-07 não virou
  finding; o mais severo que ele resolve é F-019 (LOW). Chega à Onda 4 **por descida**, que é
  exatamente como o `SKILL.md` descreve o único caminho de a Onda 4 receber TR.

Nenhum finding recebeu severidade divergente da tabelada no catálogo, logo **nenhuma linha
"Desvio de severidade"** foi necessária. O único caso considerado foi AP-20 (F-017): a nota de
composição do catálogo permitiria elevá-lo onde há autenticação por cookie — não é o caso aqui,
e o dano de escrita anônima já está contabilizado em F-004.

---

## 5. Verificações executadas (não apenas lidas)

A auditoria não se apoiou só em leitura. O que foi confirmado rodando:

| Finding | Verificação | Resultado |
|---|---|---|
| F-001 | `curl` no endpoint do debugger | `HTTP 200`, `EVALEX = true`, `SECRET` no HTML |
| F-002 | `curl http://localhost:5000/users/1` | `"password": "81dc9bdb52d04dc20036dbd8313ed055"` |
| F-003 | `hashlib.md5(b'1234').hexdigest()` | bate com o hash servido pela API |
| F-012 | contador em `before_cursor_execute` | `/tasks` 17 · `/reports/summary` 21 · `/categories` 5 · `/users` 6 |
| F-013 | 3 requisições com tipo inválido | `500 · 500 · 500` |
| F-016 | `python seed.py` e `-W always` | `DeprecationWarning` (utcnow) e `LegacyAPIWarning` (Query.get) |
| AP-01 | `stmt.statement.compile()` | `LIKE :title_1` com parâmetro vinculado → **descartado** |
| AP-14 | busca por `**payload` | nenhum → **descartado** |
| AP-07 | busca por `print` com credencial | nenhum → **descartado** |
| F-023 | listagem no projeto **e um nível acima** | tudo ausente nos dois níveis |

---

## 6. Breaking changes previstas

8 breaking changes, todas previstas **antes** de executar qualquer TR. Nenhuma remoção de
endpoint; os 22 paths, verbos e status de sucesso são preservados.

| # | Endpoints | Mudança | TR |
|---|---|---|---|
| BC-1 | 4 rotas de `User` | `password` sai da resposta | TR-04 |
| BC-2 | `POST /login` | `token` vira credencial assinada (deixa de conter o id) | TR-05 |
| BC-3 | 13 rotas | passam a responder 401 sem credencial | TR-05 |
| BC-4 | 4 listagens | `limit`/`offset`, default 50, array na raiz preservado | TR-17 |
| BC-5 | `GET /tasks` | `user_name`/`category_name` saem do item | TR-13 |
| BC-6 | `GET /users` | `task_count` sai do item | TR-13 |
| BC-7 | 22 rotas, só no erro | envelope de erro uniformizado com código estável | TR-13 |
| BC-8 | 3 caminhos de tipo inválido | 500 → 400, `text/html` → `application/json` | TR-13, TR-08 |

**Efeito previsto sobre o smoke test da Fase 3:** BC-1/5/6 alteram o `shape` de 6 dos 22 registros
do baseline; BC-3 altera o status de 13. Todas são divergências **declaradas**, portanto contam
como conformes (`validation-protocol.md` §4.1) — mas só porque estão na tabela aprovada. BC-7 e
BC-8 tocam caminhos de erro, que o baseline não capturou, e não aparecem em `M = 22`. O roteiro de
smoke precisará **autenticar antes** de exercer as 13 rotas de BC-3 — falso vermelho conhecido da
§8 do protocolo.

---

## 7. Plano por onda

| Onda | Sev. | TRs | Findings resolvidos |
|---|---|---|---|
| **1** | CRITICAL | TR-01 *(primeiro)*, TR-03, TR-04, TR-05 | F-001, F-002, F-003, F-004, F-018 |
| **2** | HIGH | TR-06 *(primeiro)*, TR-07, TR-09, TR-10, TR-16 | F-005, F-006, F-007, F-008, F-009 |
| **3** | MEDIUM | TR-08, TR-11, TR-12, TR-13, TR-15, TR-17, TR-18 | F-010 … F-017, F-020, F-021, F-022 |
| **4** | LOW | TR-14 | F-019 |

**Ondas vazias: nenhuma.** As quatro receberam TR. Critério de aceite idêntico em todas:
**smoke test 22/22 endpoints conformes → commit**.

F-023 (AP-28) **não consta do plano** — ele é reportado e não corrigido, e o catálogo é explícito:
prometer no gate o que a Fase 3 não vai fazer invalidaria o gate.

### Risco declarado no plano

`refactor-playbook.md` avisa que *"aplicar TR-04 antes de haver camadas obriga a refazê-lo"*.
Aqui TR-04 cai na Onda 1 (severidade de F-002, CRITICAL) e TR-06 — que cria as camadas — cai na
Onda 2 (severidade de F-005, HIGH). A regra de onda é a do finding e prevalece; a consequência é
que o DTO criado na Onda 1 será movido na Onda 2. Optei por absorver o retrabalho em vez de subir
TR-06 acima do seu teto, porque isso exigiria atribuir a F-005 severidade maior que a tabelada, e
não há justificativa para tanto.

---

## 8. Itens NEEDS-DECISION

6 itens, cada um com recomendação e alternativa, para que um único `y` continue sendo suficiente.

| # | Decisão | Recomendado |
|---|---|---|
| ND-1 | Quais rotas exigem autenticação (define BC-3) | 10 de escrita/remoção + 3 de leitura de terceiros |
| ND-2 | Migração dos hashes MD5 existentes | reidratação no próximo login bem-sucedido |
| ND-3 | Rotação da credencial SMTP exposta no histórico | rotacionar fora do repositório antes do merge |
| ND-4 | Direção da uniformização de contrato (BC-5/6) | alinhar a coleção ao detalhe (elimina o N+1 junto) |
| ND-5 | Tamanho de página default (BC-4) | `limit=50`, máx. 200, sem envelope |
| ND-6 | Política de senha (mínimo atual: 4 caracteres) | **não alterar** — decisão de produto, fora do escopo |

---

## 9. Prova de que a Fase 2 não escreveu em código do projeto

```console
$ git status --porcelain
?? evidence/run-3/
?? reports/audit-task-manager-api.md
?? reports/baseline-task-manager-api.json

$ git status --porcelain task-manager-api/
(vazio = intocado)
```

As únicas escritas até o gate são as duas permitidas — `BASELINE_PATH` (Fase 1) e `REPORT_PATH`
(Fase 2) —, mais os artefatos de evidência deste run, que são externos à skill. **Nenhum arquivo
de código, manifesto, configuração ou diretório do projeto foi criado, movido ou alterado.**

---

## 10. Gate

Apresentado ao usuário e **aguardando resposta explícita**. Silêncio não é `y`.

```console
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Estado da execução no momento da parada:

| stage    | sha       | smoke  | status |
|----------|-----------|--------|--------|
| baseline | `f580ee5` | —      | green  |
