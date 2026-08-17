# Catálogo de Anti-Patterns — 28 entradas

Arquivo de trabalho da **Fase 2**. Leia-o integralmente antes de varrer o código: a ordem da
varredura é a ordem deste catálogo, e pular entradas produz um relatório enviesado para o que
é fácil de ver.

## Como usar cada entrada

- **Sinal** — pergunta binária respondível **lendo o código**. Descreve forma estrutural
  (posição na camada, aresta do grafo, relação entre dois pontos), nunca token de linguagem.
- **Evidência mínima** — o que precisa estar no relatório para o finding existir. Sem
  `arquivo:linha` + bloco de código literal, **descarte o finding**; não o reporte com ressalva.
- **NÃO é finding quando** — limite superior, aplicado antes de escrever a entrada. Sem ele os
  28 APs aparecem em todo projeto e o relatório vira preenchimento de cota — a falha mais cara
  desta fase, porque derruba a credibilidade dos findings verdadeiros junto.
- **Aplica a** — escopo em que o sinal faz sentido, declarado na coluna homônima do índice.
  Separa "procurei e não achei" de "não havia o que procurar". Todo AP que não vira finding sai
  desta fase em **um de três estados**, e o relatório nomeia qual:
  **não encontrado** (o escopo se aplica, o sinal foi respondido "não") ·
  **não aplicável** (os fatos da Fase 1 não satisfazem o escopo — diga qual fato exclui) ·
  **não verificável** (o escopo se aplica, mas falta um fato da Fase 1 para responder o sinal;
  caso típico de AP-16 sem a versão real do runtime). Os três vão para a seção "o que não foi
  encontrado" do relatório; nenhum deles é finding, e nenhum deles agenda TR.
- **Manifestações por stack** — só para reconhecer a forma em código concreto. O sinal continua
  sendo a pergunta estrutural; a manifestação é ilustração.

Todos os exemplos são **sintéticos**, sobre um domínio fictício de reservas.

## Escala de severidade

| Nível | Critério de atribuição | Onda padrão |
|---|---|---|
| **CRITICAL** | Explorável por chamador anônimo, ou expõe credencial/PII, ou permite perda de dados. Não requer condição rara. | 1 |
| **HIGH** | Compromete integridade dos dados ou torna a evolução do código inviável sem reescrita. Requer condição plausível. | 2 |
| **MEDIUM** | Degrada correção sob carga, mascara defeitos ou multiplica o custo de cada mudança futura. | 3 |
| **LOW** | Custo de leitura e manutenção, sem efeito observável em produção. | 4 |

**A onda é propriedade do finding, não do TR.** Cada AP declara sua onda padrão; a onda de um TR é
a do finding de **maior severidade** que ele resolve — suba ou desça o rótulo conforme necessário,
e não agende TR que nenhum finding acione. Sobe: logging é Onda 3, mas com segredo em log (AP-07,
CRITICAL) roda na Onda 1. Desce: TR-06 é rotulado Onda 1, mas sem AP-06 e com AP-13 (HIGH) roda na
Onda 2 — e a Onda 1, sem TR atribuído, é vazia.

**Registre desvios.** Se atribuir a um finding severidade diferente da tabelada aqui, escreva
o motivo no próprio finding. Uma severidade sem justificativa é uma opinião.

## Índice

| AP | Nome | Sev. | Onda | Aplica a | TR |
|---|---|---|---|---|---|
| [AP-01](#ap-01) | Injection por concatenação de entrada externa | CRITICAL | 1 | Persistência ou execução dinâmica | TR-02 |
| [AP-02](#ap-02) | Hardcoded secret e debug ligado no bootstrap | CRITICAL | 1 | Universal | TR-01 |
| [AP-03](#ap-03) | Credencial ou PII na serialização de resposta | CRITICAL | 1 | APIs que serializam entidades | TR-04 |
| [AP-04](#ap-04) | Derivação de senha quebrada ou ausente | CRITICAL | 1 | Projetos com autenticação | TR-03 |
| [AP-05](#ap-05) | Rota privilegiada sem autenticação verificável | CRITICAL | 1 | Universal | TR-05 |
| [AP-06](#ap-06) | God class / god module | CRITICAL | 1 | Universal | TR-06 |
| [AP-07](#ap-07) | Segredo ou PII emitido em log | CRITICAL | 1 | Universal | TR-14 |
| [AP-08](#ap-08) | Lógica de negócio fora da camada de serviço | HIGH | 2 | Universal | TR-07 |
| [AP-09](#ap-09) | Acoplamento a dependência concreta, sem injeção | HIGH | 2 | Universal | TR-09 |
| [AP-10](#ap-10) | Estado global mutável compartilhado | HIGH | 2 | Universal | TR-09 |
| [AP-11](#ap-11) | Escrita multi-etapa sem fronteira transacional | HIGH | 2 | ≥2 escritas relacionadas | TR-10 |
| [AP-12](#ap-12) | Validação de domínio inline no handler | HIGH | 2 | Universal | TR-08 |
| [AP-13](#ap-13) | Rota acoplada diretamente ao ORM ou driver | HIGH | 2 | Projetos com ORM ou driver direto | TR-06 |
| [AP-14](#ap-14) | Mass assignment / bind não filtrado de entrada | HIGH | 2 | Universal | TR-08 |
| [AP-15](#ap-15) | N+1 aninhado | MEDIUM | 3 | Projetos com persistência | TR-11 |
| [AP-16](#ap-16) | Deprecated API usage | MEDIUM | 3 | Universal | TR-12 |
| [AP-17](#ap-17) | Duplicação com a abstração correta morta no repositório | MEDIUM | 3 | Universal | TR-15 |
| [AP-18](#ap-18) | Captura genérica de exceção e vazamento de detalhe interno | MEDIUM | 3 | Universal | TR-13 |
| [AP-19](#ap-19) | Saída de console como mecanismo de log | MEDIUM | 3 | Universal | TR-14 |
| [AP-20](#ap-20) | Política de origem cruzada permissiva | MEDIUM | 3 | APIs consumidas por browser | TR-18 |
| [AP-21](#ap-21) | DDL e seed executados no boot da aplicação | MEDIUM | 3 | Projetos com persistência | TR-16 |
| [AP-22](#ap-22) | Listagem sem paginação | MEDIUM | 3 | APIs de leitura de coleção | TR-17 |
| [AP-23](#ap-23) | Contrato de resposta inconsistente | MEDIUM | 3 | APIs | TR-13 |
| [AP-24](#ap-24) | Ausência de rate limiting no endpoint de autenticação | MEDIUM | 3 | APIs com autenticação | TR-05 |
| [AP-25](#ap-25) | Magic numbers e vocabulários literais inline | LOW | 4 | Universal | TR-18 |
| [AP-26](#ap-26) | Código morto e dependências declaradas e não usadas | LOW | 4 | Universal | TR-15 |
| [AP-27](#ap-27) | Nomenclatura pobre e sombreamento de builtin | LOW | 4 | Universal | TR-18 |
| [AP-28](#ap-28) | Ausência de infraestrutura de qualidade | LOW | — | Universal | reportado, não corrigido |

Distribuição: **CRITICAL 7 · HIGH 7 · MEDIUM 10 · LOW 4**.

---

<a id="ap-01"></a>
## AP-01 — Injection por concatenação de entrada externa

**CRITICAL · Onda 1 · TR-02**

**Sinal.** Existe query, comando de shell ou expressão interpretada montada por concatenação
ou interpolação de string contendo valor vindo de entrada externa (corpo, query string, path
param, header), em vez de parâmetro vinculado? Existe handler que recebe uma string de
consulta ou comando no payload e a repassa a um executor sem allowlist?

**Evidência mínima.** A linha da montagem, mostrando o operador de concatenação/interpolação
entre a constante e o valor externo, e o rastro do valor até o ponto de entrada.

**NÃO é finding quando.** O valor interpolado é constante do próprio código ou item de uma
allowlist fechada verificada imediatamente antes; ou é identificador de estrutura (nome de
tabela/coluna) que a linguagem não permite vincular como parâmetro **e** vem de allowlist.
Placeholder do driver dentro de uma f-string não é concatenação de entrada.

**Manifestações por stack.** Python: montagem por `+`/f-string entregue ao executor do driver.
JavaScript: template literal na string da consulta em vez do array de valores. Java: `Statement`
com string somada em vez de `PreparedStatement`. PHP: interpolação direta em `query()`.

---

<a id="ap-02"></a>
## AP-02 — Hardcoded secret e debug ligado no bootstrap

**CRITICAL · Onda 1 · TR-01**

**Sinal.** Existe literal atribuído a chave de configuração sensível (segredo de assinatura,
senha, chave de API, credencial de integração) no bootstrap ou no construtor de um serviço,
sem nenhuma leitura de variável de ambiente em todo o projeto? Existe flag de debug ou
verbosidade ligada em código junto de bind em todas as interfaces de rede?

**Evidência mínima.** A atribuição literal com a chave visível, mais a confirmação de que
nenhum arquivo do projeto lê o ambiente para aquela chave.

**NÃO é finding quando.** O literal é default de desenvolvimento **e** o valor de produção vem
do ambiente com precedência, **e** o nome do valor não sugere uso produtivo. Um placeholder
declaradamente inválido (que faria a aplicação falhar se usado) é aceitável.

**Reforços que elevam a confiança.** O valor carrega marcador de ambiente produtivo; a chave
nunca é referenciada em nenhum outro ponto (segredo que não protege nada, mas está versionado);
o debug aparece ligado em mais de um lugar.

**Manifestações por stack.** Python: atribuição no dicionário de config do app. JavaScript:
objeto de configuração literal no módulo de bootstrap. Java: valor fixo em anotação ou em
`application.properties` versionado. Qualquer stack: URL de conexão com usuário e senha embutidos.

---

<a id="ap-03"></a>
## AP-03 — Credencial ou PII na serialização de resposta

**CRITICAL · Onda 1 · TR-04**

**Sinal.** Existe função de mapeamento registro→DTO que projeta campo de credencial, segredo
ou PII e alimenta uma rota de leitura sem controle de acesso — inclusive a própria resposta de
autenticação? Existe endpoint de diagnóstico que serializa valor de configuração sensível?

**Evidência mínima.** O mapeamento com o campo sensível nomeado, mais a rota que o consome.

**NÃO é finding quando.** O campo é projetado apenas para o próprio titular, atrás de
verificação de identidade efetiva, e é dado que o titular já conhece. Um identificador opaco
sem valor de autenticação não é credencial.

**Reforço decisivo.** Outra cópia do mesmo mapeamento, em outro ponto do projeto, **omite** o
campo — o que indica exposição acidental e não decisão de contrato.

**Manifestações por stack.** Qualquer stack: serialização por espalhamento do registro inteiro
(`dict(row)`, `{...row}`, `toJSON()` sem allowlist) em vez de projeção campo a campo.

---

<a id="ap-04"></a>
## AP-04 — Derivação de senha quebrada ou ausente

**CRITICAL · Onda 1 · TR-03**

**Sinal.** A credencial é persistida em texto simples, ou derivada por hash rápido de propósito
geral, ou por função caseira — sem salt e sem fator de custo — e verificada por comparação de
igualdade simples?

**Evidência mínima.** A função de derivação (ou sua ausência no caminho de escrita) e a
comparação no caminho de verificação.

**Verificação decisiva.** Execute a função sobre entradas distintas e observe colisão; e
confira se existe dependência de hashing lento declarada no manifesto. Uma dependência de
hashing declarada e não importada é AP-26 no mesmo projeto, e reforça este finding: a
arquitetura pretendida existia.

**NÃO é finding quando.** O hash rápido está sendo usado para integridade ou deduplicação, não
para autenticação. Verifique o consumidor antes de classificar.

**Manifestações por stack.** Python: digest de biblioteca padrão aplicado direto à senha.
JavaScript: digest do módulo de criptografia nativo sem derivação de chave. Qualquer stack:
coluna de senha comparada com igualdade na cláusula da consulta.

---

<a id="ap-05"></a>
## AP-05 — Rota privilegiada sem autenticação verificável

**CRITICAL · Onda 1 · TR-05**

**Sinal.** Existe rota que executa operação destrutiva em massa, expõe dados de terceiros ou
tem path sugerindo privilégio administrativo, e que vai direto do registro ao acesso a dados
sem middleware ou decorator de verificação de identidade? O fluxo de login emite credencial
verificável (assinada, com expiração) ou apenas uma string derivada de forma previsível do
identificador do sujeito? O schema modela papéis que nenhuma decisão de autorização consulta?

**Evidência mínima.** O registro da rota sem middleware, mais o corpo do handler alcançando a
camada de dados; ou a linha que produz a credencial previsível.

**NÃO é finding quando.** A verificação existe dentro do handler (feio, mas presente e
efetiva); ou a rota é deliberadamente pública e não expõe dado de terceiro nem escreve.

**Sinal correlato de alto valor.** Papel modelado no schema e nunca lido por nenhuma decisão:
a autorização foi projetada e não implementada, e o campo dá falsa segurança ao leitor.

**Manifestações por stack.** Qualquer stack: registro de rota sem a cadeia de middlewares que
as demais rotas privilegiadas usam; token que é o identificador do sujeito codificado sem
assinatura.

---

<a id="ap-06"></a>
## AP-06 — God class / god module

**CRITICAL · Onda 1 · TR-06**

**Sinal.** Existe um único arquivo ou classe que reúne, no mesmo corpo, abertura de conexão de
banco, definição de schema, registro de rotas e regra de negócio — de modo que não existe
fronteira onde inserir uma camada?

**Evidência mínima.** As linhas de cada responsabilidade distinta no mesmo arquivo, citadas
como faixas, mais o total de linhas do arquivo.

**Sinal de nome.** Substantivo genérico com sufixo tipo "Manager", "Handler", "Helper" ou
"Util" que não delimita responsabilidade: o nome não permite prever o que está dentro.

**NÃO é finding quando.** O arquivo é grande mas monotemático — 400 linhas de repositório são
um repositório grande, não uma god class. O critério é **número de responsabilidades
distintas**, não número de linhas. Nem é finding quando o arquivo é o composition root: montar
o grafo de objetos é a responsabilidade única dele.

**Manifestações por stack.** Qualquer stack: módulo cujo topo importa driver de banco e
framework web ao mesmo tempo, e cujo corpo alterna definição de schema com definição de rota.

---

<a id="ap-07"></a>
## AP-07 — Segredo ou PII emitido em log

**CRITICAL · Onda 1 · TR-14**

**Sinal.** Existe chamada de log (ou saída de console usada como log) cujo template interpola
dado de portador de cartão, credencial, token, documento de identificação ou segredo de
configuração, sem mascaramento ou redação?

**Evidência mínima.** A chamada com o template e o argumento sensível identificado.

**NÃO é finding quando.** O valor emitido é derivado irreversível e truncado (últimos dígitos,
prefixo de identificador), ou já é público. Emitir o identificador opaco de uma entidade não é
vazamento; emitir o conteúdo dela pode ser.

**Nota de severidade.** Este AP é CRITICAL embora sua transformação (TR-14) esteja rotulada
para a Onda 3. Antecipe TR-14 para a Onda 1 quando este finding existir — a onda segue o
finding.

**Manifestações por stack.** Qualquer stack: template de log com o payload inteiro
interpolado, o que arrasta campos sensíveis sem que o autor os tenha nomeado.

---

<a id="ap-08"></a>
## AP-08 — Lógica de negócio fora da camada de serviço

**HIGH · Onda 2 · TR-07**

**Sinal.** Existe decisão de negócio de alto valor (autorização de pagamento, precificação,
elegibilidade, transição de estado) ou efeito colateral de negócio (notificação, integração
externa) escrito dentro do handler de protocolo? Ou, na direção inversa, dentro de uma função
da camada de acesso a dados, misturado a agregações de consulta?

**Evidência mínima.** O bloco de decisão dentro do handler ou da função de dados, com as
linhas exatas.

**Sinal correlato.** O controller inspeciona a **forma** do valor retornado — se é nulo, se é
lista vazia, se tem determinada chave — para decidir o status code. Isso é regra de domínio
codificada como formato de retorno, e é o sintoma mais confiável de que não existe service.

**NÃO é finding quando.** O que está no handler é tradução de protocolo: parse de entrada,
extração de header, montagem de resposta, escolha de status a partir de um **tipo de erro de
domínio** explícito. Nem é finding quando não há decisão alguma — um handler de CRUD puro que
delega e mapeia está correto (ver `mvc-guidelines.md` §10).

**Manifestações por stack.** Qualquer stack: sequência de condicionais de negócio entre o
parse do corpo e a montagem da resposta, no mesmo bloco de função.

---

<a id="ap-09"></a>
## AP-09 — Acoplamento a dependência concreta, sem injeção

**HIGH · Onda 2 · TR-09**

**Sinal.** As funções e classes obtêm suas dependências chamando uma factory global no próprio
corpo, ou instanciando infraestrutura no construtor, em vez de recebê-las como parâmetro? O
composition root constrói o objeto principal sem passar argumento algum? Parâmetros de
infraestrutura (destino do banco, porta, verbosidade do driver) estão fixados em literal? A
camada de apresentação importa a de infraestrutura, saltando a intermediária?

**Evidência mínima.** A chamada à factory global dentro do corpo, ou a instanciação no
construtor, mais o import que a torna possível.

**NÃO é finding quando.** A dependência é pura e sem estado (função utilitária determinística,
formatador) — injetar isso adiciona um parâmetro e não remove decisão alguma. Nem é finding no
próprio composition root: instanciar infraestrutura é a responsabilidade dele.

**Manifestações por stack.** Python: chamada à função de acesso ao handle global dentro de
cada função de dados. JavaScript: `require`/`import` do módulo de conexão dentro do módulo de
serviço, usado diretamente. Java: instanciação com `new` de repositório dentro do serviço.

---

<a id="ap-10"></a>
## AP-10 — Estado global mutável compartilhado

**HIGH · Onda 2 · TR-09**

**Sinal.** Existe handle de recurso (conexão, cliente, cache) ou variável mutável em escopo de
módulo, escrita pelo caminho de requisição, sem lock e sem política de invalidação — e com a
proteção de concorrência do driver explicitamente desabilitada?

**Evidência mínima.** A declaração em escopo de módulo, a escrita a partir do caminho de
requisição, e a linha que desabilita a proteção do driver (quando houver).

**Sinal correlato.** Acumulador global estruturalmente incapaz de funcionar: primitivo
exportado por valor e nunca relido, contador que cada worker incrementa isoladamente. O código
declara uma intenção que a linguagem não permite cumprir.

**NÃO é finding quando.** O global é imutável após a inicialização (configuração carregada uma
vez, tabela de constantes), ou é um pool cujo próprio contrato é ser compartilhado e que é
thread-safe por construção.

**Manifestações por stack.** Python: variável de módulo guardando conexão, criada sob demanda.
JavaScript: objeto exportado e mutado por handlers. Qualquer stack: cache em dicionário de
módulo sem expiração.

---

<a id="ap-11"></a>
## AP-11 — Escrita multi-etapa sem fronteira transacional

**HIGH · Onda 2 · TR-10**

**Sinal.** Existe sequência de escritas relacionadas sem limite transacional explícito, com
retorno antecipado de erro no meio da sequência e sem compensação? Existe verificação de
disponibilidade de recurso separada da sua consumação (check-then-act) sem atomicidade? Existe
deleção que remove o registro principal deixando dependentes órfãos, em schema sem integridade
referencial declarada?

**Evidência mínima.** As escritas em sequência com as linhas, e o ponto de retorno antecipado
que deixa o estado parcial; ou o par verificação/consumação com as linhas de cada um.

**NÃO é finding quando.** As escritas são idempotentes e independentes entre si, de modo que a
falha parcial não produz estado inválido; ou existe compensação explícita no caminho de erro;
ou o banco declara a constraint que torna a condição de corrida impossível.

**Cenário a citar no impacto.** Descreva a interleaving concreta que produz o estado inválido —
sem ela, o finding é uma preocupação genérica e não um defeito.

**Manifestações por stack.** Qualquer stack: duas ou mais operações de escrita consecutivas
com commit implícito por operação, ou sem bloco transacional que as envolva.

---

<a id="ap-12"></a>
## AP-12 — Validação de domínio inline no handler

**HIGH · Onda 2 · TR-08**

**Sinal.** As invariantes de domínio (faixa numérica, tamanho de campo, vocabulário fechado,
formato) estão escritas como sequência de condicionais com literais dentro do handler, sem
constraint equivalente no schema e sem camada de escrita que as imponha?

**Evidência mínima.** O bloco de condicionais com os literais, mais a ausência da constraint
correspondente na definição da tabela.

**Agravante decisivo.** A **mesma** invariante aplicada de forma divergente entre a rota de
criação e a de atualização da mesma entidade — a regra existe em dois lugares e já discordou de
si mesma. Cite as duas linhas lado a lado; é a evidência mais persuasiva deste AP.

**NÃO é finding quando.** A verificação é de protocolo, não de domínio: campo obrigatório
ausente no corpo, tipo incompatível, payload malformado. Isso pertence à borda mesmo.

**Manifestações por stack.** Qualquer stack: cadeia de condicionais com retorno de erro, uma
por campo, antes da primeira linha útil do handler.

---

<a id="ap-13"></a>
## AP-13 — Rota acoplada diretamente ao ORM ou driver

**HIGH · Onda 2 · TR-06**

**Sinal.** Os handlers manipulam a sessão ou transação de persistência diretamente e constroem
queries a partir das classes de model, sem camada de serviço ou repositório interposta, com a
sessão importada como singleton de módulo?

**Evidência mínima.** O import da sessão no módulo de rotas e a manipulação dela dentro do
handler.

**Inversão típica a procurar.** Decisão de serialização de API vivendo no model e decisão de
transação vivendo no controller — exatamente trocadas. Quando encontrar as duas juntas, relate
como uma inversão só: são a mesma causa.

**Nota de onda.** TR-06 resolve este AP e também AP-06. Quando os dois existirem, TR-06 roda na
Onda 1 pela severidade de AP-06 e fecha este de carona; quando só este existir, roda na Onda 2.

**NÃO é finding quando.** O projeto é uma única rota de leitura trivial sem regra alguma, e a
camada intermediária adicionaria um salto sem remover decisão (ver `mvc-guidelines.md` §10).
Verifique se essa isenção vale para **todas** as rotas antes de aplicá-la.

**Manifestações por stack.** Python: sessão do ORM importada no módulo de rotas e comitada no
handler. JavaScript: cliente de banco chamado dentro do callback da rota. Java: repositório
injetado direto no controller sem serviço, com transação anotada no controller.

---

<a id="ap-14"></a>
## AP-14 — Mass assignment / bind não filtrado de entrada

**HIGH · Onda 2 · TR-08**

**Sinal.** O payload de entrada é repassado inteiro ao construtor da entidade ou ao update de
persistência, sem allowlist explícita de campos — permitindo que o chamador escreva colunas que
o contrato não expõe (papel, flag de ativação, identificador de proprietário, timestamps)?

**Evidência mínima.** A linha que espalha o payload na entidade ou no update, mais a lista de
colunas graváveis do schema que não deveriam ser escritas pelo chamador.

**NÃO é finding quando.** A entidade só tem campos que o chamador legitimamente controla, ou
um schema declarativo faz strip dos campos desconhecidos antes do bind. A existência do schema
não basta: confirme que ele **remove** o extra em vez de apenas ignorá-lo na validação.

**Procedência.** Conhecimento de domínio — não observado durante a calibragem do catálogo, onde
os projetos analisados atribuíam campo a campo. Mantido porque um catálogo que só contém o que
os fixtures têm falha silenciosamente no primeiro projeto diferente.

**Manifestações por stack.** Python: `Entity(**payload)` ou update com o dicionário do corpo.
JavaScript: `Object.assign(entity, req.body)` ou espalhamento do corpo no update.

---

<a id="ap-15"></a>
## AP-15 — N+1 aninhado

**MEDIUM · Onda 3 · TR-11**

**Sinal.** Existe consulta a banco disparada dentro de laço que itera o resultado de uma
consulta anterior, em dois ou mais níveis, onde uma junção resolveria numa ida só?

**Evidência mínima.** O laço externo com a consulta que o alimenta, e a consulta interna, com
as linhas de ambos. Estime a contagem de idas ao banco em função do tamanho do resultado.

**Agravantes.** O mapeamento objeto-relacional **já declara** o relacionamento que resolveria
por eager loading — a solução está no projeto e não é usada; ou um cursor novo é alocado por
iteração, somando custo de recurso ao custo de rede.

**Variante correlata.** Agregação numérica (soma, contagem, máximo) calculada em laço na
aplicação sobre a tabela inteira, quando exprimível na própria consulta.

**NÃO é finding quando.** O laço externo tem cardinalidade fixa e pequena garantida pelo
domínio (um conjunto fechado de categorias, por exemplo) e a junção não simplificaria a
leitura. Cardinalidade "pequena hoje" que depende dos dados não conta.

**Manifestações por stack.** Python: acesso a atributo de relacionamento dentro do laço,
disparando lazy load. JavaScript: `await` de consulta dentro de `for`/`map` sobre o resultado
anterior. Qualquer stack: consulta dentro de consulta em dois níveis de aninhamento.

---

<a id="ap-16"></a>
## AP-16 — Deprecated API usage

**MEDIUM · Onda 3 · TR-12**

**Sinal.** Existe chamada a API marcada como deprecated **na versão de runtime efetivamente em
uso** — a do ambiente, não a do manifesto — repetida no caminho quente, sem aviso de migração
no projeto?

**Procedimento obrigatório.** Este AP não é detectável por leitura isolada:

1. Obtenha na Fase 1 a versão **real** do runtime executando o interpretador/VM do ambiente.
2. Cruze as APIs efetivamente chamadas contra as notas de depreciação **daquela** versão.
3. Reporte, para cada ocorrência, o equivalente moderno e a versão em que a depreciação entrou.

Checar contra a versão do manifesto produz falso negativo silencioso, e é o modo de falha mais
provável deste AP: projetos que não declaram versão alguma são os que mais acumulam chamadas
deprecated.

**Evidência mínima.** A chamada com `arquivo:linha`, a versão do runtime obtida na Fase 1, e a
nota de depreciação correspondente.

**NÃO é finding quando.** A API é deprecated numa versão **superior** à do runtime em uso, ou
existe camada de compatibilidade explícita no projeto com comentário de migração.

**Reforço.** Ausência de linter configurado explica a sobrevivência da chamada e justifica que
TR-12 fixe a regra, não apenas substitua a chamada.

**Nota de procedência.** Observado numa única stack durante a calibragem: o sinal vale para
qualquer runtime, mas a evidência de travessia entre stacks é mais fraca que a dos demais APs.

---

<a id="ap-17"></a>
## AP-17 — Duplicação com a abstração correta morta no repositório

**MEDIUM · Onda 3 · TR-15**

**Sinal.** A mesma regra ou o mesmo bloco de mapeamento aparece copiado em três ou mais pontos
**enquanto o repositório já contém a implementação correta que ninguém invoca** — método de
domínio na entidade, função utilitária, constante nomeada, ou um diretório de camada inteiro
cuja classe não é importada por nenhum caminho de execução?

**Verificação decisiva.** Para cada símbolo exportado, conte referências **fora** do módulo de
origem. Importar não é usar: um import sem chamada mantém o símbolo morto.

**Evidência mínima.** As três ou mais cópias com suas linhas, **mais** a linha da abstração
correta e a contagem de referências externas a ela (tipicamente zero).

**NÃO é finding quando.** As ocorrências são semelhantes mas divergem em regra — unificá-las
exigiria um parâmetro de comportamento, o que troca duplicação por acoplamento. Duas
ocorrências também não bastam: o limiar é três.

**Por que este AP tem rendimento desproporcional.** Em projetos parcialmente organizados, ele
converte a Fase 3 de "criar camadas" em "ligar as camadas que já existem" — que é uma
refatoração muito menor e muito menos arriscada. Procure-o **antes** de propor estrutura nova.

**Manifestações por stack.** Qualquer stack: classe de serviço presente no diretório correto,
com a lógica certa, e zero imports apontando para ela.

---

<a id="ap-18"></a>
## AP-18 — Captura genérica de exceção e vazamento de detalhe interno

**MEDIUM · Onda 3 · TR-13**

**Sinal.** Existe bloco de captura sem tipo especificado que descarta o objeto de erro sem
registro, ou que serializa a representação textual da exceção no corpo da resposta ao cliente —
repetido em todos os handlers, sem tratador centralizado e sem distinguir falha de domínio de
defeito?

**Evidência mínima.** Um bloco representativo com as linhas, mais a contagem de ocorrências do
mesmo padrão no projeto.

**Consequência a confirmar.** Erro de cliente reportado como falha de servidor: entrada
inválida que deveria virar 4xx vira 5xx porque a captura genérica não distingue. Confirme
seguindo um caminho concreto antes de afirmar.

**NÃO é finding quando.** A captura ampla está na fronteira do processo, é o tratador
centralizado, e registra o erro completo emitindo ao cliente apenas um identificador de
correlação. Isso é o alvo de TR-13, não o defeito.

**Manifestações por stack.** Qualquer stack: bloco de captura da exceção base da linguagem
devolvendo a mensagem da exceção no corpo da resposta.

---

<a id="ap-19"></a>
## AP-19 — Saída de console como mecanismo de log

**MEDIUM · Onda 3 · TR-14**

**Sinal.** A saída direta para stdout é usada como registro de eventos, sem níveis de
severidade, timestamp ou destino configurável, e sem import de biblioteca de logging em nenhum
arquivo do projeto?

**Evidência mínima.** Ocorrências representativas com linhas, mais a confirmação de que
nenhum arquivo importa biblioteca de logging.

**Reforço.** O próprio projeto define um helper de log padronizado que nenhum chamador usa
(cruza com AP-17); caminhos de erro respondem ao cliente e descartam o erro sem registrá-lo em
lugar nenhum, tornando o defeito invisível em produção.

**NÃO é finding quando.** A saída de console é a interface do programa (ferramenta de linha de
comando) e não registro de evento; ou é um script de uso único fora do caminho de requisição.

**Manifestações por stack.** Python: `print` no caminho de requisição. JavaScript:
`console.log`/`console.error` como único registro. Qualquer stack: saída sem nível nem
timestamp em código servidor.

---

<a id="ap-20"></a>
## AP-20 — Política de origem cruzada permissiva

**MEDIUM · Onda 3 · TR-18**

**Sinal.** Existe middleware de política de origem cruzada aplicado globalmente com
configuração padrão permissiva, cobrindo indistintamente rotas públicas, de escrita e de
remoção — em um sistema sem autenticação efetiva?

**Evidência mínima.** A linha de registro do middleware sem argumentos de restrição, mais a
existência de rotas de escrita não autenticadas que ela passa a cobrir.

**NÃO é finding quando.** A API é deliberadamente pública e somente leitura; ou a origem é
restrita por allowlist configurável por ambiente; ou o consumo não é por browser e nenhuma
credencial trafega por cookie.

**Nota de composição.** A severidade deste AP é função da autenticação: onde há autenticação
por cookie, ele sobe. Registre o desvio quando elevar.

**Manifestações por stack.** Qualquer stack: registro do middleware de origem cruzada com
configuração padrão, sem lista de origens.

---

<a id="ap-21"></a>
## AP-21 — DDL e seed executados no boot da aplicação

**MEDIUM · Onda 3 · TR-16**

**Sinal.** A criação de schema é executada como efeito colateral do import ou do boot, sem
ferramenta de migração no manifesto, por comando que só cria tabelas ausentes e nunca altera
colunas existentes? Existem dados de demonstração — inclusive credencial administrativa
conhecida — inseridos incondicionalmente em qualquer ambiente, no mesmo corpo que cria o schema?

**Evidência mínima.** A chamada de DDL no caminho de boot, mais a inserção de seed sem guarda
de ambiente.

**Consequência a nomear.** Como o comando só cria o que falta, qualquer evolução de coluna
passa a exigir apagar o banco. O projeto fica sem caminho de evolução de schema, e isso é o
dano real — maior que o incômodo de criar tabela no boot.

**Sinal estrutural adicional.** Definições de tabela sem restrições de integridade declaradas
(sem chave estrangeira, sem unicidade, sem não-nulo onde o domínio exige). Reporte junto: a
mesma transformação resolve.

**NÃO é finding quando.** A criação está atrás de guarda de ambiente de desenvolvimento
explícita, ou o projeto usa ferramenta de migração e o boot apenas verifica a versão aplicada.

**Manifestações por stack.** Qualquer stack: DDL executada na função que obtém a conexão, ou
no topo do módulo de banco, rodando em todo import.

---

<a id="ap-22"></a>
## AP-22 — Listagem sem paginação

**MEDIUM · Onda 3 · TR-17**

**Sinal.** Os endpoints de listagem retornam o conjunto completo sem parâmetro de limite,
offset ou cursor, tornando o tamanho da resposta função dos dados e não do contrato?

**Evidência mínima.** O handler de listagem e a consulta sem cláusula de limite.

**Sinal auxiliar valioso.** Os próprios artefatos do repositório — comentários, backlog
embutido, dados de seed em volume — já descrevem a lacuna. Citar o comentário do próprio
projeto que reconhece o problema torna o finding difícil de contestar.

**NÃO é finding quando.** A coleção tem cardinalidade fechada pelo domínio (lista de estados,
de tipos, de configurações) e não cresce com o uso.

**Cuidado de contrato.** A paginação muda o shape da resposta se envolver a lista num
envelope. Isso é breaking change e vai para a seção correspondente do relatório — ver TR-17
para a variante que preserva a forma do item.

**Manifestações por stack.** Qualquer stack: consulta de listagem sem limite, resultado
serializado inteiro no corpo.

---

<a id="ap-23"></a>
## AP-23 — Contrato de resposta inconsistente

**MEDIUM · Onda 3 · TR-13**

**Sinal.** Handlers equivalentes emitem envelopes diferentes — campo de status presente no erro
de um recurso e ausente no de outro, erro em texto puro enquanto o sucesso é JSON, ausência de
código de erro estável, idiomas misturados no mesmo handler — ou colapsam falha de
infraestrutura e recurso inexistente no mesmo status?

**Evidência mínima.** Dois handlers equivalentes lado a lado, com os envelopes divergentes
citados literalmente. A comparação **é** a evidência; uma amostra só não demonstra
inconsistência.

**NÃO é finding quando.** A divergência é deliberada e documentada (uma rota de compatibilidade
mantendo formato legado, por exemplo), ou os recursos comparados não são equivalentes.

**Cuidado de contrato.** Uniformizar envelope é a breaking change mais frequente desta skill.
Enumere na seção Breaking changes **cada endpoint** cujo corpo muda, não a mudança em geral.

**Manifestações por stack.** Qualquer stack: chaves de erro com nomes diferentes entre
handlers, ou status 500 devolvido para recurso não encontrado.

---

<a id="ap-24"></a>
## AP-24 — Ausência de rate limiting no endpoint de autenticação

**MEDIUM · Onda 3 · TR-05**

**Sinal.** O endpoint de autenticação — ou qualquer rota que revele existência de conta —
aceita tentativas ilimitadas do mesmo chamador, sem contador, backoff ou bloqueio?

**Evidência mínima.** O handler de autenticação sem contador, mais a ausência de middleware de
limite de taxa no registro da rota e de dependência correspondente no manifesto.

**NÃO é finding quando.** O limite é aplicado por infraestrutura à frente da aplicação
(gateway, proxy) e isso é verificável no repositório. Suposição de que "deve haver um proxy"
não conta como verificação.

**Procedência.** Conhecimento de domínio — não observado durante a calibragem, onde a
autenticação analisada era fraca o bastante para tornar força bruta desnecessária. Ausência de
ocorrência não é ausência de risco: registre o AP quando TR-05 corrigir a autenticação, porque
a correção torna a força bruta o próximo caminho mais barato.

**Manifestações por stack.** Qualquer stack: rota de autenticação registrada sem middleware de
limite, sem contador de tentativas por sujeito e sem atraso progressivo.

---

<a id="ap-25"></a>
## AP-25 — Magic numbers e vocabulários literais inline

**LOW · Onda 4 · TR-18**

**Sinal.** Existe literal numérico sem nome usado como limiar em regra de validação ou de
negócio, sem constante nomeada e sem correspondência com restrição declarada no schema?
Existe conjunto fechado de valores válidos declarado como lista literal reconstruída dentro do
handler, sem enum e sem constraint equivalente? Existe tradução entre valor armazenado e
rótulo de negócio embutida na montagem da resposta?

**Evidência mínima.** O literal com a linha e o significado que ele carrega, mais a ausência da
constante correspondente.

**NÃO é finding quando.** O literal é autoevidente no contexto (`0`, `1`, `-1` como sentinelas
idiomáticas, base de conversão, índice). Nomear `0` como `ZERO` piora a leitura.

**Manifestações por stack.** Qualquer stack: comparação com número solto dentro de condicional
de negócio; lista de strings válidas repetida em dois handlers.

---

<a id="ap-26"></a>
## AP-26 — Código morto e dependências declaradas e não usadas

**LOW · Onda 4 · TR-15**

**Sinal.** Existem símbolos importados e nunca referenciados, símbolos exportados e nunca
consumidos, ou dependências declaradas no manifesto e não importadas por nenhum arquivo?

**Evidência mínima.** O símbolo ou a dependência, com a linha da declaração e a contagem de
referências (zero).

**Leitura de alto valor do sinal.** Quando as dependências mortas correspondem exatamente a
lacunas apontadas por outros findings — validação declarativa, configuração por ambiente,
hashing lento — elas revelam a **arquitetura pretendida e não implementada**. Relate a
correspondência: ela converte vários findings LOW numa observação de projeto, e indica que a
correção é mais barata do que parecia, já que a dependência está no manifesto.

**NÃO é finding quando.** O símbolo é ponto de extensão público de uma biblioteca, ou a
dependência é usada por ferramenta e não por import (formatador, hook de build).

**Regra de camada.** Diretório de camada inteiro inalcançável a partir do entry point é este AP
— e é o gatilho da regra de alcançabilidade de `mvc-guidelines.md` §6. Registre o conteúdo
**antes** de propor a remoção.

---

<a id="ap-27"></a>
## AP-27 — Nomenclatura pobre e sombreamento de builtin

**LOW · Onda 4 · TR-18**

**Sinal.** Existe nome de builtin da linguagem usado como parâmetro ou variável local? Existem
identificadores de uma a três letras recebendo campos de payload em handler extenso? A
assinatura tem muitos parâmetros posicionais do mesmo tipo primitivo, permitindo troca de ordem
sem erro? Os nomes do contrato público divergem do vocabulário do domínio?

**Evidência mínima.** O identificador com a linha, e — para o caso dos parâmetros posicionais —
a assinatura completa, que é onde o risco de troca fica visível.

**NÃO é finding quando.** O nome curto é convenção estabelecida e local (índice de laço,
variável de compreensão de uma linha). Nomes curtos em escopo de três linhas são legíveis.

**Manifestações por stack.** Python: builtin usado como nome de parâmetro. JavaScript: sombra
de global do runtime. Qualquer stack: função com quatro strings posicionais seguidas.

---

<a id="ap-28"></a>
## AP-28 — Ausência de infraestrutura de qualidade

**LOW · Reportado, não corrigido**

**Sinal.** O manifesto não declara dependências de desenvolvimento, script além do de execução,
nem versão de runtime; e o repositório não tem arquivo de teste, configuração de lint, exemplo
de variáveis de ambiente ou pipeline de CI? Faixas de versão abertas convivem com lockfile?

**Evidência mínima.** O manifesto completo (é curto, nesses casos) e a listagem que comprova a
ausência dos artefatos.

**Este AP não tem TR.** Instalar test runner, linter e CI está fora do escopo declarado da
skill. Reporte-o, descreva o que faltaria, e **não** o inclua no plano apresentado no gate —
prometer no gate o que a Fase 3 não vai fazer é a forma mais direta de invalidar o gate.

**Coberturas parciais que outras transformações produzem, e que valem citar no finding:** TR-01
publica o exemplo de variáveis de ambiente; TR-12 pode fixar uma regra de linter contra a
regressão da API deprecated. São consequências, não o escopo deste AP.

**NÃO é finding quando.** A infraestrutura existe fora do diretório analisado (monorepo com
configuração na raiz) — verifique um nível acima antes de reportar.
