# Project Analysis — heurísticas da Fase 1

Arquivo da **Fase 1**, lido integralmente. Nenhum passo aqui escreve em disco.

O produto desta fase são **oito fatos** que as fases seguintes consomem. Se um deles ficar
indeterminado, diga qual e por quê — um fato inventado na Fase 1 contamina a auditoria inteira,
e o caso mais caro é a versão de runtime, de que AP-16 depende.

| # | Fato | Consumido por |
|---|---|---|
| 1 | Linguagem dominante | Escolha de idioma em toda a Fase 3 |
| 2 | Framework efetivo | Variante de árvore, manifestações por stack |
| 3 | Versão **real** do runtime | AP-16, TR-12 |
| 4 | Mecanismo de persistência | AP-01, AP-11, AP-15, AP-21 |
| 5 | Domínio de negócio | Nomes de agregado, granularidade de controller |
| 6 | Arquitetura **efetiva** | AP-06, AP-09, AP-13, AP-17, regra de alcançabilidade |
| 7 | Inventário de endpoints | Plano de refatoração, smoke test |
| 8 | Baseline de comportamento | Validação de toda a Fase 3 |

---

## 0. Ordem de leitura eficiente

Não leia o projeto inteiro antes de pensar. A ordem abaixo maximiza informação por arquivo lido:

1. **Manifesto de dependências** — declara stack, versões e scripts em poucas linhas.
2. **Listagem recursiva de arquivos**, com tamanho — revela o entry point e a god class antes
   de qualquer leitura de conteúdo.
3. **Entry points e configuração de carregamento** — de onde parte o grafo de resolução (§6).
4. **Arquivos por tamanho decrescente** — concentração de linhas é concentração de decisão.
5. **Arquivos de definição de schema ou migração**.

Projetos pequenos cabem inteiros no contexto; leia tudo quando couber. Projetos grandes: pare de
ler quando os oito fatos estiverem determinados e as rotas todas inventariadas.

---

## 1. Linguagem dominante

Cruze **duas** fontes, porque cada uma sozinha erra:

- **Extensões dominantes** por contagem de arquivos e de linhas, ignorando diretórios de
  dependências instaladas, artefatos de build e VCS.
- **Manifesto presente** na raiz.

Divergência entre as duas é informação, não ruído: um manifesto de uma linguagem com maioria de
arquivos de outra costuma indicar ferramentaria numa e aplicação noutra. Nesse caso, a
linguagem da aplicação é a que contém o entry point.

Registre também as linguagens secundárias com presença relevante — elas aparecem depois como
scripts de banco ou de build, e a Fase 3 precisa saber que existem.

---

## 2. Framework efetivo

> **Framework efetivo = declarado no manifesto ∩ resolvido por algum arquivo alcançável** (§6:
> alcançável é o que o mecanismo de resolução da stack carrega, não só o que alguém importa).

Os dois lados isolados enganam:

- **Declarado e não resolvido** → não é a stack. É candidato a AP-26, e frequentemente revela a
  arquitetura *pretendida e não implementada* — sinal de alto valor para a Fase 2.
- **Importado e não declarado** → dependência implícita. A aplicação depende de algo que a
  instalação limpa não traz; registre como risco de reprodutibilidade.

Quando não houver manifesto, derive o framework das assinaturas de import do entry point e diga
explicitamente que a stack foi inferida sem manifesto.

Registre a **versão** de cada dependência relevante como declarada e, quando o ambiente
permitir, como instalada. A diferença entre as duas importa para AP-16 e AP-28.

---

## 3. Versão real do runtime

Este é o fato que mais frequentemente se erra, e o erro é silencioso.

> **Obtenha a versão executando o runtime do ambiente. Nunca a leia do manifesto.**

```console
$ python3 --version
$ node --version
$ java -version
$ ruby --version
$ php --version
$ go version
```

Motivo: um projeto que não declara versão alguma é exatamente o que mais acumula chamadas
deprecated, e checar contra uma versão presumida produz falso negativo em AP-16 — o único AP
que o enunciado da tarefa exige nominalmente.

Registre as três coisas quando divergirem: versão do ambiente, versão declarada no manifesto,
versão exigida pelas dependências. Se o runtime não estiver disponível no ambiente, diga isso e
marque AP-16 como **não verificável nesta execução** em vez de reportar ausência de findings.

---

## 4. Mecanismo de persistência

Cruze quatro sinais:

| Sinal | O que revela |
|---|---|
| Driver ou ORM no manifesto | O mecanismo pretendido |
| Import efetivo do driver | O mecanismo real, e onde ele é tocado |
| DDL no repositório (migração, script, ou embutida em código) | O schema e onde ele nasce |
| Arquivo de banco embarcado ou string de conexão | O destino real dos dados |

Produza a lista de tabelas com suas colunas e — o dado mais útil para a Fase 2 — as
**restrições de integridade declaradas**. Tabela sem chave estrangeira, sem unicidade e sem
não-nulo é insumo direto de AP-11, AP-12 e AP-21.

DDL executada no caminho de boot já é AP-21; registre a linha agora, para não reler depois.

---

## 5. Domínio de negócio

Infira a partir de três vocabulários, na ordem: **nomes de tabela**, **segmentos de path das
rotas**, **nomes de entidade no código**. Escreva o domínio em uma frase.

Serve a três decisões concretas: quais são os agregados (`mvc-guidelines.md` §7), qual
vocabulário usar ao renomear em TR-18, e o que é "decisão de negócio de alto valor" ao julgar
AP-08 — o que varia por domínio e não pode ser decidido no vazio.

Divergência de vocabulário entre tabela, rota e código é finding de AP-27; anote onde ocorre.

---

## 6. Arquitetura efetiva

> **Mapeie o grafo de resolução de símbolos a partir dos entry points. Não descreva a árvore de
> diretórios, e não confunda resolução com import textual.**

Uma pasta chamada `services/` que nada resolve não é uma camada de serviço — é código morto com
nome bonito, e tratá-la como camada leva a Fase 3 a construir sobre o que não existe. Mas o
inverso custa mais caro: tratar como morto o que a stack resolve sem import explícito condena a
camada idiomática do framework a AP-26.

**Grafo de resolução** é o conjunto de símbolos que a aplicação carrega em execução, por
qualquer um dos mecanismos que a stack detectada use — e as stacks usam mecanismos diferentes:

| Mecanismo | Como o símbolo chega | Evidência a procurar |
|---|---|---|
| Import/require explícito | citado nominalmente por outro arquivo | a própria declaração de import |
| Autoload por convenção de caminho | o carregador deriva o símbolo do caminho do arquivo | a raiz de autoload declarada na configuração, e a convenção nome↔caminho |
| Varredura de pacote por anotação/atributo | o container registra o que a varredura encontra | o pacote-base varrido e o marcador que qualifica a classe |
| Registro em container ou arquivo de configuração | a ligação é declarada como dado, não como código | o registro que nomeia o símbolo |

**Determine primeiro qual mecanismo a stack usa; só então percorra.** Import textual sozinho é
insuficiente sempre que a stack não o usa como mecanismo primário, e nesse caso a árvore que a
convenção varre **é** a evidência de alcançabilidade — não o `require` do arquivo de boot.

Procedimento:

1. Localize os entry points: script declarado no manifesto > entry point declarado > convenção
   da stack > o arquivo que instancia o servidor. Podem ser mais de um; liste todos.
2. Monte o conjunto de símbolos **alcançáveis** pelo mecanismo identificado acima — imports
   transitivos, o que o autoloader ou a varredura carrega, e o que o container registra.
3. Para cada diretório que aparenta ser camada, verifique se ao menos um símbolo seu é
   alcançável. Inalcançável entra em AP-26 e aciona a regra de `mvc-guidelines.md` §6.
4. Para cada símbolo exportado, conte referências **fora** do módulo de origem. Importar não é
   usar: esse número é a evidência de AP-17.
5. Registre as **arestas que violam** a direção de dependência de `mvc-guidelines.md` §3 — são
   findings de AP-08, AP-09 e AP-13 já com evidência.

Descreva o resultado em uma frase por módulo alcançável: qual responsabilidade ele acumula.
Módulo com mais de uma responsabilidade é candidato a AP-06.

---

## 7. Inventário de endpoints

Produza a tabela completa. Ela é simultaneamente o insumo do plano de refatoração e o roteiro
do smoke test, então não a resuma.

| Campo | Obrigatório | Observação |
|---|---|---|
| Método | sim | |
| Path | sim | Com o parâmetro de path nomeado como o código o nomeia |
| Handler | sim | Símbolo que atende |
| `arquivo:linha` | sim | Do registro da rota, não do handler |
| Autenticação | sim | Middleware presente, verificação inline, ou nenhuma |
| Corpo esperado | quando houver | Campos que o handler lê |
| Efeito | sim | Leitura, escrita, ou destrutivo |

Duas armadilhas a evitar:

- **Rotas registradas em mais de um lugar.** Um projeto pode registrar a maior parte das rotas
  de forma centralizada e ainda declarar algumas inline no bootstrap. As inline são as mais
  propensas a saltar camadas — procure-as explicitamente em vez de confiar num único ponto de
  registro.
- **Rotas montadas dinamicamente** por laço ou por configuração. Enumere o resultado efetivo,
  não a linha que as gera.

Marque as rotas **destrutivas** e as **privilegiadas**: elas recebem tratamento próprio em
AP-05 e exigem cuidado no smoke test, que não pode apagar os dados que ele mesmo verifica.

---

## 8. Captura do baseline

O baseline é o contrato que a Fase 3 preserva. Capture-o **antes** de qualquer escrita, com o
código ainda intocado — depois é tarde, e um baseline capturado após a primeira mudança valida
a mudança contra si mesma.

O procedimento completo está em `validation-protocol.md` §2. Da Fase 1 saem os três insumos que
ele consome: a tabela de endpoints da §7, o comando de boot derivado do manifesto, e o SHA do
commit de baseline.

---

## 9. O que reportar quando um fato não se determina

Diga qual fato, o que você tentou e qual a consequência para as fases seguintes. Exemplos de
consequência que precisam aparecer no relatório:

- Runtime indisponível → **AP-16 não verificável**, não "AP-16 ausente".
- Endpoints montados dinamicamente e não enumeráveis → o smoke test cobre um subconjunto, e a
  contagem coberta precisa constar da mensagem de commit de cada onda.
- Aplicação que não sobe já no estado inicial → **não prossiga para a Fase 3**. Sem baseline
  executável não existe critério de validação, e a Fase 3 perderia sua única prova. Reporte a
  auditoria da Fase 2, que continua válida, e pare no gate.
