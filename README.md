# Desafio — Skill de Auditoria e Refatoração Arquitetural

> Enunciado original: [`docs/enunciado.md`](docs/enunciado.md)

## Índice
- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)

## A) Análise Manual

### Metodologia

Os três projetos foram lidos integralmente, arquivo a arquivo, em auditoria somente leitura — nenhuma
linha foi alterada durante a análise. Cada projeto gerou um dossiê próprio em
`.planning/analise-manual/`, aberto por um levantamento de contexto (linguagem, framework,
dependências, LOC, tabelas do banco) e por uma descrição da arquitetura efetiva, não da pretendida.
Um finding só foi registrado com **evidência literal**: o bloco de código real copiado do arquivo,
com `arquivo:linha` obtido por leitura direta, mais severidade, impacto e correção esperada. Findings
sem evidência literal foram descartados. Os dossiês também registram explicitamente **o que não foi
encontrado** — `ecommerce-api-legacy` e `task-manager-api` não têm SQL Injection (todo o acesso a
dados usa bind de parâmetros ou ORM) e `task-manager-api` não tem God Class — embora ambas as
categorias constem da escala de severidade do desafio. Registrar essas ausências é o que impede a
auditoria de virar preenchimento de cota.

A validação foi **estratificada** e executada com o script `.planning/validar.sh`, que imprime o
código-fonte real no range citado por cada finding, permitindo comparar linha a linha o arquivo com o
bloco de Evidência do dossiê. Os 33 findings CRITICAL e HIGH foram conferidos a 100%; MEDIUM e LOW
passaram por amostragem de ~30%, sem divergências. O resultado: nenhum finding foi descartado por
linha inexistente ou evidência parafraseada; AM-005, AM-029 e AM-052 tiveram a evidência ampliada
porque o recorte original era mais estreito que a acusação do título, e AM-054 foi reclassificado de
HIGH para CRITICAL (um token no formato `fake-jwt-token-<id>` é forjável por qualquer chamador, o que
equivale funcionalmente à ausência de autenticação). Essa análise precedeu deliberadamente a
construção da skill: o catálogo de anti-patterns da skill precisa ser derivado de defeitos observados
em código real, com evidência conferida, e não de uma lista genérica escrita de memória. Cada dossiê
fecha com uma tabela de **sinais genéricos** — a mesma detecção reescrita de forma agnóstica de
projeto — e são esses sinais, não os findings, que alimentam a skill.

> As tabelas por projeto abaixo são um **recorte curado**: todos os CRITICAL e HIGH, mais MEDIUM/LOW
> representativos. Os 75 findings completos, com evidência literal, impacto e correção esperada, estão
> em [`.planning/analise-manual/`](.planning/analise-manual/).

### `code-smells-project` — Python 3.12 / Flask 3.1.1 + SQLite (driver `sqlite3` direto)

| ID | Severidade | Anti-pattern | Arquivo:Linha | Por que é relevante |
|---|---|---|---|---|
| AM-001 | CRITICAL | SQL Injection por concatenação de strings | `models.py:105-111` | Senha do payload entra crua no `WHERE`: bypass total de login e leitura ou escrita de qualquer tabela por chamador anônimo. |
| AM-002 | CRITICAL | Endpoint público de execução arbitrária de SQL | `app.py:59-78` | `POST /admin/query` executa SQL do corpo sem autenticação — equivale a publicar um console de banco na internet. |
| AM-003 | CRITICAL | Credencial hardcoded e debug ativo no bootstrap | `app.py:6-9` | `SECRET_KEY` literal versionada e `debug=True` em `0.0.0.0` deixam o console Werkzeug alcançável na rede. |
| AM-004 | CRITICAL | Segredo vazado no endpoint de health | `controllers.py:285-290` | `GET /health` público devolve `secret_key`, caminho do banco e flag de debug a qualquer `curl` anônimo. |
| AM-005 | CRITICAL | Senhas armazenadas e comparadas em texto puro | `database.py:75-79` | Coluna `senha` é TEXT cru e o login compara string direta: qualquer backup ou injeção expõe credenciais reais. |
| AM-006 | CRITICAL | Credencial exposta na serialização de usuários | `models.py:79-86` | Um `GET /usuarios` anônimo devolve e-mail e senha em texto puro de toda a base, inclusive do admin. |
| AM-007 | CRITICAL | Endpoint destrutivo sem autenticação | `app.py:47-57` | Um `POST` sem token apaga as quatro tabelas; com CORS liberado, qualquer site dispara a perda total. |
| AM-008 | HIGH | Ausência completa de autenticação e autorização | `controllers.py:176-180` | O login não emite credencial verificável e nenhuma das 17 rotas consulta identidade ou papel. |
| AM-009 | HIGH | Conexão singleton global mutável entre threads | `database.py:4-11` | Conexão única sem lock faz requisições concorrentes compartilharem transação, e impede substituí-la em teste. |
| AM-010 | HIGH | Acoplamento estático às camadas inferiores, sem DI | `models.py:1-6` | Cada função resolve a própria dependência via `get_db()`: nada é testável isolado nem substituível. |
| AM-011 | HIGH | Efeito colateral de negócio dentro do controller | `controllers.py:205-210` | A notificação do pedido vive no handler HTTP; qualquer outro caminho de criação deixa de notificar silenciosamente. |
| AM-012 | HIGH | Regras de validação de domínio no controller | `controllers.py:43-54` | As invariantes só existem no `POST`; o `PUT` da mesma entidade aceita o que a criação rejeita. |
| AM-013 | HIGH | Escrita multi-etapa sem transação (check-then-act) | `models.py:139-146` | Verificação e baixa de estoque não são atômicas, e o `return` de erro sem rollback contamina a conexão compartilhada. |
| AM-014 | HIGH | Regra de precificação na camada de acesso a dados | `models.py:256-262` | As faixas de desconto — regra mais volátil do e-commerce — estão codificadas dentro da função de relatório. |
| AM-015 | MEDIUM | N+1 aninhado na listagem de pedidos | `models.py:187-193` | `GET /pedidos` custa `1 + P + (P × I)` queries: 100 pedidos de 5 itens viram 601 round-trips. |
| AM-017 | MEDIUM | Bloco de validação copiado entre criação e atualização | `controllers.py:74-79` | Cópia literal de `controllers.py:30-35` que já divergiu: duas rotas aplicam contratos diferentes à mesma entidade. |

### `ecommerce-api-legacy` — JavaScript (CommonJS) / Node + Express 4.22.1 + `sqlite3`

| ID | Severidade | Anti-pattern | Arquivo:Linha | Por que é relevante |
|---|---|---|---|---|
| AM-028 | CRITICAL | Credenciais e chave de gateway hardcoded | `src/utils.js:1-7` | Senha de banco e chave `pk_live_` versionadas — e sequer são usadas: segredo exposto sem prestar função alguma. |
| AM-029 | CRITICAL | God Class | `src/AppManager.js:4-11` | Uma classe de 141 linhas concentra conexão, DDL, rotas e regra de negócio: não há fronteira onde inserir camadas. |
| AM-030 | CRITICAL | Número de cartão e chave do gateway em log | `src/AppManager.js:43-45` | Cada checkout imprime o cartão completo e a chave de produção em stdout — violação direta de PCI-DSS. |
| AM-031 | CRITICAL | Função de derivação de senha criptograficamente inútil | `src/utils.js:17-23` | Sem salt e determinística: `"123456"` e `"123"` colidem, reduzindo todo o espaço de senhas a 4.096 valores. |
| AM-032 | HIGH | Autorização de pagamento embutida no handler | `src/AppManager.js:46-48` | A aprovação é um ternário sobre o primeiro dígito do cartão, dentro do callback da rota Express. |
| AM-033 | HIGH | Acoplamento a dependências concretas, sem injeção | `src/app.js:5-10` | O composition root não injeta nada; a classe abre o próprio SQLite `:memory:` e fixa a porta em literal. |
| AM-034 | HIGH | Estado global mutável exportado por módulo | `src/utils.js:9-15` | `globalCache` cresce sem TTL e nunca é lido; `totalRevenue`, primitivo CommonJS, jamais propaga reatribuição. |
| AM-035 | HIGH | Rotas administrativa e destrutiva sem autenticação | `src/AppManager.js:80-84` | Um `GET` anônimo devolve faturamento e PII dos alunos; um `DELETE` anônimo remove qualquer usuário. |
| AM-036 | HIGH | Checkout multi-etapa sem transação nem rollback | `src/AppManager.js:50-57` | Quatro `INSERT` aninhados sem `BEGIN`: falha no pagamento deixa a matrícula gratuita persistida no banco. |
| AM-037 | HIGH | Concorrência coordenada por contador manual | `src/AppManager.js:92-99` | `err` nunca é verificado antes de `.length`: derruba o processo, ou o contador não zera e a requisição pendura. |
| AM-038 | HIGH | Credencial default silenciosa no checkout | `src/AppManager.js:66-69` | Conta criada sem `pwd` recebe a senha `"123456"` sem avisar o titular nem exigir troca obrigatória. |
| AM-039 | MEDIUM | N+1 em cascata de três níveis no relatório | `src/AppManager.js:102-107` | Custa `1 + C + (C × E × 2)` queries: 20 cursos de 50 matrículas geram 2.021 idas ao banco. |
| AM-040 | MEDIUM | Validação de entrada por teste de falsy | `src/AppManager.js:29-35` | Só testa presença de quatro campos; um `card` não-string lança `TypeError` em callback e derruba o processo. |
| AM-045 | LOW | Import morto e driver carregado em `verbose()` | `src/AppManager.js:1-2` | `totalRevenue` importado e nunca usado sugere um acumulador que não existe; flag de depuração ativa em qualquer ambiente. |

### `task-manager-api` — Python 3.12 / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (ORM)

| ID | Severidade | Anti-pattern | Arquivo:Linha | Por que é relevante |
|---|---|---|---|---|
| AM-050 | CRITICAL | Senhas protegidas por MD5 sem salt | `models/user.py:27-32` | MD5 sem salt nem fator de custo é reversível por rainbow table, e a política mínima de senha é 4 caracteres. |
| AM-051 | CRITICAL | Serialização do model expõe o hash de senha | `models/user.py:16-25` | `to_dict()` projeta `password` em cinco respostas — inclusive no login e no `GET /users/<id>` anônimo. |
| AM-052 | CRITICAL | Chave secreta hardcoded e debug em interface pública | `app.py:11-15` | Chave literal versionada e `debug=True` em `0.0.0.0`; `python-dotenv` está no manifesto e nunca é importado. |
| AM-053 | CRITICAL | Credenciais de SMTP hardcoded no construtor | `services/notification_service.py:5-10` | Usuário e senha de e-mail real versionados habilitam phishing contra a base — numa classe que ninguém importa. |
| AM-054 | CRITICAL | Token de autenticação falso e previsível | `routes/user_routes.py:207-211` | `'fake-jwt-token-' + id` não é assinado nem expira, e nenhuma das 22 rotas chega a verificá-lo. |
| AM-055 | HIGH | Regra de domínio reimplementada seis vezes no controller | `routes/task_routes.py:30-37` | A definição de "atrasada" está copiada em seis handlers enquanto `Task.is_overdue()` existe e nunca é chamado. |
| AM-056 | HIGH | Validação de domínio embutida nos handlers | `routes/task_routes.py:110-114` | Invariantes inline competem com três implementações concorrentes já presentes no repositório, todas mortas. |
| AM-057 | HIGH | Rotas acopladas ao ORM e à sessão global | `routes/task_routes.py:146-154` | Handlers chamam `db.session` direto; serialização mora no model e transação no controller — exatamente invertido. |
| AM-058 | MEDIUM | N+1 apesar dos relacionamentos declarados | `routes/task_routes.py:41-48` | `GET /tasks` custa `1 + 2N` queries embora `db.relationship` já esteja declarado e resolvesse por eager loading. |
| AM-060 | MEDIUM | Ausência de paginação em todas as listagens | `routes/task_routes.py:266-271` | Nenhum endpoint aceita limite ou cursor: o tamanho da resposta é função dos dados, não do contrato. |
| AM-062 | MEDIUM | Regex de e-mail repetido em três pontos | `routes/user_routes.py:105-111` | Corrigir o padrão exige três edições, e criação e atualização já divergem na checagem de existência. |
| AM-069 | LOW | Módulo utilitário inteiro é código morto | `utils/helpers.py:110-116` | Nenhum dos 16 símbolos públicos é usado, e as constantes mortas duplicam literais que as rotas aplicam à mão. |

### Consolidado

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| `code-smells-project` | 7 | 7 | 8 | 5 | 27 |
| `ecommerce-api-legacy` | 4 | 7 | 6 | 5 | 22 |
| `task-manager-api` | 5 | 3 | 11 | 7 | 26 |
| **Total** | **16** | **17** | **25** | **17** | **75** |

Os números acima são os **totais reais dos dossiês**, não o recorte publicado nas tabelas por projeto
— que reúne 42 findings dos 75. Os 33 restantes, com a mesma estrutura de evidência literal, estão em
[`.planning/analise-manual/`](.planning/analise-manual/): um arquivo por projeto, com os findings, a
nota de calibragem de severidade e a tabela de sinais genéricos extraídos.

Duas leituras que o consolidado torna visíveis. `code-smells-project` concentra 14 dos 33
CRITICAL/HIGH porque acumula quatro classes independentes de falha grave de segurança, cada uma
explorável isoladamente por um chamador anônimo. `task-manager-api` inverte o perfil — menos CRITICAL,
muito mais MEDIUM — porque a estrutura em camadas realmente existe no sistema de arquivos: a maior
parte dos seus defeitos está em não exercê-la (duplicação, N+1, código morto), não em catástrofe de
segurança.

### Padrões recorrentes entre projetos

| Anti-pattern | Ocorrência em Python | Ocorrência em Node | Sinal genérico |
|---|---|---|---|
| Credencial hardcoded em bootstrap/configuração | AM-003 (`app.py:6-9`), AM-052 (`app.py:11-15`), AM-053 (`services/notification_service.py:5-10`) | AM-028 (`src/utils.js:1-7`) | Literal string atribuído a chave de configuração sensível no bootstrap ou no construtor, sem nenhuma leitura de variável de ambiente em todo o projeto. Reforço: o segredo carrega marcador de produção, ou nunca é referenciado. |
| Credencial exposta na serialização de resposta | AM-006 (`models.py:79-86`), AM-051 (`models/user.py:16-25`) | — sem par direto; o análogo mais próximo é AM-030 (`src/AppManager.js:43-45`), credencial saindo por log em vez de por resposta | Função de mapeamento registro→DTO que projeta campo de credencial e alimenta rota de leitura sem controle de acesso. Reforço: outra cópia do mesmo mapeamento omite o campo — a exposição é acidental. |
| Hash de senha inadequado ou ausente | AM-050 (`models/user.py:27-32`), AM-005 (`database.py:75-79`) | AM-031 (`src/utils.js:17-23`) | Derivação de credencial por hash rápido de propósito geral, por função caseira, ou inexistente; sem salt, sem fator de custo, comparada por igualdade simples. Verificação decisiva: executar a função e observar colisão entre entradas distintas. |
| N+1 aninhado em laço sobre resultado anterior | AM-015 (`models.py:187-193`), AM-016 (`models.py:219-225`), AM-058 (`routes/task_routes.py:41-48`) | AM-039 (`src/AppManager.js:102-107`), AM-037 (`src/AppManager.js:92-99`) | Consulta a banco disparada dentro de laço que itera o resultado de outra consulta, em dois ou mais níveis, onde uma junção resolveria numa ida só. Agravante: o ORM já declara o relacionamento, ou os cursores são realocados por iteração. |
| Validação de domínio inline na rota | AM-017 (`controllers.py:74-79`), AM-012 (`controllers.py:43-54`), AM-062 (`routes/user_routes.py:105-111`), AM-056 (`routes/task_routes.py:110-114`) | AM-040 (`src/AppManager.js:29-35`) | Invariante de domínio escrita como sequência de `if` com literais dentro do handler HTTP, sem constraint equivalente no schema e sem camada de escrita que a imponha. Agravante: as cópias entre criação e atualização já divergem. |
| Uso de API deprecated no caminho ativo | AM-055 (`routes/task_routes.py:30-37`) — `datetime.utcnow()`, deprecado desde Python 3.12, o interpretador do ambiente | — sem par registrado nos dossiês | Chamada a API marcada como deprecated na própria versão de runtime em uso, repetida no caminho quente e sem aviso de migração no projeto. Sinal barato de detectar e de alto valor: indica ausência de linter e de política de atualização. |

Os pares cruzados dessa tabela são a evidência empírica de que sinais genéricos funcionam. Nenhum
desses anti-patterns depende de linguagem, de framework ou de driver: a credencial hardcoded aparece
como `app.config['SECRET_KEY'] = '...'` no Flask e como `const config = { dbPass: "..." }` no
CommonJS; o N+1 aparece como cursor realocado dentro de laço no `sqlite3` puro, como lazy load do
SQLAlchemy e como callback aninhado no driver do Node — três sintaxes para o mesmo defeito, detectável
pela mesma pergunta ("há acesso a dados dentro de um laço que itera o resultado de outro acesso?").
Foi exatamente por sobreviverem à troca de stack que esses sinais viraram a base do catálogo de
anti-patterns da skill: o que a skill procura não é uma string de código, é a forma estrutural que se
repetiu nos três projetos. Os anti-patterns sem par cruzado — como o uso de API deprecated, observado
só no lado Python — entraram no catálogo mesmo assim, mas com essa limitação registrada.

## B) Construção da Skill

### Arquitetura da skill

A skill é uma pasta copiável. O que está versionado em cada um dos três projetos:

```text
<projeto>/.claude/
├── commands/
│   └── refactor-arch.md            37 linhas — slash command; invoca, não ensina
└── skills/refactor-arch/
    ├── SKILL.md                   293 linhas — orquestrador
    └── references/
        ├── project-analysis.md    225
        ├── antipattern-catalog.md 830
        ├── mvc-guidelines.md      334
        ├── refactor-playbook.md   819
        ├── report-template.md     238
        └── validation-protocol.md 318
```

**7 arquivos, 3.057 linhas** (`SKILL.md` + 6 references; o slash command é invocação e fica fora
da conta). Conferido por `wc -l` sobre `code-smells-project/.claude/skills/refactor-arch/`.

| Arquivo | Responsabilidade | Quando é carregado |
|---|---|---|
| `SKILL.md` | **Orquestra, não ensina.** As 3 fases, a ordem, o gate humano, os critérios de parada, o formato do console das Fases 1 e 3 e *qual reference carregar em cada momento*. Zero conhecimento de domínio. | Sempre, integralmente, na invocação |
| `references/project-analysis.md` | Heurísticas de detecção: linguagem por extensão ∩ manifesto, framework por dependência ∩ resolução efetiva, versão real do runtime, persistência por driver + DDL, grafo de **resolução**, inventário de endpoints. | Início da Fase 1, integral |
| `references/antipattern-catalog.md` | Os 28 anti-patterns: sinal de detecção, contra-exemplo (`NÃO é finding quando`), evidência mínima, manifestações por stack, onda e TR. Índice no topo. | Início da Fase 2, integral — é o arquivo mais caro, e por isso não entra na Fase 1 |
| `references/mvc-guidelines.md` | Arquitetura-alvo: as 7 responsabilidades, direção de dependência, o que cada camada não pode importar, árvore canônica com variantes por stack, regra de alcançabilidade (DECISÃO-01), limiar de granularidade de controller (DECISÃO-02). | Fase 2 (§9, para julgar AP-06/08/13/17) e Fase 3, integral |
| `references/refactor-playbook.md` | As 18 transformações TR-01…TR-18: pré-condição, passos, código antes/depois em Python **e** JavaScript, riscos, verificação pontual, onda-teto. | Fase 3, **só os TRs acionados** — nunca integral |
| `references/report-template.md` | Estrutura literal do relatório da Fase 2: cabeçalho, sumário por severidade, bloco de finding, seção "o que não foi encontrado", seção **Breaking changes** (DECISÃO-03), plano por onda, prompt do gate. | Ao redigir, fim da Fase 2 |
| `references/validation-protocol.md` | Como descobrir o comando de boot sem saber a stack, como decidir que "subiu" por evidência observável, captura e comparação do baseline, predicado binário de onda verde, registro de ondas com SHA, rollback (DECISÃO-04/05). | Pré-condições, fim da Fase 1 e **fim de cada onda** |

#### As 5 áreas exigidas pelo enunciado → o arquivo que cobre cada uma

| # | Área exigida | Arquivo |
|---|---|---|
| 1 | Análise de projeto | `references/project-analysis.md` |
| 2 | Catálogo de anti-patterns | `references/antipattern-catalog.md` |
| 3 | Template de relatório | `references/report-template.md` |
| 4 | Guidelines de arquitetura | `references/mvc-guidelines.md` |
| 5 | Playbook de refatoração | `references/refactor-playbook.md` |
| **+1** | *(não exigida)* Protocolo de validação | `references/validation-protocol.md` |

**Por que 6 arquivos e não 5.** O enunciado exige 5 *áreas de conhecimento*, não 5 arquivos, e as
cinco estão cobertas uma a uma acima. O sexto existe por um trade-off explícito, registrado em
`.planning/01-design-skill.md` §2.1: validação é **conhecimento** — como saber que um servidor
subiu sem saber qual é o framework? — e não orquestração. Dentro do `SKILL.md` empurraria o
orquestrador para ~330 linhas e quebraria o princípio de que o SKILL.md não ensina; dentro do
`refactor-playbook.md` obrigaria a carregar o arquivo mais caro do conjunto (819 linhas) já na
Fase 1, só para capturar o baseline. **Custo aceito:** um arquivo a mais para o avaliador
conferir. **Ganho:** o orquestrador cabe em 293 linhas (58,6% do teto de 500) e o baseline é
capturado sem tocar no playbook.

O `SKILL.md` declara esse desvio no próprio mapa de conhecimento — a linha do sexto arquivo é
marcada `+1`, não numerada de 1 a 5.

### Catálogo de anti-patterns — 28 entradas

Distribuição declarada e conferida no arquivo: **CRITICAL 7 · HIGH 7 · MEDIUM 9 · LOW 5**
(`antipattern-catalog.md:80`; 28 cabeçalhos `## AP-NN` contados por `grep -c`). Mínimo do
enunciado: 8 com severidade distribuída — excedido em 3,5×.

Na coluna **Origem**, `AM-XXX` significa *observado com evidência literal* nos dossiês da seção A;
`domínio` significa *sem ocorrência local registrada*, incluído mesmo assim e com a limitação
declarada. A rastreabilidade vive em `.planning/01-design-skill.md` §4 — **nenhum `AM-XXX`
aparece dentro da skill**: procedência é documento de projeto, sinal é forma estrutural.

| ID | Nome | Sev. | Origem | Por que foi incluído |
|---|---|---|---|---|
| AP-01 | Injection por concatenação de entrada externa | CRITICAL | AM-001, AM-002 | Nomeado pelo enunciado na escala CRITICAL; observado em duas formas no mesmo projeto — query concatenada e endpoint que executa SQL do payload. |
| AP-02 | Hardcoded secret e debug ligado no bootstrap | CRITICAL | AM-003, AM-028, AM-052, AM-053 | **Par cruzado Python↔Node.** O anti-pattern com mais ocorrências em toda a análise manual (4), e o único presente nos três projetos. |
| AP-03 | Credencial ou PII na serialização de resposta | CRITICAL | AM-004, AM-006, AM-051 | **Par cruzado.** Exposição de credencial por rota anônima em dois projetos; o sinal é a função de mapeamento, não o campo. |
| AP-04 | Derivação de senha quebrada ou ausente | CRITICAL | AM-005, AM-031, AM-050 | **Par cruzado**, nas três variantes possíveis: texto puro, hash caseiro, MD5 sem salt. Verificável por execução (colisão). |
| AP-05 | Rota privilegiada sem autenticação verificável | CRITICAL | AM-002, AM-007, AM-008, AM-035, AM-054 | O de maior recorrência estrutural: rota destrutiva anônima em dois projetos e token forjável no terceiro. |
| AP-06 | God class / god module | CRITICAL | AM-029 | Nomeado pelo enunciado na escala CRITICAL. Uma stack só, mas o sinal é a ausência de fronteira onde inserir camada — puramente estrutural. |
| AP-07 | Segredo ou PII emitido em log | CRITICAL | AM-030, AM-021 | Número de cartão e chave de produção em stdout: violação direta de PCI-DSS, e o log é caminho de vazamento que a serialização não cobre. |
| AP-08 | Lógica de negócio fora da camada de serviço | HIGH | AM-011, AM-014, AM-032, AM-055 | É a definição operacional de "violação de MVC" do enunciado; cobre as duas direções — regra no handler **e** regra na camada de dados. |
| AP-09 | Acoplamento a dependência concreta, sem injeção | HIGH | AM-010, AM-033 | Nomeado pelo enunciado na escala HIGH. É o que torna qualquer teste unitário impossível nos três projetos. |
| AP-10 | Estado global mutável compartilhado | HIGH | AM-009, AM-034 | Nomeado pelo enunciado na escala HIGH. Conexão singleton sem lock no Python, `let` de módulo no Node. |
| AP-11 | Escrita multi-etapa sem fronteira transacional | HIGH | AM-013, AM-036, AM-041 | Corrupção silenciosa de dados em dois projetos: checkout sem rollback e check-then-act de estoque. |
| AP-12 | Validação de domínio inline no handler | MEDIUM | AM-012, AM-017, AM-018, AM-040, AM-056, AM-062 | **Par cruzado**, e o agravante decisivo apareceu duas vezes: criação e atualização da mesma entidade já divergindo. |
| AP-13 | Rota acoplada diretamente ao ORM ou driver | HIGH | AM-057 | O perfil do projeto 3: as camadas existem no disco e o handler fala com a sessão mesmo assim. Sem ele a skill trataria o projeto 3 como monolito. |
| AP-14 | Mass assignment / bind não filtrado | HIGH | **domínio** | Sem ocorrência local — os três alvos atribuem campo a campo. Entra por honestidade de catálogo: um catálogo que só contém o que os 3 fixtures têm falha em silêncio no quarto projeto. |
| AP-15 | N+1 aninhado | MEDIUM | AM-015, AM-016, AM-037, AM-039, AM-058, AM-059 | **Par cruzado**, nomeado pelo enunciado na escala MEDIUM. Três sintaxes (cursor, lazy load, callback) para a mesma pergunta. |
| AP-16 | Deprecated API usage | MEDIUM | AM-055 | **Exigido nominalmente pelo enunciado.** Sem par cruzado — observado só no lado Python — e essa limitação está escrita na própria linha do design. |
| AP-17 | Duplicação com a abstração correta morta no repositório | MEDIUM | AM-016, AM-055, AM-061, AM-062, AM-069, AM-070, AM-071 | Nasce da nota de calibragem do dossiê do projeto 3: "abstração correta existe e é ignorada" é sinal mais forte que "código morto". É o AP de maior rendimento em projeto parcialmente organizado. |
| AP-18 | Captura genérica de exceção e vazamento de detalhe interno | MEDIUM | AM-020, AM-063, AM-064 | 12 blocos pelados só no projeto 3; transforma erro de cliente em 500 e apaga o rastro do defeito. |
| AP-19 | Saída de console como mecanismo de log | LOW | AM-021, AM-043, AM-066 | Presente nos três projetos. Classificado LOW — e o review externo contesta: *"mascarar defeitos"* é o critério **MEDIUM** da própria escala do catálogo. Correção C-A22, não aplicada. |
| AP-20 | Política de origem cruzada permissiva | MEDIUM | AM-019, AM-067 | Nomeado pelo enunciado ("middlewares inadequados"); em API sem autenticação, transforma qualquer site em cliente autorizado. |
| AP-21 | DDL e seed executados no boot | HIGH | AM-022, AM-042, AM-047, AM-068 | Presente nos três. Torna a evolução de schema inviável sem reescrita e planta credencial de admin conhecida em qualquer ambiente. |
| AP-22 | Listagem sem paginação | MEDIUM | AM-060 | O tamanho da resposta vira função dos dados, não do contrato. Uma stack só, sinal universal. |
| AP-23 | Contrato de resposta inconsistente | MEDIUM | AM-027, AM-044 | Envelopes divergentes entre handlers equivalentes; é o que faz o consumidor tratar erro por texto. |
| AP-24 | Ausência de rate limiting no endpoint de autenticação | MEDIUM | **domínio** | Sem ocorrência local — e a ausência **não é virtude**: nos três alvos a autenticação é fraca demais para que força bruta seja necessária. Registrado assim no design. |
| AP-25 | Magic numbers e vocabulários literais inline | LOW | AM-023, AM-024, AM-074 | Nomeado pelo enunciado na escala LOW. |
| AP-26 | Código morto e dependências declaradas e não usadas | LOW | AM-025, AM-045, AM-072, AM-073 | Quando as dependências mortas correspondem a lacunas apontadas por outros findings, revelam a **arquitetura pretendida e não implementada** — leitura que nenhum outro AP dá. |
| AP-27 | Nomenclatura pobre e sombreamento de builtin | LOW | AM-026, AM-046, AM-075 | Nomeado pelo enunciado na escala LOW. |
| AP-28 | Ausência de infraestrutura de qualidade | LOW | AM-049, AM-072 | Único AP **sem TR**: é reportado e não corrigido, porque instalar test runner, linter e CI está fora do escopo declarado da skill. |

**A espinha dorsal são os 6 pares cruzados** da seção A — AP-02, AP-03, AP-04, AP-12, AP-15 e
AP-16 —, os únicos com evidência de que o sinal sobrevive à troca de stack. Cinco têm ocorrência
em Python **e** em Node; AP-16 tem só em Python e carrega a limitação escrita. Os 20 seguintes são
observados em uma stack com sinal estrutural; os 2 restantes são de domínio e estão marcados.

### Estratégia de agnosticismo

Esta é a seção que o enunciado transforma em critério: *"se ela só funciona em um projeto
específico, está acoplada demais"*.

#### 1. O que foi feito por escrita

Cinco regras normativas governam todo arquivo de referência (`.planning/01-design-skill.md` §6.2).
As duas que mais moldaram o texto:

- **Sinal é forma, nunca token.** Todo sinal descreve posição na camada, aresta do grafo de
  resolução, ou relação entre dois pontos do código. Teste de conformidade declarado: *o sinal
  continua verdadeiro se o projeto for reescrito em outra linguagem?* Um sinal escrito como
  "`db.session.commit()` dentro de rota" funciona em Flask-SQLAlchemy e em nada mais; o sinal de
  AP-13 pergunta se *"os handlers manipulam a sessão/transação de persistência diretamente"*.
- **Sinal é pergunta operacional binária**, respondível lendo o código, cuja resposta "sim" produz
  um par `arquivo:linha` + bloco literal. Adjetivos de qualidade — "mal estruturado", "acoplado
  demais" — são proibidos como sinal porque não são falsificáveis.

Somam-se: **contra-exemplo obrigatório** em 28/28 entradas (`NÃO é finding quando`), que é o que
impede o relatório de virar preenchimento de cota; **exemplo em ≥2 stacks** nos 18 TRs (18 blocos
`python` + 18 `javascript`, contados por `grep`); e uma regra de higiene não negociável: nenhum
arquivo da skill cita nome de arquivo, classe, função, rota ou string dos 3 projetos-alvo.

#### 2. Como foi verificado

**Teste de acoplamento por `grep`**, executado sobre os 7 arquivos:

```console
$ grep -rniE "app\.py|appmanager|controllers\.py|models\.py|database\.py|requirements\.txt|\
package\.json|loja\.db|tasks\.db|task_routes|/produtos|/pedidos|/usuarios|/api/checkout|\
financial-report|secret_key|minha-chave" . | wc -l
0

flask        0
express      1
sqlite3      0
sqlalchemy   0
django       0
rails        0
spring       0
```

Zero identificadores dos alvos. A única ocorrência de `express` é a palavra portuguesa
**expressão**, em `antipattern-catalog.md:96` — artefato do `\b` do grep, não menção ao framework.

**Copiabilidade provada por `diff -r`**, e não por afirmação. A skill foi escrita em
`code-smells-project/`, validada lá, e só então copiada — a cópia é literal, e é isso que os dois
diffs vazios demonstram:

```console
$ diff -r code-smells-project/.claude ecommerce-api-legacy/.claude && echo "DIFF1 VAZIO"
DIFF1 VAZIO
$ diff -r code-smells-project/.claude task-manager-api/.claude && echo "DIFF2 VAZIO"
DIFF2 VAZIO
```

Nenhum fork por projeto. As três execuções rodaram sobre bytes idênticos.

**Review externo em ferramenta diferente.** `.planning/03-review-agnosticismo.md` foi produzido
por um avaliador em outra ferramenta (Cursor), com a postura declarada de que *"a skill está
acoplada até prova em contrário"*, e testando contra duas stacks que ela nunca viu: Ruby on Rails
e Java/Spring Boot. **Veredito: REPROVADO** no critério "agnóstica de tecnologia".

Ao todo foram **6 rodadas de review**. Quatro internas adversariais — as rodadas 2 e 4 têm arquivo
próprio (`.planning/02-review-rodada2.md`, `.planning/02-review-interno.md`); as rodadas 1 e 3
sobrevivem como as séries `A-n` e `D-n` citadas dentro delas, com os placares de cada uma
(rodada 1: 8✅/1⚠️ · rodada 2: 7✅/2⚠️ · rodada 3: 9✅ · rodada 4: 9✅ na matriz de 9 requisitos
literais). E duas passagens do review externo sobre o mesmo arquivo: a primeira produziu as **13
correções de agnosticismo C-A1…C-A13**, auditadas uma a uma na rodada 4 interna; a segunda é o
texto atual do arquivo, que renumera a partir de **C-A14**.

> A contagem "5 internas + 1 externa" não se sustenta contra o disco: o que está registrado é
> 4 internas + 2 passagens externas. Total de 6 confere; a divisão, não.

#### 3. O que o review externo encontrou que as rodadas internas não pegaram — e por quê

A razão é estrutural, e vale mais que a lista: **as rodadas internas testam se a skill executa nos
termos que ela mesma definiu.** Elas mediram requisitos, contagens, integridade de referências
cruzadas, partição de estados, cadeia de rollback — e nas quatro rodadas o placar dessas garantias
só melhorou. A rodada externa fez outra pergunta: *ela funciona num projeto que nunca viu?* Simulou
o percurso completo do `SKILL.md` como se o cwd fosse uma API Rails legada, e depois um WAR/JAR
Spring — `Gemfile`, Zeitwerk, `config/routes.rb`, `credentials.yml.enc`; `pom.xml`, component
scan, `application.properties`, JPA. Nenhuma auditoria interna havia saído do par Python/Node.

Quatro dos achados, dos mais caros aos mais sutis:

**a) Grafo de imports vs. grafo de resolução (C-A1).** A Fase 1 mandava mapear a arquitetura
efetiva pelo *grafo de imports* — e essa palavra é uma suposição de stack. Em Rails a classe é
carregada por autoload de convenção; em Spring, por component scan e registro em container: em
nenhuma das duas existe a aresta textual `import` que a skill pedia como prova. A consequência não
era cosmética: `services/` viva por autoload seria classificada como camada inalcançável, isto é,
**AP-26 (código morto)**, e a Fase 3 a apagaria. A correção trocou o conceito por **grafo de
resolução**, com uma tabela de quatro mecanismos (import explícito, autoload por convenção,
varredura de pacote, registro em container) e a coluna de evidência exigida por mecanismo. É a
correção mais profunda do pacote, e nenhuma das rodadas internas a havia formulado — porque em
Python e em Node import textual *é* o mecanismo, e a suposição era invisível.

**b) O baseline assumia corpo JSON, e isso aciona a máquina de rollback (C-A8).** O baseline
registrava o `shape` do corpo — chaves e tipos —, e o critério 4 do smoke test comparava shape
contra shape. Uma resposta HTML renderizada por template não tem chaves. O smoke test produziria
**vermelho onde não há regressão**, e o protocolo de onda manda `git reset --hard` sobre vermelho:
o único defeito conhecido do pacote capaz de destruir trabalho válido. Passou a registrar **media
type** e, para corpo não estruturado, um **seletor estável** em vez do objeto de chaves.

**c) AP-08 e AP-13 criminalizavam o idioma da stack (C-A6, C-A14).** O sinal de AP-13 —
*"handlers constroem queries a partir das classes de model, sem camada de serviço interposta"* —
descreve exatamente o controller Rails idiomático e o CRUD `@Autowired Repo` de Spring. Rodar a
Fase 2 num Rails produziria um finding **HIGH em todo controller do projeto**. AP-13 ganhou a
isenção para "API de domínio do framework"; AP-08, que tem a direção inversa (regra de negócio na
camada de dados — que em Rails é onde o domínio mora), **continua sem a isenção simétrica**.

**d) AP-06 estava calibrado no formato do fixture (C-A17).** O sinal exige a **conjunção** de
quatro responsabilidades no mesmo corpo: conexão de banco + definição de schema + registro de rotas
+ regra de negócio. É a descrição de `AppManager.js`. Um fat model Rails de 1.500 linhas e um god
`@Service` de 2.000 linhas nunca reúnem as quatro — logo a god class **não dispara**. O resultado
é o pior par possível: o CRITICAL mais visível do catálogo é falso negativo justamente nas stacks
onde a god class é mais comum, e o `NÃO é finding quando` da própria entrada já diz que o critério
é "número de responsabilidades distintas, não número de linhas" — o sinal e o contra-exemplo
discordam entre si.

Os itens **a**, **b** e **c** foram corrigidos; **d** não. O estado completo está em *Limitações*.

### Decisões e trade-offs

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| **DECISÃO-01** — camada preexistente é adotada **se e somente se** ao menos um símbolo seu for alcançável a partir do entry point; senão é AP-26 e é substituída, com registro prévio como finding | Adotar toda pasta com nome de camada; ou decidir caso a caso por julgamento | O critério é dado observável, não estética — reproduzível entre stacks e entre executores. Uma skill copiável não pode conter exceção nomeada para o projeto onde foi testada. O registro prévio fecha a única brecha: nada some sem o humano ver no gate. **No projeto 3 a regra decidiu os dois casos em direções opostas:** `utils/` era alcançável → foi **religado** (0 → 25 sítios de chamada); `services/` não era → foi **substituído**. |
| **DECISÃO-02** — um controller por agregado, corte em **10 handlers ou 250 linhas** | Corte em 8/200, que era a proposta original | 8/200 fragmentaria a árvore antes/depois: com 4 domínios produziria 6 ou 7 controllers, distanciando o resultado do exemplo do enunciado (2 controllers para 4 domínios). A árvore antes/depois é artefato de leitura do avaliador. 10/250 mantém o corte como válvula para o caso patológico sem acioná-lo no caso comum. |
| **DECISÃO-03** — path, verbo e status preservados; corpo pode ser normalizado, mas **toda** mudança de shape entra numa seção Breaking changes **do relatório da Fase 2** | Documentar as mudanças de shape só no relatório da Fase 3; ou aprovar item a item no gate | Documentar depois faz o humano descobrir o que mudou quando já está feito. Aprovar item a item transforma o gate num questionário e torna as 3 execuções não uniformes. Antecipar para a Fase 2 mantém o gate binário e o torna **informado**. Custo real: a Fase 2 precisa **prever** o efeito de cada TR sobre o contrato antes de executá-lo. |
| **DECISÃO-04** — corrigir todas as severidades, em 4 ondas, com smoke test e commit por onda verde | Aplicar tudo e validar no fim; ou cortar findings por severidade | Cortar findings reduz a entrega sem tornar o que sobra mais seguro. O que controla o risco é a **frequência de validação**: uma pilha de ~40 mudanças não bootáveis é indepurável. Custo: mais ciclos e 4 commits por projeto em vez de 1. Consequência aceita e registrada como R-14: a Onda 1 concentra o esqueleto inteiro mais todos os CRITICAL. |
| **DECISÃO-05** — histórico linear, sem branch por projeto | Branch de trabalho descartável por projeto | O ponto de retorno já existe no commit de baseline, e as ondas somam 4 pontos adicionais — cinco contra o único que a branch daria. O argumento decisivo é de leitura: **o histórico linear é o que o avaliador lê**; três branches produzem um grafo que exige explicação. Consequência: working tree limpo deixa de ser conveniência e vira pré-condição dura. |
| `reports/` **na raiz** do repositório, com nome `audit-<projeto>.md` | `reports/` dentro de cada projeto; ou acoplar a numeração `-1/-2/-3` do enunciado | A skill ancora os dois artefatos em `git rev-parse --show-toplevel`, *"nunca no diretório de trabalho, que pode ser um subdiretório dela"* — é o que permite que a mesma skill rode nos três projetos e escreva num só lugar. A numeração `audit-project-{1,2,3}` do enunciado **não** foi acoplada de propósito: "projeto 1" só existe do lado de fora da skill. O nome do diretório do projeto é dado que a skill tem. |
| Enunciado movido para **`docs/enunciado.md`** | Manter o enunciado no `README.md` da raiz | O repositório base entrega o enunciado *como* README. O README é o entregável avaliado e precisa ser o documento do autor; o enunciado é insumo. O commit `8d6a333` faz o movimento — 448 linhas saem do README e entram em `docs/`, com o link preservado no topo. |
| **Sem `CLAUDE.md`** no repositório | Um `CLAUDE.md` na raiz com instruções de projeto | O conhecimento operacional desta entrega já está na skill, que é copiável e auto-contida. Um `CLAUDE.md` na raiz criaria uma segunda fonte de instrução — fora da skill, não copiada com ela, e capaz de fazer uma execução passar por razões que o avaliador não consegue reproduzir a partir da pasta `.claude/skills/`. Verificável: `grep -rn "CLAUDE.md"` na árvore não devolve nada. |
| **Override do `.gitignore` global** | Depender da configuração local da máquina | O `~/.gitignore_global` desta máquina ignora `.claude/` — e a skill **é** o entregável principal. O `.gitignore` do repositório reverte isso explicitamente (`!.claude/`, `!**/.claude/`) e mantém fora só o que não é entregável: `.claude/hooks/` (workaround do ambiente local, dois scripts `exit 0`) e `settings.local.json`. Sem esse bloco, o `git push` entregaria um repositório sem skill nenhuma. |
| **ND-3** — a credencial SMTP fica no histórico: não rotacionar, não reescrever | `git filter-repo` para remover o segredo; ou rotacionar a conta | `taskmanager@gmail.com` / `senha123` é credencial de fixture num repositório de exercício: não autentica em serviço nenhum, e o código que a usava nunca foi alcançável. Rotação seria a resposta correta em produção — aqui não há o que rotacionar. Reescrever o histórico invalidaria **todos** os SHAs, inclusive os que a evidência cita como prova de que o registro de F-020 precede a remoção do arquivo: destruiria a cadeia de auditoria desta entrega para remover um segredo sem valor. Registrado como decisão consciente em AE-07, com o fato técnico verificado por `git log -S`. |

### Desafios encontrados

O que segue é a parte da construção que não aparece no artefato final. As duas iterações mais
caras foram ambas de *interação entre textos corretos isoladamente* — o modo de falha típico de um
pacote de referências, e o que os reviews adversariais existem para achar.

#### C-6 · a contradição que produziria um esqueleto MVC nunca criado, com todos os smoke tests verdes

A rodada 1 registrou como ambiguidade (`A-3`) que a regra de reatribuição de onda era
**unidirecional**: nos três lugares onde era enunciada, ela só dizia o que fazer quando um TR
precisava **subir** para uma onda anterior. Nada dizia o que fazer quando o TR está rotulado para
uma onda **anterior** à do seu único finding. Item de severidade média; ficou aberto.

Na rodada 2, uma correção legítima e não relacionada (`C-10`, normatizar os três estados de onda)
introduziu a definição: **onda vazia é a onda cuja severidade não tem finding — pule os cinco
passos: sem TR, sem boot, sem smoke test, sem commit.** Isoladamente, correta. Combinada com C-6
aberta, ela deixou de ser ambiguidade e virou **instrução explícita de pular a onda**.

O cenário que quebra é banal — e é exatamente o perfil do terceiro projeto do desafio:

1. Projeto com AP-13 (HIGH) e **sem** AP-06: acopla rota ao ORM, mas não tem god class.
2. Não há finding CRITICAL → pela definição nova, **a Onda 1 é vazia**.
3. TR-06 está rotulado Onda 1 e a regra só sabe subir → ele **não desce** para a Onda 2.
4. A Onda 1 é pulada. E o `SKILL.md` declara que TR-06 **é** o esqueleto MVC (não há onda 0:
   extrair configuração e decompor a god class *são* a estrutura).

**Resultado observável:** a Fase 3 termina com `Waves: 1 CRITICAL — · 2 HIGH ✓ · 3 MEDIUM ✓ ·
4 LOW ✓`, todos os smoke tests `M/M`, todos os commits com contagem de endpoints — e **nenhuma
camada MVC criada**. Todo marcador do bloco de saída está correto pelas definições vigentes; o
projeto não foi migrado e nada no artefato final diz isso. A rodada 2 classificou como **bloqueador
e reprovou**, com a observação de que a correção C-10 endureceu uma regra enquanto C-6 seguia
aberta, e o efeito conjunto é pior que qualquer um dos dois isolados.

A correção foram duas linhas, e as duas eram necessárias: redefinir onda vazia **pelo plano**
(*"onda para a qual o plano aprovado no gate não agendou nenhum TR"*), tornando os três estados
uma partição real; e tornar a regra de onda **bidirecional** — o rótulo do TR é **teto**, a onda
real é a do finding de maior severidade presente, e TR que nenhum finding aciona não entra no
plano. Hoje isso está escrito nos três lugares e a rodada 4 reexecutou o cenário: TR-06 desce para
a Onda 2 e o esqueleto é criado. **A trava valeu na execução real:** no projeto 1 o relatório
registra 6 ajustes de onda, entre eles TR-06 de 1→2 e TR-15 de 3→4.

#### C-16 · a validação final era uma asserção; virou procedimento — e foi ela que pegou o 500 do run-1

A mesma rodada 2 anotou, na margem da simulação: *"a validação final é a única barreira contra o
cenário acima, e não tem procedimento — é uma asserção, não um teste."* O texto pedia ao agente
que confirmasse que a refatoração estava conforme; não dizia **como** confirmar. Uma asserção é
confirmada por quem a escreve.

C-16 transformou as três verificações em procedimento executável: **(1)** reexecutar o *sinal de
detecção* de cada finding contra o código atual — finding cujo sinal ainda dispara não foi
corrigido; **(2)** comparar o resultado com o alvo **responsabilidade a responsabilidade**, com a
cláusula operante de que a verificação *falha mesmo com smoke test `M/M`*; **(3)** diff de forma e
media type contra a seção Breaking changes aprovada. Nada disso é herdado das ondas verdes.

Foi a verificação 1 que achou o defeito mais caro do run-1. Depois das quatro ondas verdes
(19/19 em todas), a validação final foi procurar mudanças de status **fora** do baseline e
encontrou: `POST /pedidos` com `usuario_id` inexistente passara a devolver **500**. A chave
estrangeira que TR-16 declarou — pedida nominalmente por dois findings — fazia a `IntegrityError`
subir sem tipo pelo caminho novo, e erro de cliente virava falha de servidor. O smoke test
**estruturalmente não podia** pegar: os 19 endpoints do baseline continuavam conformes. Corrigido
em `48b6f7b`, completando o passo 4 de TR-13, com smoke test `19/19` próprio. Registrado como
BC-12, ao lado de BC-13 e BC-14 — as três mudanças de status que a Fase 2 não previu.

No run-3 a mesma verificação 1 pegou o outro tipo de erro: um finding que uma onda **declarou
resolvido** e estava resolvido pela metade (F-020 — a camada morta saiu, duas dependências mortas
ficaram no manifesto). Corrigido em `e86217f`, e registrado como AE-04, incluindo a lacuna de
processo que ele expôs: o `validation-protocol.md` não define o que fazer com um conserto
descoberto na validação final.

#### As outras iterações, em resumo honesto

- **Rodada 1 → 2:** quatro bloqueadores de execução — `REPORT_PATH` indefinido, `reports/` sem
  âncora de raiz, predicado de "onda verde" não definido, baseline vivendo só na sessão. Todos
  fechados; o baseline passou a ser gravado em disco antes do gate, e é por isso que a Fase 3 lê
  contrato do disco em vez de confiar na memória da conversa.
- **Rodada 2 → 3 → 4:** o padrão mudou de *lacuna* para *aresta*. Definições novas, corretas
  isoladamente, falhando no contato com o texto vizinho que não foi atualizado junto — B-1 (o
  invariante do gate enunciado com dois valores diferentes em cinco arquivos), B-3 ("4 ondas"
  hardcoded em cinco lugares, incluindo uma pré-condição que se torna insatisfazível), E-1 (a
  verificação 2 mudou de unidade e o artefato que a alimenta não mudou junto). Correção por
  propagação, não por redesenho.
- **A rodada 4 reprovou por leva não aplicada, não por defeito novo:** das 13 correções de
  agnosticismo, seis edições existiam no working tree e dez estavam ausentes — verificado arquivo
  a arquivo, com `git diff --numstat` mostrando zero linhas em dois dos oito arquivos. É um achado
  desconfortável de registrar e é o mais útil do conjunto: a diferença entre *decidir corrigir* e
  *ter corrigido* não é observável sem conferir o disco.

#### C-A14…C-A23 · decisão de escopo, não omissão

A segunda passagem do review externo produziu 10 correções adicionais (C-A14…C-A23) com veredito
**REPROVADO**, não aplicadas. Aplicá-las exigiria alterar o catálogo, re-propagar a skill aos três
projetos e re-executar os três ciclos para checar regressão — o protocolo que a própria skill
define. Os 12 critérios de aceite já estavam fechados, e o custo não se justificava no prazo da
entrega. As correções ficam documentadas em `.planning/03-review-agnosticismo.md` como trabalho
identificado e não realizado.

---

## C) Resultados

### Placar dos critérios de aceite — 12 células

| Critério | `code-smells-project` | `ecommerce-api-legacy` | `task-manager-api` |
|---|---|---|---|
| **CA-1** — Fase 1 detecta a stack | ✅ **5/5 campos exatos**<br>`evidence/run-1/checagem.md` §CA-1 | ✅ **13/13 campos corretos**<br>`evidence/run-2/checagem.md` §CA-1 | ✅ **15/15 campos corretos**<br>`evidence/run-3/checagem.md` §CA-1 |
| **CA-2** — Fase 2 encontra ≥ 5 findings | ✅ **26** (contados por `grep -c "^### \["`)<br>`evidence/run-1/checagem.md` §CA-2 | ✅ **20**<br>`evidence/run-2/checagem.md` §CA-2 | ✅ **23**<br>`evidence/run-3/checagem.md` §CA-2 |
| **CA-3** — ≥ 1 CRITICAL ou HIGH | ✅ **14**<br>`evidence/run-1/checagem.md` §CA-3 | ✅ **11**<br>`evidence/run-2/checagem.md` §CA-3 | ✅ **9**<br>`evidence/run-3/checagem.md` §CA-3 |
| **CA-4** — aplicação funciona após a refatoração | ✅ boot + **19/19** conformes ao baseline<br>`evidence/run-1/validacao.md` §7 | ✅ boot + **4/4** conformes ao baseline<br>`evidence/run-2/validacao.md` §7 | ✅ boot + **22/22** conformes ao baseline<br>`evidence/run-3/validacao.md` §8 |

**12/12 células aprovadas.** As três células de CA-4 não têm o mesmo peso — ver *Limitações*.

### Resumo dos 3 relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| `code-smells-project` | 8 | 6 | 7 | 5 | **26** |
| `ecommerce-api-legacy` | 5 | 6 | 4 | 5 | **20** |
| `task-manager-api` | 4 | 5 | 9 | 5 | **23** |
| **Total** | **17** | **17** | **20** | **15** | **69** |

Rodapé literal de cada relatório: `Total: **26 findings** (8 CRITICAL · 6 HIGH · 7 MEDIUM · 5 LOW)`
(`reports/audit-code-smells-project.md:1088`), `**20 findings** (5 · 6 · 4 · 5)`
(`audit-ecommerce-api-legacy.md:969`), `**23 findings** (4 · 5 · 9 · 5)`
(`audit-task-manager-api.md:1670`).

### Cobertura do cruzamento com a análise manual

Cada run foi cruzado, finding a finding, contra o dossiê manual do mesmo projeto — o gabarito
escrito **antes** da skill existir.

| Projeto | Findings manuais | Cobertura estrita | Cobertura ponderada | Cobertura ampla | Falsos positivos |
|---|---|---|---|---|---|
| `code-smells-project` | 27 | **85,2%** (23/27, finding próprio ou dobrado) | — | **100%** (tema abordado com evidência; 0 omissões silenciosas) | 1 procedente (F-021) |
| `ecommerce-api-legacy` | 22 | **77,3%** integral | **86,4%** (parcial = 0,5) | **95,5%** (integral + parcial) | **0** |
| `task-manager-api` | 26 | **96,2%** (25/26) | **98,1%** | — | **0**, e **100% dos CRITICAL/HIGH manuais** (8/8) |

A skill também **acrescentou** findings que a auditoria humana não tinha: 6 no projeto 1 (dois em
temas que o gabarito não toca — paginação e rate limiting) e 3 no projeto 3, entre eles as 34
chamadas deprecated, que é o requisito nomeado pelo enunciado. No projeto 2 a direção se inverte:
os 3 falsos negativos do run-2 estão registrados como AE-01 a AE-03.

### Antes e depois

| Projeto | Antes | Depois |
|---|---|---|
| `code-smells-project` | 4 arquivos-fonte · **780 LOC** | 58 arquivos-fonte · **2.155 LOC** |
| `ecommerce-api-legacy` | 3 arquivos-fonte · **180 LOC** | 33 arquivos · **1.157 LOC** |
| `task-manager-api` | 15 arquivos `.py` · **1.158 LOC** | 53 arquivos `.py` · **2.286 LOC** |

#### `code-smells-project`

```text
ANTES  (commit ec6d1d4)              DEPOIS (commit 48b6f7b)
─────────────────────────            ────────────────────────────────────────────────
code-smells-project/                 code-smells-project/
├── app.py            88 LOC         ├── config/          settings.py
├── controllers.py   292 LOC         ├── models/          produto · usuario · pedido
├── models.py        314 LOC         ├── repositories/    produto · usuario · pedido · admin
├── database.py       86 LOC         ├── services/        produto · usuario · auth · pedido ·
├── requirements.txt                 │                    relatorio · admin · notificacao ·
└── README.md                        │                    paginacao · errors
                                     ├── controllers/     produto · usuario · pedido ·
4 arquivos · 780 LOC                 │                    relatorio · admin
sem camada: o entry point e o        ├── routes/          5 blueprints
controller acessam persistência      ├── middlewares/     auth · error_handler · rate_limit
direto, via fábrica global           ├── dto/             serializers.py
                                     ├── validators/      schema · produto · usuario ·
                                     │                    pedido · paginacao
                                     ├── security/        password.py · tokens.py
                                     ├── observability/   logger.py
                                     ├── infra/           connection · migrator ·
                                     │                    migrations/0001_initial.sql
                                     ├── scripts/         migrate.py · seed_dev.py
                                     ├── .env.example
                                     ├── app.py           composition root
                                     └── constants.py
                                     58 arquivos · 2.155 LOC · 0 violações de direção (AST)
```

#### `ecommerce-api-legacy`

```text
ANTES  (commit 5d02287)              DEPOIS (commit cc8d8a5)
─────────────────────────            ────────────────────────────────────────────────
ecommerce-api-legacy/                ecommerce-api-legacy/
├── src/                             ├── .env.example
│   ├── app.js         14 LOC        ├── package.json      scripts: start · migrate · seed
│   ├── AppManager.js 141 LOC        ├── scripts/          migrate.js · seed.js
│   └── utils.js       25 LOC        └── src/
├── api.http                             ├── app.js        composition root
├── package.json                         ├── config/index.js
└── package-lock.json                    ├── models/paymentStatus.js
                                         ├── repositories/  6 arquivos
3 arquivos · 180 LOC                     ├── services/      5 arquivos
AppManager acumula persistência,         ├── controllers/   3 arquivos
roteamento, regra de negócio,            ├── routes/index.js
integração de pagamento e                ├── middlewares/   auth · errorHandler · rateLimit
apresentação                             ├── errors/index.js
                                         ├── lib/           cache.js · logger.js
                                         └── db/            connection · migrate ·
                                                            migrations/0001_initial.sql · seed
                                     33 arquivos · 1.157 LOC
                                     AppManager.js e utils.js deixaram de existir
```

#### `task-manager-api`

```text
ANTES  (commit f580ee5)              DEPOIS (commit e86217f)
─────────────────────────            ────────────────────────────────────────────────
task-manager-api/                    task-manager-api/
├── app.py             34 LOC        ├── app.py            composition root · 126 LOC
├── database.py         3 LOC        ├── database.py       3 LOC
├── seed.py            99 LOC        ├── seed.py           116 LOC
├── models/                          ├── config/           settings.py
│   ├── task.py        60            ├── models/           task · user · category
│   ├── user.py        38            ├── repositories/     task · user · category ·
│   └── category.py    21            │                     unit_of_work
├── routes/                          ├── services/         task · user · category ·
│   ├── task_routes   299            │                     report · errors
│   ├── report_routes 223            ├── controllers/      task · user · category · report
│   └── user_routes   211            ├── routes/           4 tabelas de rota · 85 LOC
├── services/                        ├── middlewares/      auth · error_handler · rate_limit
│   └── notification_  48            ├── dto/              task · user · category
│       service.py    (inalcançável) ├── validators/       base · task · user · category ·
├── utils/                           │                     pagination
│   └── helpers.py    116            ├── security/         passwords.py · tokens.py
│      (alcançável, 0 chamadas)      ├── infra/            migrator.py
└── requirements.txt                 ├── observability/    logger.py
                                     ├── migrations/       0001_initial.sql
15 arquivos .py · 1.158 LOC          ├── utils/            helpers.py  ← RELIGADO
MVC parcial: models e rotas vivas,   ├── ruff.toml · requirements-dev.txt · .python-version
sem service efetivo, sem repositório └── .env.example
                                     53 arquivos .py · 2.286 LOC
```

O contraste entre `utils/` e `services/` neste projeto é a DECISÃO-01 funcionando: as duas pastas
tinham nome de camada e conteúdo não exercido; `utils/` era **alcançável** e foi **ligada** (de 0
para 25 sítios de chamada), `services/` era **inalcançável** e foi **substituída** — e o veredito
foi tomado na Fase 2, antes de qualquer código mudar. Os três módulos de rota, que somavam 733 LOC
(63,3% do projeto), somam hoje **85 LOC**.

### Validação por onda

| Projeto | `M` | Ondas | Smoke por onda (commit) |
|---|---|---|---|
| `code-smells-project` | **19** | 4 verdes · 0 vermelhas · 0 vazias · **0 rollbacks** | onda-1 `5e0591b` 19/19 · onda-2 `dc0e74c` 19/19 · onda-3 `222bb9a` 19/19 · onda-4 `d1b9b8e` 19/19 · fix pós-validação `48b6f7b` 19/19 |
| `ecommerce-api-legacy` | **4** | 4 verdes · 0 vermelhas · 0 vazias · **0 rollbacks** | onda-1 `4701894` 4/4 · onda-2 `fb19464` 4/4 · onda-3 `0d1eacc` 4/4 · onda-4 `cc8d8a5` 4/4 |
| `task-manager-api` | **22** | 4 verdes · 0 vermelhas · 0 vazias · **0 rollbacks** | onda-1 `7fd2012` 22/22 · onda-2 `9e81e4d` 22/22 · onda-3 `3235b4b` 22/22 · onda-4 `303c1f9` 22/22 · fix pós-validação `e86217f` 22/22 |

**12 ondas, 12 verdes, zero rollback.** `M` é o número de requisições do baseline, não de
endpoints: no projeto 2, 4 requisições sobre 3 endpoints (o checkout tem dois casos
representativos).

Findings resolvidos: **25/26**, **19/20** e **22/23**. Em cada projeto, o único não resolvido é
F-026 / F-020 / F-023 — todos AP-28, o anti-pattern que o catálogo declara desde a Fase 2 que
**reporta e não corrige**.

### Checklist de validação do enunciado

| Item | `code-smells-project` | `ecommerce-api-legacy` | `task-manager-api` |
|---|---|---|---|
| **Fase 1 — Análise** | | | |
| Linguagem detectada corretamente | ✅ Python 3.12.3 (executado) | ✅ JavaScript/CommonJS · Node v24.12.0 | ✅ Python 3.12.3 (executado) |
| Framework detectado corretamente | ✅ Flask 3.1.1 + flask-cors 5.0.1 | ✅ Express 4.22.1 (declarado `^4.18.2`) | ✅ Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 + Flask-CORS 4.0.0 |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS de cursos pagos com checkout | ✅ Gestão de tarefas |
| Nº de arquivos condiz com a realidade | ✅ 4 files · 780 LOC | ✅ 3 files · 180 LOC | ✅ 15 files · 1.158 LOC |
| **Fase 2 — Auditoria** | | | |
| Relatório segue o template das referências | ✅ conformidade conferida item a item | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ 20/20 com bloco literal | ✅ 23/23 |
| Findings ordenados CRITICAL → LOW | ✅ `F-001`…`F-026`, numeração contínua sem reinício | ✅ `F-001`…`F-020` | ✅ `F-001`…`F-023` |
| Mínimo de 5 findings | ✅ 26 | ✅ 20 | ✅ 23 |
| Detecção de APIs deprecated (se aplicável) | ✅ **não encontrado**, verificado contra 3.12.3 com `-W always::DeprecationWarning` e cruzamento das 17 APIs chamadas | ✅ **não encontrado**, verificado contra Node v24.12.0 | ✅ **encontrado** — F-016 (AP-16), 34 chamadas |
| Pausa e pede confirmação antes da Fase 3 | ✅ `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` | ✅ idem | ✅ idem |
| Nenhuma escrita em arquivo do projeto antes do gate | ✅ `git diff -- code-smells-project/` vazio | ✅ única escrita: o baseline | ✅ `git status --porcelain task-manager-api/` vazio |
| **Fase 3 — Refatoração** | | | |
| Estrutura de diretórios segue MVC | ✅ 7/7 responsabilidades com **um** lugar cada | ✅ 7/7 | ✅ 13 pacotes, todos alcançáveis |
| Config extraída, sem hardcoded | ✅ `config/settings.py` + fail-fast · 0 ocorrências do segredo antigo | ✅ `src/config/index.js` + `.env.example` | ✅ `config/settings.py` + `.env.example` |
| Models criados para abstrair dados | ✅ 3 módulos; mapeamento registro→entidade num lugar só | ✅ `models/paymentStatus.js` + schema com constraints | ✅ 3 módulos; serialização movida para `dto/` |
| Views/Routes separadas | ✅ `routes/` = 66 LOC, só `add_url_rule` | ✅ `src/routes/index.js` | ✅ `routes/` = 85 LOC |
| Controllers concentram o fluxo | ✅ 0 `except Exception`, 0 decisão de negócio | ✅ o maior tem 38 linhas | ✅ 0 `db.session`/`.query.` |
| Error handling centralizado | ✅ envelope único; 17 blocos genéricos → 0 | ✅ `errorHandler.js` com correlação | ✅ 12 `except:` pelados → 0 |
| Entry point claro | ✅ `app.py:44 build_app(settings)`; `sqlite3.connect` em 1 lugar | ✅ `src/app.js:36-97` | ✅ `app.py`, 126 LOC |
| Aplicação inicia sem erros | ✅ porta escutando · processo vivo · `GET /` → 200 | ✅ os três critérios | ✅ os três critérios |
| Endpoints originais respondem | ✅ **19/19** | ✅ **4/4** | ✅ **22/22** |

### Logs de boot pós-refatoração (console literal)

**`code-smells-project`** — `evidence/run-1/validacao.md` §1:

```console
$ python -m scripts.migrate
migracoes aplicadas: 0001_initial.sql
versao do schema: 1

$ python -m scripts.seed_dev
seed aplicado: 10 produtos, 3 usuarios

$ python app.py
2026-08-17T12:52:35-0300 INFO     loja servidor_iniciado ambiente=development host=127.0.0.1 port=5000
 * Tip: There are .env files present. Install python-dotenv to use them.
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
127.0.0.1 - - [17/Aug/2026 12:52:35] "GET / HTTP/1.1" 200 -
```

**`ecommerce-api-legacy`** — `evidence/run-2/validacao.md` §1:

```console
> desafio-arquitetura-ia-boilerplate@1.0.0 start
> node --env-file-if-exists=.env src/app.js

{"timestamp":"2026-08-17T19:14:23.776Z","level":"warn","event":"ephemeral_database","code":"in-memory-bootstrap"}
{"timestamp":"2026-08-17T19:14:23.778Z","level":"info","event":"migration_applied","code":"0001_initial.sql"}
{"timestamp":"2026-08-17T19:14:23.814Z","level":"info","event":"seed_applied","environment":"development"}
{"timestamp":"2026-08-17T19:14:23.820Z","level":"info","event":"server_started","port":3000,"host":"127.0.0.1","environment":"development"}
```

```console
(1) porta escutando:
State  Recv-Q Send-Q               Local Address:Port  Peer Address:PortProcess
LISTEN 0      511                      127.0.0.1:3000       0.0.0.0:*

(2) processo vivo apos 3s: VIVO
(3) primeira requisicao respondida: 404
```

**`task-manager-api`** — `evidence/run-3/validacao.md` §1:

```console
$ python -m infra.migrator upgrade
Migrações aplicadas: 0001_initial.sql

$ python seed.py
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks

$ python app.py
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 505-623-803
127.0.0.1 - - [17/Aug/2026 17:32:23] "GET /health HTTP/1.1" 200 -
```

> O `Debug mode: on` do projeto 3 é `APP_ENV=development` no `.env` local, não o defeito original:
> em `APP_ENV=production` o boot **recusa** subir com `DEBUG` ligado. Nos três projetos o bind
> deixou de ser `0.0.0.0` e passou a vir do ambiente, com default `127.0.0.1`.

### Limitações

Esta seção é parte do resultado. Nada aqui é rodapé.

**1. O `M = 4` do projeto 2 torna seu CA-4 mais fraco que os outros dois.** O baseline do
`ecommerce-api-legacy` tem 4 requisições sobre 3 endpoints, contra 19 e 22 nos outros. É o que o
projeto oferece — ele só tem três rotas —, mas a consequência é real: "aplicação funciona após a
refatoração" é uma afirmação sustentada por 4 observações num projeto cujo `src/` foi inteiramente
reescrito (180 → 1.157 LOC, `AppManager.js` e `utils.js` deletados). O mesmo predicado de onda
verde, com o mesmo rigor, cobre uma fração muito menor da superfície. Três das quatro requisições
mudaram de forma ou de status por breaking change declarada, o que deixa **uma** requisição
comparada como idêntica ponta a ponta.

**2. AP-28 fora de escopo: os três projetos seguem sem suíte de testes, e o smoke test é a única
rede.** O catálogo declara desde a Fase 2 que AP-28 é reportado e não corrigido — instalar test
runner, linter e CI está fora do escopo da skill. Isso foi cumprido à risca nos três projetos
(F-026, F-020, F-023 reportados e deliberadamente fora do plano aprovado no gate). O efeito
colateral é que **2.155 + 1.157 + 2.286 LOC de código refatorado não têm um único teste
automatizado**: a validação inteira desta entrega repousa sobre 19 + 4 + 22 requisições de smoke
test. Coberturas parciais chegaram por consequência de outros TRs — `.env.example` nos três, e
`ruff.toml` + `.python-version` + `requirements-dev.txt` no projeto 3 — mas suíte e pipeline não
existem.

**3. Breaking changes de caminho de erro nunca foram verificadas, por construção.** O
`validation-protocol.md` §2 manda capturar "uma requisição representativa" por endpoint, e a
interpretação natural — a que foi seguida nas três execuções — é a requisição feliz. **O baseline
não instrumenta nenhum caminho de erro.** Consequências observadas, não hipotéticas:

- No **run-1**, três mudanças de status em caminho de erro (BC-12, BC-13, BC-14) só apareceram
  porque a validação final foi procurá-las de propósito; uma delas era um **500** legítimo, e as
  quatro ondas estavam verdes com ele dentro.
- No **run-3**, BC-7 e BC-8 — duas das oito breaking changes aprovadas no gate — **não são
  verificáveis pelo smoke test**, do começo ao fim. Se TR-13 tivesse quebrado o contrato de erro
  em vez de melhorá-lo, as quatro ondas continuariam verdes.

A correção proposta está escrita (duas capturas por endpoint: o caminho representativo válido e um
caminho de erro determinístico) e **não foi aplicada** — dobraria `M` no pior caso e exigiria
recapturar os três baselines.

**4. Os sete achados de execução (`.planning/04-achados-execucao.md`).** Achados sobre **a skill**,
produzidos executando-a às cegas e cruzando com a análise manual prévia. Nenhum foi corrigido nesta
entrega, pela mesma razão em todos: corrigir o catálogo exige re-propagar aos 3 projetos e
re-executar os anteriores para checar regressão — e o registro honesto do que a skill não cobre
vale mais, aqui, que um AP-29 acrescentado às pressas.

| ID | Projeto | Tipo | O que é | Estado |
|---|---|---|---|---|
| **AE-01** | 2 | Lacuna do catálogo | **Nenhum dos 28 APs tem como sinal a ausência de uma fronteira de erro.** Um `card` enviado como número JSON — payload válido — derrubava o processo inteiro; com banco `:memory:`, perda total de dados por requisição anônima. Percorridos os 28 APs, nenhum alcança: AP-12 cobre validação no lugar errado, não validação inexistente; AP-18 pressupõe um bloco de captura, e aqui não havia captura nenhuma. | Registrado, **não corrigido**. Contido por efeito colateral de TR-06 + TR-13 — o defeito em si segue em `src/services/paymentGateway.js:21` |
| **AE-02** | 2 | Lacuna do catálogo | Coordenação assíncrona manual não tem AP: `err` não verificado antes de `.length`, e contadores decrementados à mão que, se um caminho de erro pular um decremento, deixam a requisição pendurada até o timeout. Severidade caiu de HIGH (manual) para MEDIUM (skill) por finding incompleto. | Registrado, **não corrigido** |
| **AE-03** | 2 | Erro de execução | A **segunda metade** do sinal de AP-02 não foi respondida — o driver carregado em `verbose()` incondicional e o bind em todas as interfaces estavam lá. Não pede alteração no catálogo: é sinal de que perguntas com duas cláusulas são respondidas pela metade quando a primeira já produziu finding forte. | Registrado; defeito corrigido por TR-01, não por detecção |
| **AE-04** | 3 | Erro de execução + lacuna de processo | Uma onda declarou F-020 resolvido na mensagem de commit; ele estava resolvido em 2 de 3 partes (duas dependências mortas seguiam no manifesto). Pego pela verificação 1 da validação final. O `validation-protocol.md` **não define** o que fazer com um conserto descoberto na validação final — o commit `e86217f` ficou fora do registro de ondas | Corrigido em `e86217f`; a lacuna de processo, **não corrigida** |
| **AE-05** | 3 | Erro de execução | BC-3 declarou **13** rotas; são **12** (3 verbos × 3 recursos = 9, mais 3 leituras de terceiros). A enumeração — que é o que regeu a execução — estava certa; o número, não. Um humano que conferisse a lista não saberia mais o que mais no documento não fecha | Corrigido nos artefatos de evidência; a causa (o template não exige que contagem citada bata com a enumeração), **não corrigida** |
| **AE-06** | 3 | Desvio de escopo | TR-13 entregou `correlation_id` além dos dois campos que BC-7 declarou. O playbook pede o que o relatório não declarou. **É a mais grave das quatro do projeto 3**, e não foi pega por verificação nenhuma — só por comparação manual do implementado com o declarado | **Não revertido**, registrado |
| **AE-07** | 3 | Enquadramento no relatório | ND-3 (credencial SMTP no histórico do git) foi classificado como pendência quando é **decisão**. O `report-template.md` só oferece `NEEDS-DECISION`, que é pergunta pendente; não há categoria para "decidido, com a razão registrada" | Decidido e documentado; a lacuna do template, **não corrigida** |

O padrão que atravessa a Parte I é o mais desconfortável: **em nenhum dos três a correção veio da
detecção.** Três defeitos reais foram resolvidos ou contidos por TRs que rodavam por outro motivo.
Isso é sorte estrutural do projeto, não propriedade da skill — um projeto com perfil de findings
diferente atravessaria a refatoração com os três intactos e um relatório declarando sucesso.

**5. A segunda passagem do review externo permanece aberta.** As 13 correções de agnosticismo
C-A1…C-A13 foram aplicadas — verificável no texto atual: tabela de mecanismos de resolução,
baseline com media type e seletor, isenção de AP-13 para a API de domínio da stack, TR-09
reconhecendo o container, tabela de tradução de forma no topo do playbook. As **10 correções da
segunda passagem (C-A14…C-A23) não foram**. Conferido por `grep` no disco:

| Correção externa | Estado atual |
|---|---|
| C-A14 — AP-08 não criminaliza o lugar de domínio da stack | ❌ o `NÃO é finding quando` de AP-08 (`:285-288`) isenta tradução de protocolo e CRUD puro, e **não** isenta a regra que vive onde a convenção da stack a coloca — model ActiveRecord, entidade JPA com invariantes |
| C-A16 — evidência sem token de fonte | ❌ o sinal de AP-02 ainda diz *"sem nenhuma leitura de variável de ambiente"* (`antipattern-catalog.md:123`); `credentials.yml.enc` e vault não são env var |
| C-A17 — AP-06 conta responsabilidades | ❌ o sinal ainda exige a **conjunção** das quatro (`:224-226`), enquanto o `NÃO é finding quando` da mesma entrada diz que o critério é número de responsabilidades |
| C-A15 — AP-16 cruza runtime **e** framework | ❌ o procedimento (`:495-497`) cruza só a versão do runtime; depreciação de framework não está no changelog da linguagem |
| C-A18 — plano com coluna de responsabilidade | ❌ `report-template.md:208` segue com `Arquivos criados/alterados/removidos` |
| C-A20 — título de TR-06 | ❌ segue *"Decompor a god class nas **cinco** camadas"*, enquanto `mvc-guidelines.md` §2 lista sete |
| C-A23 — resíduos | ❌ *"decisão de negócio de alto valor"* em `project-analysis.md:125`; *"(é curto, nesses casos)"* em AP-28; `Package mgr : <manifest file>` no singular. ✅ parcial: `Manifestações por stack` subiu de 25 para **27** dos 28 APs |

Em termos práticos: **a skill é comprovadamente copiável e comprovadamente funcional em Python e
em Node**, e o próprio review externo confirma que a Fase 1 sobrevive em Rails e em Spring. O que
não está provado — e o avaliador externo diz que não está — é que a **Fase 2** produza findings
justos e a **Fase 3** escreva código idiomático numa stack com convenção forte. As três execuções
desta entrega não testam isso, porque o enunciado fixa Python e Node como alvos.

**6. Duas inconsistências menores que a auditoria do disco encontrou, corrigidas nesta
entrega:** o `README.md` de `code-smells-project/` ainda descrevia o fluxo **pré-refatoração**
(*"o banco é criado automaticamente no primeiro boot"*), quando TR-16 tirou a DDL do boot; e o
`README.md` de `ecommerce-api-legacy/` não mencionava que o boot agora **falha** sem
`PAYMENT_GATEWAY_KEY` e `ADMIN_TOKEN`. Dos três projetos, só o `task-manager-api/README.md`
estava atualizado quando a auditoria rodou. Os três agora descrevem o fluxo pós-refatoração e as
env vars obrigatórias de cada `.env.example` — comandos corretos na seção D abaixo.

**7. Uma nota de método sobre os números desta seção.** A contagem "15 achados" do review externo
não é reconstruível a partir do disco: o arquivo `.planning/03-review-agnosticismo.md` foi
sobrescrito pela segunda passagem, e o texto da primeira sobrevive apenas como a tabela de
verdicts C-A1…C-A13 dentro da rodada 4 interna. O que é verificável e está usado acima: **12**
itens na seção "o que o review interno não pegou", **25** linhas no inventário de acoplamento,
**10** correções propostas. O número 15: `[ausente]`.

---

## D) Como Executar

### Pré-requisitos

Versões **detectadas na Fase 1 de cada projeto**, executando o runtime — não lidas do manifesto.
São as versões contra as quais a validação desta entrega foi feita.

| | `code-smells-project` | `ecommerce-api-legacy` | `task-manager-api` |
|---|---|---|---|
| Runtime | **Python 3.12.3** | **Node.js v24.12.0** | **Python 3.12.3** |
| Gerenciador | pip (`requirements.txt`) | **npm 11.6.2** (`package.json` + lock) | pip (`requirements.txt`, `.python-version` = 3.12) |
| Framework | **Flask 3.1.1** + flask-cors 5.0.1 | **Express 4.22.1** (declarado `^4.18.2`) | **Flask 3.0.0** + Flask-SQLAlchemy 3.1.1 + Flask-CORS 4.0.0 |
| Banco | SQLite via `sqlite3` stdlib (lib 3.45.1) | SQLite `:memory:` via `sqlite3` 5.1.7 | SQLite via SQLAlchemy 2.0.52 |
| Porta | 5000 | 3000 | 5000 |

Para **executar a skill** (e não apenas os projetos): Claude Code instalado e autenticado. A skill
é descoberta a partir de `<projeto>/.claude/skills/refactor-arch/`, o que significa abrir a sessão
**dentro** do diretório do projeto — uma skill escopada a subdiretório só entra no índice quando a
sessão toca aquele subdiretório (observado no run-3 e registrado em `evidence/run-3/fase1.md` §0).

### Comandos por projeto

Todos assumem o repositório clonado e o terminal na raiz.

#### Projeto 1 — `code-smells-project` (Python/Flask)

```bash
cd code-smells-project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # preencha LOJA_SECRET_KEY — o boot FALHA sem ela
python -m scripts.migrate     # aplica as migrações; a DDL não roda mais no boot
python -m scripts.seed_dev    # dados de demonstração; recusa fora de LOJA_ENV=development
python app.py                 # http://127.0.0.1:5000
```

#### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express)

```bash
cd ecommerce-api-legacy
npm install

cp .env.example .env          # preencha PAYMENT_GATEWAY_KEY e ADMIN_TOKEN — obrigatórias
npm start                     # http://127.0.0.1:3000
```

Com `DATABASE_FILE=:memory:` (o default), migração e seed rodam no bootstrap do processo — é o que
os eventos `migration_applied` e `seed_applied` do log de boot mostram. Com banco em arquivo, use
`npm run migrate` e `npm run seed` antes do `npm start`.

#### Projeto 3 — `task-manager-api` (Python/Flask)

```bash
cd task-manager-api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env               # preencha SECRET_KEY (obrigatória em produção)
python -m infra.migrator upgrade   # cria/evolui o schema
python seed.py                     # dados de demonstração; recusa rodar em produção
python app.py                      # http://127.0.0.1:5000
```

#### Invocar a skill num projeto

```bash
cd <projeto>          # a sessão precisa estar dentro do projeto
claude "/refactor-arch"
```

A skill **aborta** se o working tree não estiver limpo — é a pré-condição que torna o `git reset
--hard` do rollback seguro. Ela para no gate da Fase 2 e espera um `y` ou `n` explícito.

### Como validar que a refatoração funcionou

#### Projeto 1

```bash
curl -s localhost:5000/health
curl -s localhost:5000/produtos | head -c 200
curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
     -d '{"email":"admin@loja.com","senha":"<senha do seed>"}'
curl -s -o /dev/null -w '%{http_code}\n' localhost:5000/relatorios/vendas   # 401 sem credencial
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:5000/admin/query # 404 — rota removida (BC-3)
```

Sinais de que a refatoração está de pé: `/health` **não** devolve mais `secret_key`, `db_path` nem
a flag de debug (BC-2); `/usuarios` **não** devolve mais `senha` (BC-1); as 10 rotas privilegiadas
respondem **401** sem credencial (BC-4); e `POST /admin/query` — o console de banco publicado na
internet — responde **404**.

#### Projeto 2

```bash
curl -s -X POST localhost:3000/api/checkout -H 'Content-Type: application/json' \
     -d '{"name":"X","email":"x@y.z","password":"p","courseId":2,"card":"4111111111111111"}'
curl -s -o /dev/null -w '%{http_code}\n' localhost:3000/api/admin/financial-report   # 401
curl -s localhost:3000/api/admin/financial-report -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -o /dev/null -w '%{http_code}\n' -X DELETE localhost:3000/api/users/1        # 401
```

O relatório financeiro passou a exigir credencial (BC-1) e a responder envelope paginado em vez de
array puro (BC-6); todo erro sai em JSON com `{"error":{"code","message","correlationId"}}`.

#### Projeto 3

```bash
TOKEN=$(curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"1234"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

curl -s localhost:5000/health
curl -s localhost:5000/users -H "Authorization: Bearer $TOKEN" | head -c 200
curl -s -o /dev/null -w '%{http_code}\n' localhost:5000/users                 # 401 sem credencial
curl -s "localhost:5000/tasks?limit=999" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))'  # 200 = teto
curl -s -o /dev/null -w '%{http_code}\n' localhost:5000/users \
     -H "Authorization: Bearer fake-jwt-token-1"                              # 401 — token forjado
```

12 rotas exigem credencial e 10 permanecem públicas; 12 + 10 = **22**, que é o `M` do baseline.
`password` não aparece em nenhuma das respostas de User, e `fake-jwt-token-<id>` — o token forjável
do baseline — não autentica mais.

### Como reproduzir a comparação com o baseline

Os três baselines estão versionados em `reports/`, capturados **antes** de qualquer escrita, sobre
o código intocado:

| Arquivo | Formato | Conteúdo |
|---|---|---|
| `reports/baseline-code-smells-project.json` | lista de 19 registros | `method`, `path`, `status`, `media`, `shape` |
| `reports/baseline-task-manager-api.json` | lista de 22 registros | idem |
| `reports/baseline-ecommerce-api-legacy.json` | objeto com metadados + `baseline` | `boot` (comando, porta, evidência de que subiu), `endpoints_total`, `requests_total`, `notes` e as 4 requisições, com `selector` nos dois corpos `text/html` |

Um registro, literal:

```json
{"method": "GET", "path": "/", "status": 200, "media": "application/json",
 "shape": {"message": "string", "version": "string"}}
```

Para reproduzir, suba o projeto refatorado e compare, requisição a requisição, nos **cinco
critérios** da §4 do `validation-protocol.md`: (1) o endpoint existe; (2) método e path idênticos;
(3) status idêntico; (4) media type **e** forma do corpo comparados no mesmo termo em que o
baseline registrou — `shape` contra `shape`, `selector` contra `selector`; (5) valores
não-voláteis coerentes. Onda verde é `M/M` nos cinco; qualquer `N < M` é vermelho.

```bash
# ponto de partida: o que o baseline promete, por endpoint
python3 -c "
import json
b = json.load(open('reports/baseline-task-manager-api.json'))
for r in b:
    print(f\"{r['method']:6} {r['path']:28} {r['status']}  {r['media']}\")
"
```

Divergência **só** é aceitável se constar da seção *Breaking changes* aprovada no gate, no
relatório correspondente em `reports/audit-<projeto>.md` — 11 BCs no projeto 1, 9 no projeto 2, 8
no projeto 3. Shape alterado e não declarado é **regressão**, não melhoria: é o critério da
DECISÃO-03, e é o que a verificação 3 da validação final executa.

> **O que não está versionado, e por honestidade fica dito:** o harness de smoke test usado nas
> execuções (`smoke.py`, e os equivalentes ad hoc dos runs 1 e 2) **não** está no repositório —
> `git ls-files | grep -i smoke` não devolve nada. O que está versionado é o contrato a reproduzir
> (os três baselines) e a saída literal de cada comparação (`evidence/run-*/fase3.md` e
> `validacao.md`). Reproduzir a comparação exige reescrever o cliente HTTP a partir dos cinco
> critérios acima.
