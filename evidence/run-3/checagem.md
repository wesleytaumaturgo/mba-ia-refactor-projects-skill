# Run-3 · Checagem do operador · `task-manager-api`

Checagem sobre a execução da skill em `task-manager-api`. **CA-1, CA-2 e CA-3 foram fechados
antes de abrir `.planning/analise-manual/task-manager-api.md`** — o cruzamento da §4 usa a
análise manual como termo de comparação independente, não como gabarito consultado durante a
auditoria.

Fontes desta checagem:
- `reports/audit-task-manager-api.md` — relatório da Fase 2 produzido pela skill
- `reports/baseline-task-manager-api.json` — baseline de comportamento
- `evidence/baseline/task-manager-api.md` — meu levantamento manual, feito antes de invocar a skill
- `.planning/analise-manual/task-manager-api.md` — 26 findings, AM-050 a AM-075 (lido só agora)

---

## CA-1 — A Fase 1 detectou a stack corretamente? Campo a campo.

Critério do enunciado: *"Fase 1 detecta stack corretamente — OBRIGATÓRIO (3/3 projetos)"*.

Confronto de cada campo do bloco `PHASE 1: PROJECT ANALYSIS` contra a realidade verificada por
execução:

| # | Campo | Skill declarou | Realidade (verificada) | Como verifiquei | ✓ |
|---|---|---|---|---|---|
| 1 | Language | Python | Python — 15 arquivos `.py`, nenhuma outra extensão de código | `find`+`wc -l` | ✅ |
| 2 | runtime in use | **3.12.3** | 3.12.3 | `python3 --version` executado, não lido do manifesto | ✅ |
| 3 | Framework | Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 + Flask-CORS 4.0.0 | idem | `pip freeze` + imports efetivos | ✅ |
| 4 | Package mgr | `requirements.txt` (pip) | idem — não há `pyproject.toml`, `Pipfile`, `poetry.lock` | `ls` | ✅ |
| 5 | Database | SQLite (`instance/tasks.db`, SQLAlchemy 2.0.52) · **3 tabelas** | SQLite, 3 tabelas: `users`, `tasks`, `categories` | `PRAGMA` no banco real | ✅ |
| 6 | Domain | Gestão de tarefas — tasks atribuídas a users, agrupadas por categories, com relatórios | idem | tabelas ∩ paths ∩ entidades | ✅ |
| 7 | Entry points | `app.py` (servidor) · `seed.py` (script separado, **não** alcançável de `app.py`) | idem | `grep` de imports + `if __name__` | ✅ |
| 8 | Resolution | **explicit import** | correto — Python não tem autoload; sem `importlib`/`pkgutil`/entry-points | `grep -rnE 'importlib\|pkgutil\|__import__\|walk_packages\|entry_points'` → vazio | ✅ |
| 9 | Architecture | MVC parcial; `utils/` alcançável mas não-invocado; `services/` INALCANÇÁVEL | correto (ver §3) | grafo de imports | ✅ |
| 10 | Source files | 15 files | 15 | `find` | ✅ |
| 11 | LOC | 1158 | 1158 | `wc -l` | ✅ |
| 12 | Endpoints | 22 mapped | 22 | `url_map` do Flask | ✅ |
| 13 | baseline captured | 22 responses | 22 registros no JSON | `len()` do artefato | ✅ |
| 14 | Baseline SHA | `f580ee5` | `f580ee5ae44cba…` | `git rev-parse` | ✅ |
| 15 | Baseline file | caminho absoluto sob a raiz do repo | arquivo existe no caminho impresso | `ls` | ✅ |

**CA-1: APROVADO — 15/15 campos corretos.**

### Três acertos que merecem destaque

1. **Versão do runtime obtida executando, não lendo.** O projeto **não declara versão de Python
   em lugar nenhum** — não há `.python-version`, `pyproject.toml`, `setup.cfg` nem `Dockerfile`.
   É exatamente o caso em que a skill avisa que ler o manifesto produziria falso negativo
   silencioso em AP-16. A skill executou `python3 --version` e obteve 3.12.3, o que tornou AP-16
   **verificável** e produziu F-016 (34 chamadas deprecated). A análise manual prévia registrou a
   mesma versão no contexto, mas **não gerou finding de API deprecated** (ver §4.3).

2. **Framework efetivo = declarado ∩ resolvido.** As 6 dependências do `requirements.txt` foram
   separadas em 3 resolvidas (Flask, Flask-SQLAlchemy, Flask-CORS) e 3 declaradas-e-nunca-
   importadas (`marshmallow`, `requests`, `python-dotenv`). Estas últimas não foram tratadas como
   stack — foram para AP-26, e a skill ainda extraiu delas a leitura de "arquitetura pretendida e
   não implementada", mapeando `marshmallow`→F-011 e `python-dotenv`→F-001.

3. **Dois entry points, com a direção correta.** A skill não se enganou com `seed.py`: identificou
   que ele **não é alcançável a partir de `app.py`** e que a relação é inversa (`seed.py:2` importa
   `app`). Registrou o efeito colateral consequente — `db.create_all()` em escopo de módulo roda
   no mero `import app` do seed —, que virou parte de F-007.

---

## CA-2 — Número real de findings (contado, não declarado)

Critério do enunciado: *"Fase 2 encontra >= 5 findings — OBRIGATÓRIO"*.

Contagem feita sobre os cabeçalhos do relatório, não sobre o número que ele declara:

```console
$ grep -cE '^### \[(CRITICAL|HIGH|MEDIUM|LOW)\] F-' reports/audit-task-manager-api.md
23
$ grep -oE '^### \[(CRITICAL|HIGH|MEDIUM|LOW)\]' reports/audit-task-manager-api.md | sort | uniq -c
      4 ### [CRITICAL]
      5 ### [HIGH]
      9 ### [MEDIUM]
      5 ### [LOW]
```

Numeração `F-001` … `F-023`, contínua através das severidades, sem lacuna e sem repetição.
Toda referência cruzada `F-0NN` no documento resolve para um finding declarado (verificado por
script: **0 referências órfãs**).

**CA-2: 23 findings reais** — 4 CRITICAL · 5 HIGH · 9 MEDIUM · 5 LOW. Mínimo exigido: 5.
**APROVADO com folga de 4,6×.**

### O relatório inflou a contagem?

Não. Checagem da regra "um finding por causa, não por ocorrência":

- **F-016** agrupa 34 chamadas deprecated (18 `utcnow()` + 16 `Query.get()`) num finding. Um
  relatório inflado teria 34.
- **F-004** agrupa as 22 rotas sem autenticação num finding, não 22.
- **F-010** agrupa 21 cópias de 6 regras distintas num finding de causa única (abstração morta).
- **F-013** agrupa 12 `except:` num finding.

Total de ocorrências: 252 em 23 findings — razão de ~11 ocorrências por finding. O relatório
**comprime**, não infla.

Confirmação adicional: a skill **descartou 5 dos 28 APs** com justificativa e evidência, e o fez
em duas categorias que o enunciado nomeia explicitamente na escala de severidade (SQL Injection e
God Class). Um relatório de cota teria reportado ambas.

---

## CA-3 — Há pelo menos 1 CRITICAL ou HIGH?

Critério do enunciado: *"Fase 2 inclui pelo menos 1 CRITICAL ou HIGH — OBRIGATÓRIO"*.

**9 findings** CRITICAL ou HIGH — 4 + 5. Todos com `arquivo:linha` e bloco de código literal:

| # | Sev | Finding | Evidência-âncora |
|---|---|---|---|
| F-001 | CRITICAL | Segredo, credencial SMTP e debug literais | `app.py:13`, `app.py:34`, `notification_service.py:10` |
| F-002 | CRITICAL | Hash de senha na resposta de 4 endpoints | `models/user.py:21` |
| F-003 | CRITICAL | MD5 sem salt, comparação por igualdade | `models/user.py:29,32` |
| F-004 | CRITICAL | 22 rotas sem verificação de identidade | `user_routes.py:210` |
| F-005 | HIGH | Rotas manipulam a sessão do ORM | `task_routes.py:2,147-152` |
| F-006 | HIGH | Regra de domínio nos handlers | `task_routes.py:30-39` |
| F-007 | HIGH | DDL no boot + schema sem constraints | `app.py:30-31` |
| F-008 | HIGH | Escritas sem fronteira transacional | `user_routes.py:140-151` |
| F-009 | HIGH | Singleton global, sem injeção | `app.py:9-20` |

Quatro deles foram confirmados **por execução**, não só por leitura — hash servido pela API
batendo com `MD5("1234")`, console do Werkzeug respondendo 200, 500 em três entradas inválidas,
e a contagem de queries do N+1.

**CA-3: APROVADO — 9 findings CRITICAL/HIGH contra 1 exigido.**

---

## 4. Cruzamento com a análise manual prévia

Análise manual: **26 findings**, AM-050 a AM-075 — **5 CRITICAL · 3 HIGH · 11 MEDIUM · 7 LOW**,
contados nos cabeçalhos.
Skill: **23 findings**, F-001 a F-023 — 4 CRITICAL · 5 HIGH · 9 MEDIUM · 5 LOW.

> **Divergência interna na análise manual, encontrada ao contar.** A tabela "Resumo" do dossiê
> declara `CRITICAL 4 · HIGH 4`, mas os cabeçalhos dizem `CRITICAL 5 · HIGH 3`. A causa está na
> própria seção de metodologia do dossiê: *"AM-054 reclassificado de HIGH para CRITICAL"* — o
> cabeçalho foi atualizado e a tabela-resumo não. O total (26) e o subtotal CRITICAL+HIGH (8) estão
> corretos nas duas leituras, então nada nesta checagem muda; uso a contagem dos cabeçalhos, que é
> a fonte de verdade. Registro porque "contagem real" é o critério do CA-2, e ele vale para os dois
> lados da comparação.

A diferença de contagem **não** é diferença de cobertura: a skill agrupa por causa onde a análise
manual separa por sintoma. O mapeamento abaixo é por conteúdo.

### 4.1 Mapa AM → F

| AM | Sev (AM) | Assunto | Coberto por | Sev (F) | Grau |
|---|---|---|---|---|---|
| AM-050 | CRITICAL | MD5 sem salt | **F-003** | CRITICAL | ✅ total |
| AM-051 | CRITICAL | `to_dict` expõe hash de senha | **F-002** | CRITICAL | ✅ total |
| AM-052 | CRITICAL | `SECRET_KEY` hardcoded + debug | **F-001** | CRITICAL | ✅ total |
| AM-053 | CRITICAL | Credencial SMTP hardcoded | **F-001** | CRITICAL | ✅ total (agrupado) |
| AM-054 | CRITICAL¹ | Token falso, nenhuma rota valida | **F-004** | CRITICAL | ✅ total |
| AM-055 | HIGH | Regra "atrasada" 6× com `is_overdue` morto | **F-010** + **F-006** | MEDIUM + HIGH | ✅ total |
| AM-056 | HIGH | Validação de domínio nos handlers | **F-011** + **F-010** | MEDIUM | ✅ total |
| AM-057 | HIGH | Rotas acopladas ao ORM, sem service | **F-005** | HIGH | ✅ total |
| AM-058 | MEDIUM | N+1 com relacionamentos declarados | **F-012** | MEDIUM | ✅ total |
| AM-059 | MEDIUM | Agregações em Python sobre tabela inteira | **F-012** (variante correlata) | MEDIUM | ✅ total (agrupado) |
| AM-060 | MEDIUM | Sem paginação | **F-015** | MEDIUM | ✅ total |
| AM-061 | MEDIUM | Serialização manual duplicando `to_dict` | **F-014** + **F-010** | MEDIUM | ✅ total |
| AM-062 | MEDIUM | Validação duplicada criar/atualizar, regex 3× | **F-011** (agravante) + **F-010** | MEDIUM | ✅ total |
| AM-063 | MEDIUM | `except:` nu | **F-013** | MEDIUM | ✅ total |
| AM-064 | MEDIUM | Entrada não validada → 500 | **F-013** (consequência confirmada) | MEDIUM | ✅ total (agrupado) |
| AM-065 | MEDIUM | Política de deleção inconsistente, órfãos | **F-008** | **HIGH** | ✅ total (severidade ↑) |
| AM-066 | MEDIUM | `print()` como log | **F-019** | **LOW** | ✅ total (severidade ↓) |
| AM-067 | MEDIUM | CORS sem restrição | **F-017** | MEDIUM | ✅ total |
| AM-068 | MEDIUM | Schema criado no import | **F-007** | **HIGH** | ✅ total (severidade ↑) |
| AM-069 | LOW | `utils/helpers.py` inteiro morto | **F-020** + **F-010** | LOW + MEDIUM | ✅ total |
| AM-070 | LOW | `services/` existe e nunca é usado | **F-020** | LOW | ✅ total |
| AM-071 | LOW | Métodos de domínio nunca invocados | **F-020** + **F-010** | LOW | ✅ total |
| AM-072 | LOW | Imports não utilizados | **F-020** | LOW | ✅ total (agrupado) |
| AM-073 | LOW | Dependências declaradas e nunca importadas | **F-020** | LOW | ✅ total (agrupado) |
| AM-074 | LOW | Magic numbers / mapeamento de prioridade | **F-021** | LOW | ✅ total |
| AM-075 | LOW | `type() == list`, nomes de 1 letra, `updated_at` redundante | **F-022** | LOW | ⚠️ **PARCIAL** |

¹ AM-054 consta como CRITICAL no cabeçalho (reclassificado de HIGH pela validação do próprio
dossiê) e como HIGH na tabela-resumo dele. Adoto o cabeçalho.

### 4.2 Cobertura

| Métrica | Valor |
|---|---|
| AM cobertos **totalmente** | **25 de 26** |
| AM cobertos **parcialmente** | 1 (AM-075) |
| AM **não cobertos** | 0 |
| **Cobertura total** | **25/26 = 96,2%** |
| **Cobertura ponderada** (parcial = 0,5) | **25,5/26 = 98,1%** |

Por severidade da análise manual:

| Sev (AM) | Total | Cobertos | % |
|---|---|---|---|
| CRITICAL | 5 | 5 | **100%** |
| HIGH | 3 | 3 | **100%** |
| MEDIUM | 11 | 11 | **100%** |
| LOW | 7 | 6 totais + 1 parcial | **93%** |

**Os 8 findings CRITICAL/HIGH da análise manual foram cobertos integralmente — 100%.**

### 4.3 Findings NOVOS da skill (ausentes da análise manual)

Três, e um deles é significativo:

1. **F-016 — 34 chamadas deprecated (AP-16). NOVO E RELEVANTE.**
   A análise manual **não tem nenhum finding de API deprecated**. Ela registra a versão 3.12.3 no
   quadro de contexto e para aí. A skill cruzou as chamadas contra a versão **real** do runtime e
   contra a versão **instalada** do ORM, e produziu evidência de execução para as duas famílias:

   ```console
   DeprecationWarning: datetime.datetime.utcnow() is deprecated …    (Python 3.12, ×18)
   LegacyAPIWarning: The Query.get() method … (deprecated since: 2.0) (SQLAlchemy 2.0.52, ×16)
   ```

   Isso importa porque o enunciado exige nominalmente: *"O catálogo deve incluir detecção de APIs
   deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno"*. A skill
   entregou o que a auditoria humana deixou passar, e a detecção do `Query.get()` — que exige
   conhecer a versão *instalada do ORM*, não só a do runtime — é o achado mais fino do run.

2. **F-018 — sem rate limiting no `/login` (AP-24). NOVO.**
   Ausente da análise manual. A skill registrou também o sinal correlato que o catálogo pede: hoje
   a força bruta é desnecessária porque `GET /users/<id>` entrega o hash; quando TR-03/TR-05
   corrigirem isso, a força bruta vira o caminho mais barato — e é por isso que o controle de taxa
   precisa entrar **junto** e não depois.

3. **F-023 — ausência de infraestrutura de qualidade (AP-28). NOVO como finding próprio.**
   A análise manual menciona a ausência de lint/teste/CI *dentro do impacto de AM-072*, mas não a
   promove a finding. A skill a isolou, verificou **um nível acima** (raiz do monorepo) como o
   contra-exemplo do AP exige, e — corretamente — **não a incluiu no plano do gate**, porque o
   catálogo diz que AP-28 é reportado e não corrigido.

Sub-achados novos dentro de findings existentes:

- **`PRAGMA foreign_keys = 0` medido no banco real** (F-007). A análise manual afirma em AM-065
  que "o SQLite não impõe chave estrangeira por padrão"; a skill **verificou** o pragma no banco e
  usou isso para tornar o cenário de órfãos de F-008 concreto em vez de teórico.
- **Ausência de índice em `tasks.user_id`, `tasks.category_id`, `tasks.status`** (F-007) —
  exatamente as colunas que as rotas filtram. Ausente da análise manual.
- **Ausência de CHECK sobre `status` e `priority`** (F-007). A análise manual toca nisso em AM-056
  ("o schema também não restringe"), mas sem inventariar.
- **Check-then-act na unicidade de e-mail** (F-008) — o par verificação/consumação de
  `user_routes.py:67-69` → `:80-82`, com a observação de que o índice UNIQUE salva o banco mas a
  captura genérica converte o 409 em 500. Ausente da análise manual.
- **Contagem de queries medida** (F-012): 17 / 21 / 6 / 5 por endpoint, com instrumentação real.
  A análise manual estimou (`1 + 2N`) sem medir.

### 4.4 Falsos positivos e findings contestáveis

**Falsos positivos: nenhum.** Todos os 23 findings têm `arquivo:linha` e bloco de código literal
copiado do projeto, e reconferi por amostragem os 9 CRITICAL/HIGH linha a linha contra o fonte.
Nenhum finding aponta para linha inexistente ou parafraseia evidência.

**Um finding contestável, que registro por disciplina:**

- **F-022 (AP-27, nomenclatura).** A tese é que `reports.get_categories` é "nome do contrato
  público divergente do vocabulário do domínio". O nome do endpoint Flask é usado por `url_for`,
  mas é discutível chamá-lo de *contrato público* — o path (`/categories`) está correto, e é o
  path que o cliente HTTP vê. Se este finding fosse descartado, CA-2 cairia para 22 e nada mais
  mudaria: TR-18 continua agendado por F-017 e F-021. **Confiança que eu atribuiria em revisão:
  MÉDIA, não ALTA como o relatório declara.** É o único ponto do relatório onde discordo da
  confiança declarada.

Vale registrar o que **não** é falso positivo, apesar de parecer contra-intuitivo: a skill
**descartou** AP-06 (God Class) e AP-01 (SQL Injection), e a análise manual independente chegou à
mesma conclusão, com o mesmo raciocínio — ver a seção "Observação de disciplina de auditoria" do
dossiê manual. Duas auditorias independentes convergindo em duas rejeições é o sinal mais forte
de que o catálogo tem contra-exemplos que funcionam.

### 4.5 A lacuna real: AM-075

Único item de cobertura parcial. AM-075 reúne três coisas; a skill pegou uma:

| Item de AM-075 | `arquivo:linha` | Skill cobriu? |
|---|---|---|
| Nomes de variável de uma letra (`t`, `u`, `c`, `n`) | rotas em geral | ❌ — **descartado deliberadamente** pelo contra-exemplo do AP-27 ("índice de laço" é isenção explícita). Decisão defensável, e a skill a registrou. |
| `type(tags) == list` em vez de `isinstance` | `task_routes.py:141`, `:210`, `helpers.py:103` | ❌ **não reportado** — lacuna genuína |
| `task.updated_at = datetime.utcnow()` redundante, com `onupdate` já declarado em `models/task.py:16` | `task_routes.py:215` | ❌ **não reportado** — lacuna genuína |

**Diagnóstico da lacuna.** Nenhum dos 28 APs do catálogo tem sinal que capture "comparação de tipo
por classe exata em vez do operador de instância" ou "atribuição manual redundante com o que o
mapeamento já faz". Não é falha de execução da skill — é **lacuna de cobertura do catálogo**. O
AP-27 mais próximo trata de *nomes*, não de *construtos*.

**Impacto: baixo.** Os dois itens são LOW na escala da própria análise manual, sem efeito
observável em produção, e ambos seriam varridos por um linter — que é justamente o que TR-12
instala (F-016) e o que F-023 aponta como ausente. Ou seja, a correção deles chega de carona.

**Não estou propondo alterar a skill por causa disso.** Ver §6.

---

## 5. Alcançabilidade das quatro camadas preexistentes — o registro explícito pedido

Este era o ponto que o projeto foi escolhido para exercitar. Regra aplicada:
`mvc-guidelines.md` §6 — *"adote um diretório de camada preexistente se e somente se ao menos um
dos seus símbolos for alcançável a partir dos entry points pelo mecanismo de resolução da stack"*.

Mecanismo determinado na Fase 1: **import explícito**, e a skill provou que é o único mecanismo
em jogo antes de concluir qualquer coisa:

```console
$ grep -rnE 'importlib|pkgutil|__import__|walk_packages|entry_points' --include='*.py' .
(nenhuma saída)
```

Isso é o passo que a `project-analysis.md` §6 chama de "determine primeiro qual mecanismo a stack
usa; só então percorra". Sem ele, concluir "não importado ⇒ morto" seria atalho; com ele, é
conclusão.

### Veredito, camada a camada

| Camada | Alcançável? | Veredito | Símbolo que a torna alcançável | AP-26? |
|---|---|---|---|---|
| `models/` | **SIM** | **ADOTADA** | `Task`, `User`, `Category` — `task_routes.py:3-5`, `user_routes.py:3-4`, `report_routes.py:3-5` | não |
| `routes/` | **SIM** | **ADOTADA** | `task_bp`, `user_bp`, `report_bp` — `app.py:4-6`, registrados em `:18-20` | não |
| `utils/` | **SIM** | **ADOTADA** | `format_date`, `calculate_percentage` — `report_routes.py:7` | **não** |
| `services/` | **NÃO** | **AP-26** (F-020) | nenhum — zero importadores | **sim** |

**Três das quatro camadas preexistentes são alcançáveis e foram adotadas. Uma virou AP-26:
`services/`.**

### Por que `utils/` NÃO virou AP-26 — a decisão mais fina do run

É a distinção que a regra existe para preservar, e a skill acertou:

- `utils/` **é** alcançável. `report_routes.py:7` é import explícito — o mecanismo real desta
  stack — e o módulo entra na memória no boot da aplicação. A regra §6 é sobre **alcançabilidade
  do símbolo**, não sobre invocação. Logo: **camada adotada**.
- Mas dos seus **16 símbolos públicos**, 2 são importados e **0 são invocados**:

  ```console
  $ grep -rn -E 'format_date|calculate_percentage' --include='*.py' .
  utils/helpers.py:9:def format_date(date_obj):
  utils/helpers.py:14:def calculate_percentage(part, total):
  routes/report_routes.py:7:from utils.helpers import format_date, calculate_percentage
  ```

  Duas definições, um import, **zero chamadas**.
- A skill alocou isso corretamente em **duas categorias distintas**: os 2 importados-e-não-
  chamados em **AP-17** (F-010, duplicação com a abstração correta morta), e os 14 nunca sequer
  importados em **AP-26** (F-020). A *camada* segue adotada; o *conteúdo* é finding.

Os dois erros simétricos que a regra previne, ambos evitados:

| Erro possível | O que produziria | Evitado? |
|---|---|---|
| Rebaixar `utils/` a AP-26 porque "ninguém a chama" | remoção de uma camada que o boot carrega, e perda da distinção AP-17/AP-26 | ✅ evitado |
| Promover `services/` a camada porque "tem nome de camada e está no lugar certo" | Fase 3 construindo sobre módulo que nenhum caminho de execução alcança | ✅ evitado |

A análise manual prévia chegou à mesma conclusão material — AM-069 (`utils/` morto) e AM-070
(`services/` nunca usado) — mas **sem a distinção entre alcançável e invocado**: ela chama
`utils/helpers.py` de "integralmente código morto". Tecnicamente, o módulo é carregado no boot;
o que está morto é o seu conteúdo. A skill é mais precisa aqui, e a precisão tem consequência
operacional direta: `utils/` é **ligado** (TR-15, "consolidar na abstração existente"), enquanto
`services/` é **substituído** — transformações diferentes, decididas pela regra.

### Registro exigido antes da remoção

`mvc-guidelines.md` §6 obriga a registrar como finding tudo o que a camada inalcançável contém,
**antes** de propor removê-la. A skill cumpriu em F-020: inventariou `NotificationService`
(`send_email`, `notify_task_assigned`, `notify_task_overdue`, `get_notifications`, o acumulador
`self.notifications`) e **a credencial SMTP versionada** (`notification_service.py:9-10`) — esta
última reportada em F-001 (CRITICAL) e promovida a item **ND-3** do gate, com a observação de que
apagar o arquivo não remove o segredo do histórico do git.

### `seed.py` — verificado, como a tarefa pediu

**`seed.py` NÃO é alcançável a partir do entry point.** É um **script separado** com ponto de
entrada próprio:

- `app.py` não o importa em lugar nenhum.
- A relação é **inversa**: `seed.py:2` faz `from app import app, db`.
- `seed.py:98-99` tem `if __name__ == '__main__': seed_data()`.
- O README o documenta como passo manual anterior ao boot.

A skill o classificou como **segundo entry point**, não como código morto — o que é correto: ele
é executado, só que por outro comando. E extraiu a consequência: como `app.py:30-31` roda
`db.create_all()` em escopo de módulo, o `import app` do seed dispara a DDL como efeito colateral,
o que virou parte de F-007.

Isso também tem efeito na metade não-encontrada de AP-21: o sinal do AP inclui *"dados de
demonstração inseridos incondicionalmente em qualquer ambiente, no mesmo corpo que cria o
schema"*. Aqui o seed **está** separado e guardado por `__main__`, então a skill reportou apenas a
metade DDL e **registrou explicitamente que a metade seed não se aplica** — um ponto a favor do
projeto, dito em voz alta em vez de silenciado.

---

## 6. Ajustes na skill? Não.

A restrição da tarefa é clara: *"ajuste na skill exigiria re-propagação e re-execução dos projetos
1 e 2 → PARE E REPORTE antes de qualquer alteração"*.

**Nenhuma alteração foi feita na skill.** Registro aqui o que eu consideraria em uma rodada
futura, para decisão sua — **não** implementado:

| # | Observação | Gravidade | Exigiria re-propagação? |
|---|---|---|---|
| O-1 | O catálogo não tem sinal para "comparação de tipo por classe exata" nem para "atribuição redundante com o que o ORM já faz" (lacuna AM-075). Caberia como ocorrência dentro de AP-27 ou AP-16. | **Baixa** — LOW, sem efeito em produção, varrido por linter | **Sim** |
| O-2 | A pré-condição §3 deriva o nome do artefato do "nome do diretório do projeto", mas o comando manda executar "sobre o diretório de trabalho atual". Num monorepo com 3 projetos irmãos, o cwd é a raiz e o nome do projeto não sai dela. Resolvi como `task-manager-api` por ser o alvo declarado. | **Baixa** — ambiguidade só aparece em monorepo; a skill imprime os caminhos antes de gravar, então o operador confere | **Sim** |
| O-3 | Tensão real no plano: o playbook diz *"aplicar TR-04 antes de haver camadas obriga a refazê-lo"*, mas a regra de onda (propriedade do finding) põe TR-04 na Onda 1 e TR-06 na Onda 2 sempre que houver AP-03 CRITICAL sem AP-06. Não é defeito — as duas regras estão certas e a de onda prevalece —, mas o custo (retrabalho do DTO) merecia estar previsto no playbook. | **Baixa** — a skill **detectou e declarou** a tensão no gate por conta própria | **Sim** |

Nenhuma das três justifica, na minha avaliação, o custo de re-propagar a skill e reexecutar os
projetos 1 e 2. **Recomendo prosseguir sem alterar a skill.** Se você discordar de O-3, ele é o
único com efeito sobre a execução da Fase 3.

---

## 7. Conformidade de processo

| Regra do `SKILL.md` | Cumprida? | Evidência |
|---|---|---|
| Working tree limpo antes da Fase 1 | ✅ | `git status --porcelain` vazio, `f580ee5` registrado |
| SHA de baseline como linha 1 do registro de ondas | ✅ | tabela em `fase1.md` §1 |
| `REPORT_PATH`/`BASELINE_PATH` ancorados na **raiz do repo**, não no cwd | ✅ | ambos sob `<raiz>/reports/`, impressos antes de gravar |
| Declaração "auditoria read-only até o gate" | ✅ | emitida antes da Fase 1 |
| Versão do runtime obtida **executando** | ✅ | `python3 --version` → 3.12.3 |
| Baseline capturado por último, código intocado | ✅ | 22/22, `git status` do projeto vazio na captura |
| Baseline persistido em disco | ✅ | `reports/baseline-task-manager-api.json`, 22 registros com `shape` |
| Rotas destrutivas por último, sobre dado descartável | ✅ | 3 DELETE ao fim, sobre `smoke@baseline.test` / `Smoke Cat` / `Smoke Task` |
| Servidor derrubado ao fim | ✅ | `curl_rc=7` |
| Os 28 APs varridos na ordem do catálogo | ✅ | tabela completa em `fase2.md` §2 |
| Todo finding com `arquivo:linha` + código literal | ✅ | 23/23 |
| Seção "o que não foi encontrado" com estado nomeado | ✅ | 5 APs, todos como **não encontrado**, com a razão |
| Severidade divergente justificada | ✅ | nenhuma divergiu; o único caso considerado (AP-20) foi registrado e mantido |
| Breaking changes enumeradas **por endpoint** | ✅ | 8 BCs, com os endpoints listados, não "em geral" |
| Plano por onda, com ondas vazias nomeadas | ✅ | 4 ondas com TR; "vazias: nenhuma" dito explicitamente |
| AP-28 **fora** do plano do gate | ✅ | F-023 reportado, sem TR, e o relatório diz por quê |
| NEEDS-DECISION com recomendação + alternativa | ✅ | 6 itens (ND-1…ND-6) |
| Prompt do gate literal, e parada | ✅ | `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` |
| **Nenhuma escrita em arquivo do projeto antes do gate** | ✅ | `git status --porcelain task-manager-api/` → **vazio** |

### A verificação que mais importa

```console
$ git status --porcelain
?? evidence/run-3/
?? reports/audit-task-manager-api.md
?? reports/baseline-task-manager-api.json

$ git status --porcelain task-manager-api/
(vazio)
```

As únicas escritas são as duas que o `SKILL.md` autoriza — `BASELINE_PATH` e `REPORT_PATH` — mais
os artefatos de evidência deste run, que são externos à skill. **Zero arquivos do projeto criados,
movidos ou alterados.**

---

## 8. Resumo

| Item | Resultado |
|---|---|
| **CA-1** — Fase 1 detecta a stack | ✅ **APROVADO — 15/15 campos** |
| **CA-2** — findings reais (contados) | **23** (4 CRITICAL · 5 HIGH · 9 MEDIUM · 5 LOW) — mínimo 5 |
| **CA-3** — ≥1 CRITICAL ou HIGH | ✅ **9** |
| **CA-4** — Fase 3 aplicação funciona | ⏸ **não avaliado — parado no gate, como a tarefa pediu** |
| Cobertura vs. análise manual | **25/26 totais + 1 parcial = 96,2%** (98,1% ponderada) |
| Cobertura dos CRITICAL/HIGH manuais | **8/8 = 100%** |
| Findings novos da skill | **3** — F-016 (deprecated, o mais relevante), F-018 (rate limit), F-023 (infra) |
| Falsos positivos | **0** |
| Findings contestáveis | **1** — F-022, confiança MÉDIA e não ALTA |
| Lacunas | **1 parcial** — AM-075 (`type()==list`, `updated_at` redundante); lacuna do catálogo, não da execução |
| Camadas preexistentes **adotadas** | **3** — `models/`, `routes/`, `utils/` |
| Camadas preexistentes → **AP-26** | **1** — `services/` |
| `seed.py` | **script separado**, não alcançável do entry point — classificado corretamente |
| Alterações na skill | **nenhuma** — 3 observações registradas para decisão futura |
| Arquivos do projeto modificados | **0** |

**Estado:** parado no gate da Fase 2, aguardando `y`/`n` explícito.

| stage    | sha       | smoke  | status |
|----------|-----------|--------|--------|
| baseline | `f580ee5` | —      | green  |
