# Review externo — agnosticismo de tecnologia da skill `refactor-arch`

> **Postura:** avaliador contratado, sem participação na construção. A skill está acoplada até
> prova em contrário. O teste é um projeto que ela nunca viu — API Ruby on Rails legada, depois
> Java/Spring Boot. Os reviews internos (`.planning/02-review-interno.md`,
> `02-review-rodada2.md`) foram lidos **depois** das seções 1–4.
>
> **Alvo:** `code-smells-project/.claude/skills/refactor-arch/` (7 arquivos).
> **Enunciado:** `docs/enunciado.md` — "Deve ser agnóstica de tecnologia"; "A skill deve ser
> copiável — se ela só funciona em um projeto específico, está acoplada demais."
> **Data:** 2026-08-17.
> **Estado auditado:** texto atual em disco, não o estado citado pelos reviews internos.

**Veredito:** a skill é copiável como pasta. Não é agnóstica. Fase 1 sobrevive em Rails e em
Spring. Fase 2 criminaliza o idioma do model Rails (AP-08) e perde a god class típica dessas
stacks (AP-06). Fase 3 traduz exemplos Flask/Express. O acoplamento explícito aos três
projetos-alvo foi removido; o acoplamento restante é de evidência, de fonte de segredo e de
camada-alvo.

---

## 1. TESTE DA STACK DESCONHECIDA

Percurso do `SKILL.md` como se o cwd fosse uma API Rails 6/7 legada: `Gemfile`, Zeitwerk,
`config/routes.rb`, `app/{models,controllers,views}`, ActiveRecord, `db/migrate`,
`config/credentials.yml.enc`, respostas HTML+JSON, `bin/rails`. Sem fork, sem conhecimento do
domínio.

### 1.1 Ruby on Rails

| Passo (`SKILL.md`) | Executável em stack desconhecida? | O que quebra |
|---|---|---|
| Pré-condição 1 — VCS + working tree limpo (`:55-62`) | Sim | Abortar se não houver git. Fora do teste Rails típico. |
| Pré-condição 2 — SHA de baseline (`:64-67`) | Sim | — |
| Pré-condição 3 — `REPORT_PATH` / `BASELINE_PATH` na raiz (`:68-75`) | Sim | — |
| Pré-condição 4 — declarar auditoria read-only (`:76`) | Sim | — |
| Fase 1 — carregar `project-analysis.md` + `validation-protocol.md` (`:82`) | Sim | — |
| Fato 1 — linguagem (extensão ∩ manifesto) (`project-analysis.md` §1) | Sim | `.rb` + `Gemfile`. Conforme. |
| Fato 2 — framework efetivo = manifesto ∩ **alcançável pelo mecanismo de resolução** (`project-analysis.md:57-58`, `SKILL.md:88-94`) | Sim | Autoload por convenção está na tabela (`project-analysis.md:148`). Conforme **se** o agente determinar o mecanismo antes de percorrer. |
| Fato 3 — versão real do runtime (`project-analysis.md:82-87`) | Parcial | `ruby --version` existe. AP-16 cruza chamadas contra o runtime da **linguagem**. Deprecations de Rails (`update_attributes`, `render text:`, `ActiveRecord::Base` APIs) vivem na versão do **framework**. Fato 3 alimenta o AP errado. |
| Fato 4 — persistência (`project-analysis.md` §4) | Sim | `schema.rb` / `db/migrate` / `database.yml`. "Import efetivo do driver" é ruído; o procedimento pede cruzar quatro sinais, não só o import. |
| Fato 5 — domínio (`project-analysis.md` §5) | Sim | — |
| Fato 6 — arquitetura efetiva (`project-analysis.md` §6, `SKILL.md:88-94`) | Sim | Entry points plurais previstos (`SKILL.md:112`). Mecanismo = convention autoload. A árvore que Zeitwerk varre é evidência. Conforme neste fato. |
| Fato 7 — inventário de endpoints (`project-analysis.md` §7) | Parcial | `config/routes.rb` + `resources` + rotas de engine cabem na tabela método/path. ActiveJob, ActionCable, rake tasks não são endpoint HTTP e somem. Superfície HTTP-only. |
| Fato 8 — baseline (`validation-protocol.md` §2) | Sim | Media type + `shape` **ou** `selector` para corpo não estruturado (`:43-48`). HTML de ERB não fabrica mais um contrato JSON. Conforme. |
| Comando de boot (`validation-protocol.md:18-24`) | Parcial | Precedência 1 junta "script no manifesto, alvo do gerenciador de build, **ou** executável que o framework instala". `bin/rails server` cai no terceiro braço. O primeiro token ("script no manifesto") enviesa para `package.json#scripts`; Gemfile não tem esse campo. |
| Saída da Fase 1 (`SKILL.md:104-120`) | Sim | `Package mgr : Gemfile`. `Resolution : convention autoload`. `Entry points` admite lista. |
| Fase 2 — varrer 28 APs (`SKILL.md:132-133`) | Não | Ver §3. AP-06 não dispara no fat model. AP-08 dispara no fat model. AP-05/AP-09/AP-13 pedem evidência de middleware/import que Rails não produz. AP-02 trata credentials criptografadas como ausência de env var. |
| Fase 2 — evidência `arquivo:linha` + literal (`SKILL.md:134-135`) | Sim | — |
| Fase 2 — contra-exemplo, severidade, o que não foi encontrado (`:136-139`) | Sim | — |
| Fase 2 — camada inalcançável (`:140-142`) | Sim | Exceção de autoload em AP-26 (`antipattern-catalog.md:767-772`) impede apagar `app/models`. Conforme neste ponto. |
| Fase 2 — Breaking changes + gravar relatório + plano por onda (`:144-151`) | Sim | Plano do template lista **arquivos**, não responsabilidades (`report-template.md:206-211`). |
| Gate humano (`SKILL.md:153-173`) | Sim | — |
| Fase 3 — carregar `mvc-guidelines.md` integral + TRs acionados (`:179-181`) | Sim | — |
| Fase 3 — TR-06 passo 0 / regra 4 (`mvc-guidelines.md:47-53`, `refactor-playbook.md:280-286`) | Sim | Adota `app/`. Não ergue árvore paralela. Conforme **na estrutura**. |
| Fase 3 — aplicar TRs com boot por TR (`SKILL.md:215-221`) | Parcial | Boot Rails é lento (assets, Zeitwerk, DB). Protocolo executável, caro. Não quebra. |
| Fase 3 — conteúdo dos TRs | Não | 18 pares Python+JavaScript (`refactor-playbook.md:16-17`). Tabela de forma (`:20-27`) autoriza traduzir papel; os exemplos concretos são `jsonify`, `app.config`, `add_url_rule`, `CORS(app)`, `req.body`. TR-01 publica `.env.example` (`report-template.md:210`) contra `credentials.yml.enc`. TR-15 verifica "dependência que nenhum arquivo importa" (`:686`) e apaga `puma`/`pg`/`bootsnap`. |
| Fase 3 — smoke test + commit de onda (`SKILL.md:222-226`) | Sim | Critério 4 compara `shape` contra `shape` e `selector` contra `selector` (`validation-protocol.md:117-124`). |
| Validação final 1 — reexecutar sinais C/H (`SKILL.md:237-240`) | Parcial | Reexecuta AP-08 no model idiomático → "not fixed". Não reexecuta AP-06 que nunca disparou. |
| Validação final 2 — responsabilidade a responsabilidade (`SKILL.md:241-248`) | Não | O plano aprovado não tem coluna de responsabilidade. Com regra 4, `Arquivos criados` fica vazio. A checagem passa por vacuidade no ramo Rails. |
| Validação final 3 — Breaking changes (`:250-251`) | Sim | — |
| Saída Fase 3 (`:255-266`) | Sim | — |
| Regra "escreva no idioma da stack" (`SKILL.md:286-287`) | Parcial | Norma correta. O único código que o agente vê é Flask/Express. |

**Síntese Rails.** Copiar a pasta funciona. Rodar as três fases não: a auditoria marca o MVC do
framework como HIGH (AP-08) e deixa passar o fat model de 1.500 linhas (AP-06). A refatoração
adota `app/` e depois escreve services/repositórios no idioma dos exemplos, ou publica `.env` no
lugar de credentials.

### 1.2 Java / Spring Boot (resumo)

Mesmo percurso, cwd = WAR/JAR legado: `pom.xml` ou `build.gradle`,
`@SpringBootApplication`, component scan, `application.properties`, JPA, `src/main/java/.../web`.

| Passo | Executável? | O que quebra |
|---|---|---|
| Fatos 1–2, 4–6 | Sim | Package scan + container registry estão na tabela (`project-analysis.md:149-150`). Variante Java/Kotlin em `mvc-guidelines.md:157`. TR-09 passo 0 usa o container (`refactor-playbook.md:410-413`). |
| Fato 3 / AP-16 | Parcial | `java -version` cobre depreciação da JDK. Não cobre Spring (`WebMvcConfigurerAdapter`, `RestTemplate` vs `WebClient`, `CrudRepository` vs `ListCrudRepository`). |
| Fato 7 | Parcial | `@GetMapping` espalhado: o texto manda não confiar num único ponto de registro (`project-analysis.md:191-194`). gRPC / `@KafkaListener` / `@Scheduled` ficam de fora. |
| Boot | Sim | `./mvnw spring-boot:run` é "alvo do gerenciador de build". |
| AP-02 | Parcial | Manifestação cita `application.properties` (`antipattern-catalog.md:133-134`). O **sinal** exige "nenhuma leitura de variável de ambiente" (`:118`). `@Value("${db.password}")` lendo o properties versionado **é** o finding; o mesmo `@Value` lendo o env via Spring Relaxed Binding pode ser falso positivo se o agente só grep-ar `System.getenv`. |
| AP-06 | Não (falso negativo) | God `@Service` de 2.000 linhas não abre conexão, não define schema e não registra rota no mesmo corpo. Sinal não dispara. |
| AP-13 | Parcial | Manifestação Java: "repositório injetado direto no controller sem serviço" (`:425-426`). Idioma comum de CRUD Spring. Choque com `mvc-guidelines.md` §10 (`:323-326`: service anêmico não deve ser criado). Checklist §9 item 7 (`:307`) ainda pergunta isso como finding. |
| AP-21 | Sim | `spring.jpa.hibernate.ddl-auto=update` é efeito de schema no boot. Sinal cobre. Manifestação ("DDL na função que obtém a conexão", `:645-646`) não cita a propriedade; o sinal basta. |
| AP-26 / TR-15 | Parcial | Java tem `import`. Melhor que Rails. Starters (`spring-boot-starter-web`) não aparecem em import de aplicação; TR-15 `:686` ainda os remove. |
| Fase 3 exemplos | Não | Zero blocos Java. Agente traduz `jsonify` / `app.use` para um Spring que a comunidade não reconhece, ou gera `src/controllers` paralelo a `...web`. |
| TR-01 | Não | `.env.example` contra `application-{profile}.yml` + env. Fail-fast por env obrigatório luta com defaults de profile. |

Spring está mais perto do alvo de 7 camadas do que Rails. Continua dependente de o agente não
copiar a sintaxe Python/JS e não aplicar AP-13/checklist §9.7 em todo `@Autowired Repo`.

---

## 2. INVENTÁRIO DE ACOPLAMENTO

Nenhum nome de arquivo, rota ou variável dos três projetos-alvo aparece nos 7 arquivos.
`flask`, `express`, `sqlite3`, `app.py`, `AppManager`, `requirements.txt` como requisito: ausentes.
Acoplamento explícito aos fixtures: **não encontrado**.

O que resta é implícito e estrutural.

| Arquivo:linha | Trecho | Nível | Correção sugerida |
|---|---|---|---|
| `antipattern-catalog.md:116-118` | "sem nenhuma leitura de **variável de ambiente** em todo o projeto" | IMPLÍCITO | Trocar por "sem leitura de fonte externa de segredo (env, credentials criptografadas, vault, keystore do OS)". Rails `credentials.yml.enc` e Spring Cloud Config não são env var. |
| `antipattern-catalog.md:199-200` | "O registro da rota **sem middleware**, mais o corpo do handler" | IMPLÍCITO | Evidência = ponto de interceptação da stack (filtro, `before_action`, interceptador, `HandlerInterceptor`). O sinal (`:194-195`) já lista esses nomes; a evidência mínima os descarta. |
| `antipattern-catalog.md:219-221` | "abertura de conexão de banco, definição de schema, registro de rotas **e** regra de negócio" no mesmo corpo | ESTRUTURAL | Calibrado no monolito de 4 arquivos. God class = N responsabilidades distintas, não a conjunção das quatro. Fat `User` Rails e fat `@Service` Spring nunca reúnem as quatro. |
| `antipattern-catalog.md:268-271` | Regra de domínio no handler **ou** "dentro de uma função da **camada de acesso a dados**" | ESTRUTURAL | Em Rails o model ActiveRecord **é** o lugar da regra. AP-13 ganhou isenção para "API de domínio do framework" (`:417-422`); AP-08 não. Sem a isenção simétrica, todo fat model é HIGH. |
| `antipattern-catalog.md:301-302` | Evidência AP-09: "mais o **import** que a torna possível" | IMPLÍCITO | Evidência = aresta de resolução (import, autoload, injeção do container). `new` / factory global / class method de infra no corpo continuam válidos; exigir import mata Zeitwerk e `@Autowired` por interface. |
| `antipattern-catalog.md:405-406` | Evidência AP-13: "O **import da sessão** no módulo de rotas" | IMPLÍCITO | SQLAlchemy/Flask. Depois da isenção de `:417-422`, esta evidência torna o AP inaplicável em Rails/Spring (não há `from db import session` no controller) **ou** força o agente a forjar evidência. Pedir a linha que monta query/abre transação/controla sessão. |
| `antipattern-catalog.md:484-492` | AP-16: runtime = "interpretador/VM do ambiente" | IMPLÍCITO | Cruzar também a versão **do framework efetivo** (Fato 2). Notas de depreciação de Rails/Spring/Django não estão no changelog do runtime. |
| `antipattern-catalog.md:577-582` | AP-19: "sem **import** de biblioteca de logging em nenhum arquivo" | IMPLÍCITO | `Rails.logger` / `java.util.logging` / `org.slf4j` chegam pelo framework. Evidência = ausência de logger **alcançável**, não de import. |
| `antipattern-catalog.md:601-607` | AP-20: "middleware de política de origem cruzada aplicado globalmente" | IMPLÍCITO | Spring `CorsRegistry` / `WebMvcConfigurer` não é middleware de rota. Sinal = política permissiva no ponto em que a stack a configura. |
| `antipattern-catalog.md:755-756` | AP-26: "dependências declaradas no manifesto e **não importadas** por nenhum arquivo" | IMPLÍCITO | O `NÃO` (`:767-772`) já cobre autoload. O sinal principal não. Gem/starter usado só pelo boot da stack continua "não importado". |
| `antipattern-catalog.md:808-811` | AP-28: "O manifesto completo (**é curto**, nesses casos)" | ESTRUTURAL | `requirements.txt` de 4 linhas. `pom.xml` / `Gemfile.lock` não são curtos. Evidência = listagem dos artefatos ausentes, sem pressupor tamanho. |
| `project-analysis.md:125` | "o que é 'decisão de negócio de **alto valor**' ao julgar AP-08" | IMPLÍCITO | Resíduo. O sinal de AP-08 já não usa "alto valor". Apagar ou apontar para o predicado atual (ramificação que muda regra de domínio). |
| `mvc-guidelines.md:76` | config: entrada = "**variáveis de ambiente**" | IMPLÍCITO | Entrada = fonte de configuração da stack (env, profile YAML, credentials, flags). A responsabilidade (validar, tipar, falhar no boot) permanece. |
| `mvc-guidelines.md:136-146` | Árvore canônica `config/models/repositories/services/controllers/routes/middlewares` + entrypoint | ESTRUTURAL | Precedência 2/3 quando a regra 4 não dispara. Monólito Rails mal reconhecido (autoload não declarado na config) recebe essa árvore ao lado de `app/`. |
| `mvc-guidelines.md:307` | Checklist §9.7: "Um controller importa driver, ORM ou repositório diretamente?" → AP-09, AP-13 | ESTRUTURAL | Desalinhado da isenção de AP-13 `:417-422` e da §10 `:323-326`. Em Rails a resposta é "sim" em todo controller idiomático. |
| `refactor-playbook.md:16-17` | "Os pares de código abaixo são **Python e JavaScript** porque dois idiomas bastam" | IMPLÍCITO | `description` promete Java, PHP, Ruby, Go (`SKILL.md:9-11`). 18+18 blocos, zero das outras. A tabela de forma (`:20-27`) não tem linha Rails/Spring. |
| `refactor-playbook.md:59`, `:274` | "Decompor a god class nas **cinco** camadas" | ESTRUTURAL | `mvc-guidelines.md` §2 lista **sete**. Rails declara três. O título empurra a árvore genérica mesmo com o passo 0. |
| `refactor-playbook.md:85-87`, `report-template.md:210` | "Publique um arquivo de exemplo"; plano cria `.env.example` | IMPLÍCITO | Artefato 12-factor Flask/Node. Rails: `config/credentials.yml.enc` + editor. Spring: `application-local.yml.example` ou env no README. |
| `refactor-playbook.md:686` | Verificação TR-15: "o manifesto não declara dependência que **nenhum arquivo importa**" | IMPLÍCITO | Contradiz AP-26 `:767-772`. A verificação do TR é a que o agente executa na Fase 3. |
| `validation-protocol.md:18` | Primeiro token: "script no manifesto" | IMPLÍCITO | Manter os três braços; inverter a ordem: executável/convenção da stack **antes** de campo `scripts` de manifesto npm. |
| `report-template.md:206-211` | Plano: colunas `Arquivos criados/alterados/removidos` | ESTRUTURAL | Validação final 2 (`SKILL.md:241-248`) verifica responsabilidades. Sem coluna, o ramo "adotar convenção" passa vazio. |
| `SKILL.md:109` | `Package mgr : <manifest file>` (singular) | IMPLÍCITO | Rails: `Gemfile`+`Gemfile.lock`. Spring multi-módulo: N `pom.xml`. Admitir lista. |
| `project-analysis.md` §7; `SKILL.md:41-43` | Inventário e smoke test = método HTTP + path | IMPLÍCITO | Escopo "APIs HTTP". Declarar jobs, consumers e websocket como fora — ou inventariá-los. Hoje somem em silêncio. |

---

## 3. TESTE DE SINAL ACIONÁVEL

Critério: a pergunta do **Sinal** é respondível lendo código em qualquer linguagem, sem token de
sintaxe. Evidência/manifestação que reintroduz token não rebaixa o sinal — é anotada à parte.

| AP | Sinal | Sintaxe específica |
|---|---|---|
| AP-01 | **ACIONÁVEL.** Concatenação/interpolação de entrada externa em query/comando. | Manifestação: `+`, f-string, template literal, `Statement`. Sinal não depende disso. |
| AP-02 | **ACIONÁVEL**, com viés de fonte. Literal em chave sensível sem fonte externa. | "Variável de ambiente" no sinal. Não cobre credentials/vault. |
| AP-03 | **ACIONÁVEL.** Projeção de credencial/PII em rota de leitura. | Manifestação `dict(row)` / `{...row}` / `toJSON()`. Sinal estrutural. |
| AP-04 | **ACIONÁVEL.** Hash rápido ou texto simples na credencial persistida. | — |
| AP-05 | **ACIONÁVEL.** Rota privilegiada sem ponto de verificação da stack. | Evidência exige middleware no registro da rota. `before_action` / `HandlerInterceptor` não satisfazem a evidência. |
| AP-06 | **VAGO** na prática. A conjunção das quatro responsabilidades é um formato de arquivo, não um teste de god class. "Não existe fronteira onde inserir uma camada" não é binário. | Calibrado em `app.py`+`models.py` fundidos. |
| AP-07 | **ACIONÁVEL.** Log interpola segredo/PII sem redação. | — |
| AP-08 | **VAGO.** "Regra de domínio" é julgamento; o lugar certo da regra **depende da stack**. O correlato (inspecionar forma do retorno para status) é acionável. | Sem isenção para model da stack (ao contrário de AP-13). |
| AP-09 | **ACIONÁVEL.** Dependência resolvida no corpo, não recebida. | Evidência pede import. Rails sem container cai no finding mesmo com a isenção de container (`:307-309`). |
| AP-10 | **ACIONÁVEL.** Handle mutável em escopo de módulo, escrito no request path. | Flag de concorrência do driver é agravante, não conjunção. Conforme. |
| AP-11 | **ACIONÁVEL.** Escritas relacionadas sem fronteira transacional. | — |
| AP-12 | **ACIONÁVEL.** Invariantes como condicionais no handler, sem constraint. | — |
| AP-13 | **ACIONÁVEL** no sinal atual (mecanismo de persistência no handler, ou salto de camada alcançável). | Evidência: "import da sessão no módulo de rotas". Manifestação Java criminaliza `@Autowired Repo` no controller. |
| AP-14 | **ACIONÁVEL.** Payload inteiro no bind, sem allowlist. | Manifestação só `Entity(**payload)` / `Object.assign(..., req.body)`. Sem `params.permit` / `@JsonIgnoreProperties`. Sinal independe. |
| AP-15 | **ACIONÁVEL.** Query dentro de laço sobre resultado anterior. | Manifestação: lazy load / `await` em `for`. Sinal estrutural. |
| AP-16 | **ACIONÁVEL** como procedimento; **alvo errado**. | Runtime da VM, não versão do framework. Manifestação ausente (3 APs sem o campo: 16, 26, 28). |
| AP-17 | **ACIONÁVEL.** ≥3 cópias + abstração correta com zero referências externas. | "Importar não é usar" (`:528`) assume import. Contar referências pelo mecanismo de resolução. |
| AP-18 | **ACIONÁVEL.** Captura da exceção base serializando detalhe interno, repetida, sem tratador central. | — |
| AP-19 | **ACIONÁVEL.** stdout como log, sem níveis. | Manifestação `print` / `console.log`. Evidência: import de lib de logging. |
| AP-20 | **ACIONÁVEL** se existir política de origem. **Não aplicável** silencioso em app HTML server-rendered sem CORS. | "Middleware" no sinal. |
| AP-21 | **ACIONÁVEL.** DDL/seed no boot, sem ferramenta de migração. | Manifestação: DDL na função da conexão. Não cita `ddl-auto` / `unless table_exists?` em initializer. Sinal cobre boot. |
| AP-22 | **ACIONÁVEL.** Listagem sem limite. | — |
| AP-23 | **ACIONÁVEL.** Dois handlers equivalentes, envelopes diferentes. | "JSON" aparece no sinal (`:682`) como um dos casos, não como requisito. |
| AP-24 | **ACIONÁVEL.** Auth sem contador/backoff. | Evidência: middleware na rota + dependência no manifesto. Limite em gateway/nginx só conta se verificável — conforme. |
| AP-25 | **ACIONÁVEL.** Literal de negócio sem nome. Desempate com AP-12 presente (`:740-743`). | — |
| AP-26 | **ACIONÁVEL** com viés de import. Símbolos/deps sem referência. | Sinal diz "não importadas". `NÃO` corrige autoload; TR-15 desfaz. |
| AP-27 | **ACIONÁVEL.** Builtin da linguagem detectada; nomes de 1–3 letras; posicionais do mesmo tipo. | Builtin é específico por linguagem **por desenho**. Conforme. |
| AP-28 | **VAGO.** Conjunção de ausências (devDeps, comando de boot, versão, teste, lint, env example, CI) + lockfile vs faixa. Não está claro se é AND ou OR. "Manifesto é curto" não é sinal. | — |

**Contagem:** 20 ACIONÁVEL · 4 ACIONÁVEL com viés de token/fonte (02, 05 evidência, 16 alvo, 26) ·
3 VAGO (06, 08, 28) · AP-13 acionável no sinal e acoplado na evidência.

Dependência de sintaxe que sobrevive depois de generalizar o sinal: f-string/`+` (só manifestação),
`print`/`console.log`, `req.body`, `import da sessão`, `middleware` na evidência, `variável de
ambiente`, `import` como prova de uso.

---

## 4. COBERTURA DE SEVERIDADE

O enunciado desta tarefa cita **7/7/10/4**. O catálogo atual declara **CRITICAL 7 · HIGH 7 ·
MEDIUM 9 · LOW 5** (`antipattern-catalog.md:80`). Índice e corpo conferem: 7/7/9/5. A cota
7/7/10/4 é estado anterior; uma entrada MEDIUM virou LOW (AP-19 permanece LOW; a conta bate).

A frase "não uma cota" (`:80-82`) convive com CRITICAL = HIGH = 7 exatos. Isso não prova cota;
também não prova aplicação cega da escala. O teste é consistência entre pares.

| Par | Escala (`:29-36`) | Classificação | Veredito |
|---|---|---|---|
| AP-01 injection vs AP-02 secret | Explorável / expõe credencial → CRITICAL | Ambos CRITICAL | Conforme. |
| AP-02 secret vs debug ligado no mesmo AP | Debug em todas as interfaces não é, sozinho, perda de dados | Um AP só: debug-only herda CRITICAL | **Inflado.** Separar debug+bind `0.0.0.0` como HIGH, ou exigir debugger interativo para CRITICAL. |
| AP-03 PII na resposta vs AP-07 PII no log | Ambos expõem PII | Ambos CRITICAL | Conforme. |
| AP-06 god class vs AP-08 lógica no handler vs AP-13 handler→ORM | AP-06: sem fronteira. AP-08/13: fronteira errada | C / H / H | Consistente **se** AP-06 for a conjunção real. Com a conjunção de quatro, AP-06 quase não dispara fora dos fixtures → a distribuição 7 CRITICAL é inflada **nos alvos** e vazia **em Rails/Spring**. |
| AP-08 vs AP-13 no mesmo handler | Dois HIGH, mesma causa | Dois findings | Infla **contagem**, não a escala. Um finding por causa (`report-template.md:18`) já manda fundir; o catálogo não aponta o par. |
| AP-09 DI vs AP-10 global mutável | Ambos HIGH, ambos TR-09 | Dois HIGH | Sobrepostos. Estado global costuma ser o veículo do acoplamento concreto. |
| AP-12 validação inline MEDIUM vs AP-14 mass assignment HIGH | Mass assignment escreve `role` | M / H | Conforme. Desempate AP-12×AP-25 presente. |
| AP-05 rota privilegiada CRITICAL vs AP-24 rate limit MEDIUM | Força bruta ≠ ausência de auth | C / M | Conforme. |
| AP-20 CORS MEDIUM | Nota de subir com cookie auth (`:613-614`) | MEDIUM default | Conforme com a nota. Sem cookie, o enunciado ("middlewares inadequados") é MEDIUM. |
| AP-21 DDL no boot HIGH | "Evolução inviável" cabe em HIGH | HIGH | Limítrofe: não compromete integridade sozinho. Aceitável. |
| AP-16 deprecated MEDIUM | Enunciado exige o AP; não é explorável | MEDIUM | Conforme. |
| AP-19 console como log LOW | Enunciado LOW = legibilidade. Ausência de log **mascara defeitos** (critério MEDIUM) | LOW | **Subclassificado.** Ou sobe para MEDIUM, ou a mudança 10→9 MEDIUM foi cosmética. |
| AP-28 infra LOW, sem TR | Fora de escopo | LOW | Conforme. |

**A distribuição 7/7/9/5 não é resultado puro da escala.** AP-02 mistura dois defeitos numa
severidade; AP-06 só é CRITICAL no formato dos fixtures; AP-19 está abaixo do critério MEDIUM da
própria tabela; CRITICAL=HIGH=7 permanece simétrico demais para ser acidente. Não há padding
óbvio de APs inventados — os 28 existem como classe de defeito. Há calibração de severidade nos
monolitos Python/Node HTTP+JSON.

---

## 5. O QUE O REVIEW INTERNO NÃO PEGOU

Lidos agora: `.planning/02-review-rodada2.md` (orquestração: ondas, gate, rollback) e
`.planning/02-review-interno.md` (rótulo "rodada 4"; agnosticismo via C-A1…C-A13 e simulação
Rails 5.4). Esse interno descreve um **working tree anterior**: C-A4, C-A5, C-A6 (AP-13), C-A8,
C-A9, C-A10, C-A12 e a conta 7/7/10/4. No texto atual, esses itens estão em grande parte
aplicados. O que segue é o que **eles não formularam**, não o que já corrigiram.

1. **AP-16 mira o runtime da linguagem, não a versão do framework.** Interno pediu `ruby --version`
   e `Manifestações por stack`. Não notou que depreciação Rails/Spring não está no changelog de
   Ruby/Java. Fato 3 da Fase 1 continua incompleto para o único AP que o enunciado nomeia.
2. **AP-06 é conjunção de quatro responsabilidades.** Interno atacou AP-13 no controller
   idiomático. Não atacou o falso negativo no fat model / fat `@Service`. God class CRITICAL só
   existe no formato dos três projetos-alvo.
3. **AP-08 criminaliza o model Rails.** C-A6 cobriu AP-13/AP-09 (acesso idiomático a persistência).
   A direção inversa de AP-08 ("regra misturada a agregação na camada de dados") não recebeu a
   isenção simétrica. Com AP-13 corrigido, o HIGH migra para o model.
4. **Evidência mínima reconduz o token que o sinal tirou.** Interno (C-A7) pediu tirar decorator /
   f-string / "script do manifesto" do normativo. Não varreu **evidência mínima**: import da
   sessão (AP-13), middleware no registro da rota (AP-05), import da dependência (AP-09), import
   de logger (AP-19), "nenhum arquivo importa" na verificação de TR-15.
5. **Fonte de segredo = env var (AP-02, camada config, TR-01, `.env.example`).** Interno não citou
   `credentials.yml.enc`, profiles YAML, vault. C-A8 tratou media type do baseline, não origem do
   segredo.
6. **TR-15 `:686` contradiz AP-26 `:767-772`.** Interno celebrou a exclusão de autoload em AP-26
   (fecho 2 / C-7). A verificação do TR que **executa** a remoção na Fase 3 ainda é "não importada
   por nenhum arquivo". É o ponto que apaga `puma`/`pg`/`spring-boot-starter-*`.
7. **Checklist §9.7 vs isenção de AP-13 vs §10.** Interno não cruzou as três. O agente que julga
   pelo checklist da Fase 2 (`mvc-guidelines.md:307`) reintroduz o falso positivo que C-A6 tirou
   do catálogo.
8. **Superfície não-HTTP.** Inventário e smoke test são método+path. ActiveJob, `@KafkaListener`,
   ActionCable não entram em `M` e não são declarados fora do escopo. Interno C-A8 cobriu HTML vs
   JSON, não vs não-HTTP.
9. **TR-06 "cinco camadas" vs §2 sete vs Rails três.** Interno tratou regra 4 (adotar árvore). O
   título do TR continua empurrando a decomposição em cinco pastas.
10. **AP-28 "o manifesto é curto".** Calibração residual em `requirements.txt`. Não aparece nos
    C-A.
11. **Resíduo "alto valor" em `project-analysis.md:125`** depois de C-A12 reescrever AP-08. Ponte
    morta que reintroduz o predicado vago na Fase 1.
12. **AP-02 debug+secret num único CRITICAL.** Interno C-A11 pediu alinhar escala×classificação
    (AP-12×AP-25, cota 7/7/10/4). Não separou os dois defeitos colados em AP-02.

O interno **pegou** e eu confirmo (ainda abertos no texto atual): verificação 2 sem coluna de
responsabilidade no plano (E-1); playbook só Python/JS (E-2); mapa de carga §9 vs ponteiros §6/§10
(E-3 / C-9); `Findings fixed` só C/H (E-4); AP-16/26/28 sem manifestações.

Não reabro como novidade a inversão estrutural (grafo de imports, Ruby ausente da lista de
runtime, baseline JSON-only, TR-16 inventando `migrations/*.sql`, composition root sem container):
isso estava no interno como C-A1/2/4/8/9 e, no disco de hoje, está fechado.

---

## 6. VEREDITO E CORREÇÕES

**REPROVADO** no critério do enunciado ("agnóstica de tecnologia" / "copiável").

Cópia da pasta: funciona. Execução num Rails ou Spring que a skill nunca viu: Fase 1 quase
inteira; Fase 2 enviesada (falso positivo AP-08 no model, falso negativo AP-06, evidências que
não existem na stack); Fase 3 adota a árvore e escreve o idioma Flask/Express, com risco de
apagar gems/starters no TR-15.

Correções genéricas, nos references, sem fork por projeto. Ordenadas por impacto.

### C-A14 — AP-08 não criminaliza o lugar de domínio da stack (ALTO)

O HIGH que restou depois de C-A6.

```diff
--- a/references/antipattern-catalog.md
+++ b/references/antipattern-catalog.md
@@ AP-08 NÃO é finding quando
-O que está no handler é tradução de protocolo: …
+O que está no handler é tradução de protocolo: …
+Nem é finding quando a regra vive no lugar que a convenção da stack
+designa para domínio — model ActiveRecord, entidade JPA com invariantes,
+@Service alcançável pelo container — **e** não está no handler de protocolo.
+Regra no handler continua sendo este AP. Persistência crua no handler é AP-13.
```

Diff irmão no checklist §9.3 (`mvc-guidelines.md:302`): restringir a "agregação de consulta
misturada a regra **no repositório / mapper**, não no model da stack".

### C-A15 — AP-16 cruza runtime **e** framework (ALTO)

```diff
--- a/references/antipattern-catalog.md
+++ b/references/antipattern-catalog.md
@@ procedimento AP-16
 1. Obtenha na Fase 1 a versão real do runtime …
+   e a versão do framework efetivo (Fato 2).
 2. Cruze as APIs chamadas contra as notas de depreciação **das duas**.
 3. Reporte o equivalente moderno e a versão (runtime ou framework) em que a
    depreciação entrou.
```

Em `project-analysis.md` §3: gravar `framework --version` / manifesto do framework além de
`ruby --version` / `java -version`.

### C-A16 — evidência mínima sem token de import/middleware/env (ALTO)

Um bloco por AP, mesma ideia: evidência = a linha da forma estrutural, no mecanismo da stack.

- AP-02 `:118` — "fonte externa de segredo", não "variável de ambiente".
- AP-05 `:199` — interceptação ausente no ponto que a stack usa.
- AP-09 `:301` — aresta de resolução, não import.
- AP-13 `:405` — linha que monta query / abre transação / controla sessão; apagar "import da sessão
  no módulo de rotas".
- AP-19 `:581-582` — logger alcançável, não import de biblioteca.
- AP-26 `:755-756` e TR-15 `:686` — "não referenciadas pelo mecanismo de resolução da Fase 1".

### C-A17 — AP-06 conta responsabilidades, não as quatro do monolito (ALTO)

```diff
-Existe um único arquivo ou classe que reúne, no mesmo corpo, abertura de
-conexão de banco, definição de schema, registro de rotas e regra de negócio
-- de modo que não existe fronteira onde inserir uma camada?
+Existe um único arquivo ou classe que acumula três ou mais das
+responsabilidades de mvc-guidelines.md §2, de modo que não há fronteira
+onde inserir a próxima camada?
```

O `NÃO` (`:229-232`) já diz "número de responsabilidades, não de linhas". O sinal ainda exige as
quatro do fixture. Alinhar os dois.

### C-A18 — verificação 2 lê uma coluna de responsabilidade (ALTO)

Já E-1 no interno; continua aberto. Sem isto a regra 4 esvazia a única barreira estrutural.

```diff
--- a/references/report-template.md
+++ b/references/report-template.md
 | TR | Resolve | Arquivos criados | Arquivos alterados | Arquivos removidos |
+| TR | Resolve | Responsabilidade materializada (nome da §2) | Lugar (convenção da stack) | Arquivos … |
```

`SKILL.md:241-248`: o conjunto verificado é essa coluna, não `Arquivos criados`. Vazio só é
aceitável se o plano declarar explicitamente "já materializada pela convenção, sem mudança".

### C-A19 — TR-01 / config / `.env.example` no formato da stack (MÉDIO)

- `mvc-guidelines.md:76` — entrada da camada config = fonte da stack, não "variáveis de ambiente".
- `refactor-playbook.md` TR-01 passo 3 — "arquivo de exemplo no formato que a stack já usa
  (credentials, profile YAML, `.env`, flags)".
- `report-template.md:210` — trocar `` `config/…` , `.env.example` `` por `` `config/…` (artefato
  de exemplo da stack) ``.

### C-A20 — tabela de forma com Rails e Spring (MÉDIO)

Não acrescentar 18×N exemplos. Acrescentar duas colunas (ou duas linhas-alvo) na tabela
`refactor-playbook.md:20-27`:

| Forma | Rails | Spring |
|---|---|---|
| Rotas num só lugar | `config/routes.rb` | anotações no controller / `RouterFunction` |
| Interceptar antes do handler | `before_action` / rack middleware | `Filter` / `HandlerInterceptor` |
| Composition root | initializers + container Zeitwerk | `@SpringBootApplication` + component scan |
| Persistência | ActiveRecord no model | `@Repository` / JPA |
| Migração | `db/migrate/<timestamp>_*.rb` | Flyway/Liquibase em `resources/db/migration` |
| Erro central | `rescue_from` | `@ControllerAdvice` |

Título TR-06: "Decompor nas responsabilidades que o finding exige, nos lugares da convenção" —
apagar "cinco camadas".

### C-A21 — AP-02: debug não herda CRITICAL de secret (MÉDIO)

Extrair "debug ligado + bind em todas as interfaces" para HIGH, salvo debugger interativo
alcançável (aí CRITICAL). Ou exigir os dois braços do sinal juntos para CRITICAL.

### C-A22 — AP-19 para MEDIUM **ou** justificar LOW na escala (BAIXO)

"Máscara defeitos" é o critério MEDIUM da própria tabela. Se permanecer LOW, a linha `:80` não
pode dizer que a conta é a escala aplicada entrada a entrada.

### C-A23 — leftovers (BAIXO)

- `project-analysis.md:125`: apagar "alto valor".
- AP-28 `:813`: apagar "(é curto, nesses casos)".
- `SKILL.md:109`: `Package mgr` admite lista de manifestos.
- `validation-protocol.md:18`: executável/convenção da stack antes de "script no manifesto".
- `project-analysis.md` §7 / escopo do `SKILL.md`: uma linha "superfície não-HTTP fica fora do
  `M` e vai para Fora do escopo".
- AP-16, AP-26, AP-28: campo `Manifestações por stack` (já C-12 / C-A13 no interno).

---

Nenhum arquivo da skill foi modificado nesta auditoria.
