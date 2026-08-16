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
