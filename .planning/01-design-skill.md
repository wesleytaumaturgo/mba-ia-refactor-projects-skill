# Design da Skill `refactor-arch`

> Documento de **design**, não de implementação. Nenhum arquivo da skill é criado nesta etapa.
>
> **Insumo empírico:** os 75 findings validados em [`.planning/analise-manual/`](analise-manual/) e a
> seção "Padrões recorrentes entre projetos" do [`README.md`](../README.md). As três tabelas de
> *sinais genéricos extraídos* (AM-001…AM-075) são a fonte literal da coluna "Sinal de detecção" do
> catálogo proposto na seção 4.
>
> **Regra de rastreabilidade:** a coluna `Origem` referencia AM-XXX apenas para provar que o
> anti-pattern foi observado em código real. Nenhum AM-XXX aparece — nem pode aparecer — dentro de um
> sinal de detecção. Sinal é forma estrutural; AM-XXX é procedência.

---

## 1. Contrato da skill

### 1.1 Identidade

| Campo | Valor |
|---|---|
| **Nome** | `refactor-arch` (fixado pelo enunciado, não negociável) |
| **Path** | `.claude/skills/refactor-arch/` — replicado nos 3 projetos-alvo |
| **Invocação** | `/refactor-arch` (explícita) ou por *model-triggered discovery* via `description` |
| **Escopo de execução** | O diretório de trabalho atual (o projeto onde a skill foi copiada) |

### 1.2 Frontmatter proposto (texto final)

```yaml
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
```

**Defesa da `description`.** Três blocos deliberados, porque a description é o único texto que o
agente lê antes de decidir carregar a skill:

1. **O que faz** (3 fases nomeadas) — dá ao agente o modelo mental completo em uma frase.
2. **Quando acionar** — enumera os *verbos do usuário* ("auditar", "encontrar anti-patterns",
   "migrar para MVC"), não a implementação. Inclui o gatilho explícito `/refactor-arch`.
3. **Quando NÃO acionar** — a negativa final impede que a skill sequestre um pedido de code review
   de um arquivo só, cenário em que carregar ~2.000 linhas de referência é puro desperdício.

Menciona linguagens concretas de propósito: sem isso, o agente pode inferir que uma skill de "MVC"
é específica de um framework web e não a considerar num projeto Go ou PHP.

### 1.3 DENTRO do escopo

- Detecção de linguagem, framework, gerenciador de pacotes, banco e arquitetura efetiva (não a
  pretendida pela estrutura de diretórios).
- Auditoria contra o catálogo de anti-patterns, com **severidade + arquivo:linha exato + evidência
  literal**, ordenada CRITICAL → LOW.
- Detecção de **APIs deprecated** contra a versão de runtime efetivamente em uso.
- Geração do relatório de auditoria em formato fixo (Fase 2) — o artefato que vai para `reports/`.
- **Gate humano obrigatório** entre auditoria e escrita.
- Reestruturação para MVC: `config/`, `models/`, `controllers/`, `views|routes/`, `services/`,
  `repositories/`, `middlewares/`, composition root.
- Validação pós-refatoração: boot da aplicação + smoke test de todos os endpoints originais,
  comparando contra baseline capturado **antes** de qualquer escrita.
- Adaptação ao nível de organização preexistente: um projeto que já tem `services/` recebe um plano
  diferente de um monolito de 4 arquivos.

### 1.4 FORA do escopo

| Fora | Por quê |
|---|---|
| Migrar para arquitetura que não seja MVC (hexagonal, clean, DDD tático, microserviços) | O enunciado fixa MVC como alvo. Ampliar dilui o contrato e torna a validação impossível. |
| Trocar framework, ORM, banco ou runtime | Refatoração ≠ reescrita. Trocar a stack invalida o critério "os endpoints originais continuam respondendo". |
| Alterar path, verbo ou status code de qualquer endpoint | É o invariante que torna a validação da Fase 3 falsificável. O **shape do corpo** pode ser normalizado, mas só via seção "Breaking changes" aprovada no gate — preservação de superfície, `DECISÃO-03`. |
| Escrever a suíte de testes do projeto | Escopo próprio, ordem de grandeza de esforço distinta. A skill cria *smoke tests* de validação, não cobertura. |
| Corrigir vulnerabilidade que exija decisão de produto (política de senha, retenção de PII, LGPD) | A skill **reporta** e propõe; a decisão é do dono do produto. |
| Deploy, CI, containerização, infraestrutura | Não é arquitetura de código. |
| Rodar contra diretório sem VCS limpo | Pré-condição de segurança: sem `git status` limpo, não há como reverter a Fase 3. |

---

## 2. Mapa de arquivos

| Arquivo | Responsabilidade | Quando o agente lê | Linhas est. |
|---|---|---|---|
| `SKILL.md` | **Orquestra, não ensina.** Define as 3 fases, a ordem, o gate humano, os critérios de parada e *qual reference carregar em cada momento*. Contém o output format do console das Fases 1 e 3. Zero conhecimento de domínio. | Sempre, integralmente, no momento da invocação | **~190** |
| `references/project-analysis.md` | Heurísticas de detecção: linguagem por extensão e manifesto, framework por dependência e por assinatura de import, versão de runtime efetiva, banco por driver e por DDL, mapeamento da arquitetura efetiva por grafo de imports, inventário de endpoints, captura do baseline de validação. | Início da Fase 1, integralmente | ~280 |
| `references/antipattern-catalog.md` | Os 28 anti-patterns: ID, nome, severidade, sinal de detecção operacional, contra-exemplo (quando NÃO é finding), manifestações por stack, TR associado. **Índice obrigatório no topo** (>300 linhas). | Início da Fase 2, integralmente. É o arquivo mais caro — por isso não é lido na Fase 1. | **~640** |
| `references/report-template.md` | Estrutura literal do relatório da Fase 2: cabeçalho, sumário por severidade, bloco de finding, seção "o que NÃO foi encontrado", **seção "Breaking changes" propostas** (DECISÃO-03), rodapé com total e prompt do gate. Inclui exemplo preenchido e regras de ordenação/numeração. | Fim da Fase 2, ao redigir o relatório | ~210 |
| `references/mvc-guidelines.md` | Arquitetura-alvo: responsabilidade de cada camada, regra de direção de dependência, o que cada camada **não pode** importar, árvore de diretórios canônica com variantes por stack, **regra de alcançabilidade para camadas preexistentes** (DECISÃO-01), **critério de granularidade de controller com limiar 10 handlers / 250 linhas** (DECISÃO-02). **Índice obrigatório.** | Início da Fase 3 (e consultado na Fase 2 para julgar os APs de camada: AP-06, AP-08, AP-13, AP-17) | ~330 |
| `references/refactor-playbook.md` | As 18 transformações TR-01…TR-18, cada uma com pré-condição, passos, **código antes/depois em ≥2 stacks**, riscos, verificação pontual e **onda de severidade a que pertence**. **Índice obrigatório**; o agente lê o índice e depois só as seções dos TRs que a auditoria acionou. | Fase 3, **sob demanda por TR** — nunca integralmente | **~740** |
| `references/validation-protocol.md` | Protocolo de validação agnóstico: como descobrir o comando de boot, detectar "subiu com sucesso" sem depender de framework, executar o smoke test contra o baseline, **a cadência de validação em ondas com commit por onda verde** (DECISÃO-04), e o procedimento de rollback por `reset` ao último commit verde (DECISÃO-05). | Fim da Fase 1 (captura do baseline) e **ao fim de cada onda** da Fase 3 | ~190 |

**Total estimado:** ~2.580 linhas, das quais o agente carrega ~190 (SKILL.md) + ~280 (Fase 1) +
~640 (Fase 2) + ~210 (template) e, na Fase 3, apenas os TRs acionados — tipicamente 8 a 12 dos 18,
ou ~350 das 740 linhas do playbook.

### 2.1 Decisão: 6 arquivos de referência, não 5

O enunciado exige **5 áreas de conhecimento**, não 5 arquivos. As 5 áreas estão cobertas por
`project-analysis`, `antipattern-catalog`, `report-template`, `mvc-guidelines` e `refactor-playbook`.

`validation-protocol.md` é o sexto e existe por um trade-off explícito: a validação é *knowledge*
(como saber que um servidor subiu, sem saber qual framework é?), não *orquestração*. Se ficasse no
`SKILL.md`, empurraria o orquestrador para ~330 linhas e violaria o princípio de que SKILL.md não
ensina. Se ficasse no `refactor-playbook.md`, o agente teria de carregar o arquivo mais caro do
conjunto já na Fase 1, só para capturar o baseline.

**Custo aceito:** um arquivo a mais para o avaliador conferir. **Ganho:** o SKILL.md permanece um
orquestrador legível e o baseline é capturado sem carregar o playbook.

### 2.2 Decisão: progressive disclosure em dois eixos

O guia oficial trata progressive disclosure como "SKILL.md aponta, references ensinam". Aqui ele
opera também **dentro** do `refactor-playbook.md`: o índice do topo mapeia `AP-XX → TR-YY → âncora`,
e o agente carrega apenas as seções dos TRs que a auditoria daquele projeto acionou. Num projeto que
não tem N+1, as ~60 linhas de TR-09 nunca entram no contexto.

**Trade-off:** exige disciplina de âncoras estáveis (`## TR-09 — …`) e um índice que pode
dessincronizar do corpo. Mitigado por um checklist de consistência no fim da implementação.

---

## 3. Fluxo das 3 fases

```
INVOCAÇÃO: /refactor-arch  (cwd = raiz do projeto-alvo)

┌─ PRÉ-CONDIÇÕES (SKILL.md, antes da Fase 1) ────────────────────────────────┐
│ IN : cwd                                                                    │
│  1. Verificar repositório VCS e working tree limpo.                         │
│     → sujo: reportar e ABORTAR. O commit atual É o ponto de retorno         │
│       (DECISÃO-05: sem branch própria). Working tree sujo o invalida.       │
│  2. Registrar o SHA do commit de baseline — alvo do primeiro rollback.      │
│  3. Declarar em voz alta: "auditoria read-only até o gate da Fase 2".       │
│ OUT: garantia de reversibilidade em histórico linear                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌─ FASE 1 — ANÁLISE (read-only) ─────▼───────────────────────────────────────┐
│ LÊ : references/project-analysis.md  +  references/validation-protocol.md   │
│ IN : árvore de arquivos, manifestos de dependência, código-fonte            │
│                                                                             │
│  1.1 Detectar linguagem   → extensões dominantes + manifesto                │
│  1.2 Detectar framework   → dependência declarada ∩ import efetivo          │
│       ⚠ declarada e não importada NÃO é a stack — é candidata a AP-26       │
│  1.3 Detectar runtime efetivo → o do ambiente, não o do manifesto           │
│       (insumo obrigatório de AP-16 Deprecated API Usage)                    │
│  1.4 Detectar persistência → driver/ORM + DDL + arquivo de banco            │
│  1.5 Inferir domínio      → vocabulário de entidades, rotas e tabelas       │
│  1.6 Mapear arquitetura EFETIVA → grafo de imports, não árvore de pastas    │
│  1.7 Inventariar endpoints → método + path + handler + arquivo:linha        │
│  1.8 CAPTURAR BASELINE    → snapshot dos endpoints; contrato a preservar    │
│                                                                             │
│ OUT: bloco `PHASE 1: PROJECT ANALYSIS` no console                           │
│      + inventário de endpoints e baseline (memória de trabalho)             │
│ ESCRITA EM DISCO: nenhuma                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌─ FASE 2 — AUDITORIA (read-only) ───▼───────────────────────────────────────┐
│ LÊ : references/antipattern-catalog.md (integral)                           │
│      references/mvc-guidelines.md (§camadas, para AP-06/08/13)              │
│      references/report-template.md (ao redigir)                             │
│ IN : saída da Fase 1 + código-fonte                                         │
│                                                                             │
│  2.1 Varredura: para cada AP do catálogo, responder o sinal de detecção     │
│  2.2 Para cada "sim", COLETAR EVIDÊNCIA LITERAL: arquivo:linha + o bloco    │
│       de código real. Sem evidência literal → o finding é DESCARTADO.       │
│  2.3 Aplicar o contra-exemplo de cada AP (quando NÃO é finding)             │
│  2.4 Classificar severidade pela escala do enunciado; registrar desvio      │
│  2.5 Registrar explicitamente O QUE NÃO FOI ENCONTRADO nas categorias       │
│       nomeadas da escala — antídoto contra preenchimento de cota            │
│  2.6 Registrar como finding o conteúdo de qualquer camada preexistente      │
│       INALCANÇÁVEL a partir do entry point, ANTES de propô-la para          │
│       remoção (DECISÃO-01). Nada some sem constar do relatório.             │
│  2.7 Ordenar CRITICAL → HIGH → MEDIUM → LOW e redigir o relatório           │
│  2.8 Redigir a seção BREAKING CHANGES: toda mudança de shape de resposta    │
│       que a refatoração vai provocar, com endpoint, campo e motivo          │
│       (DECISÃO-03). É a peça que o humano aprova no gate.                   │
│  2.9 Gravar o relatório em `reports/audit-<projeto>.md`                     │
│       ⚠ é escrita, mas de ARTEFATO, não de código-fonte. Ver nota abaixo.   │
│  2.10 Montar o PLANO DE REFATORAÇÃO agrupado por ONDA de severidade:        │
│       finding → TR → onda → arquivos afetados                               │
│                                                                             │
│ OUT: relatório de auditoria (com Breaking changes) + plano em 4 ondas       │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
╔═════════════════════════════════════▼══════════════════════════════════════╗
║  ★ GATE HUMANO — ponto exato: após 2.10, antes de qualquer escrita em       ║
║    arquivo de código-fonte. É a ÚLTIMA instrução da Fase 2.                 ║
║                                                                             ║
║  O agente apresenta: total de findings por severidade, o plano de           ║
║  refatoração agrupado nas 4 ondas (TRs + arquivos que serão criados/        ║
║  movidos/removidos), a seção BREAKING CHANGES e os itens NEEDS-DECISION.    ║
║  Um único "y" aprova o conjunto — sem questionário item a item.             ║
║                                                                             ║
║      Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]            ║
║                                                                             ║
║  Regras do gate, escritas em forma imperativa no SKILL.md:                  ║
║   • PARE e aguarde resposta explícita do humano. Silêncio não é "y".        ║
║   • "n" → encerre relatando o caminho do relatório. Nada é modificado.      ║
║   • "y" → prossiga com o plano APRESENTADO, não com um plano revisado.      ║
║   • Resposta parcial ("só os CRITICAL", "não mexe em X") → replaneje e      ║
║     reapresente o gate. Um gate parcialmente aprovado é um novo gate.       ║
╚═════════════════════════════════════╤══════════════════════════════════════╝
                                     │ y
┌─ FASE 3 — REFATORAÇÃO (escrita) ───▼───────────────────────────────────────┐
│ LÊ : references/mvc-guidelines.md (integral)                                │
│      references/refactor-playbook.md (índice + SÓ os TRs acionados)         │
│      references/validation-protocol.md                                      │
│ IN : plano aprovado em 4 ondas + baseline da Fase 1 + SHA de baseline       │
│                                                                             │
│  3.1 EXECUÇÃO EM ONDAS POR SEVERIDADE (DECISÃO-04). Ordem fixa:             │
│        Onda 1 — CRITICAL : TR-01…TR-06 + o esqueleto MVC, que se            │
│                            materializa aqui porque decompor a God Class     │
│                            (AP-06) e extrair config (AP-02) SÃO a           │
│                            estrutura. Não há onda 0.                        │
│        Onda 2 — HIGH     : TR-07…TR-10                                      │
│        Onda 3 — MEDIUM   : TR-11…TR-17                                      │
│        Onda 4 — LOW      : TR-18                                            │
│                                                                             │
│  3.2 PROTOCOLO DE ONDA — idêntico nas quatro:                               │
│        a. aplicar os TRs da onda; boot após CADA TR (barato, e localiza     │
│           a quebra no TR, não na onda inteira)                              │
│        b. ao fim da onda: SMOKE TEST completo contra o baseline             │
│        c. onda VERDE  → commit `refactor(onda-N): <severidade>` e segue     │
│           onda VERMELHA → `git reset --hard <último commit verde>`,         │
│                           depois PARE E REPORTE. Não tente a onda           │
│                           seguinte sobre uma base não validada.             │
│                                                                             │
│  3.3 Validação final — herdada das 4 ondas verdes, mais:                    │
│        ✓ nenhum AP CRITICAL/HIGH do relatório permanece                     │
│        ✓ toda mudança de shape observada consta da seção Breaking changes   │
│          aprovada no gate; divergência é regressão, não melhoria            │
│                                                                             │
│  3.4 Falha em qualquer onda → NÃO declare sucesso parcial como sucesso.     │
│       Reporte: onda que quebrou, TR suspeito, evidência, e o commit verde   │
│       para onde o repositório voltou.                                       │
│                                                                             │
│ OUT: bloco `PHASE 3: REFACTORING COMPLETE` com a nova árvore + checklist    │
│      + histórico LINEAR: baseline → onda-1 → onda-2 → onda-3 → onda-4       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Nota sobre 2.9 — gravar o relatório antes do gate

O enunciado diz que a Fase 2 deve pausar "antes de modificar qualquer arquivo". Gravar
`reports/audit-<projeto>.md` é escrita em disco.

**Decisão:** gravar. O relatório é um *artefato novo de auditoria*, não uma modificação do projeto:
é aditivo, não destrutivo, e não toca nenhum arquivo preexistente. Gravá-lo antes do gate garante
que o trabalho da Fase 2 sobrevive a um "n" ou a uma queda de sessão — e o enunciado exige esse
arquivo em `reports/` independentemente da Fase 3 rodar.

**Fronteira que a skill não cruza:** nenhum arquivo de código-fonte, manifesto, configuração ou
diretório do projeto é criado, movido ou alterado antes do "y".

### 3.2 Nota sobre as ondas — por que a Onda 1 absorve o esqueleto

A ordenação por severidade (DECISÃO-04) e a ordenação "estrutura antes de conteúdo" do design
anterior colidem em um ponto: criar o esqueleto MVC não tem severidade própria.

A colisão é aparente. As duas transformações que **produzem** a estrutura — TR-01 (extrair config
para módulo próprio) e TR-06 (decompor a God Class em Model/Repository/Service/Controller/Router) —
resolvem AP-02 e AP-06, ambos CRITICAL. O esqueleto não precisa de onda própria porque ele *é* a
Onda 1. Isso preserva exatamente os 4 pontos de retorno acordados, sem uma "onda 0" que
introduziria um commit sem critério de validação próprio: um esqueleto de diretórios vazios não é
falsificável por smoke test.

**Consequência aceita, e é a mais pesada deste design:** a Onda 1 concentra o maior volume de
mudança e o maior risco de quebra — em `code-smells-project`, 7 findings CRITICAL somados à
decomposição de todo o projeto. Mitigada em 3.2a pelo boot após **cada TR**, não só ao fim da onda:
o commit é o ponto de retorno, o boot é o localizador de defeito. Registrada como R-14.

---

## 4. Catálogo proposto — 28 anti-patterns

**Distribuição de severidade:** CRITICAL 7 · HIGH 7 · MEDIUM 10 · LOW 4.
Mínimo do enunciado: 8 com severidade distribuída. Excedido em 3,5×.

**Formato do sinal:** pergunta operacional respondível lendo o código, na forma validada na seção A
do README — descreve *forma estrutural* (posição na camada, aresta do grafo de dependências,
relação entre dois pontos do código), nunca token, nome de arquivo ou string literal dos alvos.

**Coluna Origem:** `AM-XXX` = observado com evidência literal nos projetos. `domínio` = conhecimento
de domínio, **sem ocorrência local registrada** — entra no catálogo com a limitação declarada.

| ID | Nome | Sev. | Sinal de detecção genérico (pergunta operacional) | Aplica a | Origem |
|---|---|---|---|---|---|
| **AP-01** | Injection por Concatenação de Entrada Externa | CRITICAL | Existe query, comando de shell ou expressão interpretada montada por concatenação/interpolação de string contendo valor vindo de entrada externa (corpo, query string, path param, header), em vez de parâmetro vinculado? Existe handler que recebe uma string de consulta/comando no payload e a repassa a um executor sem allowlist? | Qualquer projeto com persistência ou execução dinâmica | AM-001, AM-002 |
| **AP-02** | Hardcoded Secret e Debug Ligado no Bootstrap | CRITICAL | Existe literal string atribuído a chave de configuração sensível (segredo de assinatura, senha, chave de API, credencial de integração) no bootstrap ou no construtor de um serviço, sem nenhuma leitura de variável de ambiente em todo o projeto? Existe flag de debug/verbosidade ligada no código junto de bind em todas as interfaces? Reforço: o valor carrega marcador de ambiente produtivo, ou a chave nunca é referenciada. | Universal | AM-003, AM-028, AM-052, AM-053 |
| **AP-03** | Credencial ou PII na Serialização de Resposta | CRITICAL | Existe função de mapeamento registro→DTO que projeta campo de credencial, segredo ou PII e alimenta uma rota de leitura sem controle de acesso — inclusive a própria resposta de autenticação? Existe endpoint de diagnóstico que serializa valor de configuração sensível? Reforço: outra cópia do mesmo mapeamento omite o campo, indicando exposição acidental. | APIs que serializam entidades | AM-004, AM-006, AM-051 |
| **AP-04** | Derivação de Senha Quebrada ou Ausente | CRITICAL | A credencial é persistida em texto simples, ou derivada por hash rápido de propósito geral, ou por função caseira — sem salt, sem fator de custo — e verificada por comparação de igualdade simples? Verificação decisiva: executar a função sobre entradas distintas e observar colisão; e conferir se há dependência de hashing lento no manifesto. | Qualquer projeto com autenticação | AM-005, AM-031, AM-050 |
| **AP-05** | Rota Privilegiada ou Destrutiva Sem Autenticação Verificável | CRITICAL | Existe rota que executa operação destrutiva em massa, expõe dados de terceiros ou tem path sugerindo privilégio administrativo, e que vai direto do registro ao acesso a dados sem middleware/decorator de verificação de identidade? O fluxo de login emite credencial verificável (assinada, com expiração) ou apenas uma string derivada de forma previsível do identificador do sujeito? O schema modela papéis que nenhuma decisão de autorização consulta? | Universal | AM-002, AM-007, AM-008, AM-035, AM-054 |
| **AP-06** | God Class / God Module | CRITICAL | Existe um único arquivo ou classe que reúne, no mesmo corpo, abertura de conexão de banco, definição de schema, registro de rotas e regra de negócio — de modo que não há fronteira onde inserir uma camada? Sinal de nome: substantivo genérico com sufixo tipo "Manager"/"Handler"/"Util" que não delimita responsabilidade. | Universal | AM-029 |
| **AP-07** | Segredo ou PII Emitido em Log | CRITICAL | Existe chamada de log cujo template interpola dado de portador de cartão, credencial, token, documento de identificação ou segredo de configuração, sem mascaramento ou redação? | Universal | AM-030, AM-021 |
| **AP-08** | Lógica de Negócio Fora da Camada de Serviço | HIGH | Existe decisão de negócio de alto valor (autorização de pagamento, precificação, elegibilidade, transição de estado) ou efeito colateral de negócio (notificação, integração externa) escrito dentro do handler HTTP — ou, na direção inversa, dentro de uma função da camada de acesso a dados, misturado a agregações de consulta? Sinal correlato: o controller inspeciona a *forma* do valor retornado para decidir o status code. | Universal | AM-011, AM-014, AM-032, AM-055 |
| **AP-09** | Acoplamento a Dependência Concreta, Sem Injeção | HIGH | As funções/classes obtêm suas dependências chamando uma factory global no próprio corpo, ou instanciando infraestrutura no construtor, em vez de recebê-las como parâmetro? O composition root constrói o objeto principal sem passar argumento algum? Parâmetros de infraestrutura (destino do banco, porta, verbosidade do driver) estão fixados em literal? A camada de apresentação importa a de infraestrutura, saltando a intermediária? | Universal | AM-010, AM-033 |
| **AP-10** | Estado Global Mutável Compartilhado | HIGH | Existe handle de recurso (conexão, cliente, cache) ou variável mutável em escopo de módulo, escrita pelo caminho de requisição, sem lock e sem política de invalidação — e com a proteção de concorrência do driver explicitamente desabilitada? Sinal correlato: acumulador global estruturalmente incapaz de funcionar (primitivo exportado por valor, nunca lido). | Universal | AM-009, AM-034 |
| **AP-11** | Escrita Multi-etapa Sem Fronteira Transacional | HIGH | Existe sequência de escritas relacionadas sem limite transacional explícito, com retorno antecipado de erro no meio da sequência e sem compensação? Existe verificação de disponibilidade de recurso separada da sua consumação (check-then-act) sem atomicidade? Existe deleção que remove o registro principal deixando dependentes órfãos, em schema sem integridade referencial declarada? | Projetos com ≥2 escritas relacionadas | AM-013, AM-036, AM-041 |
| **AP-12** | Validação de Domínio Inline no Handler | HIGH | As invariantes de domínio (faixa numérica, tamanho de campo, vocabulário fechado, formato) estão escritas como sequência de condicionais com literais dentro do handler HTTP, sem constraint equivalente no schema e sem camada de escrita que as imponha? Agravante decisivo: a mesma invariante aplicada de forma **divergente** entre a rota de criação e a de atualização da mesma entidade. | Universal | AM-012, AM-017, AM-018, AM-040, AM-056, AM-062 |
| **AP-13** | Rota Acoplada Diretamente ao ORM ou Driver | HIGH | Os handlers manipulam a sessão/transação de persistência diretamente e constroem queries a partir das classes de model, sem camada de serviço ou repositório interposta, com a sessão importada como singleton de módulo? Inversão típica a procurar: decisão de serialização de API vivendo no model e decisão de transação vivendo no controller — exatamente trocadas. | Projetos com ORM ou driver direto | AM-057 |
| **AP-14** | Mass Assignment / Bind Não Filtrado de Entrada | HIGH | O payload de entrada é repassado inteiro ao construtor da entidade ou ao update de persistência, sem allowlist explícita de campos — permitindo que o chamador escreva colunas que o contrato não expõe (papel, flag de ativação, identificador de proprietário, timestamps)? | Universal | **domínio** — sem ocorrência local; os 3 alvos atribuem campo a campo |
| **AP-15** | N+1 Aninhado | MEDIUM | Existe consulta a banco disparada dentro de laço que itera o resultado de uma consulta anterior, em dois ou mais níveis, onde uma junção resolveria numa ida só? Agravante: o mapeamento objeto-relacional **já declara o relacionamento** que resolveria por eager loading, ou um cursor novo é alocado por iteração. Variante correlata: agregação numérica calculada em laço na aplicação sobre a tabela inteira, quando exprimível na própria consulta. | Projetos com persistência | AM-015, AM-016, AM-037, AM-039, AM-058, AM-059 |
| **AP-16** | Deprecated API Usage | MEDIUM | Existe chamada a API marcada como deprecated **na versão de runtime efetivamente em uso** (a do ambiente, não a do manifesto), repetida no caminho quente, sem aviso de migração no projeto? Procedimento: obter a versão real do runtime na Fase 1, cruzar as APIs chamadas contra as notas de depreciação dessa versão, e reportar o equivalente moderno para cada ocorrência. Reforço: ausência de linter no projeto explica a sobrevivência da chamada. | Universal | AM-055 (`datetime.utcnow()`, deprecado desde Python 3.12 — o runtime do ambiente). **Sem par cruzado**: observado só no lado Python; limitação registrada. |
| **AP-17** | Duplicação com a Abstração Correta Morta no Repositório | MEDIUM | A mesma regra ou o mesmo bloco de mapeamento aparece copiado em três ou mais pontos **enquanto o repositório já contém a implementação correta que ninguém invoca** — método de domínio na entidade, função utilitária, constante nomeada, ou um diretório de camada inteiro cuja classe não é importada por nenhum caminho de execução? Verificação decisiva: para cada símbolo exportado, contar referências fora do módulo de origem — importar não é usar. | Universal; alto rendimento em projetos parcialmente organizados | AM-016, AM-055, AM-061, AM-062, AM-069, AM-070, AM-071 |
| **AP-18** | Captura Genérica de Exceção e Vazamento de Detalhe Interno | MEDIUM | Existe bloco de captura sem tipo especificado que descarta o objeto de erro sem registro, ou que serializa a representação textual da exceção no corpo da resposta ao cliente — repetido em todos os handlers, sem tratador centralizado e sem distinguir falha de domínio de defeito? Consequência a confirmar: erro de cliente reportado como falha de servidor. | Universal | AM-020, AM-063, AM-064 |
| **AP-19** | Saída de Console como Mecanismo de Log | MEDIUM | A saída direta para stdout é usada como registro de eventos, sem níveis de severidade, timestamp ou destino configurável, e sem import de biblioteca de logging em nenhum arquivo? Reforço: o próprio projeto define um helper de log padronizado que nenhum chamador usa; caminhos de erro respondem ao cliente e descartam o erro. | Universal | AM-021, AM-043, AM-066 |
| **AP-20** | Política de Origem Cruzada Permissiva | MEDIUM | Existe middleware de política de origem cruzada aplicado globalmente com configuração padrão permissiva, cobrindo indistintamente rotas públicas, de escrita e de remoção — em um sistema sem autenticação efetiva? | APIs consumidas por browser | AM-019, AM-067 |
| **AP-21** | DDL e Seed Executados no Boot da Aplicação | MEDIUM | A criação de schema é executada como efeito colateral do import ou do boot, sem ferramenta de migração no manifesto, por comando que só cria tabelas ausentes e nunca altera colunas existentes? Existem dados de demonstração — inclusive credencial administrativa conhecida — inseridos incondicionalmente em qualquer ambiente, no mesmo corpo que cria o schema? Sinal estrutural adicional: definições de tabela sem restrições de integridade declaradas. | Projetos com persistência | AM-022, AM-042, AM-047, AM-068 |
| **AP-22** | Listagem Sem Paginação | MEDIUM | Os endpoints de listagem retornam o conjunto completo sem parâmetro de limite, offset ou cursor, tornando o tamanho da resposta função dos dados e não do contrato? Sinal auxiliar valioso: os próprios artefatos do repositório (comentários, backlog embutido, dados de seed) já descrevem a lacuna. | APIs de leitura de coleção | AM-060 |
| **AP-23** | Contrato de Resposta Inconsistente | MEDIUM | Handlers equivalentes emitem envelopes diferentes — campo de status presente no erro de um recurso e ausente no de outro, erro em texto puro enquanto o sucesso é JSON, ausência de código de erro estável, idiomas misturados no mesmo handler — ou colapsam falha de infraestrutura e recurso inexistente no mesmo status? | APIs | AM-027, AM-044 |
| **AP-24** | Ausência de Rate Limiting no Endpoint de Autenticação | MEDIUM | O endpoint de autenticação (ou qualquer rota que revele existência de conta) aceita tentativas ilimitadas do mesmo chamador, sem contador, backoff ou bloqueio — tornando enumeração e força bruta uma questão de tempo? | APIs com autenticação | **domínio** — sem ocorrência local; nos 3 alvos a autenticação é tão fraca que força bruta é desnecessária, o que **não** significa que o controle exista |
| **AP-25** | Magic Numbers e Vocabulários Literais Inline | LOW | Existe literal numérico sem nome usado como limiar em regra de validação ou de negócio, sem constante nomeada e sem correspondência com restrição declarada no schema? Existe conjunto fechado de valores válidos declarado como lista literal reconstruída dentro do handler, sem enum e sem constraint equivalente? Existe tradução entre valor armazenado e rótulo de negócio embutida na montagem da resposta? | Universal | AM-023, AM-024, AM-074 |
| **AP-26** | Código Morto e Dependências Declaradas e Não Usadas | LOW | Existem símbolos importados e nunca referenciados, símbolos exportados e nunca consumidos, ou dependências declaradas no manifesto e não importadas por nenhum arquivo? Leitura útil do sinal: quando as dependências mortas correspondem exatamente a lacunas apontadas por outros findings (validação declarativa, configuração por ambiente, hashing), elas revelam a arquitetura **pretendida e não implementada**. | Universal | AM-025, AM-045, AM-072, AM-073 |
| **AP-27** | Nomenclatura Pobre e Sombreamento de Builtin | LOW | Existe nome de builtin da linguagem usado como parâmetro ou variável local? Existem identificadores de uma a três letras recebendo campos de payload em handler extenso? A assinatura tem muitos parâmetros posicionais do mesmo tipo primitivo, permitindo troca de ordem sem erro? Os nomes do contrato público divergem do vocabulário do domínio? | Universal | AM-026, AM-046, AM-075 |
| **AP-28** | Ausência de Infraestrutura de Qualidade | LOW | O manifesto não declara dependências de desenvolvimento, script além do de execução, nem versão de runtime; e o repositório não tem arquivo de teste, configuração de lint, exemplo de variáveis de ambiente ou pipeline de CI? Faixas de versão abertas convivem com lockfile? | Universal | AM-049, AM-072 |

### 4.1 Justificativa da composição

**A espinha dorsal são os 6 pares cruzados** da seção "Padrões recorrentes" do README — os únicos com
evidência de que o sinal sobrevive à troca de stack. Mapeamento: AP-02 (hardcoded credential),
AP-03 (credencial na serialização), AP-04 (hash inadequado), AP-15 (N+1 aninhado), AP-12 (validação
inline na rota), AP-16 (deprecated API). Cinco têm ocorrência em Python **e** em Node; AP-16 tem
ocorrência só em Python e carrega essa limitação escrita na própria linha da tabela.

**Os 20 restantes observados** cobrem findings de peso arquitetural que apareceram em uma stack só
mas cujo sinal é estrutural (AP-06 God Class, AP-13 acoplamento ao ORM), ou que apareceram nas duas
mas sem terem sido consolidados como par na tabela do README (AP-05, AP-11, AP-19, AP-21).

**Os 2 de domínio** (AP-14, AP-24) estão marcados como tal e existem por honestidade de catálogo: um
catálogo que só contém o que os 3 fixtures têm falha silenciosamente em qualquer quarto projeto. Um
deles — AP-24 — traz uma observação que vale registrar: sua ausência nos alvos não é virtude, é
consequência de a autenticação ser fraca demais para que força bruta seja necessária.

**AP-17 merece destaque de design.** Ele nasce da nota de calibragem do dossiê de `task-manager-api`,
que observou que "abstração correta existe e é ignorada" é um sinal mais forte que "código morto".
É o anti-pattern de maior rendimento em projetos parcialmente organizados — exatamente o perfil do
projeto 3 — e o que transforma a Fase 3 nesse projeto de "criar camadas" em "ligar as camadas que já
existem". Sem ele, a skill trataria o projeto 3 como se fosse o projeto 1.

---

## 5. Playbook proposto — 18 transformações

Mínimo do enunciado: 8 com código antes/depois. Cada TR terá, no `refactor-playbook.md`,
**pré-condição, passos, código antes/depois em ≥2 stacks (Python e JavaScript), riscos e verificação
pontual**.

| ID | Resolve | Transformação (1 frase) |
|---|---|---|
| **TR-01** | AP-02 | Extrair toda configuração sensível para um módulo `config/` que lê variáveis de ambiente com *fail-fast* na ausência, publicar um arquivo de exemplo sem valores reais, e desligar debug fora de desenvolvimento. |
| **TR-02** | AP-01 | Substituir concatenação por parâmetros vinculados em toda query, e remover ou fechar atrás de allowlist qualquer endpoint que aceite consulta/comando arbitrário no payload. |
| **TR-03** | AP-04 | Trocar a derivação de senha por primitiva lenta com salt e fator de custo da plataforma, verificar por comparação em tempo constante, e migrar os registros existentes por reidratação no próximo login. |
| **TR-04** | AP-03 | Separar a entidade de persistência do DTO de saída, criando um serializador por contexto que projeta uma allowlist de campos — nenhum campo de credencial atravessa a fronteira da resposta. |
| **TR-05** | AP-05, AP-24 | Introduzir middleware de autenticação com credencial assinada e expirável, aplicá-lo por rota com decisão de autorização por papel, e negar por padrão em vez de permitir por padrão. |
| **TR-06** | AP-06, AP-13 | Decompor a God Class fatiando por responsabilidade — Model, Repository, Service, Controller, Router — extraindo primeiro a persistência, depois a regra, e deixando o roteamento como casca fina. |
| **TR-07** | AP-08 | Mover regra de negócio e efeito colateral do handler (e da camada de dados) para um Service, deixando o controller com três linhas: parse da entrada, chamada ao service, mapeamento do resultado para resposta. |
| **TR-08** | AP-12, AP-14 | Centralizar as invariantes num validador declarativo por entidade, invocado pelo service, com allowlist explícita de campos vinculáveis, e espelhar as invariantes como constraints no schema. |
| **TR-09** | AP-09, AP-10 | Inverter a resolução de dependências: o composition root instancia e injeta, ninguém chama factory global no próprio corpo, e o estado de módulo mutável vira instância com ciclo de vida explícito. |
| **TR-10** | AP-11 | Envolver a sequência de escritas relacionadas numa unidade de trabalho transacional com rollback no caminho de erro, e substituir check-then-act por operação atômica ou por constraint no banco. |
| **TR-11** | AP-15 | Substituir o laço de consultas por uma única ida ao banco — junção, eager loading declarado ou carga em lote por conjunto de chaves — e mover agregação de laço de aplicação para a cláusula da consulta. |
| **TR-12** | AP-16 | Trocar cada chamada deprecated pelo equivalente moderno da versão de runtime em uso, e fixar a regra num linter para que a substituição não regrida. |
| **TR-13** | AP-18, AP-23 | Instalar um error handler centralizado com mapa exceção-de-domínio → status HTTP e envelope de resposta único, eliminando os blocos de captura genérica dos handlers. |
| **TR-14** | AP-19, AP-07 | Substituir a saída de console por um logger com níveis, timestamp e destino configurável, e aplicar redação nos campos sensíveis antes de qualquer emissão. |
| **TR-15** | AP-17, AP-26 | Consolidar cada duplicação na abstração correta que já existe no repositório, ligá-la ao caminho de execução, e remover o que sobrar de morto — inclusive dependências declaradas e não usadas. |
| **TR-16** | AP-21 | Extrair DDL e seed do boot para migração versionada e script de seed separado, declarando no schema as restrições de integridade que hoje só existem em código (ou em lugar nenhum). |
| **TR-17** | AP-22 | Introduzir paginação por limite e offset (ou cursor) com valores default explícitos, preservando a forma do item para não quebrar consumidores existentes. |
| **TR-18** | AP-25, AP-27, AP-20 | Nomear literais em constantes e enums, renomear identificadores para o vocabulário do domínio, eliminar sombreamento de builtin, e restringir a política de origem cruzada a uma allowlist por ambiente. |

**Cobertura:** os 28 anti-patterns são endereçados por 18 TRs. Os únicos sem TR próprio são AP-28
(ausência de infraestrutura de qualidade), que é **reportado mas não corrigido** — instalar test
runner, linter e CI está fora do escopo declarado em §1.4 — e os agravantes que já são consequência
de outro TR.

---

## 6. Estratégia de agnosticismo

### 6.1 Como as heurísticas evitam acoplamento

O acoplamento a stack entra por três portas, e cada uma tem uma barreira:

**Porta 1 — o sinal cita sintaxe.** Um sinal escrito como "`db.session.commit()` dentro de rota"
funciona em Flask-SQLAlchemy e em nada mais. Barreira: o sinal descreve a **aresta do grafo** — "a
camada de apresentação manipula a transação de persistência diretamente" — que é verificável em
qualquer stack. A prova empírica de que isso funciona está no README: o N+1 apareceu como cursor
realocado no `sqlite3` puro, como lazy load do SQLAlchemy e como callback aninhado no driver do
Node — três sintaxes, uma pergunta.

**Porta 2 — a estrutura-alvo assume um framework.** Uma árvore MVC fixa quebra em qualquer projeto
que não siga a convenção do framework que a inspirou. Barreira: `mvc-guidelines.md` define
**responsabilidades e direção de dependência** como o normativo, e a árvore de diretórios como
*uma* materialização, com variantes por stack e uma regra de precedência — a convenção idiomática
da stack detectada vence o layout genérico.

**Porta 3 — a validação assume um comando.** Barreira: `validation-protocol.md` deriva o comando de
boot do manifesto detectado na Fase 1 (script declarado > entry point declarado > convenção da
stack), e define "subiu" por evidência observável — porta escutando, processo vivo após N segundos,
primeira requisição respondida — nunca por string de log de um framework específico.

### 6.2 As 5 regras de escrita dos arquivos de referência

Regras normativas. Um arquivo de referência que viole qualquer uma delas volta para revisão.

> **R1 — Regra do sinal estrutural.**
> Todo sinal descreve **forma**: posição na camada, aresta do grafo de dependências, relação entre
> dois pontos do código, ou propriedade observável de execução. Nunca token de linguagem, nome de
> função de biblioteca, nem sintaxe. Teste de conformidade: *o sinal continua verdadeiro se o
> projeto for reescrito em outra linguagem?* Se não, reescreva.

> **R2 — Regra da pergunta operacional.**
> Todo sinal é uma pergunta binária respondível **lendo o código**, cuja resposta "sim" produz um
> par `arquivo:linha` + bloco de código literal. Adjetivos de qualidade — "mal estruturado",
> "código ruim", "acoplado demais" — são proibidos como sinal, porque não são falsificáveis.

> **R3 — Regra do vocabulário de papel.**
> Usar termos de **papel arquitetural**: handler, camada de acesso a dados, composition root,
> entidade de persistência, DTO de saída, middleware. Nomes de framework, ORM, driver ou biblioteca
> só aparecem dentro de blocos explicitamente rotulados `Manifestações por stack` ou
> `Exemplo — <stack>`. Nunca no corpo normativo, nunca no sinal.

> **R4 — Regra do exemplo plural.**
> Toda sintaxe concreta vem em pares: **no mínimo duas stacks** (Python e JavaScript, dado o
> conjunto de teste), lado a lado, rotuladas. Um exemplo de stack única no playbook é lido pelo
> agente como *a* forma correta e vira acoplamento por imitação — a falha mais provável e mais
> difícil de detectar em revisão.

> **R5 — Regra do contra-exemplo obrigatório.**
> Todo anti-pattern declara explicitamente **quando NÃO é finding**. Sem esse limite superior, o
> agente encontra todos os 28 em todo projeto e o relatório vira preenchimento de cota. Corolário
> operacional, derivado da disciplina dos dossiês manuais: o relatório da Fase 2 **deve** conter a
> seção "o que não foi encontrado" para as categorias nomeadas da escala de severidade.

**Regra de higiene, transversal e não negociável:** nenhum arquivo de referência cita nome de
arquivo, classe, função, variável, rota ou string literal dos 3 projetos-alvo. A skill é copiada
para dentro deles; qualquer referência cruzada é acoplamento disfarçado de exemplo. Os identificadores
`AM-XXX` aparecem apenas na coluna de procedência deste documento de design — não nos arquivos da
skill.

---

## 7. Riscos e trade-offs

| # | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| R-01 | **Fase 3 quebra a aplicação** e o agente declara sucesso mesmo assim | Alta | Crítico — reprova o critério de aceite em qualquer projeto | Baseline capturado na Fase 1 **antes** de qualquer escrita; smoke test completo ao fim de **cada onda**, com commit só na onda verde (DECISÃO-04); boot após cada TR dentro da onda; §3.4 proíbe declarar sucesso sem evidência de execução; onda vermelha → `reset --hard` ao último commit verde e parada. |
| R-02 | **Contexto estoura** carregando 2.500 linhas de referência de uma vez | Alta | Alto — a Fase 3 degrada exatamente quando precisa de mais precisão | Progressive disclosure em dois eixos (§2.2): playbook lido por TR acionado, catálogo só na Fase 2, guidelines só na Fase 3. Pico real ≈ 1.100 linhas. |
| R-03 | **Acoplamento por imitação:** o agente copia a sintaxe do exemplo do playbook em vez de aplicar o padrão | Alta | Alto — refatoração Python com idioma de Node, ou vice-versa | R4 (exemplo em ≥2 stacks, lado a lado). Instrução imperativa no topo do playbook: *"Adapte o padrão ao idioma da stack detectada na Fase 1. Os exemplos ilustram a forma, não a sintaxe a copiar."* |
| R-04 | **Preenchimento de cota:** o agente reporta os 28 APs em todo projeto para parecer completo | Média | Alto — destrói a credibilidade do relatório e desperdiça a Fase 3 | R5 (contra-exemplo obrigatório por AP); exigência de evidência literal em 2.2 (sem `arquivo:linha` + bloco real, descarte); seção "o que não foi encontrado" obrigatória no template. |
| R-05 | **Projeto 3 tratado como monolito:** a skill recria camadas que já existem | Média | Alto — refatoração destrutiva num projeto que precisava de ligação, não de criação | AP-17 no catálogo; **regra de alcançabilidade** em `mvc-guidelines.md` (DECISÃO-01) decidindo adoção por dado observável; Fase 1 mapeia a arquitetura **efetiva** (grafo de imports), não a árvore de pastas; 2.6 obriga registrar o conteúdo removido antes de removê-lo. |
| R-06 | **Gate humano contornado:** o agente interpreta silêncio, ou uma resposta ambígua, como aprovação | Média | Crítico — viola requisito explícito do enunciado | Gate como última instrução da Fase 2, em forma imperativa, com as 4 regras de §3; resposta parcial exige replanejar e reapresentar; nenhuma escrita em código-fonte antes do "y" (a exceção do relatório está justificada em §3.1). |
| R-07 | **Detecção de deprecated cega:** o agente checa contra a versão do manifesto, não a do ambiente | Média | Médio — falso negativo silencioso no único AP exigido nominalmente pelo enunciado | Fase 1.3 obriga obter o runtime **efetivo** do ambiente; AP-16 declara o procedimento de cruzamento como parte do sinal. Insumo direto de AM-055, onde o projeto não declara versão alguma e a depreciação só é visível contra o interpretador real. |
| R-08 | **SKILL.md ultrapassa 500 linhas** conforme as fases ganham detalhe | Média | Médio — degrada a aderência do agente à orquestração | Orçamento fixado em ~190 linhas com folga de 60%; qualquer conteúdo que *ensine* migra para reference por construção (§2.1). Verificação de tamanho no checklist de implementação. |
| R-09 | **Refatoração muda o contrato da API** e os endpoints do baseline param de responder como antes | Média | Alto | Preservação de superfície (DECISÃO-03): path, verbo e status intactos por regra; toda mudança de shape declarada na seção Breaking changes **do relatório da Fase 2** e aprovada no gate; 3.3 trata shape alterado e não declarado como regressão. |
| R-10 | **Granularidade de controller inconsistente** entre os 3 projetos, enfraquecendo a prova de agnosticismo | Média | Médio | Critério determinístico em `mvc-guidelines.md`: um controller por agregado de domínio, fatiado por sub-recurso ao ultrapassar **10 handlers ou 250 linhas** (DECISÃO-02). |
| R-11 | **Escopo da Fase 3 explode:** 28 APs × N ocorrências viram uma reescrita | Média | Alto — sessão longa, resultado não revisável, risco de quebra proporcional | Ondas por severidade com commit por onda verde (DECISÃO-04): a reescrita fica revisável em 4 diffs coerentes em vez de um só; o plano apresentado no gate já vem agrupado por onda; AP-28 explicitamente não corrigido. |
| R-12 | **Índice do playbook dessincroniza** do corpo após edições | Baixa | Médio — o agente carrega a seção errada ou não encontra o TR | Âncoras estáveis no formato `## TR-NN — <nome>`; checklist de consistência índice↔âncoras no fim da implementação. |
| R-13 | **`description` genérica demais** e a skill dispara em pedidos de code review de um arquivo | Baixa | Médio — desperdício de contexto e resposta fora de propósito | Cláusula negativa final na `description` (§1.2). |
| R-14 | **Onda 1 concentra risco desproporcional:** absorve o esqueleto MVC mais todos os CRITICAL, e é a onda com maior chance de terminar vermelha | Alta | Alto — uma Onda 1 vermelha faz o `reset` voltar ao baseline, descartando todo o trabalho da sessão | Boot após **cada TR** dentro da onda, não só ao fim (§3.2a): o defeito é localizado no TR, e o agente conserta antes de acumular. Ordem interna da Onda 1 fixada em `refactor-playbook.md` — TR-01 (config) e TR-06 (decomposição) primeiro, porque tudo o mais depende da estrutura existir. |
| R-15 | **Commit de onda com validação incompleta:** o agente commita declarando a onda verde sem ter rodado o smoke test completo contra o baseline | Média | Alto — destrói a garantia do rollback: o "último commit verde" não é verde | `validation-protocol.md` define o commit como **consequência** de evidência de execução, nunca como passo autônomo. A mensagem de commit da onda deve citar a contagem de endpoints verificados; sem esse dado, não há commit. |

### 7.1 Trade-offs assumidos conscientemente

| Decisão | Alternativa rejeitada | Por que assim |
|---|---|---|
| 28 anti-patterns (mínimo era 8) | Catálogo enxuto de 8-10 | O insumo empírico são 75 findings validados; um catálogo de 8 desperdiçaria a análise manual e falharia em achar 5 findings no projeto 3, que quase não tem CRITICAL. O custo — contexto — é pago com progressive disclosure. |
| Sinal em prosa longa, não em regex | Regras `grep`/AST executáveis | Regex acopla a sintaxe e quebra na troca de stack — exatamente o que o desafio testa. Prosa estrutural é o que sobreviveu à travessia Python↔Node nos 6 pares cruzados. Custo aceito: detecção depende do julgamento do agente, não é determinística. |
| Relatório gravado antes do gate | Gravar só depois do "y" | O enunciado exige o relatório em `reports/` independentemente da Fase 3; e o trabalho da Fase 2 precisa sobreviver a um "n". Justificado em §3.1. |
| 6 arquivos de referência | 5, com validação dentro do SKILL.md | Validação é conhecimento, não orquestração. Justificado em §2.1. |
| Fase 3 em 4 ondas de severidade, commit por onda verde | Aplicar tudo e validar no fim | Uma pilha de 40 mudanças não bootáveis é indepurável, e deixaria o critério de aceite "aplicação funciona" refém de depuração cega. Custo: mais ciclos de execução e 4 commits por projeto em vez de 1. |
| Histórico linear, sem branch por projeto | Branch de trabalho descartável | O ponto de retorno já existe no commit de baseline, e as ondas somam 4 pontos adicionais. O histórico linear é o que o avaliador lê. Custo: um `reset --hard` mal executado perde trabalho — mitigado por R-15. |

---

## 8. Decisões tomadas

> As cinco incertezas levantadas na primeira versão deste documento foram decididas em revisão
> humana. Cada uma está registrada abaixo com a decisão literal, a justificativa e as **consequências
> propagadas** para as seções 2, 3 e 7 — que já foram atualizadas. Nada aqui permanece em aberto.
>
> Duas decisões divergem da minha recomendação original (DECISÃO-02 e DECISÃO-03) e uma rejeita o
> enquadramento que eu havia proposto (DECISÃO-04). Registro a divergência por rastreabilidade, não
> por ressalva: as três razões apresentadas são melhores que as minhas e estão anotadas como tal.

---

### DECISÃO-01 — Camada preexistente é adotada por alcançabilidade

**Decidido: opção (c), com o registro prévio como finding.**

> Diretório de camada preexistente é adotado **se e somente se** ao menos um símbolo seu for
> alcançável a partir do entry point. Caso contrário é tratado como AP-26 (código morto) e
> substituído. O conteúdo removido é registrado como finding na Fase 2 **antes** da remoção.

**Justificativa.** A regra é agnóstica, não uma exceção escrita para o projeto 3 — e uma skill
copiável não pode conter exceções nomeadas para os projetos onde foi testada. O critério é dado
observável (alcançabilidade no grafo de imports a partir do entry point), não julgamento estético,
o que a torna reproduzível entre stacks e entre executores. O registro prévio como finding fecha a
única brecha real da opção (c): nada desaparece silenciosamente, e o humano vê no relatório da Fase 2
o que a Fase 3 vai remover — antes do gate, com tempo de vetar.

**Aplicada ao projeto 3, resulta em substituir `services/`**: sua única classe não é importada por
nenhum módulo (AM-070), portanto é inalcançável. As credenciais de SMTP hardcoded que ela carrega
(AM-053, CRITICAL) continuam sendo reportadas como finding — a remoção da classe não apaga o registro
de que o segredo esteve versionado, o que importa porque um segredo commitado permanece no histórico
independentemente de o arquivo sobreviver.

**Propagado para:** §2 (`mvc-guidelines.md` ganha a regra de alcançabilidade), §3 (novo passo 2.6 na
Fase 2), §7 (R-05).

---

### DECISÃO-02 — Um controller por agregado, corte em 10 handlers ou 250 linhas

**Decidido: opção (a), com limiar afrouxado de 8/200 para 10/250.**

> Um controller por agregado de domínio. Fatiar por sub-recurso quando ultrapassar **10 handlers
> OU 250 linhas**, o que ocorrer primeiro.

**Justificativa (do revisor, e melhor que a minha).** O limiar 8/200 que eu propus fragmentaria a
árvore antes/depois: com 4 domínios, um corte agressivo produziria 6 ou 7 controllers, distanciando o
resultado do exemplo do enunciado — que mostra 2 controllers para 4 domínios. A árvore antes/depois
é um artefato de leitura do avaliador, e fragmentá-la custa legibilidade sem ganho arquitetural
correspondente. 10/250 mantém o corte disponível como válvula para o caso patológico sem acioná-lo
no caso comum.

**Registro da divergência:** eu havia proposto 8/200 e declarado o número arbitrário. Era arbitrário
mesmo; o critério do revisor — proximidade com o exemplo do enunciado e legibilidade da comparação
antes/depois — é um critério de verdade, e o meu não era.

**Propagado para:** §2 (`mvc-guidelines.md`), §7 (R-10).

---

### DECISÃO-03 — Preservação de superfície, com Breaking changes já na Fase 2

**Decidido: opção (b), com emenda.**

> Path, verbo e status code preservados. O corpo pode ser normalizado. **Todas** as mudanças de
> shape aparecem numa seção "Breaking changes" **do relatório da Fase 2**, não apenas do relatório
> da Fase 3.

**Justificativa da emenda (do revisor).** A emenda resolve uma tensão que eu havia deixado mal
fechada. Na minha proposta original, (b) documentava as mudanças de shape *depois* de aplicá-las —
o humano descobria o que tinha mudado quando já estava feito. A opção (c) resolvia isso aprovando
item a item, ao custo de transformar o gate num questionário e de tornar as execuções nos 3 projetos
não uniformes.

Antecipar a seção para a Fase 2 fica com o melhor dos dois: o humano aprova as mudanças de shape
**antes** de qualquer escrita, e aprova como conjunto, num único "y". O gate continua sendo uma
decisão binária, e passa a ser uma decisão **informada** — que é o que o requisito de confirmação do
enunciado existe para garantir.

Consequência de projeto que isso força, e é boa: a Fase 2 precisa **prever** o efeito de cada TR
sobre o contrato de resposta antes de executá-lo. Isso é um pouco mais de trabalho de análise e
elimina a possibilidade de a Fase 3 justificar uma mudança de shape a posteriori.

**Regra derivada, escrita em 3.3:** shape alterado que **não** conste da seção aprovada é tratado
como **regressão**, não como melhoria — mesmo que o resultado pareça melhor. O critério é a
conformidade com o que foi aprovado, não o gosto do executor.

**Registro da divergência:** minha recomendação era (b) sem a emenda; a emenda a torna estritamente
superior sem custo perceptível.

**Propagado para:** §2 (`report-template.md`), §3 (novo passo 2.8; conteúdo do gate; critério 3.3),
§7 (R-09).

---

### DECISÃO-04 — Todas as severidades, em 4 ondas com validação e commit por onda

**Decidido: o enquadramento da minha INCERTEZA-04 foi rejeitado, e com razão.**

> A pergunta não é *quanto* corrigir — é *com que cadência validar*. Corrigir TODAS as severidades,
> em ondas: CRITICAL → HIGH → MEDIUM → LOW. Ao fim de cada onda: smoke test contra o baseline +
> commit. Se uma onda falha: `reset` para o último commit verde, PARE E REPORTE.
> `validation-protocol.md` descreve essa cadência.

**Justificativa (do revisor).** Eu havia formulado a incerteza como um trade-off entre completude e
risco — "corrigir tudo ou cortar por severidade?" — e recomendado corrigir tudo. A recomendação
estava certa e a pergunta estava errada: cortar findings nunca foi a forma de controlar o risco de
28 APs, porque cortar reduz a entrega sem tornar o que sobra mais seguro. O que controla o risco é a
**frequência de validação**. Com validação só no fim, o critério de aceite "aplicação funciona"
fica refém de depurar às cegas no meio de ~40 mudanças acumuladas — o modo de falha mais provável
da Fase 3, e o mais caro de sair.

A severidade é o eixo natural das ondas por dois motivos independentes: já é a ordem do relatório,
então plano e relatório têm a mesma espinha; e coloca o trabalho de maior valor nos primeiros
commits, de modo que uma interrupção em qualquer ponto deixa o projeto estritamente melhor do que
começou.

**Consequência estrutural que isso força.** A ordem antiga do §3.1 era "estrutura antes de conteúdo",
que não é uma severidade. A colisão se resolve sozinha: TR-01 (config) e TR-06 (decomposição da God
Class) resolvem AP-02 e AP-06, ambos CRITICAL — o esqueleto MVC **é** a Onda 1. Não há onda 0, o que
preserva exatamente os 4 pontos de retorno acordados. Justificado em §3.2.

**Custo aceito, e é o mais pesado do design:** a Onda 1 concentra o esqueleto inteiro mais todos os
CRITICAL, e é a onda com maior probabilidade de terminar vermelha — com o `reset` voltando ao
baseline e descartando a sessão. Mitigado por boot após **cada TR** dentro da onda, não só ao fim:
o commit é o ponto de retorno, o boot é o localizador do defeito. Registrado como R-14.

**Propagado para:** §2 (`validation-protocol.md` e `refactor-playbook.md` ganham a onda), §3 (fluxo
da Fase 3 reescrito; nova §3.2), §7 (R-01, R-11, novos R-14 e R-15), §7.1.

---

### DECISÃO-05 — Sem branch por projeto; histórico linear

**Decidido: rejeitada a branch de trabalho.**

> O commit de baseline já é o ponto de retorno (`git reset --hard`). Com as ondas da DECISÃO-04 são
> 4 pontos de retorno adicionais por projeto, tudo em histórico linear.

**Justificativa (do revisor).** A branch resolvia um problema que a DECISÃO-04 já resolve melhor.
Meu argumento era "o custo é um comando, o benefício é rollback trivial" — mas o rollback já é
trivial com o commit de baseline, e a granularidade que a branch oferecia era de um ponto só,
contra os cinco que as ondas dão. O argumento decisivo é de leitura: **o histórico linear é o que o
avaliador vai ler.** Uma branch por projeto, em 3 projetos, produz um grafo que exige explicação —
e explicar a topologia do repositório não é parte da entrega.

**Consequência:** a pré-condição de working tree limpo deixa de ser conveniência e vira requisito
duro. Sem ela o commit de baseline não é um ponto de retorno confiável, e o `reset --hard` da
DECISÃO-04 destrói trabalho não commitado do usuário. A verificação já existia no fluxo; agora
carrega o SHA do baseline explicitamente (passo 2 das pré-condições).

**Risco correlato que isso cria:** um commit de onda declarado verde sem o smoke test ter rodado
de fato envenena a cadeia inteira de rollback — o "último commit verde" deixa de ser verde.
Registrado como R-15, com a mitigação de que o commit é consequência de evidência de execução, e a
mensagem de commit precisa citar a contagem de endpoints verificados.

**Propagado para:** §3 (pré-condições; remoção do antigo passo 3.0), §7 (R-01, novo R-15), §7.1.

---

### 8.1 Nenhuma decisão em aberto

As cinco incertezas estão fechadas. `references/mvc-guidelines.md` — o arquivo que estava bloqueado
por DECISÃO-01, 02 e 03 — tem agora todo o seu conteúdo normativo determinado, e é insumo tanto do
julgamento de AP-06, AP-08, AP-13 e AP-17 na Fase 2 quanto de toda a Fase 3.

Se algo novo emergir durante a implementação, entra aqui como `DECISÃO-06+` com a mesma estrutura —
decisão, justificativa, propagação — e não como uma anotação solta no arquivo em que apareceu.

---

## Estado

**Documento de design concluído e decidido. Nenhum arquivo da skill foi criado — `.claude/skills/`
não foi tocado, conforme a restrição desta etapa.**

Bloqueios removidos: as cinco decisões da seção 8 fixam o conteúdo normativo de
`references/mvc-guidelines.md`, `references/validation-protocol.md` e `references/report-template.md`,
que eram os três arquivos com conteúdo indeterminado.

**Ordem de implementação sugerida para a próxima etapa**, do mais restritivo ao mais dependente:

1. `references/mvc-guidelines.md` — fixa a arquitetura-alvo; todo o resto se ancora nele
2. `references/antipattern-catalog.md` — os 28 APs, o arquivo de maior volume
3. `references/refactor-playbook.md` — os 18 TRs, já rotulados por onda
4. `references/project-analysis.md` e `references/validation-protocol.md` — as pontas do fluxo
5. `references/report-template.md` — depende do catálogo e da seção Breaking changes
6. `SKILL.md` — escrito **por último**, porque orquestra arquivos que já existem e cujo tamanho
   real já é conhecido, evitando que o orçamento de ~190 linhas seja estimado no vazio
