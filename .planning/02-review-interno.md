# Review interno adversarial — skill `refactor-arch` (rodada 4)

> **Postura:** revisão adversarial. O objetivo é derrubar a skill, não elogiá-la. Só passa o que
> sobrevive ao ataque. Nada foi corrigido nesta etapa — este documento apenas reporta.
>
> **Alvo:** `code-smells-project/.claude/skills/refactor-arch/` (SKILL.md + 6 references) e
> `code-smells-project/.claude/commands/refactor-arch.md`.
> **Design normativo:** `.planning/01-design-skill.md`. **Enunciado:** `docs/enunciado.md`.
> **Data da auditoria:** 2026-08-16.
> **Estado auditado:** working tree sobre `9284e32 fix(skill): close wave-assignment contradiction
> and add final validation procedure`, com as correções de agnosticismo ainda não commitadas
> (6 arquivos, +113/−38).
>
> **Protocolo idêntico ao das rodadas 1-3** (mesmos 9 requisitos verificáveis, mesmas contagens
> programáticas, mesmo teste de rollback), com a §7 desdobrada em **duas frentes** e uma **§8**
> nova para a interação entre elas.
> **Numeração:** rodada 1 usou `A-n`, rodada 2 `B-n`, rodada 3 `D-n` (`C-n` é a série de
> correções internas). Esta rodada usa **`E-n`**. As correções de agnosticismo mantêm os IDs
> `C-A n` de `.planning/03-review-agnosticismo.md`; correções internas novas continuam a série
> em C-23.

---

## 0. Achado que precede a auditoria: a leva 2 não existe no working tree

O enunciado desta rodada declara *"13 correções aplicadas em duas levas, mais três de fecho"*.
**Verificado arquivo a arquivo: seis edições existem — C-A1, C-A2, C-A3 e as três de fecho.
As dez correções da leva 2 (C-A4…C-A13) estão ausentes, todas.** Não parcialmente aplicadas:
ausentes, no texto literal que o review externo citou.

```console
$ git diff --numstat -- code-smells-project/.claude
23  13  SKILL.md
11   6  references/antipattern-catalog.md
37   4  references/mvc-guidelines.md
29  10  references/project-analysis.md
9    2  references/refactor-playbook.md
4    3  references/report-template.md
       (validation-protocol.md e commands/refactor-arch.md: zero linhas)
```

Provas pontuais, uma por correção ausente, em §7.2. A mais direta é C-A13, que pedia apagar três
notas de procedência: `grep -n "calibragem\|fixtures"` devolve **4 ocorrências**, nas linhas
`431`, `433`, `496` e `700` — exatamente as que o review externo citou.

Consequência para esta auditoria: o que segue mede **três bloqueadores fechados**, não treze
correções. Toda conclusão sobre agnosticismo abaixo é sobre esse estado.

---

## 1. Matriz de conformidade

| Req | Status | Evidência (`arquivo:linha`) | Ação corretiva |
|---|---|---|---|
| **RQ-1** — ≥8 anti-patterns com severidade distribuída em C/H/M/L | ✅ | `references/antipattern-catalog.md:51-78` (índice dos 28 APs) · `:80` declara `CRITICAL 7 · HIGH 7 · MEDIUM 10 · LOW 4` · 28 linhas de severidade no corpo, conferidas célula a célula (§2.2). Escala em `:29-36`. | Nenhuma para o requisito. Ver **C-A11**, não aplicada: a distribuição 7/7/10/4 é desenho, não resultado da escala. |
| **RQ-2** — detecção de APIs deprecated presente | ✅ | `references/antipattern-catalog.md:469-501` (AP-16), procedimento obrigatório em `:477-481`. Insumo em `references/project-analysis.md:75-97`, **agora com `ruby --version`** (`:85`). TR em `references/refactor-playbook.md:502-539`. | Nenhuma para o requisito. **C-12** (interna) e **C-A13** (externa) pediam a mesma coisa — `Manifestações por stack` em AP-16 — e nenhuma foi aplicada. |
| **RQ-3** — ≥8 padrões de transformação com código antes/depois | ✅ | `references/refactor-playbook.md:36-53` (índice dos 18 TRs) · 18 cabeçalhos · 18 blocos `python` + 18 `javascript` · 36 `antes` / 36 `depois` (§2.3). | Nenhuma para o requisito. **C-A10** não aplicada: 0 blocos Java/Ruby/PHP/Go contra 6 stacks na `description`. |
| **RQ-4** — as 5 áreas de conhecimento obrigatórias cobertas | ✅ | Mapa em `SKILL.md:25-32`. Os 6 references somam 2.680 linhas. | Nenhuma para o requisito. Ver **E-3**: o mapa segue sem autorizar 7 seções. |
| **RQ-5** — Fase 2 pausa e pede confirmação antes de escrever | ✅ | `SKILL.md:153-173`; prompt literal em `:162`, idêntico ao do enunciado. As 4 regras em `:167-173`. Invariante das duas escritas coerente em cinco pontos (`:147-150`, `:275-276`, `report-template.md:6-9`, `validation-protocol.md:59`, `commands/refactor-arch.md:17-19`). | Nenhuma. **Região não tocada por nenhuma leva** — o diff de `SKILL.md` não tem hunk entre `:127` e `:177`. |
| **RQ-6** — Fase 3 valida boot + endpoints | ✅ | `SKILL.md:207-229` (protocolo de onda). `validation-protocol.md:74-89` (boot), `:93-111` (smoke), `:113-137` (predicado). | Nenhuma. `validation-protocol.md` tem **zero linhas** de diferença. Ver **C-A8**, não aplicada: o baseline segue assumindo shape JSON (`:39`, `:53-56`). |
| **RQ-7** — frontmatter YAML válido com `name` e `description` | ✅ | `SKILL.md:1-13`. `yaml.safe_load` OK; chaves `['name','description']`; 761 caracteres / 121 palavras. | Nenhuma. Idêntico às quatro rodadas. |
| **RQ-8** — SKILL.md < 500 linhas | ✅ | `wc -l SKILL.md` → **286**. 57,2% do teto. | Nenhuma. +10 sobre a rodada 3. |
| **RQ-9** — cadência de ondas normativa no SKILL.md **e** no `validation-protocol.md`, incluindo rollback ao último commit verde | ✅ | `SKILL.md:183-229`, `validation-protocol.md:113-137` (§4.1), `:139-165` (§4.2), `:213-249` (§6.1), `:253-266` (§7). | Nenhuma. Nenhum dos dois blocos foi tocado: o diff de `SKILL.md` não tem hunk entre `:177` e `:241`, e `validation-protocol.md` está intacto. |

**Placar dos requisitos literais: 9 ✅ · 0 ⚠️ · 0 ❌.** (Rodada 1: 8/1. Rodada 2: 7/2. Rodada 3: 9/0.)

A matriz não move desde a rodada 3, e isso é informação: as correções de agnosticismo não tocaram
nenhuma das nove garantias. O que decide esta rodada está nas seções 4, 5, 7 e 8.

---

## 2. Contagens reais

Saída literal de comando executado em `code-smells-project/.claude/skills/refactor-arch/`.

### 2.1 Linhas por arquivo

```console
$ wc -l SKILL.md references/*.md
   286 SKILL.md
   805 references/antipattern-catalog.md
   326 references/mvc-guidelines.md
   225 references/project-analysis.md
   789 references/refactor-playbook.md
   237 references/report-template.md
   298 references/validation-protocol.md
  2966 total
```

| Arquivo | Design | R1 | R2 | R3 | **R4** | Δ |
|---|---|---|---|---|---|---|
| `SKILL.md` | ~190 | 216 | 258 | 276 | **286** | +10 |
| `project-analysis.md` | ~280 | 206 | 206 | 206 | **225** | +19 |
| `antipattern-catalog.md` | ~640 | 793 | 799 | 800 | **805** | +5 |
| `report-template.md` | ~210 | 203 | 234 | 236 | **237** | +1 |
| `mvc-guidelines.md` | ~330 | 293 | 293 | 293 | **326** | +33 |
| `refactor-playbook.md` | ~740 | 780 | 782 | 782 | **789** | +7 |
| `validation-protocol.md` | ~190 | 173 | 275 | 298 | 298 | 0 |
| **Total** | **~2.580** | 2.664 | 2.845 | 2.891 | **2.966** | **+75** |

`mvc-guidelines.md` foi o arquivo desta rodada (+33, 11,3%) — era o único reference nunca tocado
em três rodadas. Razão orquestrador:conhecimento **1:9,4**.

**Teto informal de 800 linhas para o catálogo: rompido, 805.** O teto nunca existiu no design
(`grep -n 800 .planning/01-design-skill.md` → nada; o design estima ~640 em `:93` e fixa 500 só
para o `SKILL.md` em `:459`). Foi um critério introduzido em review e agora foi ultrapassado sem
decisão — pela exclusão de AP-26 (+5). Registro de fidelidade, não defeito: nenhum requisito o
menciona. Mas ele deixou de ser um limite e virou um número no histórico. Ver **E-5**.

### 2.2 Anti-patterns

```console
$ grep -cE '^#{2,4} *AP-[0-9]+' references/antipattern-catalog.md
28
$ grep -oE '^\*\*(CRITICAL|HIGH|MEDIUM|LOW) · ' ... | sed 's/[^A-Z]//g' | sort | uniq -c
      7 CRITICAL   7 HIGH   10 MEDIUM   4 LOW
```

Índice (`:51-78`, cabeçalho `| AP | Nome | Sev. | Onda | Aplica a | TR |` em `:49`) confere com o
corpo célula a célula: `Sev.` 7/7/10/4, `Onda` 7·7·10·3+`—`, `Aplica a` **0 células vazias**,
11 valores distintos. AP-06 = onda 1, AP-13 = onda 2, AP-26 = onda 4 — inalterados.

### 2.3 Transformações

```console
$ grep -cE '^#{2,4} *TR-[0-9]+' references/refactor-playbook.md → 18
$ grep -oE '^```[a-z]*' ... | sort | uniq -c → 18 python · 18 javascript · 36 fecho
antes: 36  depois: 36
```

18/18 com par Python + JavaScript. **Zero blocos das outras quatro stacks prometidas.** Inalterado
desde a rodada 1; agora com um agravante novo — C-A2 acrescentou Ruby à tabela de variantes de
árvore (`mvc-guidelines.md:150`) e ao procedimento de runtime, mas **nenhum TR sabe escrever Ruby**.
A promessa de stack cresceu; a cobertura de transformação não. Ver **E-2**.

### 2.4 Campos das entradas do catálogo

```console
     28 **Sinal.**        28 **NÃO é finding quando.**     28 **Evidência mínima.**
     25 **Manifestações por stack.**
```

Os três campos estruturais em 28/28 — **incluindo depois da reescrita de AP-26**, que era o risco
declarado da correção de fecho 2. `Manifestações por stack` segue faltando nos mesmos 3 (AP-16,
AP-26, AP-28) desde a rodada 1.

### 2.5 Frontmatter

```console
YAML OK. keys = ['name', 'description']
name = 'refactor-arch'   description chars = 761 words = 121
```

Idêntico às quatro rodadas. **E isso agora é um defeito**: a `description` promete seis stacks
(`SKILL.md:9-11`) e a leva 2, que fecharia a lacuna de cobertura, não foi aplicada. Ver **E-2**.

---

## 3. Integridade de referências cruzadas

### 3.1 Conjunto de IDs

`AP-01…AP-28` (28, sem buracos) e `TR-01…TR-18` (18, sem buracos). Conjunto citado = conjunto de
cabeçalhos. **Quebras: nenhuma.**

### 3.2 Consistência bidirecional catálogo ↔ playbook

```console
pares AP->TR: 27 | sem contrapartida no playbook: []
pares TR->AP: 27 | sem contrapartida no catálogo: []
```

AP-28 declara `— | reportado, não corrigido`, coerente com `refactor-playbook.md:55`.
**Quebras: nenhuma.** As 5 divergências de onda entre rótulo e AP seguem cobertas pela regra
bidirecional, intocada nesta rodada.

### 3.3 Âncoras Markdown

28 âncoras `<a id="ap-NN">` no catálogo, 10 links de índice em `mvc-guidelines.md` resolvendo para
os 10 cabeçalhos `## N.` — **incluindo depois de o arquivo crescer 33 linhas**, que era o outro
risco da rodada. **Quebras: nenhuma.**

### 3.4 Referências de seção (`§`)

```console
      2 mvc-guidelines.md` §1        1 project-analysis.md` §6   (era 5)
      1 mvc-guidelines.md` §2        1 project-analysis.md` §9
      1 mvc-guidelines.md` §3        2 validation-protocol.md` §2
      1 mvc-guidelines.md` §4        1 validation-protocol.md` §4
      5 mvc-guidelines.md` §6        2 validation-protocol.md` §4.1
      1 mvc-guidelines.md` §7        4 validation-protocol.md` §4.2
      1 mvc-guidelines.md` §9        2 validation-protocol.md` §6.1
      2 mvc-guidelines.md` §10       1 validation-protocol.md` §8
```

Os 28 alvos existem. **Quebras de resolução: nenhuma, em quatro rodadas.**

A correção de fecho 3 é visível aqui: `project-analysis.md` §6 caiu de **5 apontadores para 1**, e
o que sobrou (`SKILL.md:94`) é Fase 1, autorizado. `mvc-guidelines.md` §6 subiu para 5, e é o
arquivo que as Fases 2 e 3 carregam. A rota de carga deixou de piorar — mas não melhorou: ver
**E-3**.

### 3.5 Veredito da seção 3

**Zero quebras em 46 IDs, 38 âncoras e 28 referências de seção.** Quarta rodada consecutiva sem
uma única quebra, agora tendo absorvido a maior reescrita estrutural do pacote.

---

## 4. Ambiguidades de instrução

Critério idêntico: trecho que um agente **sem supervisão** pode resolver de mais de uma forma, com
comportamentos observavelmente diferentes. Ordenado por dano.

---

### E-1 · A verificação 2 mudou de unidade e perdeu o artefato que a alimentava

**Trecho.** `SKILL.md:241-248`, reescrito por C-A3:

> 2. **Compare o resultado com o alvo, responsabilidade a responsabilidade** […] Cada
>    **responsabilidade** que o plano prometeu materializar tem **um** lugar identificável no
>    código atual, e esse lugar é **alcançável pelo mecanismo de resolução da stack**.

Contra `report-template.md:206-211`, o artefato onde o plano aprovado vive:

> ```
> | TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
> | TR-06 | F-001, F-006 | `repositories/…`, `services/…`, `controllers/…`, `routes/…` | todos | — |
> ```

**O problema.** Antes de C-A3 a verificação lia *"cada **camada** que o plano prometeu **criar**"*,
e isso mapeava um-para-um na coluna `Arquivos criados`: a checagem tinha um insumo literal. Agora
a verificação pergunta por **responsabilidades**, e o plano **não tem coluna de responsabilidade**.
O executor precisa inferir o conjunto verificado a partir de caminhos de arquivo.

**O caso em que fica vazia.** Numa stack que já materializa as responsabilidades, a regra 4
(`mvc-guidelines.md:47-53`) e o passo 0 de TR-06 (`refactor-playbook.md:262-268`) mandam **não
erguer árvore nova**. O plano aprovado então lista movimentações em `Arquivos alterados` e deixa
`Arquivos criados` vazio ou quase. A verificação 2 pergunta "o que o plano prometeu materializar?"
e a resposta literal, lida do artefato, é **nada** — a checagem passa por vacuidade exatamente no
ramo que C-A3 criou.

**Por que importa.** Esta é a verificação que a rodada 3 celebrou como a defesa contra TR-06
pulado (simulação 5.3, veredito ✅), e a única barreira estrutural que existe: o smoke test compara
contrato, não estrutura, como o próprio `:246-248` declara. Enfraquecê-la no ramo novo é abrir
exatamente o buraco que a rodada 2 reprovou, em outra stack.

**Interpretações possíveis:** (1) derivar responsabilidades da coluna `Arquivos criados` — funciona
no layout genérico, vazia no ramo adotado; (2) derivar de `Arquivos alterados` também — não
instruído, e "todos" não é uma lista de responsabilidades; (3) reauditar as sete responsabilidades
da §2 independentemente do plano — mais correto e mais caro, não instruído.

**Origem.** Interação entre **C-A3** (aplicada) e o `report-template.md` (não atualizado junto).
É o mesmo padrão que gerou o bloqueador da rodada 2: correção cirúrgica correta, texto vizinho não
propagado. Ver §8.

**Dano.** Alto. Não é bloqueador porque os três projetos-alvo caem no layout genérico, onde a
coluna `Arquivos criados` está populada e a verificação funciona (confirmado na 5.3). É bloqueador
na primeira stack com convenção própria.

---

### E-2 · A `description` promete seis stacks; o playbook sabe escrever duas — e a promessa cresceu nesta rodada

**Trecho.** `SKILL.md:9-11` promete *"Python, JavaScript/TypeScript, Java, PHP, Ruby, Go e
outros"*. C-A2 fechou a lacuna de Ruby nos dois lugares onde o review externo a apontou:
`project-analysis.md:85` (`ruby --version`) e `mvc-guidelines.md:150` (variante de árvore).

**O problema.** A cobertura cresceu em **detecção** e em **layout-alvo**, e não em
**transformação**. Os 18 TRs seguem com 18 blocos Python e 18 JavaScript, zero das outras quatro
(§2.3). O executor que detectar Ruby corretamente, escolher a árvore Ruby corretamente, e abrir
TR-06 encontra dois exemplos que não são da stack dele e uma instrução textual para adaptar
(`refactor-playbook.md:6-9`) — que autoriza traduzir a sintaxe, não recusar a forma.

**Por que piorou e não melhorou.** Antes de C-A2, Ruby era uma promessa não cumprida em três
pontos (runtime, árvore, transformação) e a incoerência era uniforme. Agora é cumprida em dois e
falha no terceiro — o mais caro —, o que produz um executor **mais confiante** no ponto onde ele
tem menos apoio. **C-A10** era exatamente a correção que fecharia isso com uma tabela de forma, e
não foi aplicada.

**Dano.** Alto no critério de agnosticismo; nulo nos três projetos-alvo, que são Python e
JavaScript.

---

### E-3 · Rota de carga: 7 ponteiros para seção não autorizada pela fase

**Trecho.** `SKILL.md:29`, **inalterado nas quatro rodadas**:

> | 3 | Arquitetura-alvo MVC | `references/mvc-guidelines.md` | Fase 2 (§9) e Fase 3, integral |

Sob a leitura restritiva, a Fase 2 carrega só §9. Os sete ponteiros seguem, nas linhas atuais:

| Quem pede | Linha | Seção | Fase |
|---|---|---|---|
| `SKILL.md` passo 6 | `:141` | `mvc-guidelines.md` §6 | 2 |
| `antipattern-catalog.md` AP-08 | `:279` | §10 | 2 |
| `antipattern-catalog.md` AP-13 | `:406` | §10 | 2 |
| `antipattern-catalog.md` AP-26 | `:757` | §6 | 2 |
| `project-analysis.md` | `:124` | §7 | 1 |
| `project-analysis.md` | `:163` | §6 | 1 |
| `project-analysis.md` | `:166` | §3 | 1 |

**Sete — de volta ao número das rodadas 1, 2 e 3.** A leva 1 havia levado a 11 ao criar quatro
ponteiros novos para `project-analysis.md` §6 a partir das Fases 2 e 3; a correção de fecho 3 os
eliminou, relocando a definição de alcançabilidade para `mvc-guidelines.md:206-220` e declarando
ali que *"as Fases 2 e 3 leem o fato, não o procedimento que o produziu"*. Agravamento revertido,
defeito original intacto.

**Dano.** Médio, inalterado em quatro rodadas. É **C-9**, a correção mais antiga aberta do pacote.

---

### E-4 · `Findings fixed` conta o que a validação final não verifica

Inalterado da rodada 3 (**D-3**). `SKILL.md:237-240` reexecuta o sinal de detecção para findings
CRITICAL e HIGH; `SKILL.md:261` imprime `Findings fixed: <n>/<n>` sem qualificador. Os findings
MEDIUM e LOW recebem TR e passam por smoke test, e nada verifica que o AP sumiu.

**Agravante novo desta rodada:** AP-26 é onda 4 (§2.2), e foi justamente AP-26 que ganhou uma
exclusão nova e delicada (a de resolução por convenção). O AP cuja fronteira ficou mais sutil é o
que a validação final não reexecuta.

**Dano.** Alto, inalterado. É **C-20**.

---

### E-5 · Ambiguidades menores registradas, sem ação isolada

| # | Trecho | Ambiguidade | Estado |
|---|---|---|---|
| a | `SKILL.md:76` — declarar *"auditoria read-only até o gate"* enquanto a Fase 1 grava `BASELINE_PATH` | Terminologia frouxa, desambiguada só em `:102`. | Inalterado (**B-7a**, **C-18**) |
| b | `commands/refactor-arch.md:30` — linha em branco entre os itens 4 e 5 | Quebra a lista numerada. O arquivo tem **zero linhas** de diferença nesta rodada. | Inalterado (**B-7e**, **C-18**) |
| c | `SKILL.md:113` — campo `Resolution` com quatro valores fechados | Não há valor para "mais de um mecanismo" (comum: import explícito **e** registro em container) nem para "não determinado". `:122` cobre genericamente o segundo caso, não o primeiro. | Novo, de C-A1 |
| d | Teto de 800 do catálogo rompido (805) sem decisão | O teto não é rastreável ao design (§2.1). Rompê-lo não viola requisito; deixá-lo no histórico como limite citado e não cumprido, sim. | Novo |
| e | `mvc-guidelines.md:68-72` — *"stack cuja convenção **funde** duas responsabilidades continua conforme"* | Não diz quantas. Fundir duas é conforme; fundir sete é AP-06. O limite entre os dois extremos não está declarado, e AP-06 (`:` sinal) fala em "não existe fronteira onde inserir uma camada", que é outro critério. | Novo, de C-A3 |
| f | AP-16, AP-26, AP-28 sem `Manifestações por stack` | Inalterado desde a rodada 1. **C-12** (interna) e **C-A13** (externa) pedem o mesmo; nenhuma aplicada. | Inalterado |
| g | Skill presente em 1 dos 3 projetos | Decisão de plano: a cópia vem depois da validação, para que o `diff -r` seja prova de copiabilidade. | ⏸️ deliberadamente aberta (**C-13**) |

---

## 5. Simulações

### 5.1 e 5.2 — herdadas

Ambos os cenários da rodada 3 dependem exclusivamente de `validation-protocol.md` (§4.1, §4.2,
§6.1, §7) e do protocolo de onda em `SKILL.md:207-229`. **Nenhum dos dois blocos tem uma linha de
diferença** nesta rodada: `git diff --numstat` sobre `validation-protocol.md` é vazio, e o diff de
`SKILL.md` não tem hunk entre `:177` e `:241`. Vereditos ✅ da rodada 3 mantidos por construção,
sem reexecução.

### 5.3 — projeto sem CRITICAL, AP-13 como único acionador de TR-06

Refeita contra o texto atual. Projeto com AP-13 (HIGH) e AP-15/AP-22 (MEDIUM), sem CRITICAL;
monólito Python que acopla rota ao ORM e não tem god class (AP-06 = *não encontrado*).

| # | Pergunta | Resposta | Evidência |
|---|---|---|---|
| 1 | Em que onda o plano põe TR-06? | **Onda 2.** Regra bidirecional intacta. | `SKILL.md:187-189`, `antipattern-catalog.md:41-42` (*"Desce: TR-06 […] sem AP-06 e com AP-13 (HIGH) roda na Onda 2"*), `refactor-playbook.md:17-18`, `Nota de onda` de AP-13 (`:402-403`) |
| 2 | A Onda 1 é vazia? | **Sim, pelo plano**, não pela severidade. | `validation-protocol.md:149`, `SKILL.md:191-193` |
| 3 | **Novo:** o passo 0 de TR-06 faz o agente pular a criação da árvore? | **Não.** O passo 0 pergunta se a stack materializa responsabilidades *por convenção própria*; a resposta para um monólito Python é não. | `refactor-playbook.md:262-268` → `mvc-guidelines.md:47-53`, e o gatilho apertado em `:55-62`: *"Um monólito cujos módulos são apenas alcançáveis por import explícito **não tem convenção a adotar**, por mais que seus arquivos tenham nome de camada"* |
| 4 | O esqueleto MVC é criado? | **Sim, na Onda 2**, TR-06 primeiro. | `SKILL.md:216`, `refactor-playbook.md:20-21` |
| 5 | A verificação 1 detecta TR-06 pulado? | **Sim.** Reexecuta o sinal de AP-13 (`antipattern-catalog.md:391-393`), que volta a disparar. | `SKILL.md:237-240` |
| 6 | A verificação 2 detecta? | **Sim, neste cenário.** O plano genérico preenche `Arquivos criados` com `repositories/…`, `services/…` etc., e as responsabilidades correspondentes não teriam lugar. | `SKILL.md:241-248` + `report-template.md:206-211` |

**Veredito 5.3: ✅ passa, e o passo 0 de TR-06 — o risco novo — não a quebra.** A correção de fecho
1 é o que segura: sem ela, a frase *"a camada preexistente é alcançável pelo mecanismo de resolução
da stack"* teria disparado a regra 4 sobre `controllers.py`/`models.py` e o passo 0 teria pulado a
criação da árvore. Registro que **este cenário só passa por causa de uma correção aplicada nesta
rodada**, não por herança da rodada 3.

### 5.4 — projeto Rails hipotético, com autoload por convenção e MVC próprio

Repositório com manifesto Ruby, raiz de autoload declarada em configuração, diretórios de model /
view / controller impostos pelo framework, migrações versionadas por timestamp, e inicialização por
arquivos de configuração. Nenhum nome real de projeto envolvido — o traço é contra o texto.

**A pergunta central: adota ou substitui?**

| # | Ponto | Resultado | Evidência |
|---|---|---|---|
| 1 | Runtime obtido | ✅ | `project-analysis.md:85` — `ruby --version` está na lista (C-A2) |
| 2 | Arquitetura efetiva | ✅ | `project-analysis.md:134-155`: mecanismo = autoload por convenção; evidência exigida = *"a raiz de autoload declarada na configuração"*, que existe. A árvore varrida é a evidência (`:151-153`) |
| 3 | Entry points plurais | ✅ | `project-analysis.md:161-162`, `SKILL.md:112` |
| 4 | A camada do framework vira AP-26? | ✅ **Não.** | `antipattern-catalog.md:749-754`: *"ou o símbolo é carregado pelo **mecanismo de resolução da stack** […] ainda que nenhum arquivo o importe pelo nome"* |
| 5 | Existe variante de árvore? | ✅ | `mvc-guidelines.md:150` (C-A2) |
| 6 | A Fase 3 adota ou substitui? | ✅ **Adota.** | `mvc-guidelines.md:47-53` regra 4 dispara — o framework **declara** a convenção (`:56-58`) —, e `refactor-playbook.md:262-268`: *"este TR **não ergue árvore nova**"* |
| 7 | A verificação 2 força os sete diretórios? | ✅ **Não.** | `SKILL.md:241-248`: compara responsabilidades, e *"numa stack cuja convenção o plano adotou, o lugar certo é o que a convenção indica"* |

**Os quatro pontos onde ainda quebra — todos por leva 2 ausente:**

| # | Ponto | Resultado | Causa |
|---|---|---|---|
| 8 | AP-13 sobre o controller idiomático | ❌ **Falso positivo HIGH em todo controller.** O sinal (`antipattern-catalog.md:391-393`) descreve *"handlers […] constroem queries a partir das classes de model, sem camada de serviço ou repositório interposta"* — que é o idioma. A única isenção (`:405-407`) é *"única rota de leitura trivial"*. | **C-A6 não aplicada** |
| 9 | Composition root | ❌ `mvc-guidelines.md:174-176` mantém *"o composition root é o **único** ponto autorizado a instanciar infraestrutura"*, sem reconhecer o container/initializers da stack. TR-09 manda construir o grafo no entry point. | **C-A4 não aplicada** |
| 10 | TR-16, migrações | ❌ `refactor-playbook.md:672`: *"Extraia a DDL do boot para uma migração versionada inicial"*. A stack já tem sistema de migração; o TR inventa outro, e o passo 4 pressupõe DDL no boot, que não existe aqui. | **C-A9 não aplicada** |
| 11 | Baseline de resposta HTML | ❌ `validation-protocol.md:39` e `:53-56` registram *shape do corpo (chaves e tipos)* — um objeto JSON. Resposta de template não tem chaves, e o critério 4 do smoke test (`:103`) compara shape. | **C-A8 não aplicada** |
| 12 | Comando de boot | ⚠️ `validation-protocol.md:18` privilegia *"script de execução declarado no manifesto"*; o manifesto da stack não tem esse campo. Cai em convenção (precedência 3) e funciona por fallback. | **C-A7 não aplicada** |
| 13 | Escrever o código em Ruby | ⚠️ 18 TRs com exemplos Python e JavaScript, zero na stack detectada. | **C-A10 não aplicada** |

**Veredito 5.4: ⚠️ a inversão estrutural está corrigida; a criminalização do idioma não.**

A skill **adota** a convenção — não a substitui. Os quatro mecanismos pelos quais ela destruiria o
MVC do framework (fato 6 errado, AP-26 sobre a camada viva, layout genérico imposto, verificação
final exigindo sete diretórios) estão todos fechados, e cada um por texto verificado acima. Esse
era o núcleo do REPROVADO externo, e ele caiu.

O que sobra é de outra natureza: a Fase 2 produz **findings falsos** sobre o idioma (ponto 8 é
HIGH, em todo controller), a Fase 3 **luta com a infraestrutura** da stack (9 e 10), e a Fase 3
**mede errado** o contrato quando a resposta não é JSON (11 — e este é o pior dos quatro, porque um
smoke test que compara shape contra HTML produz vermelho onde não há regressão, e o protocolo de
onda manda `git reset --hard` sobre vermelho).

O ponto 11 merece nome próprio: **é o único dos quatro que aciona a máquina de rollback**. Os
outros três produzem relatório ruim ou refatoração anti-idiomática; esse produz destruição de
trabalho verde por falso vermelho.

### 5.5 O que as simulações expuseram

1. O caminho de rollback e a cadência de ondas seguem fechados, por não terem sido tocados.
2. A 5.3 passa, e passa **por causa da correção de fecho 1** — sem ela, o passo 0 de TR-06 teria
   reaberto o cenário da rodada 2 em outra roupa.
3. A 5.4 mostra a fronteira exata do que foi feito: **estrutura corrigida, semântica não**. É
   precisamente a divisão entre a leva 1 (aplicada) e a leva 2 (ausente).
4. A verificação 2 é a única barreira estrutural do pacote, e a 5.4 revela que ela pode ficar
   vazia justamente no ramo que a leva 1 criou (**E-1**).

---

## 6. Veredito

# ❌ REPROVADO

**Não por defeito novo. Por leva não aplicada.**

Os três bloqueadores de agnosticismo estão fechados e sobreviveram a ataque direto (5.4, pontos
1-7). Os onze itens que as rodadas 1-3 fecharam continuam fechados, sete deles por impossibilidade
física — os arquivos que os contêm têm zero linhas de diferença (§7.1). A matriz de requisitos está
9 ✅. Nada disso basta:

- **Dez das treze correções externas não existem no working tree** (§0, §7.2), incluindo as três
  ALTO que o review externo declarou serem o que *"impede a Fase 2 de marcar o idioma da stack
  como finding"*. O veredito externo era REPROVADO no critério de agnosticismo; três correções
  fecharam a inversão estrutural e nenhuma fechou a criminalização do idioma. **O critério
  continua não atendido**, e a simulação 5.4 mostra onde: pontos 8 a 13.
- **Um defeito ALTO novo** nasceu da interação entre uma correção aplicada e um arquivo não
  propagado (**E-1**): a verificação 2 mudou de unidade e o `report-template.md` não ganhou a
  coluna que a alimenta. É o mesmo mecanismo que gerou o bloqueador da rodada 2.
- **Um defeito ALTO novo por assimetria de cobertura** (**E-2**): C-A2 estendeu a promessa de
  stack em detecção e layout sem estender a transformação, e C-A10 — a correção que fecharia isso
  — não foi aplicada.

O que **não** reprova, e merece registro: nenhuma correção de agnosticismo tocou gate, ondas,
rollback, predicado de onda verde, três estados ou registro de ondas. A separação entre as duas
frentes se manteve quase perfeita — uma única costura (§8).

### Lista ordenada de correções

| # | Sev. | Correção | Origem | Arquivos a tocar |
|---|---|---|---|---|
| **C-A6** | 🟠 ALTO | AP-13 / AP-09 deixam de criminalizar o acesso idiomático a persistência: o AP dispara quando o handler monta query/sessão de infra diretamente, ou salta camada intermediária alcançável — não quando usa a API do model da stack. | 03-review §C-A6, 5.4 ponto 8 | `antipattern-catalog.md:405-407`, `:300-302` |
| **C-A8** | 🟠 ALTO | Baseline registra **media type** e, quando não for JSON, um seletor estável em vez de shape de chaves. **É o único item que aciona a máquina de rollback por falso vermelho** (5.4 ponto 11). | 03-review §C-A8 | `validation-protocol.md:37-56`, `:103` |
| **C-A4** | 🟠 ALTO | Composition root reconhece o container da stack quando ele existe, em vez de mandar reimplementá-lo. | 03-review §C-A4, 5.4 ponto 9 | `mvc-guidelines.md:174-176`, `refactor-playbook.md:379-388` |
| **C-23** | 🟠 ALTO | Alinhar a verificação 2 com o artefato que ela verifica: dar ao plano do relatório uma coluna de **responsabilidade materializada**, ou reancorar a verificação nas sete responsabilidades da §2 independentemente do plano. | **E-1**, §8 | `report-template.md:206-215`, `SKILL.md:241-248` |
| **C-A10** | 🟠 ALTO | Tabela de forma no topo do playbook, mapeando cada padrão Python/JS ao equivalente idiomático das demais stacks prometidas — sem acrescentar 18×N exemplos. | **E-2**, 5.4 ponto 13 | `refactor-playbook.md:9-12` |
| **C-20** | 🟠 ALTO | Alinhar `Findings fixed` ao que a validação final verifica (hoje só C/H). | D-3, **E-4** | `SKILL.md:237-240,261` |
| **C-A9** | 🟡 MÉDIO | TR-16 usa a ferramenta de migração já presente ou idiomática da stack; só cria `migrations/*.sql` quando não houver uma. | 03-review §C-A9, 5.4 ponto 10 | `refactor-playbook.md:666-697` |
| **C-A5** | 🟡 MÉDIO | AP-10 deixa de exigir a conjunção com a flag de concorrência de um driver específico; a flag vira agravante. | 03-review §C-A5 | `antipattern-catalog.md:314-317` |
| **C-A7** | 🟡 MÉDIO | Tirar do normativo os tokens de Python/Node (decorator, f-string, builtin, "script do manifesto"). | 03-review §C-A7 | `antipattern-catalog.md:100,191,768,789`, `validation-protocol.md:18` |
| **C-9** | 🟡 MÉDIO | Desambiguar o mapa de carregamento. Aberta desde a rodada 1; `SKILL.md:29` byte a byte igual. | A-5, B-4, D-4, **E-3** | `SKILL.md:29` |
| **C-A11** | 🟡 MÉDIO | Escolher **um** dos dois: fidelidade à escala interna (reclassificar) ou reescrever a escala. Hoje convivem escala A e classificação B. | 03-review §C-A11 | `antipattern-catalog.md:29-36,80` |
| **C-A12** | 🟢 BAIXO | AP-08: trocar "decisão de alto valor" pelo predicado correlato. | 03-review §C-A12 | `antipattern-catalog.md:264-267` |
| **C-A13 / C-12** | 🟢 BAIXO | Apagar as três notas de procedência e dar `Manifestações por stack` a AP-16. Fecha a correção interna mais antiga ainda aberta junto com a externa. | 03-review §C-A13, A-10b | `antipattern-catalog.md:431-433,496-497,700-703` |
| **C-21** | 🟢 BAIXO | Declarar o gatilho da validação final e a saída do plano inteiramente vazio. | D-5 | `SKILL.md:231-235,253-266` |
| **C-18** | 🟢 BAIXO | Resolver o que sobrou de B-7: `SKILL.md:76`, `commands/refactor-arch.md:30`. | B-7 | idem |
| **C-22** | 🟢 BAIXO | Menores: campo `Resolution` sem valor múltiplo (**E-5c**), limite de "fundir responsabilidades" (**E-5e**), teto do catálogo (**E-5d**). | D-7, E-5 | `SKILL.md:113`, `mvc-guidelines.md:68-72` |
| **C-13** | ⏸️ | Replicar a skill nos outros 2 projetos. Deliberadamente aberta por decisão de plano. | A-10d | — |

**Regra de reentrada.** C-A8 primeiro, sozinho se preciso: é o único defeito conhecido do pacote
que produz `git reset --hard` sobre trabalho válido. Depois C-A6 e C-A4, que são o que resta do
REPROVADO externo. C-23 antes de a skill rodar em qualquer stack com convenção própria — sem ele a
única barreira estrutural fica vazia justamente lá.

---

## 7. Regressão em duas frentes

### 7.1 Frente (a) — contra `.planning/02-review-rodada2.md` e os fechamentos da rodada 3

Critério declarado, idêntico: **uma correção que fechou um defeito e abriu outro de severidade
igual ou maior conta como não fechada.**

O diff desta rodada permite um argumento mais forte que leitura de texto para sete dos onze itens:
os arquivos que os contêm **não foram tocados**.

```console
$ git diff --numstat -- references/validation-protocol.md   → (vazio)
$ git diff --numstat -- ../../commands/refactor-arch.md     → (vazio)
$ git diff -U0 -- SKILL.md | grep '^@@'
@@ -86 +86 @@      @@ -88,3 +88,7 @@      @@ -108,2 +112,3 @@
@@ -135,3 +140,3 @@ @@ -236,4 +241,9 @@
```

Cinco hunks em `SKILL.md`, todos na Fase 1, no passo 6 da Fase 2 e na validação final. **Nenhum
entre `:127` e `:177`** (gate) e **nenhum entre `:177` e `:241`** (ondas, protocolo, rollback).

| Item | Veredito | Evidência |
|---|---|---|
| **C-1** 🔴 `REPORT_PATH` indefinido | ✅ **fechado** | `SKILL.md:68-75` intacto — fora de todo hunk. |
| **C-2** 🔴 `reports/` sem âncora | ✅ **fechado** | `SKILL.md:68-69` intacto; `commands/refactor-arch.md` com zero linhas de diferença. |
| **C-3** 🔴 predicado "onda verde" | ✅ **fechado** | `validation-protocol.md:113-137` — arquivo com zero linhas de diferença. |
| **C-4** 🔴 baseline volátil | ✅ **fechado** | `SKILL.md:96-100` fora de hunk; `validation-protocol.md:33-71` intacto; `report-template.md` só teve o hunk de `:56`. |
| **C-5** 🟠 boot vermelho sem saída | ✅ **fechado** | `SKILL.md:217-221` intacto. |
| **C-6** 🟠 regra de onda unidirecional | ✅ **fechado** | `SKILL.md:187-189` fora de hunk; `antipattern-catalog.md:38-42` fora do único hunk do arquivo (`:749-759`); `refactor-playbook.md:16-19` fora dos dois hunks (`:262`, `:660`). Verificado também por leitura na simulação 5.3. |
| **C-7** 🟠 três estados de "não encontrado" | ✅ **fechado**, e **testado** | `NÃO é finding quando` segue em **28/28** (§2.4) **depois** da reescrita de AP-26, que foi onde a correção de fecho 2 mexeu. A exclusão de AP-26 migrou para dentro do campo normalizado (`:749-754`), e `Regra de camada` (`:756-759`) passou a referenciá-la em vez de reformulá-la. Era o item com maior risco desta rodada; resistiu. |
| **C-8** 🟠 SHA das ondas / registro | ✅ **fechado** | `validation-protocol.md:213-249` — arquivo intacto. |
| **C-14** 🔴 onda vazia definida pelo plano | ✅ **fechado** | `validation-protocol.md:139-165` intacto; `SKILL.md:191-193` e `:209-213` fora de hunk. |
| **C-15** 🟠 invariante das duas escritas | ✅ **fechado** | `report-template.md:6-9` fora do único hunk do arquivo; os outros quatro pontos intactos. |
| **C-16** 🟠 três estados propagados + validação final com procedimento | ⚠️ **fechado com defeito novo de severidade igual** | **Metade "propagação": intacta** — `refactor-playbook.md:748-749`, `report-template.md:213-215,232`, `SKILL.md:156-157` todos fora de hunk; o grep de "4 ondas / quatro ondas / ondas 1 a 3" segue devolvendo uma linha, correta. **Metade "procedimento": reescrita por C-A3** (`SKILL.md:241-248`). Continua procedimento, continua detectando na 5.3 (verificado), e a cláusula operante (*"falha mesmo com smoke test `<n>/<n>`"*) está intacta — mas perdeu o insumo literal no ramo de convenção adotada. Ver **E-1**. Pelo critério declarado, defeito novo de severidade **igual** (🟠) → registro como fechado com ressalva, rastreado como C-23. |
| **C-17** 🟡 registro reconstruível | ✅ **fechado** | `validation-protocol.md:233-249` intacto. **D-1 da rodada 3 segue aberto** (alvo reconstruído sem cota inferior) — não foi endereçado nesta rodada e não aparece na lista de correções acima porque é item da rodada 3 ainda pendente; reafirmo aqui: **C-19 continua aberta**. |

**Placar da frente (a): 10 ✅ · 1 ⚠️ · 0 ❌.** Nenhum item fechado reabriu.

### 7.2 Frente (b) — contra `.planning/03-review-agnosticismo.md`

| Correção | Veredito | Evidência do estado atual |
|---|---|---|
| **C-A1** grafo de resolução | ✅ **fechada** | Definição canônica em `project-analysis.md:134-155` (tabela de 4 mecanismos com coluna de evidência) · framework efetivo por resolução (`:57-58`) · ordem de leitura (`:29`) · `SKILL.md:86`, `:88-94`, `:112-114`, `:140-142` · `mvc-guidelines.md:38-39`, `:204-220` · `antipattern-catalog.md:749-759` · `refactor-playbook.md:660-661` · `report-template.md:56-59`. Único resíduo de "grafo de imports" no pacote é a frase que o **nega** (`SKILL.md:90`). Verificada na 5.4 pontos 2 e 4. |
| **C-A2** Ruby | ✅ **fechada** no escopo literal | `project-analysis.md:85` (`ruby --version`) e `mvc-guidelines.md:150` (variante). Verificação das demais stacks prometidas: Java, PHP e Go já tinham runtime **e** variante; TypeScript entra por JS/TS com `node`. Ruby era a única lacuna nesses dois eixos. **Mas ver E-2:** o terceiro eixo — transformação — não foi coberto, e C-A10 era a correção que o cobriria. |
| **C-A3** MVC = responsabilidade | ✅ **fechada** | `mvc-guidelines.md:47-53` (regra 4) + `:55-62` (gatilho apertado pela correção de fecho 1) · `:68-72` (§2, a coluna que normatiza) · `refactor-playbook.md:262-268` (TR-06 passo 0) · `SKILL.md:241-248` (verificação 2). Verificada na 5.4 pontos 6 e 7. Defeito novo: **E-1**. |
| **C-A4** composition root / container | ❌ **não fechada** | `mvc-guidelines.md:174-176` literal: *"O composition root é o **único** ponto do projeto autorizado a instanciar infraestrutura."* Zero menção a container da stack. |
| **C-A5** AP-10 sem conjunção de driver | ❌ **não fechada** | `antipattern-catalog.md` AP-10, sinal literal: *"sem lock e sem política de invalidação — **e com a proteção de concorrência do driver explicitamente desabilitada**?"* A conjunção segue. |
| **C-A6** AP-13/AP-09 não criminalizam o idioma | ❌ **não fechada** | `antipattern-catalog.md:405-407` literal: *"O projeto é uma única rota de leitura trivial sem regra alguma"*. A exclusão proposta não existe. É o ponto 8 da 5.4. |
| **C-A7** tokens Python/Node fora do normativo | ⚠️ **1 de 6** | Fechado: `SKILL.md:112` (`Entry points`, lista) — de carona em C-A1. Abertos: `:100` (*"f-string"*), `:191` (*"middleware ou decorator"*), `:768` (*"builtin da linguagem"*), `:789`, `validation-protocol.md:18` (*"Script de execução declarado no manifesto"*). |
| **C-A8** baseline sem assumir JSON | ❌ **não fechada** | `validation-protocol.md:39` e `:53-56` inalterados — arquivo com zero linhas de diferença. Ponto 11 da 5.4, e o único que aciona rollback. |
| **C-A9** TR-16 usa a ferramenta da stack | ❌ **não fechada** | `refactor-playbook.md:672` literal: *"Extraia a DDL do boot para uma migração versionada inicial"*. |
| **C-A10** tabela de forma no playbook | ❌ **não fechada** | `refactor-playbook.md:9-16` não tem tabela; 18 python + 18 javascript, zero das demais (§2.3). |
| **C-A11** severidade alinhada à escala | ❌ **não fechada** | `:80` segue declarando `CRITICAL 7 · HIGH 7 · MEDIUM 10 · LOW 4`; escala em `:29-36` inalterada; nenhum desempate AP-12 × AP-25 no corpo de AP-25. |
| **C-A12** AP-08 predicado correlato | ❌ **não fechada** | Sinal de AP-08 literal: *"Existe decisão de negócio **de alto valor** (autorização de pagamento, precificação, elegibilidade, transição de estado)…"*. |
| **C-A13** apagar procedência / manifestações em AP-16 | ❌ **não fechada** | `grep -n "calibragem\|fixtures"` → `:431`, `:433`, `:496`, `:700`. AP-16 segue sem `Manifestações por stack` (§2.4). |

**Placar da frente (b): 3 ✅ · 1 ⚠️ · 9 ❌.** Os três fechados são os três bloqueadores. Dos dez
restantes, três são ALTO.

---

## 8. Interação entre as duas frentes

A pergunta desta seção é a que gerou o bloqueador da rodada 2: correção cirúrgica correta criando
aresta com texto vizinho não atualizado. Auditei nos dois sentidos.

### 8.1 Agnosticismo → orquestração: uma costura, real

**A única.** `SKILL.md:241-248`, verificação 2 da validação final, é o único ponto onde uma
correção de agnosticismo tocou texto que um review interno havia fechado (C-16). C-A3 mudou a
unidade verificada de **camada criada** para **responsabilidade materializada** — correto para o
alvo de agnosticismo, porque exigir sete diretórios era o mecanismo que destruiria a convenção do
framework. O que não foi propagado é o artefato do outro lado da verificação: o plano do
`report-template.md:206-211` continua registrando **arquivos**, em três colunas, e nenhuma delas é
responsabilidade.

Efeito observável, e é a assinatura exata do defeito da rodada 2: no layout genérico a verificação
funciona porque `Arquivos criados` aproxima bem o conjunto de responsabilidades; no ramo que C-A3
criou — stack com convenção, TR-06 sem erguer árvore — `Arquivos criados` fica vazio e a
verificação passa sem verificar nada. **A garantia não foi removida; foi desancorada.** Registrado
como **E-1**, correção C-23.

Uma segunda costura foi **evitada** e merece registro porque quase aconteceu: a exclusão nova de
AP-26 poderia ter quebrado C-7 (os três estados, `NÃO é finding quando` em 28/28) se tivesse ficado
onde a leva 1 a pôs, no campo `Regra de camada`. A correção de fecho 2 a moveu para o campo
normalizado e reduziu `Regra de camada` a uma referência. Contagem verificada depois da mudança:
28/28 (§2.4).

### 8.2 Orquestração → agnosticismo: nenhuma

Nenhuma garantia de orquestração impede uma correção de agnosticismo. As três aplicadas atravessaram
gate, ondas, predicado de onda verde e rollback sem tocá-los — `validation-protocol.md` tem zero
linhas de diferença, e é onde essas garantias moram. A separação de responsabilidades entre os
arquivos, que o design fixou em `:89-101`, é o que tornou isso possível: as correções de
agnosticismo caíram em `project-analysis.md`, `mvc-guidelines.md` e no catálogo; as garantias de
orquestração moram no `validation-protocol.md` e nas seções de onda do `SKILL.md`.

### 8.3 A interação que ainda não aconteceu, e vai

**Leva 2 aplicada colidirá com a orquestração em um ponto previsível: C-A8.** O baseline hoje é um
registro de shape de chaves (`validation-protocol.md:53-56`) e o critério 4 do smoke test compara
esse shape (`:103`). C-A8 acrescenta media type e, para respostas não-JSON, um seletor estável em
vez do objeto de chaves. Isso muda o insumo de um dos cinco critérios do predicado **`onda verde`**
— o predicado que a rodada 2 fechou como C-3 e declarou *"a única definição em todo o pacote"*
(`:115-116`). Aplicar C-A8 sem propagar ao critério 4 e à §4.1 recria, no predicado mais central do
pacote, a mesma desancoragem que E-1 é hoje na validação final.

Registro isto agora, antes de a leva 2 existir, porque é a única previsão acionável que esta
auditoria consegue fazer: **C-A8 e o critério 4 da §4 são uma correção só.**

---

**PARADO E REPORTADO.** Conforme a restrição da revisão, nenhuma correção foi aplicada nesta etapa.
Nenhum arquivo da skill foi modificado durante a auditoria.
