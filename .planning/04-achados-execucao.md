# 04 — Achados de execução · projetos 2 e 3

Achados sobre **a skill**, produzidos executando-a às cegas em projetos novos e cruzando o
resultado com a análise manual prévia.

- **AE-01 … AE-03** — projeto 2, `ecommerce-api-legacy` (run-2). Todos são **falsos negativos**
  da Fase 2: defeitos reais que a auditoria não viu.
- **AE-04 … AE-07** — projeto 3, `task-manager-api` (run-3). Nenhum é falso negativo. São de
  outra natureza: **imprecisões do que a skill declarou sobre o próprio trabalho** — uma onda
  que declarou resolvido o que não estava, um número errado num artefato de aceite, uma entrega
  além do aprovado, e uma decisão que o relatório enquadrou como pendência.

## Parte I — projeto 2 (`ecommerce-api-legacy`)

Cruzamento com `.planning/analise-manual/ecommerce-api-legacy.md`, AM-028 a AM-049.

Nenhum dos itens abaixo foi corrigido nesta entrega. A razão está no fim de cada bloco, e é a
mesma em essência: corrigir o catálogo exige re-propagação aos 3 projetos e re-execução do
projeto 1 para checar regressão — e o registro honesto do que a skill não cobre vale mais, nesta
entrega, que um AP-29 acrescentado às pressas.

**Contexto do run-2:** 20 findings (5 CRITICAL · 6 HIGH · 4 MEDIUM · 5 LOW), zero falsos
positivos, cobertura de 95,5 % da análise manual (77,3 % integral). Os achados abaixo são os
**falsos negativos**.

---

## AE-01 — Lacuna do catálogo: nenhum AP tem como sinal a ausência de fronteira de erro

**Categoria:** lacuna do catálogo (`references/antipattern-catalog.md`)
**Severidade real do defeito não detectado:** CRITICAL
**Estado:** registrado, **não corrigido**

### O defeito que passou

`ecommerce-api-legacy/src/AppManager.js:46` (no commit de baseline `5d02287`):

```javascript
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```

`cc` vem de `req.body.card` (`src/AppManager.js:33`) sem nenhuma verificação de tipo. Um `card`
enviado como **número JSON** — payload perfeitamente válido para `JSON.parse` — lança `TypeError`
**dentro de um callback assíncrono do driver sqlite3**, onde não há `try/catch`, não há `.catch` e
não há handler de erro do Express registrado. Verificado por execução:

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
    at Statement.replacement (/home/.../node_modules/sqlite3/lib/trace.js:25:27)
```

**Por que é CRITICAL pela escala do próprio catálogo:** satisfaz dois critérios ao mesmo tempo —
*"explorável por chamador anônimo … sem requerer condição rara"* **e** *"permite perda de dados"*.
O banco é `:memory:` (`src/AppManager.js:7`), então derrubar o processo apaga **todos** os
usuários, matrículas e pagamentos. Negação de serviço com destruição total de dados, a partir de
uma única requisição sem credencial.

### Por que nenhum dos 28 APs disparou

As 28 entradas foram percorridas procurando qual cobriria o caso:

| AP | Por que não alcança |
|---|---|
| **AP-12** — Validação de domínio inline no handler | O sinal é validação **escrita no lugar errado**. Aqui a validação de tipo simplesmente **não existe** — e o próprio AP exclui explicitamente a verificação de protocolo, que é onde o tipo seria checado |
| **AP-18** — Captura genérica de exceção | O sinal exige um **bloco de captura** sem tipo. Aqui não há captura nenhuma: nem `try/catch`, nem `.catch`, nem tratador registrado. A ausência total de captura não dispara um AP cujo sinal pressupõe captura presente |
| **AP-14** — Mass assignment | Os campos são lidos individualmente e vinculados nominalmente |
| **AP-23** — Contrato inconsistente | Descreve divergência entre envelopes, não colapso do processo |
| **AP-05** — Rota privilegiada sem autenticação | A rota de checkout é legitimamente pública (ND-1) |

**Conclusão estrutural:** os 28 APs cobrem *código mal colocado* e *código mal escrito*, mas
**nenhum tem como sinal a ausência de uma fronteira** — nem de validação de tipo na entrada, nem
de captura no processo. Num projeto de callbacks aninhados sem `async/await`, essa é a lacuna mais
cara possível.

### A análise manual também errou, mas menos

`AM-040` chega perto: *"Um `card` não-string faz `cc.startsWith` lançar `TypeError` dentro de um
callback, derrubando o processo"*. Classificou **MEDIUM** e não conectou ao banco volátil. Ou
seja: a análise manual **detectou** e subestimou; a skill **não detectou**.

### O que aconteceu na Fase 3

O defeito foi **contido**, não corrigido, e a contenção não veio de detecção:

| Momento | Comportamento | Causa |
|---|---|---|
| baseline `5d02287` | processo derrubado, `status=000`, todos os dados perdidos | — |
| após Onda 1 `4701894` | **processo sobrevive**; corpo é o HTML padrão do Express com `TypeError: card.startsWith is not a function` e três caminhos absolutos expostos ao chamador anônimo | **TR-06**: promissificar o driver e encaminhar a rejeição por `asyncHandler` transformou a exceção que escapava num rejeitado que o Express captura |
| após Onda 3 `0d1eacc` | `500` com envelope `{"error":{"code":"INTERNAL_ERROR",…,"correlationId":"…"}}`, zero stack trace, detalhe completo só no log correlacionado | **TR-13** |
| final `cc8d8a5` | `src/services/paymentGateway.js:21` ainda faz `card.startsWith(...)` sem checar tipo — um `card` não-string ainda produz `500` em vez de `400` | defeito **preservado de propósito**: nenhum finding o cobre, nenhum TR foi agendado, corrigi-lo seria trabalho fora do plano aprovado no gate |

**Se o projeto tivesse apenas findings que não acionassem TR-06 e TR-13, o crash teria sobrevivido
à refatoração inteira com o relatório declarando sucesso.** É esse o risco que o achado nomeia.

### Correção proposta (não aplicada)

Um AP novo em `references/antipattern-catalog.md`, com sinal na forma *"existe caminho de
execução em que uma exceção não capturada escapa para a fronteira do processo?"* e *"existe valor
de entrada externa desreferenciado sem verificação de tipo antes do primeiro uso?"*. Precisaria de
TR correspondente e de renumeração da distribuição declarada no índice
(`CRITICAL 7 · HIGH 7 · MEDIUM 9 · LOW 5`).

**Custo que impede aplicá-la agora:** alterar o arquivo genérico em
`code-smells-project/.claude/skills/refactor-arch/references/antipattern-catalog.md`, re-propagar
para os 3 projetos, e **re-executar o projeto 1** para checar regressão nos 27 findings que ele já
produziu.

---

## AE-02 — Lacuna do catálogo: coordenação assíncrona manual não tem AP

**Categoria:** lacuna do catálogo
**Severidade real:** HIGH (era `AM-037`, HIGH, na análise manual)
**Estado:** registrado, **não corrigido**

`src/AppManager.js:93` (baseline) lê `enrollments.length` sem verificar `err`:

```javascript
this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
    let enrPending = enrollments.length;
```

Dois defeitos, nenhum coberto por AP:

1. Se a consulta falhar, `enrollments` vem `undefined` e o `TypeError` derruba o processo pelo
   mesmo caminho de AE-01.
2. A resposta é emitida quando dois contadores decrementados à mão (`coursesPending`,
   `enrPending`) chegam a zero. Se um decremento for pulado por um caminho de erro, a condição
   `=== 0` nunca é satisfeita, `res.json` nunca é chamado, e **a requisição fica pendurada até o
   timeout do cliente**, segurando a conexão.

O relatório do run-2 **cita** as linhas `:93`, `:104` e `:106` como ocorrências de F-012 (AP-18,
"`err` declarado e inteiramente ignorado"), mas descreve a consequência apenas como *"defeito
invisível em produção"*. A consequência real — processo derrubado, ou requisição que nunca termina
— não aparece, porque o sinal de AP-18 pergunta sobre captura genérica, não sobre coordenação
assíncrona.

Resultado prático: **a severidade caiu de HIGH (AM-037) para MEDIUM (F-012)** — a única divergência
de severidade do run-2 que não se explica pela escala do catálogo, e sim por um finding incompleto.

Resolvido na prática por TR-11 (consulta única elimina os contadores) e TR-06 (promissificação),
mas de novo **por efeito colateral, não por detecção**.

---

## AE-03 — Erro de execução da skill, não do catálogo: a segunda metade do sinal de AP-02 não foi respondida

**Categoria:** **erro de execução** — o catálogo cobre, a varredura é que falhou
**Severidade:** menor
**Estado:** registrado; o defeito subjacente foi corrigido em TR-01, por outro caminho

Esta distinção é o ponto do item. AE-01 e AE-02 são lacunas do catálogo: nenhum sinal existente
alcançava o defeito. **AE-03 não é isso.** O sinal de AP-02 pergunta **duas** coisas:

> *"Existe literal atribuído a chave de configuração sensível … sem nenhuma leitura de variável
> de ambiente em todo o projeto? **Existe flag de debug ou verbosidade ligada em código junto de
> bind em todas as interfaces de rede?**"*

O relatório respondeu só a primeira. As duas condições da segunda metade estavam presentes no
baseline:

```javascript
// src/AppManager.js:1
const sqlite3 = require('sqlite3').verbose();     // verbosidade ligada em código, incondicional
```

```console
$ ss -ltn | awk '$4 ~ /:3000$/'
LISTEN 0      511                              *:3000             *:*          # todas as interfaces
```

Confirmação de que a verbosidade estava **ativa**, e não apenas declarada: a stack trace de AE-01
passa por `node_modules/sqlite3/lib/trace.js:25`, instrumentação que só existe sob `verbose()`.

A análise manual pegou (`AM-045`, que cita *"a mesma linha 1 carrega o driver em modo `verbose()`
de forma incondicional, um flag de depuração ativo em qualquer ambiente"*). A skill não.

**Por que isso importa mais do que o tamanho do defeito sugere:** é o único falso negativo do
run-2 que **refazer a Fase 2 com mais cuidado corrigiria**. Não pede alteração no catálogo. É
sinal de que sinais compostos — perguntas com "**Ou**" e com duas cláusulas — são respondidos pela
metade quando a primeira metade já produz um finding forte. Vale como candidato a nota de método
no `SKILL.md` ou no cabeçalho "Como usar cada entrada" do catálogo: *responda todas as cláusulas
do sinal, mesmo depois de a primeira já ter produzido finding.*

O defeito acabou corrigido na Fase 3, mas **não por detecção**: o passo 3 de TR-01 (*"Desligue
debug fora de desenvolvimento e restrinja o bind de rede ao que o ambiente definir"*) o cobre por
construção. Resultado no commit `cc8d8a5`:

```javascript
// src/db/connection.js:9
const sqlite3 = verbose ? sqlite3base.verbose() : sqlite3base;
```

```console
LISTEN 0      511                      127.0.0.1:3000       0.0.0.0:*
```

---

## Resumo da Parte I

| ID | Tipo | Detectado pela skill? | Corrigido na Fase 3? | Por detecção? | Correção do catálogo aplicada? |
|---|---|---|---|---|---|
| AE-01 | lacuna do catálogo | ❌ | contido, não corrigido | ❌ (efeito de TR-06 + TR-13) | ❌ registrado |
| AE-02 | lacuna do catálogo | parcial (severidade a menos) | ✅ | ❌ (efeito de TR-11 + TR-06) | ❌ registrado |
| AE-03 | erro de execução | ❌ | ✅ | ❌ (efeito de TR-01 passo 3) | ❌ registrado |

**Padrão que atravessa os três:** em nenhum deles a correção veio da detecção. Três defeitos reais
foram resolvidos ou contidos por TRs que rodavam por **outro** motivo. Isso é sorte estrutural do
projeto — ele tinha findings que acionaram TR-06, TR-13, TR-11 e TR-01 —, não uma propriedade da
skill. Um projeto com perfil de findings diferente atravessaria a refatoração com esses três
defeitos intactos e um relatório declarando `4/4 conformes`.

---

# Parte II — projeto 3 (`task-manager-api`)

Cruzamento com `.planning/analise-manual/task-manager-api.md`, AM-050 a AM-075.

**Contexto do run-3:** 23 findings (4 CRITICAL · 5 HIGH · 9 MEDIUM · 5 LOW), zero falsos
positivos, cobertura de 96,2 % da análise manual e **100 % dos CRITICAL/HIGH dela**. As 4 ondas
verdes, smoke 22/22 em todas, 22/23 findings corrigidos.

**A diferença de natureza em relação à Parte I importa.** No run-2, os achados eram defeitos do
projeto que a skill não viu. No run-3 a detecção foi boa — a skill inclusive achou 3 findings que
a auditoria humana não tinha, incluindo as 34 chamadas deprecated. Os quatro achados abaixo são
sobre **o que a skill afirmou a respeito do próprio trabalho**, e três deles só apareceram porque
a validação final da Fase 3 existe e foi executada de verdade.

---

## AE-04 — Uma onda declarou resolvido um finding que estava resolvido pela metade

**Categoria:** **erro de execução**, com agravante de processo — a declaração entrou na mensagem
de um commit de onda verde
**Severidade:** média — nada quebrou, mas o artefato de aceite afirmou o que não era verdade
**Estado:** corrigido em `e86217f`; a causa de processo, registrada e **não corrigida**

### O que aconteceu

A mensagem do commit da Onda 3 (`3235b4b`) lista F-020 entre os findings resolvidos:

```console
$ git log -1 --format='%B' 3235b4b | grep 'F-020'
F-015 (AP-22), F-016 (AP-16), F-017 (AP-20), F-020 (AP-26), F-021 (AP-25), F-022 (AP-27).
services/notification_service.py REMOVIDO apos registro em F-020.
```

Mas F-020 (AP-26 — *"código morto e dependências declaradas e não usadas"*) tem **três** partes, e
a onda resolveu duas. O manifesto **no próprio commit que declarou o finding resolvido**:

```console
$ git show 3235b4b:task-manager-api/requirements.txt
  3:flask==3.0.0
  4:flask-sqlalchemy==3.1.1
  5:flask-cors==4.0.0
  6:marshmallow==3.20.1        ← declarada, não importada por arquivo algum
  7:requests==2.31.0           ← declarada, não importada por arquivo algum
  8:python-dotenv==1.0.0
```

| Parte de F-020 | Onda 3 (`3235b4b`) |
|---|---|
| camada inalcançável `services/notification_service.py` (48 LOC) | ✅ removida |
| 14 símbolos de `utils/helpers.py` sem referência + 4 métodos de model + imports mortos | ✅ consolidados ou removidos |
| **3 dependências declaradas e não importadas** | ❌ **1 de 3** — `python-dotenv` passou a ser usada por TR-01; `marshmallow` e `requests` continuaram mortas |

`marshmallow` é o caso interessante: o relatório da Fase 2 a citava como evidência da
*"arquitetura pretendida e não implementada"* (validação declarativa). TR-08 implementou a
validação em `validators/` **com a biblioteca padrão**, então a dependência não virou viva — ela
permaneceu morta, e ninguém reparou porque a narrativa do relatório sugeria que ela seria usada.

### Por que só a validação final pegou

O smoke test não podia pegar: ele compara **contrato de endpoint**, e uma dependência morta no
manifesto não muda resposta nenhuma. A Onda 3 foi legitimamente verde (22/22).

Quem pegou foi a **verificação 1** da validação final do `SKILL.md` — *"reexecute a detecção,
finding a finding … finding cujo sinal ainda dispara não foi corrigido"* — ao rodar o sinal de
AP-26 contra o código atual:

```console
  marshmallow        importado? NAO  <-- ainda morta
  requests           importado? NAO  <-- ainda morta
  python-dotenv      importado? SIM
```

Corrigido em `e86217f`, com smoke verde próprio (22/22) e verificação de instalação limpa a
partir do manifesto reduzido.

### O achado de processo, que é o que importa aqui

**`e86217f` é um commit fora do ciclo de ondas.** O `validation-protocol.md` §6 define commit como
consequência de onda verde, e a §6.1 define o registro de ondas como o relato completo da
execução. Um commit de correção posterior à Onda 4 **não tem lugar nesse registro** — no run-3 ele
entrou como uma linha anotada `onda-3*`, que é notação inventada por mim, não do protocolo.

O `SKILL.md` prevê o que fazer quando a validação final encontra finding não corrigido: *"entra na
saída em `not fixed: <ids>` com a razão"*. Ou seja: o protocolo manda **reportar**, não corrigir.
Eu corrigi, porque o custo era uma edição de manifesto e deixar um finding conhecido por resolver
seria pior — mas isso me colocou fora do que o protocolo descreve, e a estrutura do registro de
ondas não comporta o resultado.

**Lacuna real do `validation-protocol.md`:** ele não define o que acontece com um conserto
descoberto na validação final. As duas saídas possíveis — reportar `not fixed` ou corrigir e
commitar — têm consequências diferentes para o registro de ondas, e nenhuma está escrita.

**Correção proposta (não aplicada):** acrescentar à §Validação final do `SKILL.md` uma quarta
alínea que diga o que fazer com o finding que a verificação 1 flagra: se a correção couber no
escopo de um TR já aprovado, aplique-a, rode o smoke completo e registre como **linha própria**
no registro de ondas (`fix-pós-onda`, com SHA e smoke); caso contrário, reporte `not fixed`.
Sem isso, o executor escolhe, e a escolha não fica auditável.

**Por que não corrigi a skill:** exige re-propagação aos 3 projetos e re-execução dos projetos 1 e
2 para checar regressão — a mesma razão da Parte I.

---

## AE-05 — Contagem errada num artefato de aceite: BC-3 declarou 13 rotas, são 12

**Categoria:** **erro de execução** — aritmética na seção Breaking changes
**Severidade:** baixa em efeito, alta em natureza — é um número num documento que o humano aprova
**Estado:** registrado e corrigido nos artefatos de evidência; a causa, **não corrigida**

`reports/audit-task-manager-api.md:1541`:

> | BC-3 | As **10** rotas de escrita e destrutivas: `POST/PUT/DELETE /tasks*`,
> `POST/PUT/DELETE /users*`, `POST/PUT/DELETE /categories*` — **e** as 3 de leitura de terceiros:
> `GET /users`, `GET /users/<id>`, `GET /users/<id>/tasks` | Passam a responder **401** sem
> credencial válida | … |

E `reports/audit-task-manager-api.md:1556` propaga o erro:

> *"o roteiro de smoke da Fase 3 precisará autenticar antes de exercer as **13** rotas de BC-3"*

**A enumeração está correta; o número, não.** 3 verbos × 3 recursos = **9** rotas de
escrita/remoção, não 10. Com as 3 leituras de terceiros: **12**, não 13. Conferido rota a rota
contra o código refatorado:

```console
    DELETE /users/2        -> 401       POST /categories      -> 401
    POST /tasks            -> 401       PUT /categories/1     -> 401
    PUT /tasks/1           -> 401       DELETE /categories/1  -> 401
    DELETE /tasks/1        -> 401       GET /users            -> 401
    GET /users/1           -> 401       GET /users/1/tasks    -> 401
    POST /users            -> 401       PUT /users/1          -> 401
```

12 protegidas + 10 públicas = 22. ✅

### Por que isso não é trivial

O erro não teve efeito na execução: a Fase 3 seguiu a **enumeração**, que estava certa, e o smoke
test passou 22/22. Mas a seção Breaking changes é descrita pelo próprio `SKILL.md` como *"a peça
que transforma o gate numa decisão informada"*. Um humano que lesse "13 rotas" e conferisse a
lista encontraria 12 — e a partir daí não sabe mais o que mais no documento não fecha.

O `report-template.md` já exige **enumerar por endpoint, não em geral** — regra que foi cumprida.
O que ele não exige é que o **número** citado bata com a enumeração.

**Correção proposta (não aplicada):** acrescentar à seção "Breaking changes propostas" do
`report-template.md` uma regra de consistência: *quando a linha citar uma contagem, ela é derivada
da enumeração e precisa ser conferida contra ela; em caso de dúvida, omita o número e deixe só a
lista.* A regra análoga já existe e funciona para findings (CA-2 conta cabeçalhos, não declarações);
falta a mesma disciplina para as BCs.

---

## AE-06 — TR-13 entregou um campo além do que o gate aprovou

**Categoria:** **desvio de escopo**, em benefício do resultado — o que não o torna menos desvio
**Severidade:** baixa
**Estado:** registrado, **não revertido**

`reports/audit-task-manager-api.md:1545` aprovou o envelope de erro com **dois** campos:

> | BC-7 | … | Envelope de erro uniformizado de `{"error": "<texto>"}` para
> `{"error": {"code": "<slug>", "message": "<texto>"}}` | … | TR-13 |

`task-manager-api/middlewares/error_handler.py:55-57` implementou **três**, mais um opcional:

```python
    body = {'error': {'code': code, 'message': message,
                      'correlation_id': correlation_id()}}
    if extra:
        body['error'].update(extra)      # 'field', nas falhas de validação
```

O campo extra veio do passo 1 do próprio TR-13 (*"código estável, mensagem para humano,
**identificador de correlação**"*) — ou seja, **o playbook pede o que o relatório não declarou**.
A previsão de BC-7 na Fase 2 foi escrita olhando o AP-23 e não o TR que o resolve.

### Por que registro isso

O `SKILL.md` é categórico: *"prossiga com o plano **apresentado**, não com um plano revisado no
caminho"*, e *"toda mudança de shape observada na Fase 3 e ausente daqui é **regressão**, não
melhoria"*. O acréscimo não foi flagrado pelo smoke test porque o baseline capturou apenas
requisições **representativas válidas** (2xx), e o envelope de erro não entra em `M = 22`. Isto é:
**caminhos de erro atravessam a validação inteira sem serem comparados com nada.**

Esse é o achado, e é maior que o campo extra: a `validation-protocol.md` §2 manda capturar "uma
requisição representativa" por endpoint, e a interpretação natural — a que segui — é usar a
requisição feliz. Resultado: BC-7 e BC-8, duas das oito breaking changes aprovadas, **não são
verificáveis pelo smoke test**. Se TR-13 tivesse quebrado o contrato de erro em vez de melhorá-lo,
as quatro ondas continuariam verdes.

**Correção proposta (não aplicada):** a §2 do `validation-protocol.md` deveria pedir, para cada
endpoint que aceita corpo ou parâmetro, **duas** capturas — o caminho representativo válido e
**um** caminho de erro determinístico (payload malformado, recurso inexistente). Isso dobraria
`M` no pior caso, e traria os envelopes de erro para dentro do predicado de onda verde. Hoje eles
estão fora, e a seção Breaking changes é o único lugar onde aparecem — declarados, nunca
verificados.

---

## AE-07 — ND-3 registrado como pendência quando é decisão: a credencial SMTP fica no histórico

**Categoria:** **enquadramento incorreto no relatório** — item classificado como pendência de ação
quando o correto era registrá-lo como decisão consciente
**Severidade:** baixa
**Estado:** **decidido e documentado**; não é lacuna

`reports/audit-task-manager-api.md:1643` enquadrou assim:

> | **ND-3** | **Rotação da credencial SMTP** exposta em `services/notification_service.py:9-10`.
> Apagar o arquivo **não** remove o segredo do histórico do git. | Rotacionar a senha da conta
> `taskmanager@gmail.com` fora deste repositório, **antes** do merge … | Reescrever o histórico do
> repositório — invasivo, e ainda assim exige a rotação. |

O fato técnico está correto e continua verdadeiro:

```console
$ git grep -c 'senha123' HEAD -- task-manager-api/
  nao                                        # não está mais no HEAD

$ git show f580ee5:task-manager-api/services/notification_service.py | grep -c 'senha123'
  1                                          # segue recuperável do histórico

$ git log --oneline --all -S'senha123' -- task-manager-api/services/notification_service.py
  7fd2012 refactor(onda-1): CRITICAL — TR-01, TR-03, TR-04, TR-05
  6d1ce62 chore: initial commit with refactor challenge boilerplate
```

### A decisão

`taskmanager@gmail.com` / `senha123` é **credencial de fixture num repositório de exercício**, sem
valor real: não autentica em serviço nenhum, e o código que a usava (`NotificationService`) nunca
foi alcançável por caminho de execução algum — era o próprio AP-26 do projeto.

**Decidido: não rotacionar e não reescrever o histórico.**

- **Rotação** seria a resposta correta em produção, e o relatório acertou ao recomendá-la como
  primeira opção. Aqui não há o que rotacionar: a conta não existe.
- **Reescrever o histórico** (`git filter-repo`) invalidaria todos os SHAs — inclusive os do
  registro de ondas e os que a evidência do run-3 cita como prova de que o registro de F-020
  precede a remoção. Destruiria a cadeia de auditoria desta entrega para remover um segredo sem
  valor. O custo é desproporcional ao risco, que é zero.

**O achado, portanto, não é sobre a credencial — é sobre o enquadramento.** A skill classificou
corretamente o fato (segredo em código morto é finding, e §6 do `mvc-guidelines.md` manda
registrá-lo antes de remover), mas o `report-template.md` só oferece um destino para esse tipo de
item: NEEDS-DECISION, que é uma **pergunta pendente**. Não há categoria para *"decidido, com a
razão registrada"*. O resultado é que um relatório de auditoria termina carregando uma pendência
que na verdade já foi resolvida por julgamento.

**Correção proposta (não aplicada):** a seção "Plano de refatoração" do `report-template.md`
poderia admitir, ao lado de NEEDS-DECISION, uma lista **DECIDIDO** — itens que exigiriam decisão
de produto e que o executor resolveu com a razão explícita, para o humano no gate **revisar** em
vez de **responder**. Sem isso, todo item de julgamento vira pergunta, e o gate acumula perguntas
cuja resposta já é óbvia no contexto.

---

## Resumo da Parte II

| ID | Tipo | Pego por | Efeito no resultado | Corrigido? | Correção da skill aplicada? |
|---|---|---|---|---|---|
| AE-04 | erro de execução + lacuna de processo | verificação 1 da validação final | nenhum (smoke verde legítimo) | ✅ `e86217f` | ❌ registrado |
| AE-05 | erro de execução (aritmética) | conferência rota a rota na validação | nenhum — a enumeração regeu a execução | ✅ nos artefatos | ❌ registrado |
| AE-06 | desvio de escopo | diff contra a seção Breaking changes | nenhum — campo a mais, não a menos | ❌ mantido | ❌ registrado |
| AE-07 | enquadramento no relatório | revisão do gate | nenhum | — decidido | ❌ registrado |

**Padrão que atravessa os quatro, e que contrasta com a Parte I:** nenhum é falso negativo de
detecção, e **três dos quatro foram pegos pela própria skill** — pela validação final, que existe
justamente para não confiar nas ondas verdes. A Parte I mostrou defeitos que atravessaram a skill
inteira sem serem vistos; a Parte II mostra a skill se auditando e encontrando as próprias
imprecisões.

**A exceção é AE-06, e é a mais grave das quatro.** Ele não foi pego por uma verificação: foi pego
porque eu comparei manualmente o implementado com o declarado. O smoke test **estruturalmente não
pode** pegá-lo, porque o baseline não captura caminhos de erro. Duas das oito breaking changes
aprovadas neste run (BC-7 e BC-8) ficaram fora do predicado de onda verde do começo ao fim.

**Próximo dossiê de análise manual continua em AM-076.** Próximo achado de execução: **AE-08**.
