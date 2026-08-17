# Report Template — relatório de auditoria da Fase 2

Estrutura literal do artefato gravado em `REPORT_PATH`, resolvido nas pré-condições do
`SKILL.md`: o caminho passado pelo invocador, ou o default ancorado na raiz do repositório.

Gravar este arquivo é **uma das duas** escritas permitidas antes do gate — a outra é o baseline
em `BASELINE_PATH` (`SKILL.md`, pré-condições): ambos são artefato novo e aditivo, não modificação
do projeto. Nenhum arquivo de código, manifesto, configuração ou diretório é criado, movido ou
alterado antes do `y`.

## Regras de preenchimento

- **Ordenação:** CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, ordene por
  quantidade de ocorrências, decrescente — o finding que aparece em toda parte vem antes.
- **Numeração:** `F-001` em diante, **contínua através das severidades**, na ordem final do
  documento. Não reinicie a contagem por seção; o número é a referência estável usada no plano
  de refatoração e nas mensagens de commit.
- **Um finding por causa, não por ocorrência.** O mesmo defeito em 18 lugares é um finding com
  18 ocorrências listadas — não 18 findings. Inflar a contagem por repetição é a forma mais
  fácil de destruir a credibilidade do relatório.
- **Evidência literal obrigatória.** Sem `arquivo:linha` + bloco de código real copiado do
  projeto, o finding é descartado. Não o inclua com ressalva.
- **Confiança** declarada por finding: ALTA quando a evidência é autossuficiente; MÉDIA quando
  depende de uma inferência que você nomeia; nunca reporte com confiança BAIXA — investigue
  mais ou descarte.
- **Baseline resumido obrigatório.** A seção "Baseline de comportamento" traz a contagem por
  método e por status e o total `M`, e cita o caminho absoluto de `BASELINE_PATH`. É o que
  permite ao humano no gate saber o que a Fase 3 promete preservar — e `M` é o denominador de
  toda onda (`validation-protocol.md` §4.1).
- **Idioma:** português no texto, inglês nos nomes técnicos e nos blocos de console.

---

## Esqueleto do documento

````markdown
# Auditoria de Arquitetura — `<nome-do-projeto>`

> Fase 2 de `/refactor-arch`. Auditoria somente leitura. Nenhum arquivo do projeto foi
> modificado. Todo `arquivo:linha` foi obtido por leitura direta nesta execução.

## Contexto

| Item | Valor |
|---|---|
| Linguagem | <linguagem> (runtime do ambiente: <versão real>) |
| Framework | <framework e versão> |
| Persistência | <driver/ORM, banco, nº de tabelas> |
| Domínio | <uma frase> |
| Arquivos-fonte / LOC | <n> arquivos, <n> linhas |
| Endpoints | <n> — baseline capturado em <n> respostas |
| Commit de baseline | `<SHA curto>` |

### Arquitetura efetiva

<Um parágrafo descrevendo o grafo de resolução a partir dos entry points, nomeando o mecanismo
que a stack usa para resolver: que responsabilidade cada módulo alcançável acumula, e quais
camadas nominais são inalcançáveis. Descreva o que o código faz, não o que os nomes de diretório
sugerem — e não confunda "não importado" com "não alcançável".>

### Baseline de comportamento

| Método | Endpoints | Status codes observados |
|---|---|---|
| GET | <n> | 200 ×<n> · 404 ×<n> |
| POST | <n> | 201 ×<n> · 400 ×<n> |
| <…> | <n> | <…> |
| **Total (`M`)** | **<M>** | — |

Baseline completo, com media type e forma do corpo por endpoint, em `<BASELINE_PATH absoluto>`.
Pré-existentes quebrados: <lista `método path → status`, ou "nenhum">.
Não enumeráveis, fora de `M`: <lista e motivo, ou "nenhum">.

`M` é o denominador de toda onda da Fase 3: onda verde exige `M/M` conformes.

## Sumário

| Severidade | Findings | Ocorrências |
|---|---|---|
| CRITICAL | <n> | <n> |
| HIGH | <n> | <n> |
| MEDIUM | <n> | <n> |
| LOW | <n> | <n> |
| **Total** | **<n>** | **<n>** |

## Findings

<blocos, na ordem definida acima>

## O que não foi encontrado

<uma linha por categoria nomeada da escala que foi verificada e não produziu finding>

## Breaking changes propostas

<tabela; vazia é resposta válida e deve ser dita explicitamente>

## Plano de refatoração

<tabela por onda>

## Fora do escopo desta skill

<lista curta: o que foi observado, é real, e a skill não vai corrigir>

## Próximo passo

<prompt do gate>
````

---

## Bloco de finding

````markdown
### [CRITICAL] F-001 — <título curto, descreve o defeito e não o sintoma>

- **Anti-pattern:** AP-01 · **Transformação:** TR-02 · **Onda:** 1
- **Arquivo:** `<caminho>:<linha ou faixa>`
- **Evidência:**

```<linguagem>
<bloco literal copiado do projeto, curto o bastante para caber na tela>
```

- **Descrição:** <o que o código faz, estruturalmente. Cite as demais ocorrências como lista de
  `arquivo:linha` — sem repeti-las como findings separados.>
- **Impacto:** <consequência concreta e alcançável, com o caminho que a produz. "É inseguro"
  não é impacto; "um chamador anônimo lê a tabela inteira via <caminho>" é.>
- **Correção esperada:** <o estado final, em uma frase. O detalhe do como está no TR.>
- **Confiança:** ALTA | MÉDIA
````

Quando a severidade atribuída divergir da tabelada no catálogo, acrescente uma linha
`- **Desvio de severidade:** <motivo>`. Severidade sem justificativa é opinião.

---

## Seção "o que não foi encontrado"

Existe para tornar a auditoria falsificável. Sem ela, um relatório com 20 findings e um
relatório que reporta os 28 APs por reflexo são indistinguíveis para quem lê.

Escreva uma linha por AP que **não produziu finding**, em um dos três estados definidos em
`antipattern-catalog.md` ("Como usar cada entrada"), e **nomeie o estado na linha**:

- **não encontrado** — o AP se aplica à stack, o sinal foi respondido e a resposta foi "não".
- **não aplicável** — os fatos da Fase 1 não satisfazem o escopo da coluna `Aplica a` do AP.
  Diga qual fato o exclui.
- **não verificável** — o AP se aplica, mas falta um fato da Fase 1 para responder o sinal.
  Nunca colapse este estado em "não encontrado": ausência de verificação não é ausência de defeito.

Ao fim, cada um dos 28 APs do catálogo está em findings ou em um destes três estados. Não liste
categoria que não seja um AP do catálogo.

````markdown
- **Mass assignment (AP-14) — não encontrado:** os caminhos de escrita atribuem campo a campo,
  com allowlist implícita pela própria assinatura.
- **Rate limiting (AP-24) — não aplicável:** não há autenticação a proteger no estado atual, e o
  escopo do AP é "APIs com autenticação". Como não existe finding de AP-24, ele **não agenda TR
  algum**: o controle de taxa entra como parte de TR-05, na onda do finding que de fato aciona
  esse TR — aqui, F-00X (AP-05, CRITICAL, Onda 1).
- **Deprecated API (AP-16) — não encontrado:** verificado contra o runtime <versão real> do
  ambiente; nenhuma chamada deprecated nos caminhos alcançáveis.
````

A terceira linha é o modelo a seguir para AP-16: cite a versão contra a qual você verificou.
"Não encontrado" sem a versão não prova nada.

---

## Seção "Breaking changes propostas"

A peça que transforma o gate numa decisão informada. Preencha-a **prevendo** o efeito de cada
TR do plano sobre o contrato de resposta, antes de executá-lo.

Path, verbo e status code de sucesso são preservados por regra. O que entra aqui é mudança de
**forma do corpo** ou do **media type**, mudança de status para um mesmo cenário, e remoção de
endpoint.

````markdown
| # | Endpoint | Mudança | Motivo | TR |
|---|---|---|---|---|
| BC-1 | `POST /<recurso>` | O campo de credencial deixa de constar da resposta | Credencial não atravessa a fronteira de saída | TR-04 |
| BC-2 | `GET /<coleção>` | Resposta passa a trazer no máximo <n> itens por página | Tamanho da resposta deixa de ser função dos dados | TR-17 |
| BC-3 | `<método> /<rota privilegiada>` | Passa a responder 401 sem credencial | Rota destrutiva sem verificação de identidade | TR-05 |
| BC-4 | `<método> /<rota>` | Endpoint removido | Executa entrada arbitrária contra o banco | TR-02 |
| BC-5 | todos | Envelope de erro uniformizado para `{"error":{"code","message"}}` | Contrato de erro divergente entre handlers | TR-13 |
````

Regras:

- **Enumere por endpoint, não em geral.** "Os erros mudam de formato" não permite ao humano
  avaliar o impacto; a linha BC-5 acima só é aceitável acompanhada da lista de endpoints
  afetados quando eles não forem todos.
- **Nenhuma breaking change é resposta válida** — escreva "Nenhuma. Todos os contratos de
  resposta são preservados." Deixar a seção vazia é ambíguo.
- Toda mudança de shape observada na Fase 3 e ausente daqui é **regressão**, não melhoria.

---

## Seção "Plano de refatoração"

Agrupado por onda, porque é assim que a Fase 3 executa e é assim que o gate aprova.

````markdown
### Onda 1 — CRITICAL
| TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
|---|---|---|---|---|
| TR-01 | F-003 | `config/…` , `.env.example` | `<entry point>` | — |
| TR-06 | F-001, F-006 | `repositories/…`, `services/…`, `controllers/…`, `routes/…` | todos | — |
````

Repita para cada onda que recebeu TR. Onda sem TR atribuído entra como `Onda N — vazia, nenhum
TR`: é o que torna o plano uma partição verificável no gate. Ao fim, uma linha por onda com TR e o
critério de aceite: `smoke test <n>/<n> endpoints conformes → commit`.

**Itens NEEDS-DECISION.** Liste separadamente o que exige decisão de produto e que a skill não
decide sozinha — política de senha, retenção de dados pessoais, remoção de funcionalidade.
Cada item traz a opção recomendada e a alternativa, para que um único `y` continue sendo
suficiente.

---

## Rodapé e prompt do gate

O relatório termina exatamente assim, e o agente reproduz o mesmo prompt no console:

````markdown
## Próximo passo

Total: **<n> findings** (<n> CRITICAL · <n> HIGH · <n> MEDIUM · <n> LOW) ·
**<n> breaking changes** propostas · plano em **<n> ondas com TR** (vazias: <lista ou "nenhuma">).

Nenhum arquivo do projeto foi modificado até aqui.

    Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````
