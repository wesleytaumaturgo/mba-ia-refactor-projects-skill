# Run 1 — Checagem da skill `refactor-arch` (Fases 1 e 2)

Auditoria da execução, feita pelo operador. A análise manual (`AM-001`–`AM-027`) só foi lida
**após** o gate da Fase 2, para preservar a independência do cruzamento.

- **Data:** 2026-08-17
- **Projeto alvo:** `code-smells-project/`
- **Invocação:** `/refactor-arch` **sem argumento** — caminhos default resolvidos pela skill
- **Commit de baseline:** `ec6d1d4`
- **Gate:** apresentado e **não respondido**. Fase 3 não executada.

---

## CA-1 — A stack detectada bate com a realidade?

Comparação campo a campo do bloco `PHASE 1` contra os fatos conhecidos do projeto.

| Campo | Realidade | Bloco PHASE 1 da skill | Veredito |
|---|---|---|---|
| Linguagem / runtime | Python 3.12 | `Python (runtime in use: 3.12.3)` | ✅ confere — mais preciso que o esperado (patch incluído) |
| Framework | Flask 3.1.1 | `Flask 3.1.1 (+ flask-cors 5.0.1)` | ✅ confere — acrescenta `flask-cors 5.0.1`, que também é real |
| Persistência | sqlite3 direto | `SQLite · sqlite3 stdlib (lib 3.45.1) · 4 tables` | ✅ confere |
| Arquivos-fonte | 4 | `4 files` | ✅ confere |
| LOC | ~780 | `780 LOC` | ✅ confere — exato |

**CA-1: APROVADO.** Nenhuma divergência em nenhum dos cinco campos.

Verificação do procedimento, não só do resultado: a skill obteve a versão **executando** o
interpretador (`python3 --version` → `Python 3.12.3`) e não lendo do manifesto — que aliás não
declara versão alguma. Isso é o que o `project-analysis.md` §3 exige, e é a diferença entre
verificar AP-16 contra a versão certa e produzir falso negativo silencioso.

### Campos extras conferidos (não exigidos pelo CA-1)

| Campo | Valor da skill | Conferência |
|---|---|---|
| Endpoints | `19 mapped` | ✅ confere — `grep -c add_url_rule` = 16, `grep -c @app.route` = 3, total 19 |
| Entry point | `app.py` | ✅ confere |
| Mecanismo de resolução | `explicit import` | ✅ confere — sem autoload, sem varredura, sem container |
| Baseline SHA | `ec6d1d4` | ✅ confere com `git rev-parse --short HEAD` |

> **Divergência encontrada — no dossiê manual, não na skill.** O dossiê `AM` conta as rotas de
> forma inconsistente consigo mesmo: diz "registra 15 rotas via `add_url_rule`" e "define três
> rotas inline" (= 18) na seção de arquitetura, e "17 rotas" em AM-008 e AM-019. A contagem real
> é **19** (16 + 3), confirmada por `grep`. A skill acertou; o gabarito é que erra aqui, em três
> números mutuamente incompatíveis.

---

## CA-2 — Número real de findings

**Contado, não estimado** — `grep -c "^### \[" reports/audit-code-smells-project.md` = **26**.

| Severidade | Findings | Conferência por `grep`+`uniq -c` |
|---|---|---|
| CRITICAL | 8 | ✅ 8 |
| HIGH | 6 | ✅ 6 |
| MEDIUM | 7 | ✅ 7 |
| LOW | 5 | ✅ 5 |
| **Total** | **26** | ✅ 26 |

Numeração contínua e sem lacuna, conferida: `F-001` … `F-026`, 26 identificadores únicos, sem
reinício por seção — conforme a regra do `report-template.md`.

**CA-2: 26 findings.**

---

## CA-3 — Há ≥1 CRITICAL ou HIGH?

**Sim — 14** (8 CRITICAL + 6 HIGH), contra o mínimo de 1.

Três dos CRITICAL não foram apenas lidos, foram **provados por execução** durante a Fase 2:

| Finding | Prova executada | Resultado literal |
|---|---|---|
| F-001 (AP-01) | `POST /login` com `{"senha":"x' OR '1'='1"}` | `200` + `{"tipo":"admin"}` — autenticou como administrador sem a senha |
| F-001 (AP-01) | `GET /produtos/busca?categoria=informatica' OR '1'='1` | `200` + os 10 produtos, incluindo `moveis` e `vestuario` — filtro derrotado |
| F-013 (AP-21) | dois `POST /usuarios` com o mesmo e-mail | `201` e `201` — sem `UNIQUE` |
| F-012 (AP-11) | `POST /pedidos` → `DELETE /produtos/3` → `GET /pedidos` | `"produto_nome": "Desconhecido"` — órfão confirmado |
| F-015 (AP-18) | `POST /produtos` com `"preco":"abc"` | `500` + `{"erro":"'<' not supported between instances of 'str' and 'int'"}` |

**CA-3: APROVADO.**

---

## CRUZAMENTO — 27 findings manuais × relatório da skill

Legenda de "Reencontrado": **✅ finding próprio** — a skill abriu um finding dedicado ·
**🔶 dobrado** — coberto dentro de um finding da skill com outro recorte ·
**⚠️ parcial** — parte da acusação coberta, parte não ·
**📄 documentado** — descrito no relatório com evidência, mas deliberadamente **não** como finding.

| AM-ID | Severidade manual | Reencontrado? | F-ID | Severidade da skill | Divergência de severidade? |
|---|---|---|---|---|---|
| AM-001 SQL injection pervasiva | CRITICAL | ✅ | F-001 | CRITICAL | — |
| AM-002 `/admin/query` SQL arbitrário | CRITICAL | ✅ | F-008 | CRITICAL | — |
| AM-003 segredo hardcoded + debug | CRITICAL | ✅ | F-003 | CRITICAL | — |
| AM-004 segredo vazado em `/health` | CRITICAL | ✅ | F-007 | CRITICAL | — |
| AM-005 senhas em texto puro | CRITICAL | ✅ | F-004 | CRITICAL | — |
| AM-006 `senha` na serialização | CRITICAL | ✅ | F-006 | CRITICAL | — |
| AM-007 `/admin/reset-db` sem auth | CRITICAL | 🔶 | F-002 | CRITICAL | — |
| AM-008 ausência de auth/authz | HIGH | ✅ | F-002 | **CRITICAL** | **⬆ skill mais severa (HIGH → CRITICAL)** |
| AM-009 conexão global mutável | HIGH | ✅ | F-014 | HIGH | — |
| AM-010 acoplamento sem DI | HIGH | ✅ | F-009 | HIGH | — |
| AM-011 efeitos colaterais no controller | HIGH | ✅ | F-010 | HIGH | — |
| AM-012 validação de domínio no controller | HIGH | ✅ | F-018 | **MEDIUM** | **⬇ skill menos severa (HIGH → MEDIUM)** |
| AM-013 escrita multi-etapa sem transação | HIGH | ✅ | F-012 | HIGH | — |
| AM-014 precificação na camada de dados | HIGH | 🔶 | F-010 | HIGH | — |
| AM-015 N+1 na listagem de pedidos | MEDIUM | ✅ | F-019 | MEDIUM | — |
| AM-016 duplicação integral do bloco de listagem | MEDIUM | **📄** | — | — | **não virou finding** |
| AM-017 bloco de validação copiado | MEDIUM | ⚠️ | F-018 | MEDIUM | — (só a divergência criar/atualizar) |
| AM-018 validação ausente em rotas de escrita | MEDIUM | ⚠️ | F-013, F-015 | HIGH, MEDIUM | — (2 de 4 sub-acusações) |
| AM-019 CORS irrestrito | MEDIUM | ✅ | F-020 | MEDIUM | — |
| AM-020 detalhe de exceção vazado | MEDIUM | ✅ | F-015 | MEDIUM | — |
| AM-021 `print()` como log | MEDIUM | ✅ | F-022 (+F-005) | **LOW** (+CRITICAL) | **↕ dividido: mecanismo ⬇ LOW, PII ⬆ CRITICAL** |
| AM-022 DDL + seed na factory | MEDIUM | ✅ | F-013 | **HIGH** | **⬆ skill mais severa (MEDIUM → HIGH)** |
| AM-023 magic numbers | LOW | ⚠️ | F-024 | LOW | — (limiares de desconto sim; tamanhos de nome excluídos por regra) |
| AM-024 vocabulários literais inline | LOW | ⚠️ | F-018, F-010 | MEDIUM, HIGH | — (citados como ocorrência, sem finding próprio) |
| AM-025 imports mortos | LOW | ✅ | F-025 | LOW | — |
| AM-026 builtin `id` sombreado | LOW | ✅ | F-023 | LOW | — |
| AM-027 contrato de resposta inconsistente | LOW | ✅ | F-017 | **MEDIUM** | **⬆ skill mais severa (LOW → MEDIUM)** |

### Cobertura

| Categoria | Qtde | % dos 27 |
|---|---|---|
| ✅ Finding próprio na skill | 21 | 77,8% |
| 🔶 Dobrado em finding de outro recorte | 2 | 7,4% |
| ⚠️ Parcial | 3 | 11,1% |
| 📄 Documentado, sem finding | 1 | 3,7% |
| ❌ Ausente do relatório | **0** | **0%** |

- **Cobertura estrita** (finding próprio ou dobrado): **23/27 = 85,2%**
- **Cobertura ampla** (o assunto aparece no relatório com evidência, em qualquer forma): **27/27 = 100%**

Nenhum dos 27 findings manuais passou despercebido. O gabarito não pegou a skill em omissão
silenciosa: os quatro casos abaixo de "finding próprio" são todos de **recorte declarado**, não
de cegueira — o relatório diz onde cada um está e por quê.

### Divergências de severidade — cinco, todas justificadas no relatório

| AM-ID | Manual | Skill | Direção | Justificativa dada pela skill |
|---|---|---|---|---|
| AM-008 | HIGH | CRITICAL | ⬆ | Escala do catálogo: AP-05 é CRITICAL porque explorável por chamador anônimo sem condição rara. As 11 rotas privilegiadas foram exercidas anonimamente com sucesso. |
| AM-012 | HIGH | MEDIUM | ⬇ | AP-12 é tabelado MEDIUM ("multiplica o custo de cada mudança futura"). A skill não elevou porque a invariante não é explorável nem causa perda de dados — o agravante da divergência criar/atualizar está registrado, mas não muda a classe. |
| AM-021 | MEDIUM | LOW + CRITICAL | ↕ | A skill **separou as duas causas**: o mecanismo (AP-19, LOW — "custo de manutenção, sem efeito observável") e o vazamento de PII no mesmo fluxo (AP-07, CRITICAL). O manual tratou as duas como uma coisa só, em MEDIUM. |
| AM-022 | MEDIUM | HIGH | ⬆ | AP-21 é tabelado HIGH: o dano nomeado é a **ausência de caminho de evolução de schema**, não o incômodo do boot. Reforçado pelo teste de e-mail duplicado. |
| AM-027 | LOW | MEDIUM | ⬆ | AP-23 é tabelado MEDIUM. A skill apresentou dois handlers equivalentes lado a lado (`controllers.py:20` vs `:142`), que é a evidência que o próprio AP exige. |

**Leitura:** nenhuma divergência é arbitrária — as cinco decorrem de a skill aplicar a escala
tabelada do catálogo, enquanto o dossiê manual atribuiu severidade por julgamento livre. Três
subiram, uma desceu, uma se dividiu em duas. A skill **registrou desvio de severidade em zero
findings**, porque em nenhum ela se afastou da tabela — a divergência é com o manual, não com o
próprio catálogo, e isso é conformidade e não falha.

O tratamento de AM-021 é o ponto mais forte do cruzamento: o manual enterrou "alguns `print`
registram dado sensível" como observação de impacto dentro de um finding MEDIUM sobre logging. A
skill promoveu isso a **F-005, CRITICAL**, com as três linhas isoladas
(`controllers.py:161, 179, 182`) e o argumento de enumeração de contas. Foi a auditoria
automatizada que classificou melhor.

---

## Findings NOVOS — presentes na skill e ausentes da análise manual

Seis, dos quais **três são temas que o dossiê manual não toca em ponto algum**.

| F-ID | AP | Sev. | Novo em que sentido | Evidência |
|---|---|---|---|---|
| **F-016** — listagens sem paginação | AP-22 | MEDIUM | **Tema inteiramente ausente** do dossiê manual. Nenhum AM menciona paginação, limite ou tamanho de resposta. | 5 consultas sem `LIMIT`: `models.py:7, 75, 174, 206, 289-299` |
| **F-021** — sem rate limiting no login | AP-24 | MEDIUM | **Tema inteiramente ausente.** | `app.py:21` sem middleware; nenhuma dependência no manifesto |
| **F-026** — ausência de infra de qualidade | AP-28 | LOW | **Ausente como finding.** O manual só menciona "nenhum linter roda" como frase de impacto dentro de AM-025. | `requirements.txt` íntegro (2 linhas); ausência verificada **no projeto e um nível acima** |
| **F-011** — 3 handlers saltam a camada de dados | AP-13 | HIGH | Ausente como finding próprio. O manual espalha o fato pelos impactos de AM-007 e AM-010. | `app.py:50-55`, `app.py:66-76`, `controllers.py:266-274` |
| **F-005** — PII em log | AP-07 | CRITICAL | Ausente como finding próprio (era sub-observação de AM-021, MEDIUM). | `controllers.py:161, 179, 182` |
| **F-012 (parte b)** — deleção deixa órfãos | AP-11 | HIGH | Sub-acusação nova dentro de um finding que existe. AM-013 cobre só check-then-act e transação. | Verificado por execução: `produto_nome: "Desconhecido"` |

**F-016 e F-021 são o achado mais relevante deste cruzamento**: são dois anti-patterns reais,
com evidência literal, que uma auditoria manual cética e bem-feita simplesmente não procurou. É
exatamente o valor que um catálogo fechado de 28 entradas entrega sobre a inspeção livre —
varrer a lista inteira força a fazer perguntas que não ocorreriam.

---

## Falsos positivos suspeitos

Três, em ordem decrescente de gravidade. Nenhum é um finding sem evidência — todos têm
`arquivo:linha` verificado. A suspeita é de **classificação**, não de fabricação.

### 1. F-021 (AP-24, rate limiting) — provável violação de escopo do próprio AP

**Razão.** A coluna `Aplica a` do AP-24 diz "APIs com autenticação". A skill argumenta em
**F-002** que **não existe autenticação alguma** neste projeto — o login "não emite credencial
alguma [...] o chamador não recebe nada que possa apresentar na requisição seguinte". Se não há
autenticação, o escopo do AP-24 não é satisfeito, e o estado correto seria **"não aplicável"**,
não finding.

Agravante: o `report-template.md` da própria skill usa **exatamente este caso** como o exemplo
canônico de linha "não aplicável" na seção "o que não foi encontrado" — texto literal do
template: *"Rate limiting (AP-24) — não aplicável: não há autenticação a proteger no estado
atual [...] Como não existe finding de AP-24, ele não agenda TR algum"*.

A skill fez o oposto do que o próprio template exemplifica. O efeito prático é pequeno (TR-05 já
está agendado na Onda 1 por F-002, e a skill anotou F-021 como resolvido "de carona"), mas ele
**infla o total em 1 finding** e contamina a contagem de MEDIUM. Contra-argumento razoável: existe
um endpoint de verificação de credenciais, ainda que não emita token, e ele é forçável por bruta
contra as três senhas fracas do seed. É defensável — mas o template pedia a outra decisão.

### 2. F-006 / F-007 e F-001 / F-008 — quatro findings onde a regra sugere dois

**Razão.** O `report-template.md` manda "um finding por causa, não por ocorrência", e adverte que
inflar a contagem é "a forma mais fácil de destruir a credibilidade do relatório". A skill abriu
**dois** findings de AP-03 (`senha` em `/usuarios` + `secret_key` em `/health`) e **dois** de
AP-01 (concatenação + `/admin/query`).

A defesa está escrita no relatório e é técnica: em AP-01, F-001 se corrige vinculando parâmetros
sem tocar na superfície, enquanto F-008 só se corrige **removendo o endpoint** — são correções
incompatíveis, logo causas distintas. Em AP-03, um é mapeamento de entidade e o outro é payload de
diagnóstico montado à mão. O argumento se sustenta, e a análise manual chegou à mesma divisão
(AM-001/AM-002 e AM-004/AM-006). **Registro como suspeita e a considero improcedente** — mas ela
existe porque quatro findings CRITICAL sobre dois APs é o padrão visual de um relatório inflado.

### 3. F-024 — uma das três ocorrências é fraca

**Razão.** F-024 (AP-25, magic numbers) sustenta-se bem nos seis literais das faixas de desconto
(`models.py:257-262`). Mas inclui como terceira ocorrência o `"ambiente": "producao"` de
`controllers.py:286`, que não é um limiar numérico nem um vocabulário fechado — é um rótulo
factualmente errado. Pertence conceitualmente a F-007 (payload de diagnóstico) ou a F-003, não a
AP-25. Impacto: nenhum na severidade nem no plano; é imprecisão de alocação dentro de um finding
LOW que se sustenta sem ela.

### Não classifiquei como falso positivo

- **A ausência de AP-06 (god class).** Seria fácil marcar `controllers.py` (292 linhas, quatro
  responsabilidades) como god class e ganhar mais um CRITICAL. A skill recusou, aplicando o
  contra-exemplo literal do AP ("o critério é número de responsabilidades distintas [...] exige
  os quatro no mesmo corpo") e **assumindo a consequência**: TR-06 desceu da Onda 1 para a Onda 2.
  Recusar um CRITICAL fácil e aceitar o custo no plano é o comportamento correto, e a análise
  manual também não reportou god class.
- **A ausência de AP-17.** A skill documentou toda a duplicação (AM-016) com faixas de linha
  exatas dentro da seção "o que não foi encontrado", explicando que o sinal exige **duas** metades
  e que a segunda — abstração correta morta no repositório — não existe aqui. É a diferença entre
  "não achei" e "achei e o sinal não fecha", e ela está escrita.

---

## Comparação de baselines

`BASELINE_PATH` da skill × baseline manual do Passo 1.

| Dimensão | Baseline manual (Passo 1) | Baseline da skill | Divergência |
|---|---|---|---|
| Endpoints cobertos | 19 | 19 | **nenhuma** |
| Nº de chamadas registradas | 21 | 19 | 2 a mais no manual |
| Status codes dos endpoints comuns | 200×16, 201×3 | 200×16, 201×3 | **nenhuma** |
| Caminho de erro (`GET /produtos/9999`) | `404` registrado | **ausente** | ⚠️ **relevante** |
| `GET /health` pós-reset | registrado | ausente | menor |
| Media type | não registrado | `application/json` ×19 | skill mais rica |
| Forma do corpo | body truncado em 500 chars | `shape` tipada por chave, recursiva | skill mais rica |
| Formato | Markdown legível | JSON comparável por máquina | skill mais útil para o smoke test |

**Divergência em número de endpoints: nenhuma.** Ambos chegaram a 19 de forma independente.
**Divergência em status code: nenhuma.** Os 19 endpoints comuns têm status idêntico nos dois.

### A divergência que importa: o baseline da skill não registra nenhum caminho de erro

Verificado por leitura do JSON: `4xx/5xx registrados: NENHUM`. Os 19 registros são
`200 ×16` e `201 ×3`.

Isso é uma lacuna real, e ela colide com o próprio plano da skill:

- O `validation-protocol.md` §4 define o critério 3 como "status code idêntico ao do baseline".
  Um endpoint cujo **caminho de erro** regredir — `404` virando `500`, ou `404` virando `200` —
  **não é detectável**, porque não há linha de baseline para comparar.
- A skill declarou **BC-8**, que promete mudar `500` → `4xx` em três caminhos de entrada
  inválida, e **BC-10/BC-11**, que introduzem `400` e `409` novos. São mudanças de status em
  cenários de erro **que o baseline não cobre** — ou seja, a Fase 3 prometeu alterar
  precisamente a região do contrato que ela não instrumentou.
- O `report-template.md` pede a contagem por status justamente para que o humano no gate saiba
  o que a Fase 3 promete preservar. A tabela do relatório mostra `200 ×10`, `201 ×3`, `200 ×3`,
  `200 ×2`, `200 ×1` — cem por cento de caminho feliz, e isso **não é sinalizado como lacuna** em
  lugar nenhum do relatório.

O baseline manual do Passo 1, por ter incluído `GET /produtos/9999 → 404`, cobre um caminho de
erro que o da skill não cobre. É pouco — um só — mas é um a mais que zero.

**Isto é uma lacuna de instrumentação da skill, não uma falha de execução.** O
`validation-protocol.md` §2 diz "para cada endpoint [...] envie uma requisição representativa" e
não exige exercitar caminhos de erro. A skill cumpriu a instrução literalmente. A instrução é que
está incompleta para um projeto cujo plano inclui quatro breaking changes de status em cenário de
erro.

### Observação menor sobre o baseline da skill

O último registro é `POST /admin/reset-db`, marcado `"note": "DESTRUCTIVE; ran last"`. Está
correto conforme §2 ("trate as rotas destrutivas por último"), mas significa que **replayar o
baseline em ordem apaga o banco ao final de cada smoke test**. Como o próximo smoke test recria o
seed no boot, funciona — mas depende de o seed automático de `database.py:56-84` continuar
existindo, e a Onda 2 (TR-16) vai justamente separá-lo do boot. É um falso vermelho previsível
para a Fase 3 que o relatório não antecipou.

---

## Conformidade da skill com as próprias regras

| Regra do `SKILL.md` | Cumprida? | Evidência |
|---|---|---|
| Working tree limpo antes da Fase 1 | ✅ | `git status --porcelain` vazio, `ec6d1d4` |
| Imprimir os dois caminhos absolutos antes de gravar | ✅ | `REPORT_PATH` e `BASELINE_PATH` impressos nas pré-condições |
| Caminhos ancorados na **raiz do repositório** | ✅ | `reports/` na raiz, não em `code-smells-project/` |
| Nenhuma escrita em arquivo do projeto antes do gate | ✅ | `git diff -- code-smells-project/` **vazio** |
| Apenas duas escritas (relatório + baseline) | ✅ | `reports/` contém exatamente 2 arquivos |
| Runtime obtido executando, não do manifesto | ✅ | `python3 --version` |
| Baseline gravado em disco antes do gate | ✅ | 19 registros com `shape` |
| Varrer os 28 APs e nomear o estado de cada um | ✅ | 24 em findings + 4 nomeados (`AP-06`, `AP-14`, `AP-16`, `AP-17`) = 28 |
| AP-16 verificado contra a versão real, citando-a | ✅ | 3.12.3, com `-W always::DeprecationWarning` e cruzamento manual das 17 APIs chamadas |
| Ordenação CRITICAL→HIGH→MEDIUM→LOW | ✅ | conferido |
| Numeração `F-NNN` contínua entre severidades | ✅ | `F-001`…`F-026`, sem lacuna |
| Seção Breaking changes preenchida por endpoint | ✅ | 11 BCs, enumerando endpoints, não "em geral" |
| Ondas vazias nomeadas como vazias | ✅ | "Nenhuma" — declarado explicitamente |
| TR sem finding não é agendado | ✅ | TR-12 declarado não agendado (AP-16 não encontrado) |
| Ajuste de onda justificado | ✅ | tabela de 6 ajustes; TR-06 1→2, TR-08 2→3, TR-15 3→4 |
| Prompt do gate literal | ✅ | `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` |
| Parar e aguardar no gate | ✅ | não respondido |

**Nenhuma violação de regra detectada.** A única inconsistência com o pacote de referências é o
F-021 descrito acima, que contradiz um **exemplo** do `report-template.md`, não uma regra
normativa.

---

## Veredito

| Critério | Resultado |
|---|---|
| **CA-1** — stack detectada bate com a realidade | ✅ **APROVADO** — 5/5 campos exatos |
| **CA-2** — número real de findings | **26** (8C · 6H · 7M · 5L), contados |
| **CA-3** — há ≥1 CRITICAL ou HIGH | ✅ **SIM — 14** |
| **Cobertura do gabarito manual** | **85,2% como finding** · **100% como tema abordado** · **0 omissões silenciosas** |
| **Findings novos** | 6, sendo **2 temas que o gabarito não toca** (paginação, rate limiting) |
| **Falsos positivos suspeitos** | 1 procedente (F-021), 1 improcedente após análise, 1 imprecisão menor |
| **Baselines** | endpoints e status **idênticos**; skill mais rica em media type e shape; **lacuna: zero caminhos de erro** |
| **Conformidade com as próprias regras** | ✅ sem violações |

**Fase 3 não executada. Gate não respondido.**

### Recomendação para a skill (não aplicada — fora do escopo deste run)

1. `validation-protocol.md` §2 deveria exigir **ao menos um caminho de erro por recurso** no
   baseline, ou obrigar o relatório a declarar a lacuna quando o baseline for 100% caminho feliz.
   Sem isso, o critério 3 da §4 não pode validar as breaking changes de status que a própria
   skill propõe.
2. `report-template.md` deveria dizer se AP-24 é finding ou "não aplicável" quando existe
   endpoint de credencial **sem** emissão de credencial — o exemplo atual induz a decisão oposta
   à que a execução tomou.
