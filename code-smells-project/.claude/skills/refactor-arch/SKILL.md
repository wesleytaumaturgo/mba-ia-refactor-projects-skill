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
| **+1** | **Protocolo de validação** | `references/validation-protocol.md` | Fim da Fase 1 e fim de **cada onda** |

O sexto arquivo é deliberado, não desvio: validação é conhecimento — como saber que um servidor
subiu sem saber qual é o framework? — e não orquestração. Mantê-lo aqui dentro empurraria este
arquivo para além do que um orquestrador legível suporta; mantê-lo no playbook obrigaria a
carregar o arquivo mais caro do conjunto já na Fase 1, só para capturar o baseline.

## Escopo

**Dentro:** detecção de stack e arquitetura efetiva, auditoria contra o catálogo com severidade
e `arquivo:linha`, relatório em `reports/`, reestruturação para MVC, validação por boot e smoke
test contra baseline.

**Fora:** arquitetura que não seja MVC, troca de framework/ORM/banco/runtime, alteração de path
ou verbo de endpoint, escrita da suíte de testes do projeto, decisões de produto (política de
senha, retenção de PII), deploy e CI, e qualquer execução sobre working tree sujo.

---

## Pré-condições

Antes da Fase 1, sem exceção:

1. Verifique que o diretório é um repositório VCS e que o working tree está **limpo**.
   Sujo → reporte e **aborte**. O commit atual é o ponto de retorno do rollback; um working
   tree sujo o invalida, e um `git reset --hard` posterior destruiria trabalho não commitado.
2. Registre o **SHA do commit de baseline**. É o alvo do primeiro rollback.
3. Declare em voz alta: *"auditoria read-only até o gate da Fase 2"*.

---

## Fase 1 — Análise (read-only)

Carregue `references/project-analysis.md` e `references/validation-protocol.md`.

Determine os oito fatos da §0 daquele arquivo: linguagem, framework efetivo, **versão real do
runtime obtida executando-o** (não a do manifesto), persistência, domínio, arquitetura efetiva
por grafo de imports, inventário de endpoints e baseline de comportamento.

Duas armadilhas que custam a fase inteira se ignoradas: dependência declarada e não importada
**não** é a stack (é candidata a AP-26), e a arquitetura efetiva é o grafo de imports, **não** a
árvore de diretórios.

Capture o baseline por último, com o código ainda intocado (`validation-protocol.md` §2).

**Nenhuma escrita em disco nesta fase.** Emita no console:

```console
PHASE 1: PROJECT ANALYSIS
─────────────────────────────────────────────
Language      : <lang> (runtime in use: <version>)
Framework     : <framework> <version>
Package mgr   : <manifest file>
Database      : <engine> · <n> tables
Domain        : <one line>
Entry point   : <file>
Architecture  : <effective, from the import graph>
Source files  : <n> files · <n> LOC
Endpoints     : <n> mapped · baseline captured (<n> responses)
Baseline SHA  : <short sha>
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
6. **Registre como finding o conteúdo de qualquer camada inalcançável** a partir do entry point
   **antes** de propô-la para remoção (`mvc-guidelines.md` §6). Nada some sem constar do
   relatório — inclusive segredos versionados dentro de código morto.
7. **Ordene** CRITICAL → HIGH → MEDIUM → LOW e redija conforme `references/report-template.md`.
8. **Redija a seção Breaking changes:** toda mudança de shape de resposta que a refatoração vai
   provocar, com endpoint, campo e motivo. Preveja o efeito de cada TR **antes** de executá-lo;
   é isso que transforma o gate numa decisão informada.
9. **Grave** `reports/audit-<projeto>.md`. Esta é a única escrita permitida antes do gate: é
   artefato novo e aditivo, e o trabalho da fase precisa sobreviver a um "n".
10. **Monte o plano de refatoração agrupado por onda:** finding → TR → onda → arquivos afetados.

### ★ Gate humano — última instrução da Fase 2

Nenhum arquivo de código, manifesto, configuração ou diretório do projeto é criado, movido ou
alterado antes da resposta. Apresente: findings por severidade, o plano nas 4 ondas com os
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

Ordem fixa, por severidade. A onda é propriedade do **finding**, não do TR: um TR rotulado para
uma onda posterior sobe para a onda do finding de maior severidade que ele resolve.

| Onda | Severidade | TRs padrão |
|---|---|---|
| 1 | CRITICAL | TR-01…TR-06 — e o esqueleto MVC, que **é** esta onda |
| 2 | HIGH | TR-07…TR-10 |
| 3 | MEDIUM | TR-11…TR-17 |
| 4 | LOW | TR-18 |

Não há onda 0: extrair configuração (TR-01) e decompor a god class (TR-06) resolvem findings
CRITICAL e, ao fazê-lo, produzem a estrutura. Um esqueleto de diretórios vazios não é
falsificável por smoke test e não merece um commit próprio.

### Protocolo de onda — idêntico nas quatro

1. Aplique os TRs da onda. **Boot após cada TR** — barato, e localiza a quebra no TR em vez de
   na onda inteira. Dentro da Onda 1, aplique TR-01 e TR-06 primeiro.
2. Ao fim da onda: **smoke test completo** contra o baseline (`validation-protocol.md` §4).
3. **Verde** → commit `refactor(onda-N): <severidade>`, com a **contagem de endpoints
   verificados na mensagem**. Sem esse número não há commit: é o que distingue uma onda
   validada de uma onda declarada validada.
4. **Vermelho** → `git reset --hard <último commit verde>`, depois **pare e reporte**. Não tente
   a onda seguinte sobre uma base não validada.

### Validação final

Herdada das quatro ondas verdes, mais:

- Nenhum AP CRITICAL ou HIGH do relatório permanece.
- Toda mudança de shape observada consta da seção Breaking changes aprovada no gate.
  Divergência é **regressão**, não melhoria — mesmo que o resultado pareça melhor.

### Saída

```console
PHASE 3: REFACTORING COMPLETE
─────────────────────────────────────────────
Waves         : 1 CRITICAL ✓ · 2 HIGH ✓ · 3 MEDIUM ✓ · 4 LOW ✓
Smoke test    : <n>/<n> endpoints conform to baseline
Breaking chg  : <n> applied, all declared in the approved report
Findings fixed: <n>/<n> (<n> reported, not fixed: <ids>)
History       : <baseline sha> → onda-1 → onda-2 → onda-3 → onda-4
─────────────────────────────────────────────
New structure:
<árvore de diretórios resultante>
```

Falha em qualquer onda → **não declare sucesso parcial como sucesso**. Reporte a onda que
quebrou, o TR suspeito, a evidência, e o commit verde para onde o repositório voltou.

---

## Regras invioláveis

- Nenhuma escrita em arquivo do projeto antes do `y`. O relatório em `reports/` é a única
  exceção, e é artefato, não código.
- Sem `arquivo:linha` + código literal, o finding não existe.
- Path, verbo e status code de sucesso são preservados. Mudança de shape só a declarada.
- Commit é consequência de smoke test verde, com a contagem na mensagem.
- Os exemplos das referências ilustram a **forma**. Escreva no idioma da stack detectada na
  Fase 1, nunca copiando a sintaxe de outra.
