# MVC Guidelines — arquitetura-alvo

Este arquivo define **o que a Fase 3 constrói** e **o critério com que a Fase 2 julga** os
anti-patterns de camada (AP-06, AP-08, AP-13, AP-17).

O normativo aqui são as **responsabilidades** e a **direção de dependência**. A árvore de
diretórios é apenas uma materialização delas — troque a árvore se a stack detectada tiver
convenção própria, nunca as responsabilidades.

Todos os exemplos deste arquivo são **sintéticos** e usam um domínio fictício de reservas
(`reservation`, `guest`, `invoice`). Não os copie: eles ilustram forma, não sintaxe a reproduzir.

---

## Índice

| § | Seção | Consulte quando |
|---|---|---|
| [1](#1-o-que-é-normativo) | O que é normativo | Antes de decidir qualquer layout |
| [2](#2-as-sete-camadas) | As sete camadas e suas responsabilidades | Definir onde um trecho de código pertence |
| [3](#3-direção-de-dependência) | Direção de dependência | Julgar AP-08, AP-09, AP-13 |
| [4](#4-árvore-canônica-e-variantes-por-stack) | Árvore canônica e variantes por stack | Criar a estrutura na Onda 1 |
| [5](#5-composition-root) | Composition root | Aplicar TR-09 |
| [6](#6-regra-de-alcançabilidade-camadas-preexistentes) | Regra de alcançabilidade | O projeto já tem pastas de camada |
| [7](#7-granularidade-de-controller) | Granularidade de controller | Decidir quantos controllers criar |
| [8](#8-preservação-de-superfície) | Preservação de superfície | Antes de mudar qualquer resposta |
| [9](#9-checklist-de-conformidade-de-camada) | Checklist de conformidade | Fase 2: julgar AP-06/08/13/17 |
| [10](#10-quando-não-criar-uma-camada) | Quando NÃO criar uma camada | Evitar over-engineering em projeto pequeno |

---

## 1. O que é normativo

Ordene as três coisas por força, da maior para a menor:

1. **Responsabilidade única por camada** — inegociável. Uma camada que faz duas coisas não é
   uma camada, é um módulo com nome bonito.
2. **Direção de dependência** — inegociável. É o que torna a arquitetura verificável pelo grafo
   de resolução (§6), e não por opinião.
3. **Nome e posição dos diretórios** — negociável. Cede à convenção idiomática da stack
   detectada na Fase 1.

A regra de precedência existe porque uma árvore genérica imposta sobre uma stack que tem
convenção própria produz um projeto que nenhum desenvolvedor daquela comunidade reconhece —
e o custo de manutenção disso é maior que o ganho de uniformidade entre projetos diferentes.

**4. Stack que já materializa as responsabilidades.** Quando a Fase 1 detectar que a stack
carrega, por convenção própria, diretórios ou pacotes que já cumprem responsabilidades desta
lista, a Fase 3 **adota essa árvore** e trabalha dentro dela: corrige as violações de
responsabilidade e de direção onde elas estão, e cria **apenas** a responsabilidade que algum
finding exige e que a convenção não cobre — no lugar que a própria convenção indicaria para ela.
Erguer uma árvore paralela ao lado da convenção do framework é **desvio do alvo**, não o alvo:
duplica o mesmo papel em dois lugares e viola a regra 1 no ato de tentar cumpri-la.

**O gatilho não é alcançabilidade.** Módulo alcançável não é camada: camada é responsabilidade
com **lugar convencionado**. Esta regra só se aplica quando a stack ou o framework **declara** a
convenção de camadas — raiz de autoload, pacote-base varrido, ou estrutura de diretórios imposta
pelo framework — e o lugar que ela convenciona existe no projeto. Um monólito cujos módulos são
apenas alcançáveis por import explícito **não tem convenção a adotar**, por mais que seus
arquivos tenham nome de camada: cai na §4, precedência 2 ou 3. Alcançabilidade (§6) decide se
uma camada preexistente é adotada ou é AP-26; **é esta regra**, e só ela, que decide se existe
convenção a adotar.

---

## 2. As sete camadas

A coluna que normatiza é **Responsabilidade única**; o nome da camada é rótulo de referência
deste arquivo. Uma stack cuja convenção funde duas destas responsabilidades num lugar só, ou as
chame por outros nomes, continua conforme — desde que cada responsabilidade tenha **um** lugar
identificável e a direção da §3 se preserve. O que não é negociável é uma responsabilidade sem
lugar, ou espalhada por vários.

| Camada | Responsabilidade única | Entrada | Saída |
|---|---|---|---|
| **config** | Ler o ambiente, validar a presença do que é obrigatório, expor valores tipados. Falha no boot se faltar. | variáveis de ambiente | objeto de configuração imutável |
| **models** | Definir a forma dos dados e as invariantes que valem sempre, independentemente de caso de uso. | — | entidade / schema |
| **repositories** | Traduzir entre entidade e mecanismo de persistência. Único lugar do projeto que conhece SQL, driver ou ORM. | entidade, critério de busca | entidade, coleção de entidades |
| **services** | Executar a regra de negócio e orquestrar efeitos colaterais. Único lugar que decide *o quê* acontece. | dados já validados | resultado de domínio ou exceção de domínio |
| **controllers** | Traduzir entre protocolo e domínio: parse da entrada, chamada ao service, mapeamento do resultado para resposta. | requisição | resposta |
| **routes / views** | Declarar o mapeamento `método + path → handler + middlewares`. Sem lógica. | — | tabela de rotas |
| **middlewares** | Aplicar preocupações transversais: autenticação, autorização, correlação, tratamento de erro, limite de taxa. | requisição | requisição enriquecida ou rejeição |

### 2.1 Testes de pertencimento

Quando não souber onde um trecho vive, responda:

- *A regra continua verdadeira se o protocolo mudar de HTTP para uma fila de mensagens?*
  Sim → **service**. Não → **controller**.
- *O trecho menciona tabela, coluna, cursor, sessão de persistência ou dialeto de consulta?*
  Sim → **repository**, sem exceção.
- *A regra vale para toda instância da entidade, em qualquer caso de uso?*
  Sim → **model**. Vale só neste fluxo → **service**.
- *O trecho seria copiado idêntico em todas as rotas se não existisse?*
  Sim → **middleware**.

---

## 3. Direção de dependência

```text
routes ──▶ middlewares ──▶ controllers ──▶ services ──▶ repositories ──▶ (driver / ORM)
                                               │              │
                                               └──────▶ models ◀──────┘
                       config ──▶ (lido apenas pelo composition root e injetado adiante)
```

Regras derivadas, todas verificáveis por leitura de imports:

| Camada | **Pode** importar | **Não pode** importar |
|---|---|---|
| routes | controllers, middlewares | services, repositories, driver |
| controllers | services, models (só para tipo/DTO) | repositories, driver, ORM, sessão |
| services | repositories, models, outros services | qualquer símbolo de protocolo (request, response, status) |
| repositories | models, driver/ORM | services, controllers |
| models | nada do projeto (ou apenas outros models) | qualquer camada acima |
| middlewares | config, services de autenticação | repositories, driver |
| config | biblioteca de ambiente | qualquer camada do projeto |

Duas violações merecem nome próprio porque são as mais frequentes:

- **Salto de camada** — a apresentação importa a infraestrutura diretamente, pulando o meio.
  O grafo passa a ter uma aresta que a arquitetura declarada proíbe. É AP-09/AP-13.
- **Inversão de papéis** — a decisão de serialização de API vive no model e a decisão de
  transação vive no controller. Cada uma está exatamente na camada errada. É AP-13.

Um import de protocolo dentro de um service é sintoma decisivo: significa que a regra de
negócio só funciona sob HTTP, e portanto não é testável sem subir um servidor.

---

## 4. Árvore canônica e variantes por stack

Layout genérico, usado quando a stack não impõe convenção:

```text
<raiz>/
├── config/          leitura e validação do ambiente
├── models/          entidades e schema
├── repositories/    acesso a dados
├── services/        regra de negócio
├── controllers/     tradução protocolo ↔ domínio
├── routes/          tabela de rotas (ou views/ quando renderiza template)
├── middlewares/     preocupações transversais
└── <entrypoint>     composition root: monta o grafo e sobe a aplicação
```

### 4.1 Variantes idiomáticas

Aplique a variante da stack detectada; ela **vence** o layout genérico.

| Stack detectada | Ajuste idiomático a adotar |
|---|---|
| Python (framework web de rotas explícitas) | Diretórios em `snake_case`, `__init__.py` por pacote, entrypoint em módulo próprio; `routes/` costuma virar blueprints/routers registrados no composition root. |
| Python (framework com camadas próprias) | Respeite a nomenclatura do framework para o que ele já nomeia; crie apenas as camadas ausentes (tipicamente `services/` e `repositories/`). |
| JavaScript / TypeScript | `src/` como raiz das camadas, arquivos em `camelCase` ou `kebab-case` conforme o já usado no projeto, sufixo no nome do arquivo (`*.service`, `*.repository`) quando o projeto já usar sufixos. |
| Java / Kotlin | Pacotes sob a raiz do grupo, camada como último segmento (`...domain`, `...repository`, `...service`, `...web`); `resources/` para configuração. |
| Ruby | Diretórios em `snake_case` sob a raiz de autoload do framework, nome do arquivo derivado do nome da classe; rotas em arquivo de configuração declarativo, migrações versionadas por timestamp no diretório do framework, e inicialização por arquivos de configuração em vez de um construtor manual do grafo. |
| PHP | `src/` com PSR-4, `Namespace\Layer\ClassName`, uma classe por arquivo em `PascalCase`. |
| Go | Pacotes por responsabilidade sob `internal/`, sem sufixo redundante no nome do tipo; `cmd/<app>/main.go` como composition root. |

**Regra de precedência, aplicada nesta ordem:**
1. Convenção já praticada e **alcançável** dentro do próprio projeto (§6).
2. Convenção idiomática da stack detectada.
3. Layout genérico acima.

Nunca misture duas convenções na mesma árvore. Um projeto com metade dos diretórios em
`snake_case` e metade em `camelCase` custa mais atenção de leitura do que ganha em fidelidade.

---

## 5. Composition root

O composition root é o **único** ponto do projeto autorizado a instanciar infraestrutura. Ele
lê a configuração, constrói repositórios, injeta-os nos serviços, injeta serviços nos
controllers, registra as rotas e sobe o servidor.

**Quando a stack já tem um.** Composition root é um papel, não um arquivo. Stacks com container
de injeção ou com ciclo de inicialização próprio já o cumprem: o container **é** o composition
root, e os arquivos de inicialização que a convenção define são onde a configuração entra. Nesse
caso a Fase 3 **usa** o mecanismo existente — declara ali o que precisa ser construído — e
**não** reimplementa a montagem do grafo num entry point paralelo. Reimplementá-lo cria dois
donos do ciclo de vida dos objetos, que é um acoplamento pior do que o que TR-09 veio corrigir.
O exemplo abaixo é a forma para stacks **sem** esse mecanismo.

**Exemplo — Python [sintético]**

```python
# entrypoint: único lugar que instancia infraestrutura
settings = load_settings()                       # falha aqui se faltar variável obrigatória
db = Database(settings.database_url)
reservation_repo = ReservationRepository(db)
reservation_service = ReservationService(reservation_repo, clock=system_clock)
app = build_app(ReservationController(reservation_service), settings)
```

**Exemplo — JavaScript [sintético]**

```javascript
// entrypoint: único lugar que instancia infraestrutura
const settings = loadSettings();                 // lança se faltar variável obrigatória
const db = createDatabase(settings.databaseUrl);
const reservationRepo = makeReservationRepository(db);
const reservationService = makeReservationService(reservationRepo, systemClock);
const app = buildApp(makeReservationController(reservationService), settings);
```

Propriedade que isso compra, e é a razão de existir da regra: qualquer camada abaixo passa a
ser instanciável em teste com uma implementação alternativa, sem tocar em variável de ambiente
nem em banco. Uma camada que só funciona com o singleton global do projeto não é uma camada.

---

## 6. Regra de alcançabilidade (camadas preexistentes)

Projetos parcialmente organizados chegam com diretórios de camada já criados. Adotar o que
existe e recriar o que existe são erros simétricos, e a diferença entre eles é observável.

> **Adote um diretório de camada preexistente se e somente se ao menos um dos seus símbolos
> for alcançável a partir dos entry points pelo mecanismo de resolução da stack** — import
> explícito, autoload por convenção, varredura de pacote ou registro em container. **Onde a
> stack resolve por convenção, o diretório que a convenção varre é alcançável mesmo que nenhum
> arquivo o importe nominalmente.**

Qual dos quatro mecanismos vale aqui **não se redescobre nesta fase**: é fato determinado na
Fase 1 e registrado no relatório junto da arquitetura efetiva. As Fases 2 e 3 leem o fato, não o
procedimento que o produziu. Esta seção é a definição de alcançabilidade que o resto do pacote
referencia — AP-26 e TR-15 apontam para cá, e nenhum a reformula.

Procedimento:

1. Parta dos entry points identificados na Fase 1 e percorra o grafo de resolução
   transitivamente, pelo mecanismo que a Fase 1 determinou.
2. Para cada símbolo exportado pelo diretório candidato, conte referências **fora** do módulo
   que o define. Importar não é usar: um import sem chamada não torna o símbolo alcançável.
3. **Alcançável** → adote o diretório, preserve sua nomenclatura e **ligue** o que estiver
   solto. A transformação é de ligação (TR-15), não de criação.
4. **Inalcançável** → trate como AP-26 (código morto) e substitua pela camada nova.

**Obrigação que acompanha a substituição:** registre na Fase 2, como finding, tudo o que a
camada inalcançável contém — inclusive segredos, regras e decisões que ela carrega — **antes**
de propor a remoção. Nada desaparece sem constar do relatório que o humano aprova no gate.

Um segredo versionado dentro de código morto continua sendo um finding: apagar o arquivo não
o remove do histórico do repositório, e é o histórico que precisa ser rotacionado.

---

## 7. Granularidade de controller

> **Um controller por agregado de domínio. Fatie por sub-recurso quando o controller
> ultrapassar 10 handlers OU 250 linhas — o que ocorrer primeiro.**

Agregado de domínio é o conjunto de entidades que muda junto e tem uma raiz de identidade
própria. Rotas aninhadas sob a mesma raiz pertencem ao mesmo controller até o limiar.

| Situação | Decisão |
|---|---|
| 4 rotas de reserva + 3 rotas de item da reserva | Um controller de reserva. 7 handlers, abaixo do limiar. |
| 14 rotas sob a mesma raiz | Fatie por sub-recurso: um controller para a raiz, outro para o sub-recurso mais volumoso. |
| 2 rotas de um recurso administrativo isolado | Controller próprio mesmo sendo pequeno — o agregado é outro. |
| 1 rota de health check | Fora dos controllers de domínio; trate como rota de infraestrutura. |

O limiar é uma válvula para o caso patológico, não uma meta. Fatiar cedo demais espalha a
mesma decisão por vários arquivos e piora a leitura da árvore antes/depois, que é o principal
artefato de revisão da refatoração.

---

## 8. Preservação de superfície

Invariantes que a Fase 3 **não** altera, porque são o que torna a validação falsificável:

- **Path** de cada endpoint.
- **Verbo** HTTP.
- **Status code** de sucesso e de erro para o mesmo cenário de entrada.

O **shape do corpo** pode ser normalizado — e frequentemente precisa ser, porque contrato
inconsistente é o próprio AP-23. Mas toda mudança de shape:

1. É prevista na Fase 2, não descoberta na Fase 3.
2. Consta da seção **Breaking changes** do relatório, com endpoint, campo e motivo.
3. É aprovada no gate junto com o resto do plano.

Shape alterado que não conste da seção aprovada é **regressão**, não melhoria — mesmo que o
resultado pareça melhor. O critério é conformidade com o aprovado, não gosto do executor.

Caso especial: quando um campo sai da resposta por ser credencial ou PII (AP-03), a remoção
**é** uma breaking change e vai para a seção — a justificativa de segurança explica o porquê,
não dispensa a declaração.

---

## 9. Checklist de conformidade de camada

Use na Fase 2 para converter "parece desorganizado" em finding com evidência. Cada linha
responde sim/não por leitura direta; um "sim" produz `arquivo:linha` e o AP correspondente.

| # | Pergunta | AP quando "sim" |
|---|---|---|
| 1 | Existe arquivo que abre conexão, define schema, registra rota e decide regra no mesmo corpo? | AP-06 |
| 2 | Existe decisão de negócio ou efeito colateral escrito dentro de um handler de protocolo? | AP-08 |
| 3 | Existe agregação de consulta misturada a regra de negócio na camada de dados? | AP-08 |
| 4 | O handler manipula sessão/transação de persistência diretamente? | AP-13 |
| 5 | O handler inspeciona a forma do valor retornado para decidir o status code? | AP-08 |
| 6 | Um service importa símbolo de protocolo (request, response, status)? | AP-08 |
| 7 | Um controller importa driver, ORM ou repositório diretamente? | AP-09, AP-13 |
| 8 | Existe diretório de camada cujos símbolos são inalcançáveis do entry point? | AP-26 (§6) |
| 9 | Existe abstração correta no repositório que nenhum caminho de execução invoca? | AP-17 |
| 10 | O composition root constrói o objeto principal sem receber nenhuma dependência? | AP-09 |

---

## 10. Quando NÃO criar uma camada

Limite superior explícito, porque uma arquitetura com mais camadas do que decisões é tão
custosa quanto uma sem camada nenhuma.

- **Repository que só delega.** Se o repositório de uma entidade tem exatamente os métodos do
  ORM, com os mesmos argumentos e sem tradução alguma, ele não isola nada. Crie-o assim mesmo
  **apenas** se outro repositório do projeto já justifica a camada; caso contrário, mantenha o
  acesso no service e registre a decisão.
- **Service anêmico por entidade.** Uma entidade sem regra de negócio alguma não precisa de
  service próprio. O controller pode chamar o repositório **se e somente se** nenhum outro
  fluxo do mesmo agregado tiver regra — caso contrário a exceção vira a porta de entrada da
  próxima violação.
- **Middleware para uma rota só.** Preocupação que atinge um único handler é código do
  handler. Middleware é para o que se repetiria.
- **Camada de DTO com mapeamento identidade.** Se o DTO tem exatamente os campos da entidade,
  ele só protege contra a entidade ganhar campos no futuro — o que é real quando a entidade
  tem credencial ou PII (AP-03), e é ruído quando não tem.

Regra de desempate: crie a camada quando ela **remove** uma decisão de onde ela não deveria
estar. Não crie quando ela apenas **adiciona** um salto no caminho da chamada.
