# Validation Protocol — boot, baseline, ondas e rollback

Lido **duas vezes**: no fim da Fase 1, para capturar o baseline; e ao fim de **cada onda** da
Fase 3, para decidir entre commit e rollback.

Princípio único deste arquivo, do qual tudo o mais deriva:

> **Commit é consequência de evidência de execução, nunca um passo autônomo.** Um commit de
> onda declarado verde sem o smoke test ter rodado envenena toda a cadeia de rollback: o
> "último commit verde" deixa de ser verde, e o `reset` passa a restaurar código quebrado.

---

## 1. Descobrir o comando de boot

Precedência, do mais confiável ao menos:

1. **Script de execução declarado no manifesto** — é a intenção registrada do autor.
2. **Entry point declarado** no manifesto ou em configuração de empacotamento.
3. **Convenção da stack detectada** aplicada ao arquivo que instancia o servidor.
4. **Instrução no README do projeto** — última opção: costuma estar desatualizada, então
   confirme que o arquivo citado existe antes de usá-la.

Registre o comando escolhido e a fonte. Se dois candidatos discordarem, teste o do manifesto
primeiro; se ele falhar já no estado inicial, isso é finding, não obstáculo.

Capture também: porta, host de bind e variáveis de ambiente necessárias. Depois de TR-01 a
aplicação passa a falhar no boot sem as variáveis obrigatórias — comportamento correto que
parece regressão se o ambiente de validação não as tiver.

---

## 2. Capturar o baseline (fim da Fase 1)

Execute **antes de qualquer escrita em código do projeto**, com o código intocado.

1. Suba a aplicação com o comando descoberto na §1.
2. Para **cada** endpoint da tabela da Fase 1, envie uma requisição representativa e registre:
   **status code**, **shape do corpo** (chaves e tipos, não os valores voláteis) e um resumo do
   corpo. Para rotas com parâmetro, use um identificador que exista.
3. Trate as rotas destrutivas por último e, quando possível, contra dado descartável. Um smoke
   test que apaga a base destrói o insumo das verificações seguintes.
4. Registre o SHA do commit de baseline como a primeira linha do registro de ondas da §6.1.

**Grave o baseline em `BASELINE_PATH`** — o caminho resolvido nas pré-condições, ancorado na raiz
do repositório. Um registro por endpoint, com método, path, status code e shape do corpo: é o
formato mínimo que os critérios 3 e 4 da §4 conseguem comparar. Contagem não serve — dois
inteiros não reconstroem um contrato.

```console
$ cat "<BASELINE_PATH>"
[
  {"method":"GET",  "path":"/<collection>",      "status":200, "shape":{"items":"array","total":"number"}},
  {"method":"GET",  "path":"/<collection>/<id>", "status":200, "shape":{"id":"number","name":"string"}},
  {"method":"POST", "path":"/<collection>",      "status":201, "shape":{"id":"number"}, "note":"destructive-adjacent, ran last"}
]
```

O baseline persistido é a **segunda exceção** à regra de não-escrita da Fase 1, pela mesma razão
do relatório: artefato novo e aditivo, nenhum arquivo do projeto tocado. A razão de existir é o
gate — o ponto do fluxo desenhado para pausar, e portanto o mais provável de atravessar uma
quebra de sessão. Baseline em memória de trabalho não sobrevive a ela, e sem baseline a Fase 3
perde o único critério que a torna falsificável.

Reproduza-o no relatório da Fase 2 na forma resumida que o `report-template.md` define — contagem
por método e por status, mais o total `M`. Sem isso, o humano no gate não tem como saber o que a
Fase 3 promete preservar.

Endpoint que já falha no baseline **não é regressão da Fase 3**. Marque-o como
*pré-existente quebrado* agora; depois será tarde para provar que já estava assim.

---

## 3. Definir "subiu com sucesso" sem depender de framework

Nunca use string de log de um framework específico como critério — ela muda de versão para
versão e não existe em outra stack. Use evidência observável, na ordem:

1. **A porta está escutando** após o comando de boot.
2. **O processo continua vivo** alguns segundos depois de subir — a falha mais comum é subir,
   estourar exceção de import e morrer, o que um teste instantâneo não pega.
3. **A primeira requisição é respondida**, com qualquer status. Um 404 prova que o servidor
   está de pé; uma conexão recusada prova que não está.

Um boot que satisfaz (1) e não (2) é falha, não sucesso lento: espere e reconfirme antes de
concluir.

Ao encerrar, derrube o processo. Um servidor esquecido segurando a porta faz o boot seguinte
falhar por motivo que não é o código — o falso vermelho mais frequente desta skill.

---

## 4. Executar o smoke test contra o baseline

Reenvie as mesmas requisições da §2 e compare **na ordem** abaixo. A ordem importa porque cada
critério é mais forte que o seguinte:

| # | Critério | Divergência significa |
|---|---|---|
| 1 | O endpoint existe (não é 404 novo) | **Vermelho.** Rota perdida na refatoração. |
| 2 | Método e path idênticos | **Vermelho.** Superfície alterada — proibido. |
| 3 | Status code idêntico ao do baseline | **Vermelho**, salvo se declarado em Breaking changes. |
| 4 | Shape do corpo idêntico | **Vermelho**, salvo se declarado em Breaking changes. |
| 5 | Valores não-voláteis coerentes | **Vermelho**, salvo se você nomear o dado de teste que o próprio smoke test alterou. Divergência não explicada é vermelha. |

Diferenças esperadas e **não** contabilizadas como vermelho: timestamps, identificadores
gerados, ordem de coleção quando o baseline também não a garante, e o 401/403 que TR-05
introduz nas rotas que o relatório declarou como passando a exigir autenticação.

Registre o resultado como uma contagem explícita: `N/M endpoints conformes`. Essa contagem é
requisito da mensagem de commit (§6) e alimenta o predicado da §4.1.

### 4.1 Definição de "onda verde"

Esta é a **única** definição do predicado em todo o pacote. Os demais arquivos referenciam esta
seção; nenhum a reformula.

> **Onda verde ⇔ os `M` endpoints do baseline estão conformes nos cinco critérios acima**, sendo
> `M` o total capturado na §2. Contam como conformes as divergências que a seção Breaking changes
> aprovada no gate declara — e só elas.

Quatro consequências, todas deliberadas:

- **Fração parcial não é verde.** `N < M` é vermelho, sem exceção e sem "verde com ressalva". O
  predicado é binário porque governa a escolha entre `commit` e `git reset --hard`; um predicado
  gradiente nessa posição transforma o histórico numa cadeia de pontos de retorno de
  confiabilidade desconhecida, que é exatamente o que o princípio no topo deste arquivo proíbe.
- **Endpoint não enumerável não reduz `M`.** O que nunca entrou no baseline não é comparável, e o
  relatório da Fase 2 já declarou a lacuna (`project-analysis.md` §9). Mas o que **está** no
  baseline e não pôde ser exercido agora é vermelho: baseline capturado é promessa feita.
- **Endpoint *pré-existente quebrado* (§2) entra em `M` e conta como conforme** quando reproduz a
  mesma falha do baseline. Ele faz parte do contrato; o contrato é que ele falha.
- **Divergência declarada em Breaking changes é conforme; a não declarada é vermelha**, mesmo que
  o resultado pareça melhor. O critério é conformidade com o aprovado, não gosto do executor.

Numa onda verde, `N = M` por definição. A fração existe na mensagem de commit para que o número
seja auditável, não para admitir resultado parcial.

### 4.2 Os três estados de onda

Toda onda termina em **exatamente um** destes estados, cada um com marcador próprio:

| Estado | Marcador | Significado | Commit | Linha no registro (§6.1) |
|---|---|---|---|---|
| **verde** | `✓` | Executou e o smoke test conformou (`M/M`, §4.1) | sim | `green`, com SHA |
| **vazia** | `—` | O plano não atribui TR algum a esta onda: nada aplicado, nada validado | não | `empty`, sem SHA |
| **vermelha** | `✗` | Executou e falhou — smoke test divergente, ou boot que não se recuperou | não | `RED`, sem SHA |

> **Onda vazia ⇔ o plano de refatoração aprovado no gate não atribui nenhum TR a esta onda.**

O critério é o **plano**, nunca a severidade. Ausência de finding daquela severidade é a causa
típica de uma onda vazia, não a sua definição — e as duas coisas divergem: um TR pode ser
atribuído a uma onda cuja severidade não tem finding algum, porque a onda de um TR é a onda do
finding que o aciona (`SKILL.md`, "Ondas"). Definir vazia pela severidade faria essa onda ser
pulada com um TR agendado dentro dela — tipicamente o TR-06 que constrói o esqueleto MVC, cuja
ausência nenhum smoke test detecta, porque smoke test compara contrato de endpoint e não estrutura.

**Onda vazia não é onda verde.** Nada foi aplicado, logo nada foi validado: não existe evidência
de execução, e o princípio no topo deste arquivo proíbe declarar verde o que não rodou. Marcar
`✓` uma onda vazia é falso positivo num artefato que vira evidência de critério de aceite.

Uma onda vazia, portanto, **não gera commit** e **não entra no registro como linha `green`**. Ela
consta como `empty` para que o registro continue sendo o relato completo da execução, e o alvo de
rollback segue sendo a última linha `green` — a última onda **efetivamente** verde, que pode ser
uma onda anterior ou o próprio baseline.

---

## 5. Cadência da Fase 3

Quatro ondas; protocolo idêntico em todas as que o plano preencheu (as vazias pulam, §4.2):

```text
Onda N
  ├─ para cada TR da onda:
  │     aplicar o TR  →  BOOT
  │        ├─ verde     →  próximo TR
  │        └─ vermelho  →  conserte (máx. 2 tentativas)
  │              └─ não recuperou  →  ONDA VERMELHA, com o TR já isolado ─┐
  └─ ao fim da onda:  SMOKE TEST completo contra o baseline               │
        ├─ verde (§4.1: M/M)  →  commit  →  anote o SHA (§6.1)  →  próxima onda
        └─ vermelho  ←──────────────────────────────────────────────────┘
              └─ git reset --hard <última linha green do registro §6.1>  →  PARE E REPORTE
```

**Por que boot por TR e smoke por onda.** O smoke test completo é caro; o boot é barato. Boot
após cada TR localiza o defeito **no TR** em vez de na onda inteira — a diferença entre
consertar uma mudança e investigar seis. Isso importa mais na Onda 1, que concentra o esqueleto
MVC e todos os CRITICAL, e é a que tem maior chance de terminar vermelha.

**Não tente a onda seguinte sobre uma base não validada.** É tentador seguir e "consertar
depois"; o resultado é uma pilha de mudanças não bootáveis cuja depuração custa mais que toda a
refatoração.

---

## 6. Commit da onda

Só existe depois do smoke test verde. A mensagem cita a evidência:

```console
$ git commit -m "refactor(onda-1): CRITICAL — TR-01, TR-06, TR-02, TR-04, TR-05, TR-14

Smoke test: 15/15 endpoints conformes ao baseline.
Breaking changes aplicadas: <lista da seção aprovada no gate>."
```

Sem a contagem de endpoints verificados, **não há commit** — o número é o que distingue uma
onda validada de uma onda declarada validada. A contagem de um commit de onda é sempre `M/M`
(§4.1); se o que você tem nas mãos é uma fração menor, não é um commit de onda, é uma onda
vermelha ainda não reportada.

### 6.1 Registro de ondas

Mantenha na resposta ao usuário, atualizado a cada evento, um registro de quatro colunas. É ele
que torna o alvo do rollback um **dado registrado**, e não uma dedução feita sob pressão:

```console
| stage    | sha       | smoke  | status |
|----------|-----------|--------|--------|
| baseline | <sha>     | —      | green  |
| onda-1   | <sha>     | 15/15  | green  |
| onda-2   | —         | —      | empty  |
| onda-3   | —         | 12/15  | RED    |
```

`empty` é linha de relato, não ponto de retorno: só `green` é alvo de rollback (§4.2).

Escreva a linha do baseline nas pré-condições, antes da Fase 1. Escreva a linha de cada onda
imediatamente após o commit, colando o SHA que o `git commit` devolveu — não no fim da fase, não
de memória.

**Se o registro se perder** — ele vive na resposta ao usuário, e a Fase 3 é longa o bastante para
atravessar uma quebra de sessão —, **reconstrua-o do log antes de qualquer decisão de rollback, e
diga que reconstruiu.** A convenção de mensagem da §6 existe para isso:

```console
$ git log --oneline --grep '^refactor(onda-'    # ondas commitadas, da mais recente à mais antiga
```

Todo commit dessa convenção é uma onda verde por construção (§6 não admite commit sem smoke test
verde), e a linha `Smoke test: N/M` da mensagem devolve a coluna `smoke`. O que **não** se recupera
do log é a onda vazia e a vermelha — nenhuma das duas gera commit —, e nenhuma das duas é alvo de
rollback. O alvo, portanto, sobrevive à perda do registro: é o commit mais recente da convenção,
ou o baseline se não houver nenhum.

> **O último commit verde é a última linha `green` deste registro, sempre.** O baseline ocupa
> essa posição apenas enquanto for a única linha verde, isto é, enquanto a Onda 1 não tiver
> commitado.

---

## 7. Rollback

Onda vermelha — pelo smoke test da §4, ou pelo boot que não se recuperou no meio da onda
(`SKILL.md`, protocolo de onda, passo 2):

```console
$ git reset --hard <sha of the last green row in the wave registry>
```

O alvo é **sempre** a última linha `green` do registro da §6.1, nunca o baseline por default. O
baseline é o alvo em exatamente um caso: quando a **Onda 1** é a que falha, porque aí ele é a
única linha verde que existe. Depois do commit da Onda 1, resetar para o baseline destrói
trabalho verde já validado — o erro mais caro possível neste ponto, e o mais fácil de cometer,
porque o SHA do baseline é o que está mais à mão.

Quando é a Onda 1 que falha, o reset descarta todo o trabalho da sessão. É o custo aceito do
histórico linear, e a razão de o boot por TR existir.

Depois do reset, **pare**. Não retome, não tente uma variante, não pule para a próxima onda.
Reporte:

- Qual onda ficou vermelha e por quê: o critério da §4 que divergiu, ou o TR cujo boot não se
  recuperou nas duas tentativas.
- Qual TR é o suspeito, com a evidência que aponta para ele (tipicamente o último boot verde).
- O SHA para onde o repositório voltou e o que sobreviveu — as ondas anteriores continuam
  commitadas e válidas.
- O que seria preciso investigar para retomar.

Sucesso parcial relatado como sucesso é a falha mais grave possível nesta fase, porque remove
do humano a informação de que existe trabalho pendente.

---

## 8. Falsos vermelhos conhecidos

Verifique estes antes de declarar uma onda vermelha; todos já foram causados pela própria
validação e não pelo código:

| Sintoma | Causa provável |
|---|---|
| Boot falha logo após TR-01 | Variável de ambiente obrigatória não definida no ambiente local. |
| Porta ocupada / conexão recusada | Processo de um boot anterior ainda vivo. |
| Endpoint de autenticação estoura o tempo | Derivação lenta de TR-03 funcionando como deveria; o timeout do roteiro é que é curto. |
| Rotas protegidas respondem 401 | TR-05 aplicado; o roteiro de smoke precisa autenticar antes. |
| Migração falha ao criar constraint | Dados preexistentes violam a regra que nunca existiu (TR-16). É finding de dados, não defeito do código novo. |
| Coleção com ordem diferente | Junção de TR-11 sem cláusula de ordenação; o baseline também não a garante. |
