# run-2 · Checagem · `ecommerce-api-legacy`

Checagem do operador sobre a execução da skill. **CA-1, CA-2 e CA-3 foram fechados antes de
abrir `.planning/analise-manual/ecommerce-api-legacy.md`**; o cruzamento veio depois, na ordem
exigida, para que a leitura da análise manual não contaminasse o julgamento sobre a Fase 1 nem a
contagem de findings.

---

## CA-1 — A Fase 1 detectou Node/Express corretamente? Campo a campo.

Confrontando cada linha da saída de console contra o que foi verificado independentemente:

| Campo | Skill emitiu | Verificação independente | Veredito |
|---|---|---|---|
| `Language` | JavaScript / CommonJS | 3/3 arquivos `.js`; `package.json` sem campo `type` → CommonJS é o default de Node. Todos os módulos usam `require`/`module.exports`, nenhum `import`/`export` | ✅ correto |
| `Language` (runtime in use) | Node.js **v24.12.0** | `node --version` **executado**. O manifesto não declara `engines` — se a skill tivesse lido do manifesto, não haveria o que ler | ✅ correto, e obtido pelo método certo |
| `Framework` | Express **4.22.1** (declarado `^4.18.2`) | `require('express/package.json').version` → `4.22.1`; `package.json:10` → `^4.18.2`. Declarado **∩** resolvido; nenhuma dependência declarada e não resolvida | ✅ correto, com as duas versões separadas |
| `Package mgr` | `package.json` + `package-lock.json` (npm 11.6.2) | Ambos existem na raiz do projeto; `npm --version` → 11.6.2 | ✅ correto |
| `Database` | SQLite in-memory (sqlite3 5.1.7) · **5 tables** | `require('sqlite3/package.json').version` → 5.1.7; `AppManager.js:7` → `':memory:'`; DDL em `:12-16` → `users`, `courses`, `enrollments`, `payments`, `audit_logs` = 5 | ✅ correto |
| `Domain` | LMS de cursos pagos | Vocabulário cruzado nas três fontes: tabelas → paths → entidades | ✅ correto |
| `Entry points` | `src/app.js` | `package.json` → `main: "src/app.js"` **e** `scripts.start: "node src/app.js"`. Fonte de maior precedência, não o README | ✅ correto |
| `Resolution` | explicit import (CommonJS require) | Não há autoloader, varredura de pacote nem container. O mecanismo foi nomeado **antes** de concluir alcançabilidade, que é a ordem que `project-analysis.md` §6 exige | ✅ correto |
| `Architecture` | monolito de 3 arquivos sem camadas | Descreve o **grafo de resolução**, não a árvore de diretórios. Não existe diretório de camada no projeto, então não havia armadilha de "pasta bonita que nada resolve" a cair | ✅ correto |
| `Source files` | 3 files · **180 LOC** | `wc -l src/*.js` → 14 + 141 + 25 = 180 | ✅ correto |
| `Endpoints` | 3 mapped · baseline captured (4 responses) | `grep` de registro de rota → 3 (`:28`, `:80`, `:131`); `M = 4` porque `POST /api/checkout` teve dois casos representativos | ✅ correto |
| `Baseline SHA` | `5d02287` | `git rev-parse --short HEAD` no momento das pré-condições | ✅ correto |
| `Baseline file` | caminho absoluto sob `reports/` | Ancorado na raiz devolvida por `git rev-parse --show-toplevel`, **não** no diretório de trabalho (que era `ecommerce-api-legacy/`) | ✅ correto |

**CA-1: APROVADO — 13/13 campos corretos.** Três acertos merecem destaque porque são exatamente
onde a skill avisa que a fase se perde:

1. **Versão de runtime obtida executando**, não lida do manifesto. Aqui o erro seria silencioso e
   fatal: o manifesto **não tem** `engines`, então a leitura teria produzido "indeterminado" e
   AP-16 sairia como *não verificável* em vez de *não encontrado*.
2. **Declarado × resolvido separados.** `^4.18.2` × `4.22.1` e `^5.1.6` × `5.1.7` foram registrados
   como fatos distintos, e a divergência virou insumo de F-020.
3. **Mecanismo de resolução nomeado antes da conclusão de alcançabilidade.** Como o projeto não
   tem nenhuma pasta com nome de camada, a armadilha não chegou a ser testada nesta execução —
   registro isso como cobertura **não exercida**, não como acerto comprovado.

**Desvio irrelevante encontrado:** um único campo textual da análise manual diverge — ela afirma
que `node_modules/` "não está instalado no diretório", o que era verdade quando ela foi escrita e
deixou de ser quando o baseline exigiu `npm install`. Não afeta nenhum fato da Fase 1.

---

## CA-2 — Número real de findings (contado)

Contagem sobre o artefato, não sobre o que o relatório declara no sumário:

```console
$ grep -c '^### \[' reports/audit-ecommerce-api-legacy.md
20
$ grep -o '^### \[[A-Z]*\]' reports/audit-ecommerce-api-legacy.md | sort | uniq -c
      5 ### [CRITICAL]
      6 ### [HIGH]
      5 ### [LOW]
      4 ### [MEDIUM]
```

**CA-2: 20 findings reais** — F-001 a F-020, numeração contínua através das severidades, sem
salto nem repetição. A contagem bate com o sumário declarado no relatório (5 · 6 · 4 · 5) e com a
linha de "Próximo passo". Nenhum finding inflado por repetição: os casos com mais ocorrências
(F-006 com 11, F-012 com 11, F-016 com 11) são **um** finding cada, com as ocorrências listadas
como `arquivo:linha`.

---

## CA-3 — Há ≥1 CRITICAL ou HIGH?

**Sim, com folga: 11 findings CRITICAL ou HIGH** (5 + 6), contra o mínimo de 1.

| # | Sev. | Finding | AP |
|---|---|---|---|
| F-001 | CRITICAL | Credenciais de produção literais, sem leitura de ambiente | AP-02 |
| F-002 | CRITICAL | Rota admin e rota destrutiva sem autenticação | AP-05 |
| F-003 | CRITICAL | Derivação de senha caseira com colisão demonstrada | AP-04 |
| F-004 | CRITICAL | God class: 5 responsabilidades em 141 linhas | AP-06 |
| F-005 | CRITICAL | PAN completo e chave de gateway em log | AP-07 |
| F-006 | HIGH | Handlers falam SQL diretamente | AP-13 |
| F-007 | HIGH | DDL e seed no boot, sem constraint alguma | AP-21 |
| F-008 | HIGH | Regra de negócio dentro dos handlers | AP-08 |
| F-009 | HIGH | Infra no construtor, composition root sem injeção | AP-09 |
| F-010 | HIGH | Escritas sem transação; deleção produz órfãos | AP-11 |
| F-011 | HIGH | Estado global mutável de módulo | AP-10 |

**CA-3: APROVADO.**

---

## CRUZAMENTO com a análise manual

Análise manual lida **agora**, pela primeira vez: 22 findings validados, AM-028 a AM-049.

| AM-ID | Título (resumido) | Sev. manual | Reencontrado? | F-ID | Divergência de severidade |
|---|---|---|---|---|---|
| AM-028 | Credenciais e chave de gateway hardcoded | CRITICAL | ✅ sim | F-001 | — |
| AM-029 | God Class | CRITICAL | ✅ sim | F-004 | — |
| AM-030 | Cartão e chave do gateway em log | CRITICAL | ✅ sim | F-005 | — |
| AM-031 | `badCrypto` criptograficamente inútil | CRITICAL | ✅ sim | F-003 | — |
| AM-032 | Autorização de pagamento no handler | HIGH | ✅ sim | F-008 | — |
| AM-033 | Acoplamento concreto, sem injeção | HIGH | ✅ sim | F-009 | — |
| AM-034 | Estado global mutável exportado | HIGH | ✅ sim | F-011 | — |
| AM-035 | Rotas admin/destrutiva sem auth | HIGH | ✅ sim | F-002 | **skill +1** (CRITICAL vs HIGH) |
| AM-036 | Checkout sem transação nem rollback | HIGH | ✅ sim | F-010 | — |
| AM-037 | Coordenação por contador; erros ignorados; request pendurada | HIGH | ⚠️ **parcial** | F-012, F-014 | **skill −1** na parte reportada (MEDIUM); a parte grave não foi reportada |
| AM-038 | Credencial default `"123456"` silenciosa | HIGH | ⚠️ **parcial** | F-003 (citado como ocorrência) | absorvido em CRITICAL, mas sem finding nem impacto próprios |
| AM-039 | N+1 de três níveis | MEDIUM | ✅ sim | F-014 | — |
| AM-040 | Validação de entrada ausente e incompleta | MEDIUM | ❌ **não** | — | **falso negativo** |
| AM-041 | Deleção com órfãos, erro ignorado, 200 sempre | MEDIUM | ✅ sim | F-010 + F-012 | **skill +1** na parte dos órfãos (HIGH vs MEDIUM) |
| AM-042 | Schema no boot, sem migrações e sem constraints | MEDIUM | ✅ sim | F-007 | **skill +1** (HIGH vs MEDIUM) |
| AM-043 | `console.log` como observabilidade | MEDIUM | ✅ sim | F-019 | **skill −1** (LOW vs MEDIUM) |
| AM-044 | Contrato de resposta inconsistente | MEDIUM | ✅ sim | F-013 | — |
| AM-045 | Import morto, primitivo por valor, `verbose()` | LOW | ⚠️ **parcial** | F-018 | `verbose()` **não reportado** |
| AM-046 | Nomenclatura críptica | LOW | ✅ sim | F-016 | — |
| AM-047 | Seed embutido no código de aplicação | LOW | ✅ sim | F-007 (absorvido) | **skill +2** (HIGH vs LOW) |
| AM-048 | Alias `self` com arrow functions | LOW | ⚠️ **parcial** | F-016 (uma ocorrência) | citado, sem a armadilha dos três `this` |
| AM-049 | Ausência de infraestrutura de qualidade | LOW | ✅ sim | F-020 | — |

### Cobertura

| Critério | Conta | % |
|---|---|---|
| Reencontrado **integralmente** | 17 / 22 | **77,3 %** |
| Reencontrado **integral ou parcialmente** | 21 / 22 | **95,5 %** |
| **Cobertura ponderada** (parcial = 0,5) | 19 / 22 | **86,4 %** |

Divergências de severidade: **6 de 21 reencontrados (28,6 %)** — 4 para cima (AM-035, AM-041,
AM-042, AM-047) e 2 para baixo (AM-037, AM-043).

### Leitura das divergências de severidade

As divergências **não são ruído**: 5 das 6 são consequência direta da escala do catálogo, e são
defensáveis pela regra escrita.

- **AM-035 → F-002 (HIGH → CRITICAL).** A escala do catálogo define CRITICAL como "explorável por
  chamador anônimo … sem requerer condição rara". Um `DELETE` anônimo satisfaz literalmente o
  critério. A skill está certa; a análise manual foi conservadora.
- **AM-042 → F-007 e AM-047 → F-007 (MEDIUM/LOW → HIGH).** O catálogo tabela AP-21 como HIGH e o
  finding herda; o seed foi absorvido como ocorrência do mesmo AP em vez de virar finding próprio.
  Correto pela regra "um finding por causa, não por ocorrência" — mas o efeito colateral é que o
  seed com credencial `'123'` em texto puro perde visibilidade própria no relatório.
- **AM-043 → F-019 (MEDIUM → LOW).** O catálogo fixa AP-19 como LOW, e a skill não desviou. A
  análise manual é mais severa por considerar a ausência total de observabilidade; a skill
  distribuiu esse peso em F-005 (CRITICAL) e F-012. Divergência de escala, não de detecção.
- **AM-037 → F-012/F-014 (HIGH → MEDIUM).** Esta é a única divergência para baixo que **não** se
  explica pela escala: é consequência de um finding incompleto (ver abaixo).

---

## Findings novos (a skill achou, a análise manual não tem)

| F-ID | Sev. | Finding | Avaliação |
|---|---|---|---|
| F-015 | MEDIUM | `GET /api/admin/financial-report` sem paginação: `SELECT * FROM courses` (`:83`) e `SELECT * FROM enrollments` (`:92`) sem `LIMIT`; o handler não lê parâmetro de query | **Legítimo.** A análise manual não tem nenhum finding de paginação. O tamanho da resposta é função dos dados, e a coleção não tem cardinalidade fechada |
| F-017 | LOW | Vocabulário fechado `{PAID, DENIED}` reconstruído inline em `:46`, `:48`, `:108`, `:21`, sem constante e sem `CHECK` em `payments.status` (`:15`) | **Legítimo, porém marginal.** A análise manual cita o literal `"4"` em AM-032 mas não o vocabulário de status |
| F-006 | HIGH | Handlers manipulam o driver diretamente — 11 ocorrências | **Legítimo como finding, discutível como finding separado** (ver falsos positivos) |
| — | — | **Ordem da coleção não-determinística, provada por execução:** duas execuções do código intocado devolveram os cursos em ordens diferentes | **Contribuição real de método.** A análise manual **deduz** isso em AM-037 ("depende de qual callback retorna primeiro"); a skill **provou** por execução repetida e registrou `"order_guaranteed": false` no baseline, evitando um falso vermelho na Fase 3 |

---

## Falsos positivos suspeitos no relatório da skill

Revisão cética dos 20 findings. **Nenhum carece de evidência literal** — todos trazem
`arquivo:linha` e bloco copiado do projeto. Duas ressalvas, ambas de granularidade, não de
veracidade:

1. **F-006 (AP-13) vs F-004 (AP-06) — mesma causa, dois findings.** Ambos descrevem o mesmo fato
   estrutural: não existe camada entre a rota e o driver. O catálogo **prevê** isso (a nota de
   onda de AP-13 diz que TR-06 fecha os dois, e o relatório registra a carona), então não é
   violação da regra — mas infla a contagem de HIGH em 1. Um leitor que compare 20 contra 22 sem
   ler os corpos concluiria coisa errada.
2. **F-017 (AP-25) — no limite inferior.** Três cópias de um vocabulário de dois valores. Passa o
   limiar do AP, mas é o finding mais fraco do conjunto, e o relatório teria a mesma força sem ele.

**Nenhum finding foi descartado como falso positivo.** Os quatro que eu mais suspeitava de serem
"preenchimento de cota" (F-015, F-017, F-019, F-020) foram reconferidos contra o código e todos
se sustentam.

O inverso também merece registro: a skill **descartou** cinco APs que um relatório inflado teria
incluído — AP-01 (injeção), AP-03 (PII na serialização), AP-12, AP-14 e AP-17 — e a análise
manual **concorda com todos os cinco**, inclusive dedicando uma seção própria à ausência de SQL
Injection. Convergência nos negativos vale tanto quanto convergência nos positivos.

---

## Falsos negativos — o que a skill deixou passar

Aqui está o resultado mais importante desta checagem. **Todos os três foram verificados por
execução nesta sessão**, não aceitos da análise manual por autoridade.

### FN-1 (grave) — Requisição anônima única derruba o processo inteiro

`src/AppManager.js:46` chama `cc.startsWith(...)` sem verificar o tipo. `card` vindo como número
JSON — payload perfeitamente válido para `JSON.parse` — lança `TypeError` **dentro de um callback
assíncrono do driver**, onde não há `try/catch`, `.catch` nem handler de erro do Express que possa
contê-lo. Verificado:

```console
$ curl -X POST http://localhost:3000/api/checkout -H 'Content-Type: application/json' \
       -d '{"usr":"X","eml":"x@y.z","pwd":"p","c_id":2,"card":4111222233334444}'
[status=000]

$ (processo vivo depois?)
MORTO - processo derrubado

/home/.../src/AppManager.js:46
                        let status = cc.startsWith("4") ? "PAID" : "DENIED";
                                        ^
TypeError: cc.startsWith is not a function
    at processPaymentAndEnroll (/home/.../src/AppManager.js:46:41)
    at Statement.<anonymous> (/home/.../src/AppManager.js:71:29)
```

**Severidade real: CRITICAL.** Satisfaz dois critérios da escala simultaneamente — explorável por
chamador anônimo sem condição rara **e** permite perda de dados: como o banco é `:memory:`
(`:7`), derrubar o processo apaga **todos** os usuários, matrículas e pagamentos. É negação de
serviço com destruição total de dados a partir de uma requisição, e passou em branco.

A análise manual chega perto em AM-040 ("um `card` não-string faz `cc.startsWith` lançar
`TypeError`… derrubando o processo") mas classifica MEDIUM e não conecta ao banco volátil.
**Ambas as auditorias erraram a severidade; a skill errou também a detecção.**

### FN-2 (médio) — Requisição que nunca responde e erro que derruba o relatório

`src/AppManager.js:93` lê `enrollments.length` sem verificar `err`; se a consulta falhar,
`enrollments` vem `undefined` e o `TypeError` derruba o processo pelo mesmo caminho de FN-1. E se
qualquer decremento de `coursesPending`/`enrPending` for pulado, a condição `=== 0` nunca é
satisfeita e `res.json` nunca é chamado — a conexão fica pendurada até o timeout do cliente.

O relatório da skill **cita** `:93`, `:104` e `:106` como ocorrências de F-012 ("`err` declarado e
inteiramente ignorado"), mas descreve a consequência apenas como "defeito invisível em produção".
A consequência real — processo derrubado, ou requisição que nunca termina — não aparece.

### FN-3 (menor, e é erro de execução da skill, não do catálogo) — `verbose()` incondicional

`src/AppManager.js:1` — `require('sqlite3').verbose()` — é flag de verbosidade do driver ligada em
código, em qualquer ambiente, e a aplicação faz bind em **todas** as interfaces
(`LISTEN 0 511 *:3000 *:*`). Isso é literalmente a **segunda pergunta do sinal de AP-02**:
*"Existe flag de debug ou verbosidade ligada em código junto de bind em todas as interfaces de
rede?"* O relatório respondeu só a primeira metade do sinal. Deveria ser uma quinta ocorrência de
F-001. Confirmado ativo pela própria stack trace de FN-1, que passa por
`node_modules/sqlite3/lib/trace.js:25` — instrumentação que só existe sob `verbose()`.

### Outros dois defeitos confirmados, não reportados por nenhum AP

```console
$ curl -X POST .../api/checkout -d '{"usr":"X","eml":"x@y.z","pwd":"p","c_id":0,"card":"4111"}'
Bad Request
[status=400]                     # c_id = 0 é legítimo e é rejeitado pelo teste falsy de :35

$ curl -X DELETE http://localhost:3000/api/users/99999
Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
[status=200]                     # id inexistente responde 200 e mensagem de sucesso
```

---

## Diagnóstico: por que os falsos negativos aconteceram

Separando o que é erro desta execução do que é limite do catálogo — a distinção importa porque
uma coisa se corrige refazendo, e a outra exige mexer na skill.

**FN-3 é erro de execução.** O sinal de AP-02 pergunta duas coisas e só uma foi respondida.
Refazer a Fase 2 com mais cuidado o pegaria.

**FN-1 e FN-2 são lacuna do catálogo.** Percorri as 28 entradas procurando qual dispararia para
"ausência de validação de tipo na borda faz o processo morrer" e para "coordenação assíncrona
manual deixa a requisição pendurada":

- **AP-12** cobre validação de domínio **escrita inline no handler** — o defeito de estar no lugar
  errado. Aqui a validação simplesmente **não existe**, que é outro defeito.
- **AP-18** cobre **bloco de captura genérico**. Aqui não há captura nenhuma — não há `try/catch`,
  não há `.catch`, não há error handler do Express registrado.
- **AP-14, AP-23, AP-05** não alcançam nenhum dos dois.

Ou seja: os 28 APs cobrem *código mal colocado* e *código mal escrito*, mas **nenhum tem como
sinal a ausência de uma fronteira de erro** — nem de validação de tipo na entrada, nem de captura
no processo. Num projeto de callbacks aninhados sem `async/await`, essa é a lacuna mais cara
possível: é por onde vaza o único defeito CRITICAL que as duas auditorias não classificaram
corretamente.

**Isto é achado sobre a skill, não sobre o projeto**, e cai na restrição declarada: o ajuste iria
no arquivo de referência **genérico** em `code-smells-project/.claude/skills/refactor-arch/references/antipattern-catalog.md`,
exigiria re-propagação e re-execução no projeto 1 para checar regressão. **Não foi feito. Está
reportado para decisão.**

---

## Veredito da checagem

| Critério | Resultado |
|---|---|
| CA-1 — detecção Node/Express | ✅ **13/13 campos corretos** |
| CA-2 — findings reais (contados) | **20** (5 CRITICAL · 6 HIGH · 4 MEDIUM · 5 LOW) |
| CA-3 — ≥1 CRITICAL ou HIGH | ✅ **11** |
| Cobertura da análise manual | **77,3 % integral · 86,4 % ponderada · 95,5 % integral+parcial** |
| Falsos positivos confirmados | **0** |
| Falsos negativos | **3** — 1 grave (CRITICAL não detectado), 1 médio, 1 menor |
| Escritas antes do gate | **2** — relatório e baseline. Projeto intocado |
| Gate | Emitido; **não respondido**. Fase 3 não iniciada |

A skill se sustenta como instrumento de auditoria: recuperou 95,5 % da análise manual, não
produziu nenhum falso positivo, e adicionou dois findings e uma prova por execução que a análise
manual não tinha. A lacuna é real e é estrutural, não de esforço — o catálogo não tem entrada para
ausência de fronteira de erro, e é exatamente por ali que passou um CRITICAL.
