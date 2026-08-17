# 04 — Achados de execução · projeto 2 (`ecommerce-api-legacy`)

Achados sobre **a skill**, produzidos executando-a às cegas num projeto novo (run-2) e cruzando o
resultado com a análise manual prévia (`.planning/analise-manual/ecommerce-api-legacy.md`,
AM-028 a AM-049).

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

## Resumo

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

**Próximo dossiê de análise manual continua em AM-050.** Próximo achado de execução: **AE-04**.
