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

Execute **antes de qualquer escrita**, com o código intocado.

1. Suba a aplicação com o comando descoberto na §1.
2. Para **cada** endpoint da tabela da Fase 1, envie uma requisição representativa e registre:
   **status code**, **shape do corpo** (chaves e tipos, não os valores voláteis) e um resumo do
   corpo. Para rotas com parâmetro, use um identificador que exista.
3. Trate as rotas destrutivas por último e, quando possível, contra dado descartável. Um smoke
   test que apaga a base destrói o insumo das verificações seguintes.
4. Registre o SHA do commit de baseline. Ele é o ponto de retorno de última instância.

Guarde o baseline em memória de trabalho e reproduza-o no relatório da Fase 2 em forma
resumida — contagem por método e por status. Sem isso, o humano no gate não tem como saber o
que a Fase 3 promete preservar.

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
| 5 | Valores não-voláteis coerentes | Investigue: pode ser dado de teste, pode ser defeito. |

Diferenças esperadas e **não** contabilizadas como vermelho: timestamps, identificadores
gerados, ordem de coleção quando o baseline também não a garante, e o 401/403 que TR-05
introduz nas rotas que o relatório declarou como passando a exigir autenticação.

Registre o resultado como uma contagem explícita: `N/M endpoints conformes`. Essa contagem é
requisito da mensagem de commit — ver §6.

---

## 5. Cadência da Fase 3

Quatro ondas, protocolo idêntico em todas:

```text
Onda N
  ├─ para cada TR da onda:
  │     aplicar o TR  →  BOOT  →  vermelho? conserte antes do próximo TR
  └─ ao fim da onda:  SMOKE TEST completo contra o baseline
        ├─ verde     →  commit  →  próxima onda
        └─ vermelho  →  git reset --hard <último commit verde>  →  PARE E REPORTE
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
onda validada de uma onda declarada validada. Se a contagem for parcial porque alguns endpoints
não são enumeráveis, escreva a fração real e o motivo.

---

## 7. Rollback

Onda vermelha:

```console
$ git reset --hard <SHA do último commit verde>
```

Na Onda 1, o último commit verde é o **commit de baseline** — o reset descarta todo o trabalho
da sessão. É o custo aceito do histórico linear, e a razão de o boot por TR existir.

Depois do reset, **pare**. Não retome, não tente uma variante, não pule para a próxima onda.
Reporte:

- Qual onda ficou vermelha e em qual critério da §4.
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
