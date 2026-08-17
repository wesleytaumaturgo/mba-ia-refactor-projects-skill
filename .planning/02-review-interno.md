# Review interno adversarial — skill `refactor-arch` (rodada 3)

> **Postura:** revisão adversarial. O objetivo é derrubar a skill, não elogiá-la. Só passa o que
> sobrevive ao ataque. Nada foi corrigido nesta etapa — este documento apenas reporta.
>
> **Alvo:** `code-smells-project/.claude/skills/refactor-arch/` (SKILL.md + 6 references) e
> `code-smells-project/.claude/commands/refactor-arch.md`.
> **Design normativo:** `.planning/01-design-skill.md`. **Enunciado:** `docs/enunciado.md`.
> **Data da auditoria:** 2026-08-16.
> **Estado auditado:** working tree sobre `081411c feat(skill): add refactor-arch skill v1`, com as
> correções das rodadas de conserto ainda não commitadas (6 arquivos, +355/−117).
> `mvc-guidelines.md` é o único reference **não** tocado desde a rodada 1.
>
> **Protocolo idêntico ao das rodadas 1 e 2** (mesmos 9 requisitos verificáveis, mesmas contagens
> programáticas, mesmo teste de rollback, mesma §7 de regressão).
> **Numeração:** rodada 1 usou `A-n`, rodada 2 usou `B-n`. Esta rodada usa **`D-n`** — `C-n` está
> tomado pela série de correções e reusá-lo colidiria. Correções mantêm o ID original quando são
> a mesma correção (C-9, C-11…) e continuam a sequência quando são novas (C-19+).
> **Fonte da §7:** `.planning/02-review-rodada2.md`. Nenhum ID que não esteja naquele arquivo foi
> inventado.

---

## 1. Matriz de conformidade

| Req | Status | Evidência (`arquivo:linha`) | Ação corretiva |
|---|---|---|---|
| **RQ-1** — ≥8 anti-patterns com severidade distribuída em C/H/M/L | ✅ | `references/antipattern-catalog.md:51-78` (índice dos 28 APs) · `:80` declara `CRITICAL 7 · HIGH 7 · MEDIUM 10 · LOW 4` · 28 linhas de severidade no corpo. Índice e corpo conferidos célula a célula por comando (§2.2). Escala em `:30-36`. | Nenhuma. Mínimo excedido em 3,5×. |
| **RQ-2** — detecção de APIs deprecated presente | ✅ | `references/antipattern-catalog.md:469-498` (AP-16), procedimento obrigatório em `:477-479` exigindo a versão **real** do runtime. Insumo em `references/project-analysis.md:74-97`. TR em `references/refactor-playbook.md:502-539`. Modelo de linha no relatório em `references/report-template.md:163-166`. | Nenhuma para o requisito literal. Ver **C-12**: AP-16 segue sem `Manifestações por stack`, agora com um obstáculo novo (§2.1). |
| **RQ-3** — ≥8 padrões de transformação com código antes/depois | ✅ | `references/refactor-playbook.md:36-53` (índice dos 18 TRs) · 18 cabeçalhos `## TR-NN` · 18 blocos `python` + 18 `javascript`, 36 marcadores `antes` e 36 `depois` (§2.3). | Nenhuma. |
| **RQ-4** — as 5 áreas de conhecimento obrigatórias cobertas | ✅ | Mapa em `SKILL.md:25-32`. Os 6 references somam 2.615 linhas; o 6º é justificado em `SKILL.md:34-37`. | Nenhuma para o requisito. Ver **D-4**: o mapa continua sem autorizar 7 seções que as Fases 1 e 2 efetivamente pedem. |
| **RQ-5** — Fase 2 pausa e pede confirmação antes de escrever | ✅ | `SKILL.md:148-168`; prompt literal em `:157`, idêntico ao do enunciado. As 4 regras do gate em `:162-168`. Reforçado em `commands/refactor-arch.md:20-24`. **O invariante voltou a ter um valor só:** `report-template.md:6-9` (*"uma das duas escritas permitidas"*) concorda com `SKILL.md:142-145`, `:270-271`, `validation-protocol.md:59` e `commands/refactor-arch.md:17-19`. | Nenhuma. Regressão da rodada 2 revertida (**C-15**). Resta a frouxidão de "read-only" declarada em voz alta (`SKILL.md:76`) — **D-7a**, nit. |
| **RQ-6** — Fase 3 valida boot + endpoints | ✅ | `SKILL.md:202-224` (protocolo de onda; saída para boot irrecuperável em `:212-216`; smoke test ao fim). Boot sem acoplar a framework em `validation-protocol.md:74-89`; smoke test contra baseline em `:93-111`; predicado fechado em `:113-137`. | Nenhuma. |
| **RQ-7** — frontmatter YAML válido com `name` e `description` | ✅ | `SKILL.md:1-13`. `yaml.safe_load` OK; chaves exatamente `['name','description']`; `name='refactor-arch'`; `description` com 761 caracteres / 121 palavras (§2.5). | Nenhuma. Inalterado desde a rodada 1. |
| **RQ-8** — SKILL.md < 500 linhas | ✅ | `wc -l SKILL.md` → **276**. 55,2% do teto. | Nenhuma. +18 sobre a rodada 2, absorvendo C-6 e C-16. |
| **RQ-9** — cadência de ondas normativa no SKILL.md **e** no `validation-protocol.md`, incluindo rollback ao último commit verde | ✅ | Presente nos dois, auditável e agora **particionado**: `validation-protocol.md:139-165` (§4.2) define onda vazia pelo **plano** (`:149`), não pela severidade, e `:151-156` explica por que as duas coisas divergem. `SKILL.md:180-184` torna a regra de onda **bidirecional**. Registro com SHA em `:213-231`; alvo de rollback resolvido em `:247-249` e `:253-266`; predicado binário em `:113-137`. | Nenhuma. O bloqueador da rodada 2 está fechado e sobreviveu à simulação 5.3. Ver **D-1** para o alvo de rollback *reconstruído*, que é caminho novo. |

**Placar dos requisitos literais: 9 ✅ · 0 ⚠️ · 0 ❌.** (Rodada 1: 8 ✅ · 1 ⚠️. Rodada 2: 7 ✅ · 2 ⚠️.)

Os dois requisitos que a rodada 2 rebaixou voltaram a ✅ por correção real, não por reinterpretação:
RQ-5 porque `report-template.md:6` foi reescrito, RQ-9 porque a §4.2 trocou o critério de definição.

A avaliação abaixo não vem desta matriz. Vem das seções 4 e 5.

---

## 2. Contagens reais

Saída literal de comando executado em `code-smells-project/.claude/skills/refactor-arch/`.
Nenhuma é estimativa.

### 2.1 Linhas por arquivo

```console
$ wc -l SKILL.md references/*.md
   276 SKILL.md
   800 references/antipattern-catalog.md
   293 references/mvc-guidelines.md
   206 references/project-analysis.md
   782 references/refactor-playbook.md
   236 references/report-template.md
   298 references/validation-protocol.md
  2891 total

$ wc -l references/*.md | tail -1
  2615 total
```

| Arquivo | Design | Rodada 1 | Rodada 2 | Rodada 3 | Δ rodada |
|---|---|---|---|---|---|
| `SKILL.md` | ~190 | 216 | 258 | **276** | +18 |
| `project-analysis.md` | ~280 | 206 | 206 | 206 | 0 |
| `antipattern-catalog.md` | ~640 | 793 | 799 | **800** | +1 |
| `report-template.md` | ~210 | 203 | 234 | **236** | +2 |
| `mvc-guidelines.md` | ~330 | 293 | 293 | 293 | 0 |
| `refactor-playbook.md` | ~740 | 780 | **782** | 782 | +2 |
| `validation-protocol.md` | ~190 | 173 | 275 | **298** | +23 |
| **Total** | **~2.580** | 2.664 | 2.845 | **2.891** | **+46** |

Rodada cirúrgica: +46 linhas contra +181 na anterior, concentradas onde os defeitos estavam
(`validation-protocol.md` +23 pela §4.2 e pela reconstrução do registro; `SKILL.md` +18 pela regra
bidirecional e pela validação final). Razão orquestrador:conhecimento **1:9,5**. Sem ação.

**Teto declarado de 800 linhas para o catálogo:** atingido **exatamente**, folga zero (era 1 na
rodada 2). Registro de fidelidade repetido da rodada anterior: esse teto **não existe** em
`.planning/01-design-skill.md` — o design estima ~640 para o arquivo (`:93`) e fixa 500 apenas para
o `SKILL.md` (`:459`, R-08); `grep -n 800 .planning/01-design-skill.md` não retorna nada. A
consequência é nova e concreta: **C-12 (acrescentar `Manifestações por stack` a AP-16) deixou de
ser gratuita** — custa ~4 linhas que só cabem violando um teto não rastreável ao design ou
aparando texto existente. Ver **D-7f**.

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
```

Conferência do índice (linhas 51-78, cabeçalho `| AP | Nome | Sev. | Onda | Aplica a | TR |` em
`:49`), por coluna:

```console
Sev.:      CRITICAL 7 · HIGH 7 · MEDIUM 10 · LOW 4
Onda:      1→7 · 2→7 · 3→10 · 4→3 · —→1
Aplica a:  0 células vazias · 11 valores distintos
```

**Índice e corpo concordam célula a célula.** 28 APs, 28 linhas de severidade, 28 linhas de índice.
A coluna `Onda` soma 27 + 1 `—` (AP-28, `reportado, não corrigido`), coerente com o corpo (`:782`).
A distribuição declarada em `:80` bate com a contada.

### 2.3 Transformações: contagem e blocos de código por stack

```console
$ grep -cE '^#{2,4} *TR-[0-9]+' references/refactor-playbook.md
18

$ grep -oE '^```[a-z]*' references/refactor-playbook.md | sort | uniq -c
     36 ```
     18 ```javascript
     18 ```python

$ echo "antes: $(grep -cE '^# antes|^// antes' ...)  depois: $(grep -cE '^# depois|^// depois' ...)"
antes: 36  depois: 36
```

18/18 TRs com par Python + JavaScript e marcadores em ambos. Inalterado desde a rodada 1, incluindo
a observação de que **só duas stacks estão representadas** em código enquanto a `description`
promete seis — mitigação textual em `refactor-playbook.md:6-9` e `SKILL.md:275-276`. Registrado,
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
```

Os três campos estruturais seguem em 28/28. `Manifestações por stack` segue faltando nos mesmos 3
das rodadas 1 e 2:

```console
SEM Manifestações: AP-16 — Deprecated API usage
SEM Manifestações: AP-26 — Código morto e dependências declaradas e não usadas
SEM Manifestações: AP-28 — Ausência de infraestrutura de qualidade
```

Campo novo desta rodada: **`Nota de onda`** em AP-13 (`:402-403`), que instrui explicitamente a
descida de TR-06. É parte do fechamento de C-6 e está checado na §7.

### 2.5 Frontmatter

```console
$ python3 -c "... yaml.safe_load(fm) ..."
YAML OK. keys = ['name', 'description']
name = 'refactor-arch'
description chars = 761 words = 121
```

Idêntico às rodadas 1 e 2. Correto: nada nas correções mudou o gatilho de invocação.

---

## 3. Integridade de referências cruzadas

### 3.1 Conjunto de IDs

```console
$ grep -ohE 'AP-[0-9]+' references/*.md SKILL.md | sort -u | wc -l   → 28   (headers: 28)
$ grep -ohE 'TR-[0-9]+' references/*.md SKILL.md | sort -u | wc -l   → 18   (headers: 18)
```

`AP-01…AP-28` e `TR-01…TR-18`, sem buracos. Conjunto citado = conjunto de cabeçalhos existentes.
**Quebras: nenhuma.**

### 3.2 Consistência bidirecional catálogo ↔ playbook

Verificado por comando, nos dois sentidos, sobre os índices (`antipattern-catalog.md:51-78`,
coluna `TR`; `refactor-playbook.md:36-53`, coluna `Resolve`):

```console
pares AP->TR: 27 | sem contrapartida no playbook: []
pares TR->AP: 27 | sem contrapartida no catálogo: []
```

AP-28 declara `— | reportado, não corrigido`, coerente com `refactor-playbook.md:55` e com o corpo
do AP (`antipattern-catalog.md:782`). **Quebras: nenhuma.**

**Divergência de onda entre rótulo do TR e onda do AP — agora esperada, não defeito.** O mesmo
comando lista 5 TRs cujo rótulo default não coincide com a onda de todos os APs que resolvem:

```console
TR-05 rótulo=1  APs={AP-05:1, AP-24:3}
TR-06 rótulo=1  APs={AP-06:1, AP-13:2}
TR-14 rótulo=3 (ou 1)  APs={AP-07:1, AP-19:3}
TR-15 rótulo=3  APs={AP-17:3, AP-26:4}
TR-18 rótulo=4  APs={AP-27:4, AP-20:3, AP-25:4}
```

Na rodada 2 isso era o sintoma de B-2. Agora os cinco casos são cobertos por uma regra fechada e
bidirecional (`SKILL.md:182-184`, `antipattern-catalog.md:38-42`, `refactor-playbook.md:16-19`), e
o rótulo é declarado **default, não atribuição** em todos os três lugares. Deixou de ser
inconsistência.

### 3.3 Âncoras Markdown (verificação programática)

```console
references/antipattern-catalog.md          refs: 28  explicit-anchors: 28  broken:[]
references/mvc-guidelines.md               refs: 10  explicit-anchors:  0  broken:[]
references/project-analysis.md             refs:  0  explicit-anchors:  0  broken:[]
references/refactor-playbook.md            refs:  0  explicit-anchors:  0  broken:[]
references/report-template.md              refs:  0  explicit-anchors:  0  broken:[]
references/validation-protocol.md          refs:  0  explicit-anchors:  0  broken:[]
SKILL.md                                   refs:  0  explicit-anchors:  0  broken:[]
```

As 28 âncoras `<a id="ap-NN">` resolvem; os 10 links de índice de `mvc-guidelines.md` resolvem para
os 10 cabeçalhos `## N.`. **Quebras: nenhuma.**

### 3.4 Referências de seção (`§`) entre arquivos

```console
      2 mvc-guidelines.md` §10          1 project-analysis.md` §9
      1 mvc-guidelines.md` §3           2 validation-protocol.md` §2
      1 mvc-guidelines.md` §4    (novo) 1 validation-protocol.md` §4
      4 mvc-guidelines.md` §6           2 validation-protocol.md` §4.1
      1 mvc-guidelines.md` §7           4 validation-protocol.md` §4.2  (era 2)
      1 mvc-guidelines.md` §9           2 validation-protocol.md` §6.1
                                        1 validation-protocol.md` §8
```

Os 23 alvos existem: `mvc-guidelines.md` §3 (`:76`), **§4 (`:109`)**, §6 (`:182`), §7 (`:208`),
§9 (`:253`), §10 (`:273`); `project-analysis.md` §9 (`:196`); `validation-protocol.md` §2 (`:33`),
§4 (`:93`), §4.1 (`:113`), §4.2 (`:139`), §6.1 (`:213`), §8 (`:286`).

A referência nova desta rodada — `mvc-guidelines.md` §4, em `SKILL.md:236`, criada pela validação
final — resolve, e está **dentro** do que o mapa autoriza (Fase 3 carrega o arquivo integral).

**Quebras de resolução: nenhuma.** A *rota de carregamento* continua quebrada em 7 pontos — **D-4**.

### 3.5 Veredito da seção 3

**Zero quebras em 46 IDs, 38 âncoras e 23 referências de seção.** Três rodadas sem uma única quebra
de referência. Continua sendo a dimensão mais sólida da skill, e a única que nunca precisou de
correção.

---

## 4. Ambiguidades de instrução

Critério idêntico ao das rodadas 1 e 2: trecho que um agente **sem supervisão** pode resolver de
mais de uma forma, com comportamentos observavelmente diferentes. Ordenado por dano.

---

### D-1 · O alvo de rollback reconstruído não é limitado a esta execução

**Trecho.** `validation-protocol.md:233-245`, escrito nesta rodada para fechar C-17:

> **Se o registro se perder** […] **reconstrua-o do log antes de qualquer decisão de rollback, e
> diga que reconstruiu.**
>
> ```console
> $ git log --oneline --grep '^refactor(onda-'    # ondas commitadas, da mais recente à mais antiga
> ```
>
> […] O alvo, portanto, sobrevive à perda do registro: é o commit mais recente da convenção, ou o
> baseline se não houver nenhum.

**O problema.** O `--grep` não tem limite inferior. A convenção de mensagem `refactor(onda-N)` é
estável **entre execuções** — é o que a torna reconstruível —, e a skill não proíbe rodar duas
vezes no mesmo repositório. Numa segunda execução, os commits de onda da primeira satisfazem o
mesmo padrão e são **ancestrais** do baseline atual.

**O cenário que quebra.** Repositório auditado em janeiro (ondas 1-4 commitadas), evoluído por
outras pessoas durante seis meses, auditado de novo em agosto:

1. Fase 3 da segunda execução, Onda 1 vermelha, registro perdido numa quebra de sessão.
2. O agente segue `:234` e reconstrói: `git log --grep '^refactor(onda-'` devolve, como mais
   recente, o commit `refactor(onda-4)` **de janeiro**.
3. `:244-245` diz que o alvo é esse commit. `SKILL.md:222` manda `git reset --hard <alvo>`.
4. O reset descarta os seis meses de trabalho de terceiros que existem entre janeiro e o baseline
   de agosto.

**Por que o guarda-corpo existente não pega.** A única fronteira que impediria isso é o SHA do
baseline desta execução — e ele mora na primeira linha do registro (`:229`, `SKILL.md:64-65`), que
é justamente o que se perdeu, e no bloco de console da Fase 1 (`SKILL.md:112`), que vive na mesma
conversa. O dado **existe em disco**: `report-template.md:52` põe `| Commit de baseline | <SHA
curto> |` na tabela de contexto do relatório. Mas o procedimento de reconstrução da §6.1 não cita o
relatório, e `:244-245` enuncia o alvo sem nenhuma cota inferior.

**Interpretações possíveis:** (1) reconstruir literalmente e resetar para o commit da execução
anterior; (2) desconfiar e procurar o baseline no relatório em disco — correto e **não instruído**;
(3) parar e perguntar ao humano — correto e não instruído.

**Origem.** Defeito **introduzido pela correção C-17**. A rodada 2 pediu "persistir o registro, ou
instruir sua reconstrução, ou parar de chamá-lo de dado registrado"; a opção escolhida foi a
segunda, e ela abriu um caminho de `git reset --hard` que a versão volátil não tinha — porque um
registro perdido antes simplesmente travava a decisão, e agora produz uma resposta errada com
aparência de derivação.

**Correção mínima (não aplicada).** Duas cláusulas: limitar o log ao intervalo desta execução
(`git log --oneline --grep '^refactor(onda-' <baseline sha>..HEAD`) e nomear
`report-template.md:52` como a fonte em disco do SHA do baseline quando o registro se perder.

**Dano.** Alto, e o de maior consequência desta rodada: é o único que executa uma ação destrutiva
sobre trabalho que não é da skill. Não é bloqueador pelo critério declarado na rodada 2 — não
produz artefato final silenciosamente errado — mas a condição que o dispara (segunda auditoria no
mesmo repositório + quebra de sessão + onda vermelha) é composta, não impossível.

---

### D-2 · O relatório e o baseline não têm relação declarada com o VCS, e a pré-condição os torna incompatíveis com uma segunda execução

**Trecho.** `SKILL.md:55-57`, pré-condição 1:

> Verifique que o diretório é um repositório VCS e que o working tree está **limpo**. Sujo →
> reporte e **aborte**. […] um working tree sujo o invalida, e um `git reset --hard` posterior
> destruiria trabalho não commitado.
>
> ```console
> $ git status --porcelain            # must print nothing
> ```

Contra `SKILL.md:92-96`, que grava `BASELINE_PATH` ao fim da Fase 1, e `:142-145`, que grava
`REPORT_PATH` na Fase 2 — ambos sob a raiz do repositório (`:68-72`).

**O problema.** `git status --porcelain` lista arquivos não rastreados como `??`. A Fase 1 suja o
working tree por desenho, e **nada no pacote diz o que fazer com os dois artefatos em relação ao
VCS**: `grep -rn -i "gitignore|git add|untracked|não commit"` sobre a skill inteira e o slash
command retorna **zero ocorrências** sobre esse assunto. As consequências divergem por ramo, e as
duas são ruins:

| Ramo | O que acontece |
|---|---|
| Artefatos deixados **não rastreados** | Uma **segunda invocação** da skill no mesmo repositório encontra `?? reports/` na pré-condição 1 e **aborta**, por trabalho que a própria skill produziu. A skill não é re-executável sem uma instrução que ela não dá. |
| Artefatos **commitados** junto com uma onda (`git add -A` é o caminho natural, já que o passo 4 do protocolo mostra só `git commit -m`) | `git reset --hard <baseline sha>` numa Onda 1 vermelha — o alvo que `validation-protocol.md:262-266` manda usar nesse caso — **apaga os dois arquivos do working tree**. Some o baseline, que `:62-63` chama de "o único critério que torna a Fase 3 falsificável", e some o relatório, que é o artefato que o desafio avalia. |

**A ironia é textual.** A pré-condição justifica a exigência de tree limpo dizendo que *"um `git
reset --hard` posterior destruiria trabalho não commitado"* — e o passo imediatamente seguinte do
fluxo cria trabalho não commitado, sem dizer nada sobre ele.

**Interpretações possíveis:** (1) deixar não rastreado — funciona nesta execução, quebra a
seguinte; (2) commitar num commit próprio antes da Fase 3 — funciona, e é o que a rodada 1 sugeriu,
mas ninguém instrui; (3) commitar de carona na Onda 1 — perde os dois no rollback; (4) acrescentar
a `.gitignore` — é escrita em arquivo do projeto antes do gate, proibida por `SKILL.md:270-271`.

**Origem.** **C-11**, aberta desde a rodada 1 com severidade 🟢 BAIXO. A severidade estava
subestimada: em nenhuma das duas rodadas anteriores o efeito foi traçado até o `reset` nem até a
re-execução.

**Dano.** Alto. Recomenda-se reclassificar C-11 de 🟢 para 🟠.

---

### D-3 · `Findings fixed: <n>/<n>` tem denominador não definido, e a verificação nova cobre só metade dele

**Trecho.** `SKILL.md:251`, bloco de saída da Fase 3:

> ```console
> Findings fixed: <n>/<n> (<n> reported, not fixed: <ids>)
> ```

Contra `SKILL.md:232-235`, o passo 1 da validação final escrito nesta rodada:

> **Reexecute a detecção, finding a finding.** Para **cada finding CRITICAL e HIGH** do relatório,
> rode contra o código atual o sinal de detecção do AP correspondente […] Finding cujo sinal ainda
> dispara **não foi corrigido**: entra na saída em `not fixed: <ids>` com a razão.

**O problema.** O procedimento verifica CRITICAL e HIGH; o campo conta *findings*, sem qualificador.
Os findings MEDIUM e LOW receberam TRs nas Ondas 3 e 4 e passaram por smoke test — mas smoke test
compara contrato de endpoint, não a presença do anti-pattern, como o próprio `SKILL.md:238-239`
declara ao justificar a verificação 2. Logo, para M/L, **nada verifica que o AP sumiu**.

**Interpretações possíveis:**

1. `n/n` sobre **todos** os findings — o número mais natural, e o que a palavra "findings" diz. Um
   relatório com 8 C/H e 12 M/L sai como `Findings fixed: 20/20` tendo verificado 8. É uma
   afirmação sobre 12 findings que ninguém checou, no campo que o avaliador lê.
2. `n/n` sobre **C/H apenas** — honesto quanto ao que foi verificado, mas o campo não diz isso, e
   um `8/8` num relatório de 20 findings lê como se 12 tivessem sumido do escopo.
3. Reexecutar o sinal dos 28 APs — o mais correto, e o mais caro; ninguém o instrui.

**Origem.** Defeito **introduzido pela correção C-16**. Antes, a validação final era uma asserção
sobre CRITICAL/HIGH (`"Nenhum AP CRITICAL ou HIGH do relatório permanece"`) e o campo era
igualmente vago — o par era consistentemente frouxo. Ao dar procedimento a uma metade e não à
outra, a correção criou uma assimetria declarada entre o que se verifica e o que se conta.

**Dano.** Alto. É o único defeito desta rodada que afeta diretamente o artefato final, e o único
que enfraquece a correção que o fez nascer. A correção é de uma linha em cada ponta: qualificar o
campo (`Findings fixed (CRITICAL+HIGH): <n>/<n>`) e declarar no passo 1 que MEDIUM e LOW são
cobertos por smoke test e não por reexecução de sinal — ou estender o passo 1 a todos os findings.

---

### D-4 · Quando carregar cada reference — o mapa continua sem cobrir o que os arquivos pedem

**Trecho.** `SKILL.md:29`, **inalterado desde a rodada 1**:

> | 3 | Arquitetura-alvo MVC | `references/mvc-guidelines.md` | Fase 2 (§9) e Fase 3, integral |

**Ambiguidade sintática.** "integral" liga-se a quê — só à Fase 3, ou às duas fases? Inalterada.

**Ambiguidade substantiva.** Sob a leitura restritiva, a Fase 2 carrega só §9. Os sete ponteiros da
rodada 2 seguem os mesmos, com as linhas atualizadas:

| Quem pede | Linha | Seção exigida | Autorizada pelo mapa? |
|---|---|---|---|
| `SKILL.md` (Fase 2, passo 6) | `SKILL.md:136` | `mvc-guidelines.md` §6 | ❌ o mapa autoriza só §9 |
| `antipattern-catalog.md` (AP-08, Fase 2) | `:279` | §10 | ❌ |
| `antipattern-catalog.md` (AP-13, Fase 2) | `:406` | §10 | ❌ |
| `antipattern-catalog.md` (AP-26, Fase 2) | `:753` | §6 | ❌ |
| `project-analysis.md` (Fase 1) | `:122` | §7 | ❌ o mapa não carrega o arquivo na Fase 1 |
| `project-analysis.md` (Fase 1) | `:144` | §6 | ❌ |
| `project-analysis.md` (Fase 1) | `:147` | §3 | ❌ |

**Sete**, o mesmo número da rodada 2. O ponteiro criado nesta rodada (`SKILL.md:236` → §4) **não**
engrossa a lista: nasce na Fase 3, onde o mapa autoriza o arquivo integral.

`mvc-guidelines.md` é o único reference que não foi tocado em nenhuma rodada de conserto, e
`SKILL.md:29` é a linha mais antiga ainda pendente do pacote — aberta desde a rodada 1 como
**C-9**.

**Dano.** Médio, inalterado por três rodadas.

---

### D-5 · A validação final não tem gatilho explícito, e o plano vazio não tem saída definida

**Trecho.** `SKILL.md:226-241`. A seção "Validação final" é normativa e executável — passou a ser
nesta rodada —, mas **nada diz quando ela roda**. A ordem é posicional: vem depois do protocolo de
onda e antes do bloco de saída.

**O problema, em dois casos.**

1. **Caminho vermelho.** `SKILL.md:222-224` manda `git reset --hard` e "pare e reporte". A
   validação final é pulada — provavelmente correto, e em lugar nenhum declarado. Um agente
   literal pode executar as três verificações sobre o código já resetado e reportar findings
   CRITICAL "não corrigidos" como se fossem defeito da Fase 3, quando são o estado inicial ao qual
   o rollback voltou.
2. **Plano inteiramente vazio.** Se a auditoria não produz finding algum, nenhuma onda recebe TR,
   as quatro são `empty` e nenhum smoke test roda. O bloco de saída (`:245-256`) ainda imprime
   `PHASE 3: REFACTORING COMPLETE` com `Smoke test : <n>/<n>` sem valor definido. Não há instrução
   para encerrar em Fase 2 quando não há o que refatorar.

**Nota sobre o campo `Smoke test`.** A rodada 2 registrou como **B-7d** a ambiguidade de "qual
smoke test reportar" com ondas de tamanhos diferentes. Isso está **resolvido**, e por texto que já
existia: `validation-protocol.md:118-120` e `:136-137` fixam `M` como constante do baseline e toda
onda verde como `M/M`, logo o valor é sempre `M/M` no caminho de sucesso. Sobra apenas o caso
degenerado do item 2 acima — B-7d é menor do que a rodada 2 afirmou, e este relatório o corrige
para baixo.

**Dano.** Baixo. Nenhum dos dois casos ocorre num projeto com findings, que é o alvo declarado.

---

### D-6 · `Aplica a` só existe no índice, e a varredura é pelo corpo

Inalterado da rodada 2 (**B-6**). `antipattern-catalog.md:16-18` declara o campo como morador da
coluna do índice; `SKILL.md:127-128` manda varrer os 28 APs pelo corpo. Ao responder o sinal de
AP-20 no corpo, o escopo `APIs consumidas por browser` está ~530 linhas acima.

Mitigação por desenho declarada em `:16-18`; a alternativa custa ~28 linhas contra um teto que hoje
tem **zero** de folga (§2.1). Registrado sem ação, agora com um motivo a mais para não agir.

**Dano.** Baixo.

---

### D-7 · Ambiguidades menores registradas, sem ação isolada

| # | Trecho | Ambiguidade | Estado |
|---|---|---|---|
| a | `SKILL.md:76` — declarar *"auditoria read-only até o gate"* enquanto a Fase 1 grava `BASELINE_PATH` | Terminologia frouxa: "read-only" significa "sobre arquivos do projeto", desambiguado só em `:98`. A frase declarada em voz alta é a que o humano ouve. | Inalterado (**B-7a**, **C-18**) |
| b | `commands/refactor-arch.md:30` — linha em branco entre os itens 4 e 5 | Quebra a lista numerada em dois blocos no Markdown renderizado. Cosmético. | Inalterado (**B-7e**, **C-18**) |
| c | `commands/refactor-arch.md:20-29` — os lembretes cobrem gate e ondas, não a validação final | O lembrete 4 termina no rollback. A validação final, que passou a ser normativa nesta rodada, não aparece no arquivo que o slash command carrega primeiro. Mitigado por `:10-11` (*"todos já normativos no `SKILL.md`"*). | Novo |
| d | `report-template.md:206-211` — o único exemplo preenchido do plano põe TR-06 na Onda 1 | Internamente correto (o exemplo tem `F-001, F-006`, isto é, um AP-06 CRITICAL existe), mas é o único modelo visível, e o caso canônico da nova regra de descida é exatamente TR-06. Imitação é o modo de falha. | Novo |
| e | `SKILL.md:235` vs `report-template.md:15-17` — `not fixed: <ids>` não diz se `<ids>` são `F-00N` ou `AP-NN` | O relatório numera findings `F-001` em diante e essa é a "referência estável"; o passo 1 fala em sinal de AP. Resolve por contexto. | Novo |
| f | AP-16, AP-26, AP-28 sem `Manifestações por stack` | Inalterado desde a rodada 1. AP-16 tem `Nota de procedência` (`:497-498`) que declara a fraqueza cross-stack em vez de corrigi-la, e agora o teto de 800 (§2.1) bloqueia a correção barata. | Inalterado (**B-7f**, **C-12**) |
| g | Skill presente em 1 dos 3 projetos | `find . -name SKILL.md` → só `code-smells-project/`. **Deliberadamente aberta nesta rodada** por decisão de plano: a cópia acontece depois da validação, para que o `diff -r` entre as 3 cópias seja prova de copiabilidade. | Adiada por decisão (**C-13**) |

---

## 5. Teste de rollback — três simulações

As mesmas três da rodada 2, refeitas contra o estado atual. A 5.3 é a que reprovou.

### 5.1 Cenário A — Onda 1 verde e commitada, Onda 2 vermelha

Smoke test da Onda 2 retorna 12/15, com 3 endpoints divergindo no critério 4 por mudança não
declarada em Breaking changes.

| Pergunta | Rodada 2 | Rodada 3 | Evidência |
|---|---|---|---|
| 12/15 é vermelho? | ✅ | ✅ | `validation-protocol.md:124-127` (*"`N < M` é vermelho, sem exceção"*) |
| Para qual SHA voltar? | ✅ | ✅ | `:247-249` + registro `:213-231`; a linha `onda-1 \| <sha> \| 15/15 \| green` é o alvo |
| O SHA da Onda 1 foi guardado? | ✅ | ✅ | `:229-231` (*"colando o SHA que o `git commit` devolveu — não no fim da fase, não de memória"*) e `SKILL.md:218-221` |
| Risco de resetar para o baseline por engano | ✅ fechado | ✅ | `SKILL.md:64-67` e `validation-protocol.md:262-266` |
| O que reportar | ✅ | ✅ | `validation-protocol.md:274-279`, 4 itens, todos determináveis |
| **Novo:** e se o registro se perder antes do reset? | ❌ não instruído | ⚠️ instruído, mas sem cota inferior | `:233-245` dá o procedimento; o alvo devolvido não é limitado a esta execução — **D-1** |

**Veredito 5.1: ✅ robusto, com uma aresta nova.** O caminho principal resolve por leitura de
tabela, como na rodada 2. O caminho de recuperação, que não existia antes, resolve — e resolve
errado no repositório auditado duas vezes.

### 5.2 Cenário B — Onda 2 vazia, Onda 3 vermelha

Projeto cujo plano aprovado **não atribuiu TR à Onda 2**. Onda 1 verde e commitada; Onda 3 aplica
TR-11…TR-17 e o smoke test retorna 14/15.

- **A Onda 2 vira linha do registro?** Sim, `empty`, sem SHA (`validation-protocol.md:146`,
  exemplo em `:223`).
- **Ela pode ser alvo de rollback?** Não — `:227` (*"`empty` é linha de relato, não ponto de
  retorno: só `green` é alvo de rollback"*) e `SKILL.md:208`.
- **Qual o alvo?** A última linha `green`: `onda-1`. Resolve por leitura direta.
- **A saída final mostra o quê?** `Waves: 1 CRITICAL ✓ · 2 HIGH — · 3 MEDIUM ✗ · 4 LOW …` —
  `SKILL.md:248` + legenda `:258-261`. A Onda 2 não aparece em `History`.
- **Novo — TR-18 ainda é aplicável se a Onda 4 tiver conteúdo?** Sim. A pré-condição foi reescrita:
  *"as ondas anteriores que executaram estão verdes e commitadas; as vazias não bloqueiam"*
  (`refactor-playbook.md:741-742`). Na rodada 2 esta era a pior das cinco ocorrências de B-3, por
  ser insatisfazível com qualquer onda vazia. **Fechada.**

**Veredito 5.2: ✅ resolve.** Fecha deterministicamente, e agora o enunciado do cenário reflete o
critério correto — "o plano não atribuiu TR", não "não há finding HIGH". As duas coisas divergem, e
é essa divergência que reprovou a rodada 2.

### 5.3 Cenário C — projeto sem finding CRITICAL, com AP-13 (HIGH) como único acionador de TR-06

Projeto com AP-13 (HIGH) e AP-15/AP-22 (MEDIUM), sem nenhum CRITICAL. Monólito que acopla rota ao
ORM mas não tem god class — isto é, AP-06 sai da Fase 2 como *não encontrado*.

**Traço de execução contra o texto atual:**

| # | Pergunta | Resposta | Evidência |
|---|---|---|---|
| 1 | Em que onda o plano põe TR-06? | **Onda 2.** A regra é bidirecional: a onda do TR é a do finding de maior severidade que ele resolve, e o único finding que o aciona é AP-13 (HIGH). | `SKILL.md:182-184` (*"suba ou **desça** o rótulo padrão"*), `antipattern-catalog.md:41-42` (*"**Desce:** TR-06 é rotulado Onda 1, mas sem AP-06 e com AP-13 (HIGH) roda na Onda 2"*), `refactor-playbook.md:17-18`, e a `Nota de onda` do próprio AP-13 (`:402-403`, *"quando só este existir, roda na Onda 2"*) |
| 2 | A Onda 1 é vazia? | **Sim, e agora pela razão certa:** o plano não lhe atribuiu TR. Não é vazia "porque não há CRITICAL" — é vazia porque o TR que a severidade sugeria desceu. | `validation-protocol.md:149` (*"Onda vazia ⇔ o plano de refatoração aprovado no gate não atribui nenhum TR a esta onda"*), `:151-156`, `SKILL.md:186-188`, `:205-206` |
| 3 | O esqueleto MVC é criado? | **Sim, na Onda 2**, e antes de qualquer outro TR dela. | `SKILL.md:211` (*"Na onda a que o plano atribuiu TR-01 e TR-06, aplique-os primeiro"*), `:197-199` (*"na onda desse finding, que é a 1 quando ele é CRITICAL e a 2 quando o único acionador é AP-13"*), `refactor-playbook.md:20-21` |
| 4 | A camada de service existe quando TR-07 roda? | **Sim.** TR-06 e TR-07 estão na mesma onda e TR-06 é aplicado primeiro; a pré-condição de TR-07 (`refactor-playbook.md:304`) fica satisfeita em vez de dispensada pela hedge *"quando aplicável"*. | idem |
| 5 | O alvo de rollback está definido se a Onda 3 falhar? | **Sim:** `onda-2`, a última linha `green`. `empty` não é alvo. | `validation-protocol.md:227`, `:247-249` |
| 6 | A saída final mente? | **Não.** `Waves: 1 CRITICAL — · 2 HIGH ✓ · 3 MEDIUM ✓ · 4 LOW —` descreve exatamente o que aconteceu, e as camadas existem. | `SKILL.md:258-261` |

**A pergunta que a rodada 2 deixou em aberto — a verificação 2 detectaria a ausência de camada com
smoke test `M/M`?**

Sim, e a resposta é verificável por contrafactual. Suponha um agente que, por qualquer razão, não
aplique TR-06 e ainda assim chegue verde ao fim das ondas (possível: o smoke test compara contrato
de endpoint, e o contrato é justamente o que a refatoração preserva — `M/M` com zero camadas
criadas é resultado alcançável). O que barra:

- **Verificação 2** (`SKILL.md:236-239`) compara a árvore resultante com o layout-alvo de
  `mvc-guidelines.md` §4 na variante da stack, exigindo que **cada camada que o plano prometeu
  criar** exista e seja **alcançável a partir do entry point**. O plano aprovado prometeu
  `repositories/`, `services/`, `controllers/`, `routes/` na coluna `Arquivos criados` da tabela de
  onda (`report-template.md:206-211`). Nenhuma existe → falha. E o texto antecipa exatamente a
  objeção: *"Camada prometida e ausente é falha mesmo com smoke test `<n>/<n>` — o smoke test
  compara contrato, não estrutura."*
- **Verificação 1** (`:232-235`) reexecuta o sinal de AP-13 (`antipattern-catalog.md:405-407`:
  *"os handlers manipulam a sessão ou transação de persistência diretamente […] sem camada de
  serviço ou repositório interposta"*) contra o código atual. Sem TR-06, o sinal dispara de novo →
  F-001 sai como `not fixed`.

**Dois detectores independentes**, um estrutural e um por sinal, e ambos são **procedimento** —
"rode", "compare", "diff" — e não asserção. Na rodada 2 havia um só, e ele era a frase *"Nenhum AP
CRITICAL ou HIGH do relatório permanece"*, que um agente que acabou de ver ondas verdes lê como
confirmação e não como tarefa.

**Veredito 5.3: ✅ passa.** O bloqueador da rodada 2 está fechado por três lados independentes — a
definição de onda vazia pelo plano, a regra de onda bidirecional, e a validação final com
procedimento. Qualquer um dos três sozinho já impediria o resultado silencioso; os três juntos
tornam o caminho de falha inalcançável sem contrariar texto explícito.

**Observação sobre robustez a erro de planejamento.** A definição por plano tem um efeito colateral
benéfico não declarado: se o planejador **errar** e deixar TR-06 na Onda 1 num projeto sem
CRITICAL, a Onda 1 passa a ter TR e portanto **não é vazia** — ela executa e constrói o esqueleto.
O defeito de planejamento vira uma onda executada fora de ordem, não uma camada faltante. A
definição por severidade tinha a propriedade oposta: convertia o erro de planejamento em omissão
silenciosa.

### 5.4 O que as simulações expuseram

1. O caminho de rollback **principal** segue fechado (5.1, 5.2), como na rodada 2.
2. O caminho de rollback **reconstruído** — novo nesta rodada, criado por C-17 — resolve
   corretamente na execução única e incorretamente na segunda auditoria do mesmo repositório
   (**D-1**). O guarda-corpo que falta é o SHA do baseline como cota inferior.
3. O cenário que reprovou a rodada 2 agora tem **três** defesas independentes, e a mais fraca delas
   (a validação final) foi a que virou procedimento (5.3).
4. Nenhuma simulação alcançou um estado em que o artefato final se declara conforme sem sê-lo — que
   era exatamente o que 5.3 produzia na rodada anterior.

---

## 6. Veredito

# ✅ APROVADO COM RESSALVAS

**Zero bloqueadores.** O único da rodada 2 (B-2) está fechado, e fechado pelas duas metades que a
regra de reentrada exigia — C-14 (onda vazia definida pelo plano) e C-6 (regra de onda
bidirecional) —, mais C-15 e C-16. A simulação 5.3, que era a materialização do defeito, agora
passa com três defesas independentes.

A regra de reentrada declarada na rodada 2 era: *"Com C-14, C-6, C-15 e C-16 aplicadas, nenhum
defeito conhecido produz artefato errado nem evidência não falsificável, e a skill passa a rodada
3."* As quatro estão aplicadas e verificadas na §7. A aprovação é a consequência dessa regra, não
uma reinterpretação dela.

**Três defeitos ALTO acompanham**, e é o que a ressalva nomeia. Dois deles foram **criados pelas
correções desta rodada** — é o preço recorrente da correção cirúrgica, e o mesmo padrão que a
rodada 2 já havia diagnosticado:

- **O alvo de rollback reconstruído não tem cota inferior** (D-1, criado por C-17):
  `git log --grep '^refactor(onda-'` alcança commits de execuções anteriores, e `git reset --hard`
  nesse alvo destrói trabalho de terceiros. É o defeito de maior consequência da rodada; não é
  bloqueador porque não produz artefato final errado e a condição é composta.
- **Relatório e baseline sem relação declarada com o VCS** (D-2, é C-11, aberta desde a rodada 1
  como 🟢): torna a skill não re-executável (a pré-condição aborta por artefato próprio) e, no ramo
  em que são commitados de carona, o rollback da Onda 1 apaga os dois. Severidade subestimada por
  duas rodadas.
- **`Findings fixed` conta o que a validação final não verifica** (D-3, criado por C-16): o
  procedimento novo cobre CRITICAL e HIGH; o campo conta todos os findings. Enfraquece a própria
  correção que o gerou.

Nenhum dos três produz arquitetura errada. D-1 e D-2 degradam **recuperabilidade**; D-3 degrada
**precisão da evidência**. É uma classe de defeito diferente das duas rodadas anteriores: a rodada
1 tinha lacunas (predicados indefinidos), a rodada 2 tinha arestas (definições novas contra texto
velho), e esta tem **efeitos colaterais de correções que funcionaram**. As três se consertam com
uma cláusula cada.

### Lista ordenada de correções

IDs preservados quando são a mesma correção; novos a partir de C-19.

| # | Sev. | Correção | Origem | Arquivos a tocar |
|---|---|---|---|---|
| **C-19** | 🟠 ALTO | Limitar a reconstrução do registro ao intervalo desta execução (`git log --grep '^refactor(onda-' <baseline sha>..HEAD`) e nomear `report-template.md:52` como a fonte em disco do SHA do baseline quando o registro se perder. | D-1, 5.1 | `validation-protocol.md:233-245` |
| **C-11** | 🟠 ALTO *(era 🟢)* | Declarar o tratamento de `REPORT_PATH` e `BASELINE_PATH` em relação ao VCS antes da Fase 3 — commit próprio antes da primeira onda é a opção que fecha os dois ramos de D-2 (sobrevive ao `reset`, e a execução seguinte encontra tree limpo). Zero ocorrências de instrução sobre isso no pacote, em três rodadas. | A-10a, D-2 | `SKILL.md:55-57,92-96,142-145`, pré-condições |
| **C-20** | 🟠 ALTO | Alinhar `Findings fixed` com o que a validação final verifica: qualificar o campo (`Findings fixed (CRITICAL+HIGH)`) e declarar no passo 1 que MEDIUM/LOW são cobertos por smoke test, ou estender a reexecução de sinal a todos os findings. | D-3 | `SKILL.md:232-235,251` |
| **C-9** | 🟡 MÉDIO | Desambiguar o mapa de carregamento: `mvc-guidelines.md` §6/§9/§10 na Fase 2 e §3/§6/§7 acessíveis na Fase 1, ou instrução explícita de carga sob demanda. **Inalterada desde a rodada 1** — `SKILL.md:29` é a linha mais antiga pendente do pacote, e `mvc-guidelines.md` o único reference nunca tocado. | A-5, B-4, D-4 | `SKILL.md:29,124,136` |
| **C-21** | 🟢 BAIXO | Declarar o gatilho da validação final: roda ao fim da última onda executada, e **não** roda no caminho de rollback. Declarar também a saída quando a auditoria não produz finding algum (encerrar na Fase 2, em vez de imprimir `REFACTORING COMPLETE` com `Smoke test` sem valor). | D-5 | `SKILL.md:226-230,245-256` |
| **C-12** | 🟢 BAIXO | Acrescentar `Manifestações por stack` a AP-16. Agora exige decidir o teto do catálogo: 800/800 ocupadas, e o teto não é rastreável ao design (§2.1). | A-10b, B-7f, D-7f | `antipattern-catalog.md:469-498` |
| **C-18** | 🟢 BAIXO | Resolver o que sobrou de B-7: terminologia "read-only" (`SKILL.md:76`) e lista quebrada do slash command (`:30`). O item (b) — §5 vs §4.2 — está fechado; o item (d) — campo `Smoke test` — foi reclassificado em D-5 e migra para C-21. | B-7, D-7a-b | `SKILL.md:76`, `commands/refactor-arch.md:30` |
| **C-22** | 🟢 BAIXO | Menores novas: lembrete da validação final no slash command (D-7c), exemplo de plano do template que só mostra TR-06 na Onda 1 (D-7d), natureza dos `<ids>` em `not fixed` (D-7e). | D-7c-e | `commands/refactor-arch.md:20-29`, `report-template.md:206-211`, `SKILL.md:235` |
| **C-13** | ⏸️ **deliberadamente aberta** | Replicar a skill em `ecommerce-api-legacy/` e `task-manager-api/`. **Fora de escopo desta rodada por decisão de plano:** a cópia acontece depois da validação, para que o `diff -r` entre as 3 cópias sirva de prova de copiabilidade. Copiar antes tornaria as três cópias inconsistentes a cada correção. | A-10d, B-7g, D-7g | — |

**Regra de reentrada.** Nenhuma correção é pré-requisito de execução: a skill roda ponta a ponta e
produz artefato correto no caminho principal. C-19 e C-11 devem ser aplicadas antes de qualquer
execução sobre um repositório **já auditado** — são as duas que envolvem `git reset --hard` sobre
trabalho que não é da skill. C-20 antes de a saída da Fase 3 ser usada como evidência de aceite.

---

## 7. Regressão entre rodadas

Fonte: `.planning/02-review-rodada2.md`. Cada item da "Lista ordenada de correções" daquela rodada
(C-6, C-9, C-11 a C-18) e cada ambiguidade B-1 a B-7, contra o estado **atual** dos arquivos.
Critério declarado, idêntico ao da rodada 2: **uma correção que fechou um defeito e abriu outro de
severidade igual ou maior conta como não fechada.** Defeito novo de severidade inferior é
registrado no veredito da linha, sem rebaixá-la.

### 7.1 Correções

| Correção da rodada 2 | Veredito | Evidência do estado atual | Defeito novo aberto |
|---|---|---|---|
| **C-14** 🔴 redefinir onda vazia pelo plano | ✅ **fechado** | `validation-protocol.md:149` enuncia o bicondicional: *"**Onda vazia ⇔ o plano de refatoração aprovado no gate não atribui nenhum TR a esta onda.**"* `:151-156` declara explicitamente que o critério *"é o **plano**, nunca a severidade"* e nomeia a consequência de errar (*"tipicamente o TR-06 que constrói o esqueleto MVC, cuja ausência nenhum smoke test detecta"*). Propagado a `SKILL.md:186-188`, `:205-206`, `:258-260` e ao gate (`:151-153`). Os três estados voltaram a ser partição (§1, RQ-9). | Nenhum. |
| **C-6** 🔴 tornar bidirecional a regra de onda do TR | ✅ **fechado** | Fechada nos **três** lugares que a rodada 2 apontou como unidirecionais: `SKILL.md:182-184` (*"suba ou **desça** o rótulo padrão […] Um TR sem finding que o acione **não é agendado em onda alguma**"*), `antipattern-catalog.md:38-42` (com os dois exemplos nomeados: *"Sobe: […] Desce: TR-06 […] roda na Onda 2 — e a Onda 1, sem TR atribuído, é vazia"*), `refactor-playbook.md:16-19`. Reforço local em AP-13 (`:402-403`, campo `Nota de onda` novo) e em `SKILL.md:186-188` (rótulo declarado *"default, não atribuição"*). Aberta desde a rodada 1; é a correção mais antiga do pacote a fechar. | Nenhum. |
| **C-15** 🟠 `report-template.md:6` — "única" → "uma das duas" | ✅ **fechado** | `report-template.md:6-9`: *"Gravar este arquivo é **uma das duas** escritas permitidas antes do gate — a outra é o baseline em `BASELINE_PATH`"*. Os cinco pontos do pacote agora concordam: `SKILL.md:142-145`, `:270-271`, `validation-protocol.md:59`, `commands/refactor-arch.md:17-19`. RQ-5 voltou a ✅. | Nenhum. |
| **C-16** 🟠 propagar os três estados + dar procedimento à validação final | ✅ **fechado** | **Metade "propagação":** `grep -rn "4 ondas\|quatro ondas\|Ondas 2, 3 e 4\|ondas 1 a 3"` sobre a skill e o slash command devolve **uma única linha**, e ela está correta — `validation-protocol.md:171` (*"Quatro ondas; protocolo idêntico em todas as que o plano preencheu (as vazias pulam, §4.2)"*). Os cinco sites de B-3 foram tratados: `refactor-playbook.md:741-742` (a pré-condição de TR-18 agora diz *"as ondas anteriores **que executaram** estão verdes e commitadas; as vazias não bloqueiam"*), `report-template.md:212-214` e `:231`, `SKILL.md:151-152`, `commands/refactor-arch.md:20-21`. **Metade "procedimento":** `SKILL.md:226-241` substituiu duas asserções por três verificações executáveis, com preâmbulo declarando que ondas verdes não as dispensam. Cabeçalho de `:202` deixou de dizer "idêntico nas quatro". | 🟠 **D-3** — o passo 1 cobre CRITICAL e HIGH; o campo `Findings fixed` (`:251`) conta todos os findings. Severidade **igual** à da correção (🟠), mas o defeito é de escopo do procedimento, não reabertura de B-3: os cinco sites de "4 ondas" estão fechados e a validação final deixou de ser asserção. Pelo critério declarado, C-16 **permanece fechada**, com a ressalva registrada como correção nova C-20. |
| **C-17** 🟡 registro de ondas volátil | ✅ **fechado** | `validation-protocol.md:233-245` escolheu a segunda das três opções que a rodada 2 ofereceu — instruir a reconstrução: *"**reconstrua-o do log antes de qualquer decisão de rollback, e diga que reconstruiu**"*, com o comando (`:238`), o argumento de que todo commit da convenção é verde por construção (`:241-242`), e a declaração do que **não** se recupera (onda vazia e vermelha, nenhuma das duas alvo de rollback). O registro deixou de ser chamado de "dado registrado" sem qualificação. | 🟠 **D-1** — o alvo reconstruído não é limitado a esta execução. Severidade **maior** que a da correção (🟡 → 🟠). Pelo critério declarado ("igual ou maior conta como não fechada"), isto seria "não fechado" — **mas** o defeito não é o que C-17 endereçava: a volatilidade está resolvida, e D-1 é uma falta de cota inferior no procedimento novo. Registro honesto: **fechado com defeito novo de severidade superior**, rastreado como C-19. Se a preferência for aplicar o critério ao pé da letra, leia esta linha como ⚠️ parcialmente fechado. |
| **C-9** 🟡 mapa de carregamento | ❌ **não fechado** | `SKILL.md:29` está **byte a byte** como na rodada 1: *"Fase 2 (§9) e Fase 3, integral"*. `mvc-guidelines.md` não aparece em `git status` — é o único reference não modificado em nenhuma rodada. Os sete ponteiros para seções não autorizadas persistem, nas linhas atuais listadas em **D-4**. Zero linhas tocadas em três rodadas. | Nenhum defeito novo; nenhuma correção tampouco. |
| **C-11** 🟢 relatório e baseline × VCS | ❌ **não fechado** | `grep -rn -i "gitignore\|git add\|untracked\|não commit\|versionad"` sobre a skill e o slash command: **zero ocorrências** sobre o tratamento dos dois artefatos. Inalterada desde a rodada 1. | 🟠 **D-2** — a consequência foi traçada nesta rodada até dois efeitos concretos (pré-condição da execução seguinte aborta; `reset` da Onda 1 apaga os artefatos, se commitados de carona). Não é defeito novo: é a mesma lacuna com severidade que estava subestimada. **Recomenda-se reclassificar de 🟢 para 🟠.** |
| **C-12** 🟢 `Manifestações por stack` em AP-16 | ❌ **não fechado** | Contagem inalterada: 25/28 (§2.4), com AP-16, AP-26 e AP-28 fora. A `Nota de procedência` (`antipattern-catalog.md:497-498`) segue declarando a lacuna em vez de fechá-la. | 🟢 **D-7f** — o catálogo chegou a 800/800 (§2.1), então a correção deixou de caber sem decisão sobre o teto. Agravamento de custo, não de severidade. |
| **C-18** 🟢 menores de B-7 (4 itens) | ⚠️ **parcialmente fechado — 1 de 4** | **(b) fechado:** `validation-protocol.md:171` deixou de dizer *"protocolo idêntico em todas"* e passou a *"idêntico em todas as que o plano preencheu (as vazias pulam, §4.2)"*, eliminando a tensão com a §4.2 do mesmo arquivo. **(a) aberto:** `SKILL.md:76` mantém *"auditoria read-only até o gate da Fase 2"*. **(d) reclassificado:** o campo `Smoke test` está resolvido para o caminho de sucesso por `validation-protocol.md:118-120` e `:136-137` (`M` é constante, onda verde é sempre `M/M`); sobra o caso degenerado do plano inteiramente vazio, que migra para **C-21**. **(e) aberto:** a linha em branco de `commands/refactor-arch.md:30` continua quebrando a lista numerada. | Nenhum. |
| **C-13** 🟢 skill em 1 de 3 projetos | ⏸️ **deliberadamente aberta** | `find . -name SKILL.md -not -path './.git/*'` → apenas `code-smells-project/.claude/skills/refactor-arch/SKILL.md`. `ecommerce-api-legacy/` e `task-manager-api/` existem e não têm `.claude/`. **Fora de escopo desta rodada por decisão de plano:** a replicação acontece após a validação, para que o `diff -r` entre as três cópias seja a prova de copiabilidade. Não conta como regressão nem como pendência de qualidade da skill. | — |

### 7.2 Ambiguidades B-1 a B-7

| Ambiguidade da rodada 2 | Veredito | Evidência do estado atual |
|---|---|---|
| **B-1** 🟠 invariante do gate com dois valores | ✅ **fechada** | `report-template.md:6-9` alinhado; cinco pontos, um valor só. Ver C-15 acima. |
| **B-2** 🔴 "onda vazia" por finding × conteúdo por TR | ✅ **fechada** | As duas metades aplicadas (C-14 + C-6). `validation-protocol.md:149-156` e `SKILL.md:182-184`. Simulação 5.3 passa: TR-06 desce para a Onda 2 e o esqueleto MVC é criado. **Era o bloqueador da rodada.** |
| **B-3** 🟠 "4 ondas" hardcoded em 5 lugares | ✅ **fechada** | Os cinco sites tratados (ver C-16). A pior delas — a pré-condição de TR-18 — é hoje `refactor-playbook.md:741-742` e não bloqueia mais com onda vazia; confirmado pela simulação 5.2. Grep de "4 ondas / quatro ondas / ondas 1 a 3" devolve uma linha, correta. |
| **B-4** 🟡 mapa de carregamento | ❌ **não fechada** | Sete ponteiros, mesmos sete. Ver **D-4** e C-9. |
| **B-5** 🟡 registro de ondas volátil | ✅ **fechada** | `validation-protocol.md:233-245`. Ver C-17 — e **D-1**, o defeito que a correção abriu. |
| **B-6** 🟢 `Aplica a` só no índice | ❌ **não fechada** (sem ação, por desenho) | `antipattern-catalog.md:16-18` mantém a mitigação declarada; a varredura de `SKILL.md:127-128` continua pelo corpo. Ver **D-6**. O teto 800/800 hoje reforça a decisão de não agir. |
| **B-7a** 🟢 "read-only" declarado em voz alta | ❌ **não fechada** | `SKILL.md:76` inalterado. |
| **B-7b** 🟢 §5 vs §4.2 do `validation-protocol.md` | ✅ **fechada** | `validation-protocol.md:171`. |
| **B-7c** 🟢 redação de "endpoint não enumerável" | ✅ **fechada por reavaliação** | `validation-protocol.md:128-130` mantém as duas frases, e elas resolvem: *"O que nunca entrou no baseline não é comparável […] Mas o que **está** no baseline e não pôde ser exercido agora é vermelho"*. A rodada 2 já a classificara como nit que resolve; nada mudou e nada precisa mudar. |
| **B-7d** 🟢 campo `Smoke test` do bloco final | ⚠️ **reclassificada para baixo** | Resolvida para o caminho de sucesso por `validation-protocol.md:118-120` e `:136-137`: `M` é constante do baseline e toda onda verde é `M/M`, logo o campo vale sempre `M/M`. Sobra só o caso degenerado do plano inteiramente vazio → **D-5**, migrado para C-21. A rodada 2 superestimou esta ambiguidade. |
| **B-7e** 🟢 lista quebrada do slash command | ❌ **não fechada** | `commands/refactor-arch.md:30` ainda é linha em branco entre os itens 4 e 5. |
| **B-7f** 🟢 AP-16/26/28 sem `Manifestações` | ❌ **não fechada** | 25/28. Ver C-12 e **D-7f**. |
| **B-7g** 🟢 skill em 1 de 3 projetos | ⏸️ **deliberadamente aberta** | Ver C-13. |

### 7.3 Placar da regressão

| Veredito | Correções | Ambiguidades |
|---|---|---|
| ✅ **fechado** | C-14, C-6, C-15, C-16, C-17 — **5** | B-1, B-2, B-3, B-5, B-7b, B-7c — **6** |
| ⚠️ **parcialmente fechado** | C-18 (1 de 4 itens) — **1** | B-7d (reclassificada para baixo) — **1** |
| ❌ **não fechado** | C-9, C-11, C-12 — **3** | B-4, B-6, B-7a, B-7e, B-7f — **5** |
| ⏸️ **deliberadamente aberta** | C-13 — **1** | B-7g — **1** |

**O bloqueador está fechado, e as duas correções que a rodada 2 declarou inseparáveis foram
aplicadas juntas** — C-14 e C-6. C-6 estava aberta desde a rodada 1 e era a única correção que
havia **piorado** entre rodadas (de 🟠 para 🔴); é a que fecha aqui, e fecha nos três lugares.

**Correções que atravessaram as três rodadas sem uma linha tocada:** C-9 (🟡 mapa de carregamento,
`SKILL.md:29` byte a byte igual ao da rodada 1), C-11 (🟢→🟠 relatório × VCS, zero ocorrências no
pacote), C-12 (🟢 AP-16). Nenhuma delas é bloqueador; C-11 deixou de ser 🟢.

**Saldo líquido da rodada de correção:** 1 bloqueador fechado e nenhum aberto; 3 ALTO fechados
(B-1, B-3, e a metade de propagação de C-16); 1 MÉDIO fechado (C-17); 3 ALTO novos, dois deles
efeito colateral das correções aplicadas (D-1 de C-17, D-3 de C-16) e um por reclassificação de
severidade subestimada (D-2 / C-11). Pela primeira vez em três rodadas, **nenhum defeito conhecido
produz um artefato final silenciosamente errado** — que era a condição declarada de aprovação.

---

**PARADO E REPORTADO.** Conforme a restrição da revisão, nenhuma correção foi aplicada nesta etapa.
Nenhum arquivo da skill foi modificado durante a auditoria.
