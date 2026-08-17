# Review interno adversarial — skill `refactor-arch` (rodada 2)

> **Postura:** revisão adversarial. O objetivo é derrubar a skill, não elogiá-la. Só passa o que
> sobrevive ao ataque. Nada foi corrigido nesta etapa — este documento apenas reporta.
>
> **Alvo:** `code-smells-project/.claude/skills/refactor-arch/` (SKILL.md + 6 references) e
> `code-smells-project/.claude/commands/refactor-arch.md`.
> **Design normativo:** `.planning/01-design-skill.md`. **Enunciado:** `docs/enunciado.md`.
> **Data da auditoria:** 2026-08-16.
> **Estado auditado:** working tree sobre `081411c feat(skill): add refactor-arch skill v1`, com as
> correções das rodadas de conserto ainda não commitadas (5 arquivos, +277/−86).
>
> **Protocolo idêntico ao da rodada 1** (mesmos 9 requisitos verificáveis, mesmas contagens
> programáticas, mesmo teste de rollback), acrescido da **§7 — regressão entre rodadas**.
> Ambiguidades desta rodada são numeradas **B-n** para não colidir com os **A-n** da rodada 1;
> correções mantêm o ID original quando são a mesma correção (C-6, C-9, C-11…) e continuam a
> sequência quando são novas (C-14+).

---

## 1. Matriz de conformidade

| Req | Status | Evidência (`arquivo:linha`) | Ação corretiva |
|---|---|---|---|
| **RQ-1** — ≥8 anti-patterns com severidade distribuída em C/H/M/L | ✅ | `references/antipattern-catalog.md:50-77` (índice dos 28 APs, agora com coluna `Aplica a`) · `:79` declara `CRITICAL 7 · HIGH 7 · MEDIUM 10 · LOW 4` · linha de severidade no corpo de cada AP, 28 ocorrências. Índice e corpo conferidos célula a célula por comando (§2.2). Escala em `:29-36`. | Nenhuma. Mínimo excedido em 3,5×. |
| **RQ-2** — detecção de APIs deprecated presente | ✅ | `references/antipattern-catalog.md:468-497` (AP-16). Procedimento obrigatório em `:476-478`, exigindo a versão **real** do runtime e o equivalente moderno por ocorrência. Insumo em `references/project-analysis.md:74-97`. TR em `references/refactor-playbook.md:501-538`. | Nenhuma para o requisito literal. Ver **C-12**: AP-16 segue sem `Manifestações por stack`; ganhou uma `Nota de procedência` (`:495-497`) que **declara** a lacuna em vez de fechá-la. |
| **RQ-3** — ≥8 padrões de transformação com código antes/depois | ✅ | `references/refactor-playbook.md:29-52` (índice dos 18 TRs) · 18 cabeçalhos `## TR-NN` · 18 blocos `python` + 18 `javascript`, 36 marcadores `antes` e 36 `depois` — verificado por comando (§2.3). | Nenhuma. |
| **RQ-4** — as 5 áreas de conhecimento obrigatórias cobertas | ✅ | Mapa em `SKILL.md:25-32`. Os 6 arquivos somam 2.587 linhas; o 6º (`validation-protocol.md`) é justificado em `SKILL.md:34-37`. | Nenhuma para o requisito. Ver **B-4**: o mapa continua sem autorizar as seções de `mvc-guidelines.md` que as Fases 1 e 2 efetivamente pedem. |
| **RQ-5** — Fase 2 pausa e pede confirmação antes de escrever | ⚠️ | `SKILL.md:148-167`; prompt literal em `:156`, idêntico ao do enunciado. As 4 regras do gate em `:159-167`. Reforçado em `commands/refactor-arch.md:20-23`. | **O invariante que sustenta o gate está enunciado com dois valores diferentes:** `SKILL.md:142-145` e `:252-253` dizem **duas** escritas permitidas antes do gate (`REPORT_PATH` + `BASELINE_PATH`); `report-template.md:6` continua dizendo que o relatório é a **única**. Ver **B-1**. |
| **RQ-6** — Fase 3 valida boot + endpoints | ✅ | `SKILL.md:193-215` (protocolo de onda: boot após cada TR, saída explícita para boot irrecuperável em `:203-207`, smoke test ao fim). Boot definido sem acoplar a framework em `validation-protocol.md:74-89`; smoke test contra baseline em `:93-111`; predicado fechado em `:113-137`. | Nenhuma. Esta é a dimensão que mais melhorou desde a rodada 1. |
| **RQ-7** — frontmatter YAML válido com `name` e `description` | ✅ | `SKILL.md:1-13`. `yaml.safe_load` OK; chaves exatamente `['name','description']`; `name='refactor-arch'`; `description` com 761 caracteres / 121 palavras. Saída literal em §2.5. | Nenhuma. |
| **RQ-8** — SKILL.md < 500 linhas | ✅ | `wc -l SKILL.md` → **258**. 51,6% do teto. | Nenhuma. Cresceu 19,4% desde a rodada 1 (216 → 258), absorvendo C-1, C-3, C-5, C-8 e C-10. Folga ainda larga. |
| **RQ-9** — cadência de ondas normativa no SKILL.md **e** no `validation-protocol.md`, incluindo rollback ao último commit verde | ⚠️ | Presente nos dois e agora **auditável**: registro de ondas com SHA (`validation-protocol.md:204-225`), alvo de rollback resolvido para todas as ondas (`:230-243`, `SKILL.md:213-215`), predicado binário (`:113-137`). | **Mas o conjunto das ondas deixou de ser uma partição.** A §4.2 define "vazia" por ausência de **finding** da severidade, enquanto o conteúdo da onda é definido por **TR** agendado; quando um TR cai numa onda cuja severidade não tem finding, a onda é simultaneamente vazia e não-vazia. Ver **B-2** — é o bloqueador desta rodada. |

**Placar dos requisitos literais: 7 ✅ · 2 ⚠️ · 0 ❌.** (Rodada 1: 8 ✅ · 1 ⚠️.)

O RQ-5 regrediu de ✅ para ⚠️ por efeito colateral da correção C-4, e o RQ-9 continua ⚠️ por
motivo **diferente** do da rodada 1 — o predicado antes indefinido agora está definido, mas a
definição nova não particiona o domínio.

A reprovação abaixo não vem desta matriz. Vem das seções 4 e 5.

---

## 2. Contagens reais

Saída literal de comando executado em `code-smells-project/.claude/skills/refactor-arch/`.
Nenhuma é estimativa.

### 2.1 Linhas por arquivo

```console
$ wc -l SKILL.md references/*.md
   258 SKILL.md
   799 references/antipattern-catalog.md
   293 references/mvc-guidelines.md
   206 references/project-analysis.md
   780 references/refactor-playbook.md
   234 references/report-template.md
   275 references/validation-protocol.md
  2845 total

$ wc -l references/*.md | tail -1
  2587 total
```

Evolução desde a rodada 1 e contraste com o design (`.planning/01-design-skill.md:89-101`):

| Arquivo | Design | Rodada 1 | Rodada 2 | Δ rodada |
|---|---|---|---|---|
| `SKILL.md` | ~190 | 216 | **258** | +42 |
| `project-analysis.md` | ~280 | 206 | 206 | 0 |
| `antipattern-catalog.md` | ~640 | 793 | **799** | +6 |
| `report-template.md` | ~210 | 203 | **234** | +31 |
| `mvc-guidelines.md` | ~330 | 293 | 293 | 0 |
| `refactor-playbook.md` | ~740 | 780 | 780 | 0 |
| `validation-protocol.md` | ~190 | 173 | **275** | +102 |
| **Total** | **~2.580** | 2.664 | **2.845** | **+181** |

O crescimento é concentrado onde os bloqueadores estavam: `validation-protocol.md` +59% (C-3, C-4,
C-8, C-10), `SKILL.md` +19% (C-1, C-2, C-5), `report-template.md` +15% (C-4, C-7). Razão
orquestrador:conhecimento passou de 1:11,3 para **1:10,0** — o orquestrador ganhou peso relativo,
ainda longe do teto de 500. Sem ação.

**Teto declarado de 800 linhas para o catálogo:** cumprido com 1 linha de folga (799). Registro de
fidelidade: esse teto **não existe** em `.planning/01-design-skill.md` — o design estima ~640 para
o arquivo (`:93`) e fixa 500 apenas para o `SKILL.md` (`:459`, R-08). O teto de 800 é um critério
introduzido depois; a auditoria o aplica como declarado, mas ele não é rastreável ao design.

### 2.2 Anti-patterns: contagem e distribuição de severidade

```console
$ grep -cE '^#{2,4} *AP-[0-9]+' references/antipattern-catalog.md
28

$ grep -oE '^\*\*(CRITICAL|HIGH|MEDIUM|LOW) · ' references/antipattern-catalog.md \
    | sed 's/[^A-Z]//g' | sort | uniq -c
      7 CRITICAL
      7 HIGH
      4 LOW
     10 MEDIUM

$ sed -n '50,77p' references/antipattern-catalog.md | awk -F'|' '{print $4}' | tr -d ' ' | sort | uniq -c
      7 CRITICAL
      7 HIGH
      4 LOW
     10 MEDIUM

$ sed -n '50,77p' references/antipattern-catalog.md | awk -F'|' '{print $5}' | tr -d ' ' | sort | uniq -c
      1 —
      7 1
      7 2
     10 3
      3 4
```

**Índice e corpo concordam célula a célula.** 28 APs, 28 linhas de severidade, 28 linhas de índice.
A coluna `Onda` soma 27 + 1 `—` (AP-28, `reportado, não corrigido`), coerente com o corpo (`:781`).

### 2.3 Transformações: contagem e blocos de código por stack

```console
$ grep -cE '^#{2,4} *TR-[0-9]+' references/refactor-playbook.md
18

$ grep -oE '^```[a-z]*' references/refactor-playbook.md | sort | uniq -c
     36 ```
     18 ```javascript
     18 ```python

$ echo "antes: $(grep -cE '^# antes|^// antes' references/refactor-playbook.md)  depois: $(grep -cE '^# depois|^// depois' references/refactor-playbook.md)"
antes: 36  depois: 36
```

18/18 TRs com par Python + JavaScript e marcadores em ambos. Inalterado desde a rodada 1, incluindo
a observação de que **só duas stacks estão representadas** em código enquanto a `description`
promete seis — mitigação textual em `refactor-playbook.md:6-9` e `SKILL.md:256-257`. Registrado,
não é blocker.

### 2.4 Campos presentes nas entradas do catálogo

```console
$ grep -oE '^\*\*[A-ZÀ-Ú][^*]{2,40}\.?\*\*' references/antipattern-catalog.md | sort | uniq -c | sort -rn | head -8
     28 **Sinal.**
     28 **NÃO é finding quando.**
     28 **Evidência mínima.**
     25 **Manifestações por stack.**
      2 **Verificação decisiva.**
      2 **Sinal correlato.**
      2 **Reforço.**
      2 **Procedência.**

$ grep -c 'Aplica a' references/antipattern-catalog.md
2
```

Os três campos estruturais seguem em 28/28. `Manifestações por stack` segue faltando em 3, os
mesmos da rodada 1:

```console
SEM 'Manifestações por stack': AP-16 — Deprecated API usage
SEM 'Manifestações por stack': AP-26 — Código morto e dependências declaradas e não usadas
SEM 'Manifestações por stack': AP-28 — Ausência de infraestrutura de qualidade
```

**A coluna `Aplica a` voltou** — as 2 ocorrências são a definição do campo (`:16-23`) e o cabeçalho
do índice (`:48`). Verificação de preenchimento:

```console
$ sed -n '50,77p' references/antipattern-catalog.md | awk -F'|' '{if($6 ~ /^ *$/) print "VAZIA "NR}'
(nenhuma saída)

$ ... | awk -F'|' '{print $6}' | sort | uniq -c | sort -rn
     17 Universal
      2 Projetos com persistência
      1 Projetos com ORM ou driver direto
      1 Projetos com autenticação
      1 Persistência ou execução dinâmica
      1 APIs que serializam entidades
      1 APIs de leitura de coleção
      1 APIs consumidas por browser
      1 APIs com autenticação
      1 APIs
      1 ≥2 escritas relacionadas
```

28/28 células preenchidas, 11 valores distintos, os mesmos vocábulos que o design previa
(`.planning/01-design-skill.md:293`). **Ataque residual:** o escopo vive só no índice, não no corpo
de cada AP. Um agente que varra o corpo entrada por entrada — que é o que `SKILL.md:128` manda
fazer — não tem o escopo diante dos olhos ao responder o sinal. Mitigado por `:16-18`, que declara
explicitamente que o campo mora na coluna do índice, e pelo fato de o arquivo ser lido integralmente.
Registrado como **B-6**, sem ação isolada.

### 2.5 Frontmatter

```console
$ python3 -c "... yaml.safe_load(fm) ..."
YAML OK. keys = ['name', 'description']
name = 'refactor-arch'
description chars = 761 words = 121
```

Idêntico à rodada 1. A `description` não foi tocada pelas correções — o que é correto: nada nas
correções mudou o gatilho de invocação.

---

## 3. Integridade de referências cruzadas

### 3.1 Conjunto de IDs

```console
$ grep -ohE 'AP-[0-9]+' references/*.md SKILL.md | sort -u
AP-01 … AP-28   (28 IDs, sem buracos)

$ grep -ohE 'TR-[0-9]+' references/*.md SKILL.md | sort -u
TR-01 … TR-18   (18 IDs, sem buracos)
```

Conjunto citado = conjunto de cabeçalhos existentes, nos dois casos. **Quebras: nenhuma.**

### 3.2 Consistência bidirecional catálogo ↔ playbook

Os 27 pares AP→TR do índice do catálogo (`:50-77`) batem com a coluna `Resolve` do índice do
playbook (`:29-52`) nos dois sentidos. AP-28 declara `— | reportado, não corrigido`, coerente com
`refactor-playbook.md:54` e com o corpo do AP (`antipattern-catalog.md:781`).

**Quebras: nenhuma.** A divergência de **onda** entre os dois lados persiste em 2 casos (TR-05 e
TR-18) — inconsistência semântica, não de referência, tratada em **B-2**.

### 3.3 Âncoras Markdown (verificação programática)

```console
references/antipattern-catalog.md          refs: 28 anchors: 28 broken:[]
references/mvc-guidelines.md               refs: 10 anchors:  0 broken:[]
references/project-analysis.md             refs:  0 anchors:  0 broken:[]
references/refactor-playbook.md            refs:  0 anchors:  0 broken:[]
references/report-template.md              refs:  0 anchors:  0 broken:[]
references/validation-protocol.md          refs:  0 anchors:  0 broken:[]
SKILL.md                                   refs:  0 anchors:  0 broken:[]
```

As 28 âncoras `<a id="ap-NN">` do catálogo sobreviveram à remoção da régua da linha 46 (a única
edição estrutural do arquivo nesta rodada). Os 10 links de índice de `mvc-guidelines.md` resolvem
para os 10 cabeçalhos `## N.`. **Quebras: nenhuma.**

### 3.4 Referências de seção (`§`) entre arquivos

```console
$ grep -ohE '[a-z-]+\.md.{0,3}§ ?[0-9]+(\.[0-9]+)?' references/*.md SKILL.md | sort | uniq -c
      2 mvc-guidelines.md` §10
      1 mvc-guidelines.md` §3
      4 mvc-guidelines.md` §6
      1 mvc-guidelines.md` §7
      1 mvc-guidelines.md` §9
      1 project-analysis.md` §9
      2 validation-protocol.md` §2
      1 validation-protocol.md` §4
      2 validation-protocol.md` §4.1
      2 validation-protocol.md` §4.2
      2 validation-protocol.md` §6.1
      1 validation-protocol.md` §8
```

Todos os 20 alvos existem: `mvc-guidelines.md` §3 (`:76`), §6 (`:182`), §7 (`:208`), §9 (`:253`),
§10 (`:273`); `project-analysis.md` §9 (`:196`); `validation-protocol.md` §2 (`:33`), §4 (`:93`),
**§4.1 (`:113`)**, **§4.2 (`:139`)**, **§6.1 (`:204`)**, §8 (`:263`). As quatro referências de
subseção são novas desta rodada e todas resolvem.

**Quebras de resolução: nenhuma.** A *rota de carregamento* continua quebrada — ver **B-4**.

### 3.5 Veredito da seção 3

**Zero quebras em 46 IDs, 38 âncoras e 20 referências de seção.** As correções adicionaram 8
referências cruzadas novas e não quebraram nenhuma das antigas. Continua sendo a dimensão mais
sólida da skill.

---

## 4. Ambiguidades de instrução

Critério idêntico ao da rodada 1: trecho que um agente **sem supervisão** pode resolver de mais de
uma forma, com comportamentos observavelmente diferentes. Ordenado por dano.

---

### B-1 · Duas escritas permitidas ou uma? O invariante do gate tem dois valores

**Trecho.** `report-template.md:6`:

> Gravar este arquivo é a **única** escrita permitida antes do gate: é artefato novo e aditivo,
> não modificação do projeto.

Contra `SKILL.md:142-145`:

> 9. **Grave o relatório em `REPORT_PATH`** […] Com `BASELINE_PATH`, são as **duas únicas escritas
>    permitidas** antes do gate

E `SKILL.md:252-253` (Regras invioláveis), `validation-protocol.md:59` (*"O baseline persistido é a
**segunda exceção** à regra de não-escrita"*) e `commands/refactor-arch.md:17-19` (*"As únicas
escritas permitidas antes do gate são o baseline […] e o relatório"*).

**O problema.** Quatro pontos do pacote dizem "duas"; um diz "uma". O que diz "uma" é o arquivo
que descreve o próprio artefato do gate, e é o único que um agente pode ler isoladamente ao redigir
o relatório. Não é uma diferença de ênfase: é o **invariante que sustenta RQ-5** enunciado com dois
valores incompatíveis dentro do mesmo pacote.

**Interpretações possíveis:** (1) seguir `SKILL.md` e ignorar a linha do template — provável, mas
por sorte de ordem de leitura; (2) tratar `report-template.md:6` como norma e concluir que gravar
`BASELINE_PATH` na Fase 1 violou a regra, e então **não gravar**, ou gravar e reportar violação
inexistente; (3) notar a contradição e pedir esclarecimento ao humano — comportamento correto e não
instruído.

**Origem.** Defeito **introduzido pela correção C-4**: a persistência do baseline criou uma segunda
exceção e ela foi propagada para `SKILL.md`, `validation-protocol.md` e o slash command, mas não
para a frase do `report-template.md` que contava as exceções.

**Dano.** Alto e barato de consertar: uma palavra. Não quebra a execução — o baseline é gravado na
Fase 1, antes de `report-template.md` entrar em contexto (`SKILL.md:31`, *"ao redigir, fim da Fase
2"*) —, mas deixa o pacote com uma afirmação normativa falsa exatamente sobre a garantia central.

**Nota relacionada.** `SKILL.md:76` ainda manda declarar em voz alta *"auditoria read-only até o
gate da Fase 2"* enquanto a mesma fase grava `BASELINE_PATH`. `SKILL.md:98` desfaz a ambiguidade
("nenhuma escrita **em arquivo do projeto**"), mas a frase declarada em voz alta é a que o humano
ouve. Frouxidão terminológica, não contradição — registrada em **B-7**.

---

### B-2 · "Onda vazia" é definida por finding; o conteúdo da onda é definido por TR

**Trecho.** `validation-protocol.md:143-147` (§4.2, introduzida nesta rodada):

> | **vazia** | `—` | Nenhum finding da severidade da onda: nenhum TR aplicado, nenhum boot,
> nenhum smoke test | não | `empty`, sem SHA |

E `SKILL.md:195-199`:

> **vazia** `—` — a severidade da onda não tem finding, nada é aplicado e nada é validado […]
> Onda vazia pula os cinco passos abaixo: sem TR, sem boot, sem smoke test, **sem commit**.

**O problema.** A definição trata "nenhum finding daquela severidade" e "nenhum TR aplicado" como a
**mesma** condição, ligadas por dois-pontos. Elas não são a mesma condição, e o próprio pacote
produz o caso em que divergem — o caso que a rodada 1 já havia registrado como **A-3 / C-6** e que
segue aberto:

| TR | Rótulo de onda | Resolve | Onda dos APs |
|---|---|---|---|
| TR-05 | Onda 1 (`refactor-playbook.md:216`) | AP-05, AP-24 | AP-05 = 1; **AP-24 = 3** |
| TR-06 | Onda 1 (`refactor-playbook.md:257`) | AP-06, AP-13 | AP-06 = 1; **AP-13 = 2** |
| TR-18 | Onda 4 (`refactor-playbook.md:740`) | AP-25, AP-27, AP-20 | AP-25/27 = 4; **AP-20 = 3** |

A regra de reatribuição continua **unidirecional** em todos os três lugares onde é enunciada —
`SKILL.md:179-180` (*"um TR rotulado para uma onda posterior **sobe**"*),
`antipattern-catalog.md:38-41` (*"antecipe o TR"*), `refactor-playbook.md:16-18` (*"antecipe-o"*).
Nada diz o que fazer quando o TR está rotulado para uma onda **anterior** à do seu único finding.

**O cenário que quebra.** Projeto com AP-13 (HIGH) e **sem** AP-06 — monólito que acopla rota ao
ORM mas não tem uma god class. Não há finding CRITICAL, logo:

1. Pela §4.2, **Onda 1 é vazia** — "nenhum finding da severidade da onda" é verdadeiro.
2. Pela regra unidirecional, TR-06 **não desce**: ele está rotulado Onda 1 e só há instrução para
   subir. Ele continua agendado na Onda 1.
3. `SKILL.md:195-199` manda a Onda 1 pular os cinco passos: **sem TR, sem boot, sem commit.**

A onda é simultaneamente vazia (critério de finding) e não-vazia (critério de TR), e a instrução
mais recente — a que acabou de ser escrita — manda pular. **Consequência:** TR-06 nunca roda, e
`SKILL.md:184` diz que TR-06 **é** o esqueleto MVC (*"TR-01…TR-06 — e o esqueleto MVC, que **é**
esta onda"*), reforçado em `:189-191` (*"Não há onda 0 […] extrair configuração e decompor a god
class […] produzem a estrutura"*). A Onda 2 então aplica TR-07, cuja pré-condição é
*"existe camada de service (TR-06, quando aplicável)"* (`refactor-playbook.md:303`) — a hedge
"quando aplicável" não cria a camada, só desobriga de verificar.

**Resultado observável:** a Fase 3 termina com `Waves: 1 CRITICAL — · 2 HIGH ✓ · 3 MEDIUM ✓ ·
4 LOW ✓`, todos os smoke tests `M/M`, todos os commits com contagem — e **nenhuma camada MVC
criada**. Todo marcador do bloco de saída está correto pelas definições vigentes. O projeto não foi
migrado para MVC e nada no artefato final diz isso.

**Por que é pior que A-3 era.** Na rodada 1 a ambiguidade tinha três leituras e a mais provável
(*"as 4 ondas são obrigatórias"*, A-6) rodava TR-06 na Onda 1 por inércia. A §4.2 fechou essa
leitura: agora existe instrução explícita mandando pular. A correção C-10 endureceu uma regra
enquanto C-6 seguia aberta, e o efeito conjunto é pior que qualquer um dos dois isolados.

**Correção mínima (não aplicada).** Duas linhas, e as duas são necessárias:
- Redefinir vazia pelo **plano**, não pela severidade: *"onda vazia é a onda para a qual o plano
  aprovado no gate não agendou nenhum TR"*. Isso torna os três estados uma partição real.
- Fechar C-6 tornando a regra bidirecional: *"um TR migra para a onda do finding de maior
  severidade que ele resolve — sobe quando esse finding é mais severo que o rótulo, desce quando é
  menos severo. TR sem finding não entra no plano."*

**Dano.** Bloqueador. É o único defeito desta rodada que produz um resultado silenciosamente errado
no artefato que o desafio avalia.

---

### B-3 · "4 ondas" continua hardcoded fora do bloco de saída da Fase 3

**Trecho.** A correção C-10 normatizou os três estados e ajustou a linha `Waves` (`SKILL.md:230`) e
a linha `History` (`:234`). Quatro pontos ficaram para trás:

| Local | Texto | Efeito com onda vazia |
|---|---|---|
| `report-template.md:229` | *"plano em **4 ondas**"* — rodapé do relatório, lido no gate | O humano aprova um plano que declara 4 ondas quando há 3 (ou 2) |
| `report-template.md:211` | *"Repita para as Ondas 2, 3 e 4"* | Manda escrever seção de onda sem TR algum |
| `SKILL.md:151` | *"o plano nas 4 ondas"* — apresentação do gate | Idem |
| `commands/refactor-arch.md:20` | *"plano em 4 ondas"* | Idem |
| `refactor-playbook.md:740` | TR-18: *"**Pré-condição:** as ondas 1 a 3 estão **verdes e commitadas**"* | Pré-condição **insatisfazível** quando alguma delas é vazia: vazia não é verde e não gera commit (`validation-protocol.md:143-152`) |

A última é a mais grave das cinco: um agente que respeite a pré-condição de TR-18 ao pé da letra
**não aplica TR-18** num projeto sem findings MEDIUM, mesmo havendo findings LOW — e a Onda 4, que
tinha conteúdo, é abortada por uma pré-condição que fala de uma onda que não tinha.

**Interpretações possíveis:** (1) tratar "verdes e commitadas" como "não vermelhas" e prosseguir;
(2) tratar literalmente e pular TR-18; (3) criar um commit vazio para satisfazer a pré-condição —
exatamente o que `validation-protocol.md:145-152` proíbe.

**Dano.** Alto. Mesmo raiz que B-2: a normatização dos três estados não foi propagada aos textos que
pressupunham quatro ondas sempre executadas.

---

### B-4 · Quando carregar cada reference — o mapa continua sem cobrir o que os arquivos pedem

**Trecho.** `SKILL.md:29`, **inalterado desde a rodada 1**:

> | 3 | Arquitetura-alvo MVC | `references/mvc-guidelines.md` | Fase 2 (§9) e Fase 3, integral |

**Ambiguidade sintática.** "integral" liga-se a quê — só à Fase 3, ou às duas fases? O plural
seguido de um qualificador único não desambigua.

**Ambiguidade substantiva.** Sob a leitura restritiva, a Fase 2 carrega só §9. Mas:

| Quem pede | Linha | Seção exigida | Autorizada pelo mapa? |
|---|---|---|---|
| `SKILL.md` (Fase 2, passo 6) | `SKILL.md:136` | `mvc-guidelines.md` §6 | ❌ o mapa autoriza só §9 |
| `antipattern-catalog.md` (AP-08, Fase 2) | `:278` | §10 | ❌ |
| `antipattern-catalog.md` (AP-13, Fase 2) | `:405` | §10 | ❌ |
| `antipattern-catalog.md` (AP-26, Fase 2) | `:752` | §6 | ❌ |
| `project-analysis.md` (Fase 1) | `:122` | §7 | ❌ o mapa não carrega o arquivo na Fase 1 |
| `project-analysis.md` (Fase 1) | `:144` | §6 | ❌ |
| `project-analysis.md` (Fase 1) | `:147` | §3 | ❌ |

**Sete ponteiros para seções não autorizadas na fase em que são pedidos**, um a mais que na rodada 1
(AP-26 → §6 não havia sido contabilizado). As referências *resolvem* (§3.4); falta a autorização de
carga.

**Dano.** Médio, inalterado. As três interpretações da rodada 1 continuam todas defensáveis.
Nenhuma correção tocou `SKILL.md:29`.

---

### B-5 · O registro de ondas é volátil — o mesmo defeito que C-4 consertou para o baseline

**Trecho.** `validation-protocol.md:206-207`:

> **Mantenha na resposta ao usuário**, atualizado a cada evento, um registro de quatro colunas. É
> ele que torna o alvo do rollback um **dado registrado**, e não uma dedução feita sob pressão.

**O problema.** O argumento que justificou persistir o baseline em disco (`validation-protocol.md:
59-63`: *"Baseline em memória de trabalho não sobrevive a [uma quebra de sessão]"*) se aplica
literalmente ao registro de ondas — que é o **único** lugar onde o alvo do rollback está declarado
(`:230-232`, *"O alvo é **sempre** a última linha `green` do registro da §6.1"*). Ele mora na
resposta ao usuário, isto é, no histórico de conversa.

A Fase 3 é longa (quatro ondas, quatro smoke tests, boot por TR) e é onde a quebra de sessão custa
mais caro. Perdido o registro, o agente precisa reconstruí-lo por `git log` — recuperável na
prática, porque a mensagem de commit é convencionada e agora carrega `Smoke test: N/M`
(`validation-protocol.md:188-201`), mas **não instruído em lugar nenhum**, e a §7 declara que o
alvo é um dado registrado, não uma dedução.

**Assimetria registrada:** o baseline, usado 4 vezes, é artefato em disco; o registro de ondas,
usado a cada evento e consultado no momento de maior pressão (rollback), é texto de conversa.

**Dano.** Médio. Diferente de C-4, aqui existe uma fonte de verdade redundante (`git log` + a
convenção de mensagem), então a perda é recuperável — mas por inferência não autorizada, que é
exatamente o que o texto diz que não quer.

---

### B-6 · `Aplica a` só existe no índice, e a varredura é pelo corpo

**Trecho.** `antipattern-catalog.md:16-18` declara o campo *"escopo em que o sinal faz sentido,
declarado na coluna homônima do índice"*. `SKILL.md:128` manda *"varrer os 28 APs na ordem do
catálogo, respondendo o sinal de detecção de cada um"* — varredura pelo corpo.

**O problema.** Ao responder o sinal de AP-20 no corpo (`:585`), o escopo `APIs consumidas por
browser` está 550 linhas acima, no índice. O relatório precisa do escopo para escrever a linha
"não aplicável" (`report-template.md:146-147`, *"os fatos da Fase 1 não satisfazem o escopo da
coluna `Aplica a`"*). A informação existe e é alcançável — o arquivo é lido integralmente — mas
está fora do bloco que o agente tem sob os olhos na hora de decidir.

**Dano.** Baixo. Mitigação por desenho declarada em `:16-18`; a alternativa (repetir o escopo em 28
cabeçalhos) custa ~28 linhas contra o teto de 800, que tem 1 de folga. Registrado sem ação.

---

### B-7 · Ambiguidades menores registradas, sem ação isolada

| # | Trecho | Ambiguidade |
|---|---|---|
| a | `SKILL.md:76` — declarar *"auditoria read-only até o gate"* enquanto a Fase 1 grava `BASELINE_PATH` | Terminologia frouxa: "read-only" significa "sobre arquivos do projeto", desambiguado só em `:98`. A frase declarada em voz alta é a que o humano ouve. Relacionada a **B-1**. |
| b | `validation-protocol.md:162` — *"Quatro ondas, protocolo idêntico em todas"* (§5) | Contradiz a §4.2 do mesmo arquivo, que isenta a onda vazia do protocolo. Tensão interna a um arquivo, resolvida pela ordem de leitura (§4.2 vem antes), mas não declarada. |
| c | `validation-protocol.md:129-130` — *"Endpoint não enumerável não reduz `M`"* | Lido isoladamente sugere que o endpoint entra em `M`; a frase seguinte esclarece que o que nunca entrou no baseline não é comparável. Resolve, mas exige as duas frases. |
| d | `SKILL.md:231` — `Smoke test : <n>/<n>` no bloco final | Com ondas de tamanhos diferentes, não diz **qual** smoke test reportar (o da última onda verde, presumivelmente). Se todas as ondas forem vazias, não há smoke test algum e o campo não tem valor definido. |
| e | `commands/refactor-arch.md:29-30` | Linha em branco entre os itens 4 e 5 quebra a lista numerada em dois blocos no Markdown renderizado. Cosmético. |
| f | `antipattern-catalog.md` AP-16, AP-26, AP-28 sem `Manifestações por stack` | Inalterado desde a rodada 1. AP-16 ganhou `Nota de procedência` (`:495-497`) que declara a fraqueza cross-stack em vez de corrigi-la. Ver **C-12**. |
| g | Skill presente em 1 dos 3 projetos | `find . -name SKILL.md` → só `code-smells-project/`. `ecommerce-api-legacy/` e `task-manager-api/` existem e não têm `.claude/`. Fronteira de entregável. Ver **C-13**. |

---

## 5. Teste de rollback — três simulações

A rodada 1 simulou um cenário. Esta rodada simula três: o mesmo de antes (para medir a correção
C-8), e dois que exercitam a §4.2 recém-escrita.

### 5.1 Cenário A — Onda 1 verde e commitada, Onda 2 vermelha (repetição da rodada 1)

Smoke test da Onda 2 retorna 12/15, com 3 endpoints divergindo no critério 4 por mudança não
declarada em Breaking changes.

| Pergunta | Rodada 1 | Rodada 2 | Evidência |
|---|---|---|---|
| 12/15 é vermelho? | ⚠️ indefinido | ✅ sim, sem ambiguidade | `validation-protocol.md:124-127` (*"Fração parcial não é verde. `N < M` é vermelho, sem exceção"*) |
| Para qual SHA voltar? | ⚠️ por inferência | ✅ dado registrado | `:230-232` + registro `:204-225`; a linha `onda-1 | <sha> | 15/15 | green` é o alvo |
| O SHA da Onda 1 foi guardado? | ❌ nenhuma instrução | ✅ instruído | `:221-223` (*"colando o SHA que o `git commit` devolveu — não no fim da fase, não de memória"*) e `SKILL.md:209-212` |
| Risco de resetar para o baseline por engano | ⚠️ real | ✅ fechado | `SKILL.md:64-67` (*"o baseline nunca mais volta a ser o alvo"*) e `validation-protocol.md:234-238` |
| O que reportar | ✅ | ✅ | `validation-protocol.md:249-256`, 4 itens, todos determináveis |

**Veredito 5.1: ✅ robusto.** O cenário que na rodada 1 dependia de redescoberta por `git log` agora
é resolvido por leitura de tabela. C-3 e C-8 sustentam o ataque.

### 5.2 Cenário B — Onda 2 vazia, Onda 3 vermelha

Projeto sem findings HIGH. Onda 1 verde e commitada; Onda 2 vazia; Onda 3 aplica TR-11…TR-17 e o
smoke test retorna 14/15.

- **A Onda 2 vira linha do registro?** Sim, `empty`, sem SHA (`validation-protocol.md:147`,
  exemplo em `:213`).
- **Ela pode ser alvo de rollback?** Não — `:217` (*"`empty` é linha de relato, não ponto de
  retorno: só `green` é alvo de rollback"*) e `SKILL.md:199`.
- **Qual o alvo?** A última linha `green`: `onda-1`. Resolve por leitura direta.
- **A saída final mostra o quê?** `Waves: 1 CRITICAL ✓ · 2 HIGH — · 3 MEDIUM ✗ · 4 LOW …` —
  `SKILL.md:230` + legenda `:240-243`. A Onda 2 não aparece em `History` (`:234`, *"one entry per
  committed wave"*).

**Veredito 5.2: ✅ resolve.** Este é o cenário para o qual C-10 foi escrita e ele fecha
deterministicamente. Nenhuma onda não executada aparece como validada.

### 5.3 Cenário C — Onda 1 vazia num projeto sem findings CRITICAL

Projeto com AP-13 (HIGH) e AP-15/AP-22 (MEDIUM), sem nenhum CRITICAL.

- **Onda 1 é vazia?** Pela §4.2, sim: não há finding CRITICAL.
- **TR-06 estava agendado nela?** Sim — rótulo `Onda 1` (`refactor-playbook.md:257`), acionado por
  AP-13, e a regra de reatribuição só cobre subida (**B-2**).
- **O que o agente faz?** `SKILL.md:197-199` manda pular: *"sem TR, sem boot, sem smoke test, sem
  commit"*.
- **A camada de service existe quando TR-07 roda na Onda 2?** Não. A pré-condição de TR-07
  (`:303`) diz *"existe camada de service (TR-06, quando aplicável)"* e a hedge desobriga de
  verificar.
- **O smoke test detecta?** Não. O smoke test compara **contrato de endpoint**, não estrutura —
  e o contrato é justamente o que a refatoração preserva. `M/M` conformes com zero camadas criadas
  é um resultado perfeitamente possível.
- **A validação final detecta?** `SKILL.md:219-223` verifica que nenhum AP CRITICAL ou HIGH
  permanece — AP-13 permaneceria, porque TR-06 não rodou. **Esta é a única defesa que existe**, e
  ela depende de o agente reauditar em vez de assumir que o plano aprovado foi executado. Nada em
  `:219-224` manda reauditar; a frase é *"Nenhum AP CRITICAL ou HIGH do relatório permanece"*, uma
  asserção a verificar, sem procedimento de verificação.

**Veredito 5.3: ❌ falha.** A skill produz um resultado que se declara conforme em todos os
marcadores e não entrega a arquitetura-alvo. É a materialização de **B-2**.

### 5.4 O que as simulações expuseram

1. O caminho de rollback — o ponto mais frágil da rodada 1 — está **fechado** (5.1, 5.2). C-3, C-8
   e C-10 sustentam ataque direto.
2. O caminho novo aberto é o **oposto**: não é o rollback que falha, é a onda que nunca executa e
   ainda assim é contabilizada como estado legítimo (5.3).
3. A validação final (`SKILL.md:219-224`) é a única barreira contra 5.3 e não tem procedimento —
   é uma asserção, não um teste. Registrado como **C-16**.

---

## 6. Veredito

# ❌ REPROVADO

**Um bloqueador, contra quatro da rodada 1.** Os quatro bloqueadores originais estão fechados e
sobreviveram a ataque direto (§7). O que reprova é um defeito **novo**, criado pela interação entre
uma correção aplicada (C-10, ondas vazias) e uma correção não aplicada (C-6, regra de onda
unidirecional):

- **A Onda 1 pode ser declarada vazia num projeto que precisa dela** (B-2, simulação 5.3). A §4.2
  define "vazia" por ausência de finding da severidade, enquanto o conteúdo da onda é definido por
  TR agendado. Quando TR-06 — que `SKILL.md:184` declara **ser** o esqueleto MVC — é acionado por
  um finding HIGH num projeto sem CRITICAL, a Onda 1 é vazia e não-vazia ao mesmo tempo, e a
  instrução mais recente manda pulá-la. O resultado é uma Fase 3 que termina com todos os
  marcadores corretos, todos os smoke tests `M/M`, e nenhuma camada MVC criada.

Dois defeitos ALTO acompanham, ambos da mesma raiz — normatização não propagada:

- **O invariante do gate tem dois valores** (B-1): `report-template.md:6` diz "única escrita
  permitida"; `SKILL.md:142-145`, `:252-253`, `validation-protocol.md:59` e o slash command dizem
  "duas". Uma palavra.
- **"4 ondas" continua hardcoded em 5 lugares** (B-3), incluindo a pré-condição de TR-18
  (`refactor-playbook.md:740`, *"as ondas 1 a 3 estão verdes e commitadas"*), que se torna
  insatisfazível quando qualquer uma delas é vazia.

O padrão desta rodada é diferente do da anterior. Na rodada 1 os defeitos eram **lacunas** —
predicados não definidos, alvos não resolvidos, artefatos não ancorados. Aqui são **arestas**: as
definições novas são corretas e fechadas isoladamente, e falham no contato com o texto que não foi
atualizado junto. É o modo de falha esperado de uma rodada de correção cirúrgica, e ele se conserta
com propagação, não com redesenho.

### Lista ordenada de correções

IDs preservados da rodada 1 quando é a mesma correção; novos a partir de C-14.

| # | Sev. | Correção | Origem | Arquivos a tocar |
|---|---|---|---|---|
| **C-14** | 🔴 BLOQUEADOR | Redefinir onda vazia pelo **plano** (*"nenhum TR agendado para a onda no plano aprovado"*), não pela severidade dos findings, tornando os três estados uma partição real. | B-2, 5.3 | `validation-protocol.md:139-158`, `SKILL.md:195-199` |
| **C-6** | 🔴 BLOQUEADOR | Tornar bidirecional a regra de onda do TR: sobe quando o finding é mais severo que o rótulo, **desce** quando é menos severo; TR sem finding não entra no plano. Aberta desde a rodada 1; agora é o outro metade de C-14 e não pode mais ser adiada. | A-3, B-2 | `SKILL.md:179-180`, `antipattern-catalog.md:38-41`, `refactor-playbook.md:16-18` |
| **C-15** | 🟠 ALTO | Corrigir `report-template.md:6` para "uma das duas escritas permitidas antes do gate", alinhando com `SKILL.md:142-145`. | B-1 | `report-template.md:6` |
| **C-16** | 🟠 ALTO | Propagar os três estados aos textos que pressupõem 4 ondas executadas — em especial a pré-condição de TR-18, hoje insatisfazível com qualquer onda vazia. Dar procedimento (não asserção) à validação final. | B-3, 5.4 | `refactor-playbook.md:740`, `report-template.md:211,229`, `SKILL.md:151,219-223`, `commands/refactor-arch.md:20` |
| **C-9** | 🟡 MÉDIO | Desambiguar o mapa de carregamento: `mvc-guidelines.md` §6/§9/§10 na Fase 2 e §3/§6/§7 acessíveis na Fase 1, ou instrução explícita de carga sob demanda. Inalterada desde a rodada 1; um ponteiro a mais foi contabilizado (AP-26 → §6). | A-5, B-4 | `SKILL.md:29,124,136` |
| **C-17** | 🟡 MÉDIO | Persistir o registro de ondas, ou instruir sua reconstrução por `git log` + convenção de mensagem, ou parar de chamá-lo de "dado registrado". | B-5 | `validation-protocol.md:204-225` |
| **C-11** | 🟢 BAIXO | Declarar o que fazer com relatório e baseline em relação ao VCS antes de entrar na Fase 3. Zero ocorrências de instrução sobre isso no pacote — inalterada desde a rodada 1. | A-10a | `SKILL.md:68-73`, pré-condições |
| **C-12** | 🟢 BAIXO | Acrescentar `Manifestações por stack` a AP-16. A `Nota de procedência` (`:495-497`) declarou a lacuna sem fechá-la. | A-10b, B-7f | `antipattern-catalog.md:468-497` |
| **C-18** | 🟢 BAIXO | Resolver as menores de B-7: terminologia "read-only" (a), §5 vs §4.2 (b), campo `Smoke test` do bloco final (d), lista quebrada do slash command (e). | B-7 | `SKILL.md:76,231`, `validation-protocol.md:162`, `commands/refactor-arch.md:29-30` |
| **C-13** | 🟢 BAIXO | Replicar a skill em `ecommerce-api-legacy/` e `task-manager-api/` — fronteira de entregável, não da skill. | A-10d, B-7g | — |

**Regra de reentrada:** C-14 e C-6 são a mesma correção vista de dois lados e devem ser aplicadas
juntas — fechar só uma delas mantém o defeito de 5.3. C-15 é uma palavra. Com C-14, C-6, C-15 e
C-16 aplicadas, nenhum defeito conhecido produz artefato errado nem evidência não falsificável, e a
skill passa a rodada 3.

---

## 7. Regressão entre rodadas

Para cada bloqueador da rodada 1 — C-1 a C-4, os ALTO A-2 a A-4 e o teste de rollback. Critério
declarado: **uma correção que fechou um bloqueador e abriu outro bloqueador conta como não
fechado.** Defeito novo de severidade inferior é registrado no veredito da linha, sem rebaixá-la.

| Item da rodada 1 | Veredito | Evidência da correção | Defeito novo aberto |
|---|---|---|---|
| **C-1** 🔴 `REPORT_PATH` indefinido | ✅ **fechado** | `SKILL.md:68-73` define a precedência (argumento do invocador → default `<raiz>/reports/audit-<nome do diretório>.md`), `:74` manda imprimir os dois caminhos absolutos antes de gravar, `:142-143` repete o caminho na apresentação do gate. `commands/refactor-arch.md:30-34` interpreta argumento terminado em `.md` como `REPORT_PATH` e declara que ele vence o default. `report-template.md:3-4` deixou de hardcodar o caminho. Numeração `-1/-2/-3` não foi acoplada, como exigido. | Nenhum. |
| **C-2** 🔴 `reports/` sem âncora | ✅ **fechado** | `SKILL.md:68-69` ancora explicitamente na raiz devolvida por `git rev-parse --show-toplevel`, *"nunca no diretório de trabalho, que pode ser um subdiretório dela"*. Reforçado em `commands/refactor-arch.md:14-16,19` e `validation-protocol.md:45-46`. | Nenhum. |
| **C-3** 🔴 predicado "onda verde" | ✅ **fechado** | `validation-protocol.md:113-137` (§4.1) é a definição única e binária: `M/M` nos cinco critérios. O critério 5 passou a emitir veredito (`:104`, *"**Vermelho**, salvo se você nomear o dado de teste que o próprio smoke test alterou"*). `N < M` é vermelho sem exceção (`:124-127`). *Pré-existente quebrado* entra em `M` e conta como conforme ao reproduzir a falha (`:131-132`). Não enumerável fica fora de `M` (`:129-130`, `report-template.md:70`). Todos os demais arquivos referenciam a §4.1 em vez de reformular. | Nenhum. `validation-protocol.md:129-130` tem redação que exige duas frases para resolver (B-7c) — nit, não defeito. |
| **C-4** 🔴 baseline volátil | ✅ **fechado** | `BASELINE_PATH` resolvido nas pré-condições (`SKILL.md:72`), gravado ao fim da Fase 1 (`:92-96`), com formato por endpoint especificado (`validation-protocol.md:45-57`: método, path, status, shape). Resumo obrigatório no relatório (`report-template.md:25-28,59-72`), com `M` como denominador declarado. A dependência de sessão desapareceu: a Fase 3 lê do disco. | 🟠 **B-1** — a segunda exceção à regra de não-escrita não foi propagada a `report-template.md:6`, que ainda diz "única escrita permitida". Defeito ALTO, não bloqueador: não altera o comportamento do gate, apenas o enuncia errado. Pela regra declarada, C-4 **permanece fechado**. |
| **A-2 / C-5** 🟠 boot vermelho sem saída | ✅ **fechado** | `SKILL.md:203-207` dá a saída explícita: consultar os falsos vermelhos da §8, consertar antes do TR seguinte, e *"se **duas tentativas** não recuperarem o boot, ou se a correção exigir mudança fora do escopo daquele TR, a onda **está vermelha com a causa já isolada**: vá direto ao passo 5 nomeando esse TR"*. Proibição explícita de aplicar o próximo TR sobre boot vermelho. Espelhado no diagrama `validation-protocol.md:164-175` e em `commands/refactor-arch.md:24-25`. | Nenhum. |
| **A-3 / C-6** 🟠 regra de onda unidirecional | ❌ **não fechado** | O exemplo contraditório do template foi corrigido — `report-template.md:157-160` agora diz que AP-24 sem finding *"**não agenda TR algum**"* e coloca o controle de taxa na onda do finding que de fato aciona TR-05. **Mas a regra em si continua unidirecional nos três lugares:** `SKILL.md:179-180` (*"sobe"*), `antipattern-catalog.md:38-41` (*"antecipe"*), `refactor-playbook.md:16-18` (*"antecipe-o"*). Nenhum texto cobre o TR rotulado para onda **anterior** à do seu finding. | 🔴 **B-2**: combinada com a §4.2 nova, a lacuna deixou de ser ambiguidade e passou a produzir instrução explícita de pular a onda que contém o TR. Piorou de ALTO para BLOQUEADOR sem que uma linha de C-6 fosse tocada. |
| **A-4 / C-7** 🟠 três estados de "não encontrado" | ✅ **fechado** | Normatizados no catálogo (`antipattern-catalog.md:16-23`: não encontrado · não aplicável · não verificável, com a regra de que nenhum deles é finding nem agenda TR) e no template (`report-template.md:142-152`, uma linha por AP, estado nomeado na linha, com a exigência explícita de nunca colapsar "não verificável" em "não encontrado"). A coluna `Aplica a` foi reintroduzida e está preenchida em 28/28 (§2.4), com os mesmos valores que o design previa. `report-template.md:151` fecha o conjunto: cada um dos 28 APs está em findings ou em um dos três estados. | 🟢 **B-6**: o escopo vive só no índice, não no corpo de cada AP, enquanto a varredura é pelo corpo. Baixo, mitigação declarada. C-7 permanece fechado. |
| **Teste de rollback (§5 da rodada 1) / C-8** 🟠 SHA das ondas 2-4 | ✅ **fechado** | Registro de ondas de quatro colunas (`validation-protocol.md:204-225`), escrito *"imediatamente após o commit, colando o SHA que o `git commit` devolveu — não no fim da fase, não de memória"* (`:221-223`). Alvo resolvido para todas as ondas: *"O último commit verde é a última linha `green` deste registro, **sempre**"* (`:227-229`) e §7 (`:230-238`). A leitura perigosa de "primeiro rollback" foi eliminada: `SKILL.md:64-67` agora diz *"o baseline nunca mais volta a ser o alvo"*. Simulação 5.1 confirma que o cenário que antes dependia de `git log` resolve por leitura de tabela. | 🟡 **B-5**: o registro é mantido na resposta ao usuário, não em disco — o mesmo argumento de volatilidade que justificou C-4. Médio, recuperável por `git log`. C-8 permanece fechado. |

### Placar da regressão

| Veredito | Itens |
|---|---|
| ✅ **fechado** | C-1, C-2, C-3, C-4, C-5 (A-2), C-7 (A-4), C-8 (rollback) — **7 de 8** |
| ⚠️ parcialmente fechado | — |
| ❌ **não fechado** | C-6 (A-3) — **1 de 8**, e agravado de ALTO para BLOQUEADOR |

**Os quatro bloqueadores originais estão fechados.** Nenhum deles reabriu, e os dois que tinham
maior chance de reabrir — C-3 e C-8 — foram atacados diretamente pelas simulações 5.1 e 5.2 e
resistiram.

**Correções não-bloqueadoras da rodada 1 que seguem abertas:** C-9 (🟡, mapa de carregamento,
zero linhas tocadas), C-11 (🟢, relatório × VCS, zero ocorrências no pacote), C-12 (🟢, AP-16 sem
`Manifestações por stack`, lacuna declarada mas não fechada), C-13 (🟢, skill em 1 de 3 projetos).

**Saldo líquido da rodada de correção:** 4 bloqueadores fechados, 1 aberto; 3 ALTO fechados, 1 não
fechado e agravado; 2 defeitos ALTO novos (B-1, B-3) e 2 MÉDIO novos (B-5, e a interação registrada
em B-3), todos de propagação. A skill está substancialmente mais executável do que na rodada 1 — o
que a reprova agora é uma aresta de duas linhas, não uma lacuna de desenho.

---

**PARADO E REPORTADO.** Conforme a restrição da revisão, nenhuma correção foi aplicada nesta etapa.
Nenhum arquivo da skill foi modificado durante a auditoria.
