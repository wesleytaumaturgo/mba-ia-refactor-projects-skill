---
name: refactor-arch
description: >-
  Audita e refatora uma codebase inteira para o padrão MVC em três fases sequenciais:
  detecção de stack e arquitetura atual, relatório de auditoria de anti-patterns com
  severidade e arquivo:linha, e refatoração validada por boot e smoke test dos endpoints.
  Use quando o usuário pedir para auditar arquitetura, encontrar anti-patterns ou code
  smells, avaliar dívida técnica, separar camadas, reestruturar ou migrar um projeto para
  MVC, ou quando invocar /refactor-arch. Agnóstica de linguagem e framework — aplica-se a
  Python, JavaScript/TypeScript, Java, PHP, Ruby, Go e outros, tanto em monolitos de
  arquivo único quanto em projetos que já têm alguma separação de camadas. Não use para
  revisão de um único arquivo ou de um diff — o alvo é o projeto como um todo.
---

# refactor-arch

Este arquivo **orquestra**; não ensina. Todo conhecimento de domínio vive em `references/`.
Carregue cada referência no momento indicado — carregar tudo de uma vez consome o contexto de
que a refatoração precisa depois.

## Mapa de conhecimento

As cinco áreas de conhecimento exigidas, e o arquivo que cobre cada uma:

| # | Área de conhecimento | Arquivo | Quando carregar |
|---|---|---|---|
| 1 | Análise e detecção de projeto | `references/project-analysis.md` | Início da Fase 1, integral |
| 2 | Catálogo de anti-patterns (28) | `references/antipattern-catalog.md` | Início da Fase 2, integral |
| 3 | Arquitetura-alvo MVC | `references/mvc-guidelines.md` | Fase 2 (§9) e Fase 3, integral |
| 4 | Playbook de refatoração (18 TRs) | `references/refactor-playbook.md` | Fase 3, **só os TRs acionados** |
| 5 | Formato do relatório | `references/report-template.md` | Ao redigir, fim da Fase 2 |
| **+1** | **Protocolo de validação** | `references/validation-protocol.md` | Pré-condições (§6.1), fim da Fase 1 e fim de **cada onda** |

O sexto arquivo é deliberado, não desvio: validação é conhecimento — como saber que um servidor
subiu sem saber qual é o framework? — e não orquestração. Mantê-lo aqui dentro empurraria este
arquivo para além do que um orquestrador legível suporta; mantê-lo no playbook obrigaria a
carregar o arquivo mais caro do conjunto já na Fase 1, só para capturar o baseline.

## Escopo

**Dentro:** detecção de stack e arquitetura efetiva, auditoria contra o catálogo com severidade
e `arquivo:linha`, relatório e baseline gravados sob a raiz do repositório, reestruturação para
MVC, validação por boot e smoke test contra baseline.

**Fora:** arquitetura que não seja MVC, troca de framework/ORM/banco/runtime, alteração de path
ou verbo de endpoint, escrita da suíte de testes do projeto, decisões de produto (política de
senha, retenção de PII), deploy e CI, e qualquer execução sobre working tree sujo.

---

## Pré-condições

Antes da Fase 1, sem exceção:

1. Verifique que o diretório é um repositório VCS e que o working tree está **limpo**.
   Sujo → reporte e **aborte**. O commit atual é o ponto de retorno do rollback; um working
   tree sujo o invalida, e um `git reset --hard` posterior destruiria trabalho não commitado.

   ```console
   $ git rev-parse --show-toplevel     # repository root: the anchor for every artifact
   $ git status --porcelain            # must print nothing
   ```

2. Registre o **SHA do commit de baseline** como a primeira linha do registro de ondas
   (`validation-protocol.md` §6.1). Ele é o alvo do rollback **enquanto nenhuma onda tiver sido
   commitada**; a partir do primeiro commit de onda o alvo passa a ser o último commit verde, e
   o baseline nunca mais volta a ser o alvo.
3. **Resolva os caminhos dos dois artefatos** que esta execução grava, ancorados na raiz devolvida
   pelo comando acima — nunca no diretório de trabalho, que pode ser um subdiretório dela:
   - `REPORT_PATH` — o caminho que o invocador passou como argumento, se passou; caso contrário
     `<raiz>/reports/audit-<nome do diretório do projeto>.md`.
   - `BASELINE_PATH` — `<raiz>/reports/baseline-<nome do diretório do projeto>.json`.

   Imprima os dois caminhos absolutos antes de gravar qualquer um deles. A skill não infere
   numeração nem convenção de nome de nenhum repositório: quem quer outro nome o passa.
4. Declare em voz alta: *"auditoria read-only até o gate da Fase 2"*.

---

## Fase 1 — Análise (read-only)

Carregue `references/project-analysis.md` e `references/validation-protocol.md`.

Determine os oito fatos da §0 daquele arquivo: linguagem, framework efetivo, **versão real do
runtime obtida executando-o** (não a do manifesto), persistência, domínio, arquitetura efetiva
pelo grafo de resolução, inventário de endpoints e baseline de comportamento.

Duas armadilhas que custam a fase inteira se ignoradas: dependência declarada e não resolvida
**não** é a stack (é candidata a AP-26); e a arquitetura efetiva é o **grafo de resolução de
símbolos**, não a árvore de diretórios — e também não o grafo de imports, que é apenas um dos
mecanismos de resolução. Determine qual mecanismo a stack usa (import explícito, autoload por
convenção, varredura de pacote, registro em container) **antes** de concluir o que é alcançável:
onde a stack resolve por convenção, a árvore que ela varre é a evidência, e tratá-la como morta
por ausência de import é o erro mais caro desta fase (`project-analysis.md` §6).

Capture o baseline por último, com o código ainda intocado, e **grave-o em `BASELINE_PATH`**
(`validation-protocol.md` §2). O baseline persistido é a segunda e última exceção à regra de
não-escrita, pela mesma razão do relatório: artefato novo e aditivo, nenhum arquivo do projeto
tocado. Sem ele em disco, uma sessão interrompida no gate leva junto o contrato que a Fase 3
promete preservar — e o gate é justamente o ponto do fluxo desenhado para pausar.

**Nenhuma escrita em arquivo do projeto nesta fase**; só `BASELINE_PATH`. Emita no console:

```console
PHASE 1: PROJECT ANALYSIS
─────────────────────────────────────────────
Language      : <lang> (runtime in use: <version>)
Framework     : <framework> <version>
Package mgr   : <manifest file>
Database      : <engine> · <n> tables
Domain        : <one line>
Entry points  : <file, or list when the stack has more than one>
Resolution    : <explicit import | convention autoload | package scan | container registry>
Architecture  : <effective, from the resolution graph>
Source files  : <n> files · <n> LOC
Endpoints     : <n> mapped · baseline captured (<n> responses)
Baseline SHA  : <short sha>
Baseline file : <BASELINE_PATH, absolute>
─────────────────────────────────────────────
```

Se um fato não se determinar, diga qual e qual a consequência. Runtime indisponível torna AP-16
**não verificável** — o que é diferente de ausente, e precisa aparecer assim no relatório.

---

## Fase 2 — Auditoria (read-only)

Carregue `references/antipattern-catalog.md` integralmente. Consulte `mvc-guidelines.md` §9 ao
julgar os APs de camada (AP-06, AP-08, AP-13, AP-17).

1. **Varra os 28 APs na ordem do catálogo.** Responda o sinal de detecção de cada um. Pular
   entradas enviesa o relatório para o que é fácil de ver.
2. **Colete evidência literal** para cada "sim": `arquivo:linha` + o bloco de código real.
   Sem isso, **descarte o finding** — não o reporte com ressalva.
3. **Aplique o contra-exemplo** de cada AP antes de escrever a entrada.
4. **Classifique a severidade** pela escala do catálogo; justifique qualquer desvio.
5. **Registre o que NÃO foi encontrado** nas categorias verificadas. É o que torna a auditoria
   falsificável e distingue este relatório de um preenchimento de cota.
6. **Registre como finding o conteúdo de qualquer camada inalcançável** pelo mecanismo de
   resolução da stack **antes** de propô-la para remoção (`mvc-guidelines.md` §6). Nada some sem
   constar do relatório — inclusive segredos versionados dentro de código morto.
7. **Ordene** CRITICAL → HIGH → MEDIUM → LOW e redija conforme `references/report-template.md`.
8. **Redija a seção Breaking changes:** toda mudança de **forma ou media type** de resposta que a
   refatoração vai provocar, com endpoint, campo e motivo. Preveja o efeito de cada TR **antes** de executá-lo;
   é isso que transforma o gate numa decisão informada.
9. **Grave o relatório em `REPORT_PATH`**, resolvido nas pré-condições, e repita o caminho
   absoluto na apresentação do gate. Com `BASELINE_PATH`, são as duas únicas escritas permitidas
   antes do gate: ambas são artefato novo e aditivo, e o trabalho da fase precisa sobreviver a
   um "n".
10. **Monte o plano de refatoração agrupado por onda:** finding → TR → onda → arquivos afetados.

### ★ Gate humano — última instrução da Fase 2

Nenhum arquivo de código, manifesto, configuração ou diretório do projeto é criado, movido ou
alterado antes da resposta. Apresente: findings por severidade, o plano por onda — nomeando as
ondas vazias como vazias, porque é o plano que as define (`validation-protocol.md` §4.2) — com os
arquivos que serão criados/movidos/removidos, a seção Breaking changes e os itens
NEEDS-DECISION. Depois pergunte, literalmente:

```console
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Então **pare e aguarde**. As quatro regras:

- **Silêncio não é "y".** Aguarde resposta explícita do humano. Não infira aprovação de
  qualquer outra coisa que o usuário diga; se a mensagem seguinte não for uma resposta ao gate,
  responda-a e reapresente o prompt.
- **"n"** → encerre relatando o caminho do relatório. Nada é modificado.
- **"y"** → prossiga com o plano **apresentado**, não com um plano revisado no caminho.
- **Resposta parcial** ("só os CRITICAL", "não mexe em X") → replaneje e **reapresente o gate**.
  Um gate parcialmente aprovado é um gate novo.

---

## Fase 3 — Refatoração (escrita)

Carregue `references/mvc-guidelines.md` integralmente, `references/validation-protocol.md`, e do
`references/refactor-playbook.md` **apenas o índice e as seções dos TRs que a auditoria
acionou**.

### Ondas

Ordem fixa, por severidade. A onda é propriedade do **finding**, não do TR:

> **A onda de um TR é a onda do finding de maior severidade que ele resolve** — suba ou desça o
> rótulo padrão conforme necessário. **Um TR sem finding que o acione não é agendado em onda
> alguma.**

**O rótulo de onda de cada TR no playbook é o teto**: a onda do AP mais severo que aquele TR
resolve, e portanto a **mais cedo** que ele pode rodar. O ajuste normal é para **mais tarde**,
quando o AP que fixou o teto não virou finding. Só se sobe acima do teto quando um finding recebe
severidade maior que a tabelada — e esse desvio já vem justificado no próprio finding
(`antipattern-catalog.md`, escala de severidade).

A coluna `Teto` abaixo é **rótulo default, não atribuição**. A atribuição efetiva é a do plano
aprovado no gate, e é ela que define quais ondas têm conteúdo e quais são vazias
(`validation-protocol.md` §4.2).

| Onda | Severidade | Teto — TRs que podem começar aqui |
|---|---|---|
| 1 | CRITICAL | TR-01…TR-06, TR-14 — o esqueleto MVC nasce de TR-06, na onda que o plano lhe der |
| 2 | HIGH | TR-07…TR-10, TR-16 |
| 3 | MEDIUM | TR-11, TR-12, TR-13, TR-15, TR-17, TR-18 |
| 4 | LOW | nenhum por teto — todo TR que resolve um AP LOW também resolve um mais severo. A Onda 4 recebe TR **por descida**, quando só o AP LOW virou finding |

Não há onda 0: extrair configuração (TR-01) e decompor a god class (TR-06) produzem a estrutura ao
resolver o finding que os aciona — na onda desse finding, que é a 1 quando ele é CRITICAL e a 2
quando o único acionador é AP-13. Um esqueleto de diretórios vazios não é falsificável por smoke
test e não merece um commit próprio.

### Protocolo de onda — idêntico em toda onda que o plano preencheu

**Antes de tudo, os três estados** (`validation-protocol.md` §4.2): **verde** `✓` — executou e o
smoke test conformou; **vazia** `—` — o plano aprovado não atribuiu TR algum a esta onda, nada é
aplicado e nada é validado; **vermelha** `✗` — executou e falhou. Onda vazia pula os cinco passos abaixo:
sem TR, sem boot, sem smoke test, **sem commit**. Registre-a como `empty` e siga para a próxima.
Vazia **não é** verde — não entra no registro como linha verde nem serve de alvo de rollback.

1. Aplique os TRs da onda. **Boot após cada TR** — barato, e localiza a quebra no TR em vez de
   na onda inteira. Na onda a que o plano atribuiu TR-01 e TR-06, aplique-os primeiro.
2. **Boot vermelho depois de um TR:** consulte os falsos vermelhos (`validation-protocol.md` §8)
   e conserte antes do TR seguinte. Se **duas tentativas** não recuperarem o boot, ou se a
   correção exigir mudança fora do escopo daquele TR, a onda **está vermelha com a causa já
   isolada**: vá direto ao passo 5 nomeando esse TR. Nunca aplique o próximo TR sobre um boot
   vermelho — é o que transforma um conserto em investigação.
3. Ao fim da onda: **smoke test completo** contra o baseline (`validation-protocol.md` §4).
4. **Verde** — no sentido fechado da definição única em `validation-protocol.md` §4.1 → commit
   `refactor(onda-N): <severidade>`, com a **contagem de endpoints verificados na mensagem**, e
   anote o SHA devolvido no registro de ondas (`validation-protocol.md` §6.1). Sem esse número
   não há commit: é o que distingue uma onda validada de uma onda declarada validada.
5. **Vermelho** → `git reset --hard <SHA da última linha verde do registro>`, depois **pare e
   reporte**. O alvo é o último commit verde, não o baseline — os dois só coincidem quando é a
   Onda 1 que falha. Não tente a onda seguinte sobre uma base não validada.

### Validação final

Herdada das ondas que executaram e ficaram verdes, mais três verificações que **você executa
agora** — ondas verdes não as dispensam, porque nenhuma delas foi testada por onda alguma.
Nenhuma é opcional: são o que distingue "declarou conforme" de "verificou".

1. **Reexecute a detecção, finding a finding.** Para cada finding CRITICAL e HIGH do relatório,
   rode contra o código atual o sinal de detecção do AP correspondente
   (`antipattern-catalog.md`) e registre o resultado. Finding cujo sinal ainda dispara **não
   foi corrigido**: entra na saída em `not fixed: <ids>` com a razão.
2. **Compare o resultado com o alvo, responsabilidade a responsabilidade** — as
   responsabilidades em `mvc-guidelines.md` §2, a materialização na convenção adotada em
   `mvc-guidelines.md` §4. Cada responsabilidade que o plano
   prometeu materializar tem **um** lugar identificável no código atual, e esse lugar é
   **alcançável pelo mecanismo de resolução da stack** (§6). O que se verifica é a
   responsabilidade, não a existência de um diretório com nome específico: numa stack cuja
   convenção o plano adotou, o lugar certo é o que a convenção indica (`mvc-guidelines.md` §1,
   regra 4). Responsabilidade prometida e sem lugar — ou espalhada por vários — é falha mesmo
   com smoke test `<n>/<n>`: o smoke test compara contrato, não estrutura.
3. **Diff a forma e o media type observados contra a seção Breaking changes aprovada no gate.**
   Divergência não declarada é **regressão**, não melhoria — mesmo que o resultado pareça melhor.

### Saída

```console
PHASE 3: REFACTORING COMPLETE
─────────────────────────────────────────────
Waves         : 1 CRITICAL <✓|—|✗> · 2 HIGH <✓|—|✗> · 3 MEDIUM <✓|—|✗> · 4 LOW <✓|—|✗>
Smoke test    : <n>/<n> endpoints conform to baseline
Breaking chg  : <n> applied, all declared in the approved report
Findings fixed: <n>/<n> (<n> reported, not fixed: <ids>)
History       : <baseline sha> → <one entry per committed wave>
─────────────────────────────────────────────
New structure:
<árvore de diretórios resultante>
```

Marcadores da linha `Waves` (`validation-protocol.md` §4.2): `✓` verde — executou e o smoke test
conformou · `—` vazia — o plano não lhe atribuiu TR, nada aplicado e nada validado · `✗`
vermelha. Marcar `✓` uma onda vazia declara validado o que nunca executou. `History` lista
commits: onda vazia não aparece nela.

Falha em qualquer onda → **não declare sucesso parcial como sucesso**. Reporte a onda que
quebrou, o TR suspeito, a evidência, e o commit verde para onde o repositório voltou.

---

## Regras invioláveis

- Nenhuma escrita em arquivo do projeto antes do `y`. `BASELINE_PATH` e `REPORT_PATH` são as
  duas exceções, e são artefato, não código.
- Sem `arquivo:linha` + código literal, o finding não existe.
- Path, verbo e status code de sucesso são preservados. Mudança de forma ou de media type só a
  declarada.
- Commit é consequência de smoke test verde, com a contagem na mensagem.
- Os exemplos das referências ilustram a **forma**. Escreva no idioma da stack detectada na
  Fase 1, nunca copiando a sintaxe de outra.
