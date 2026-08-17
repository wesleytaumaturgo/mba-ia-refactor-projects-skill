# Refactor Playbook — 18 transformações

Arquivo da **Fase 3**. Leia o índice; depois leia **apenas as seções dos TRs que a auditoria
acionou**. Carregar as 18 seções desperdiça o contexto de que a refatoração precisa.

> **Adapte o padrão ao idioma da stack detectada na Fase 1. Os exemplos ilustram a forma, não
> a sintaxe a copiar.** Um refactor em Python escrito com idioma de JavaScript (ou o inverso)
> é o modo de falha mais provável deste arquivo, e o mais difícil de perceber em revisão:
> o código funciona e parece estrangeiro.

Todos os exemplos são **sintéticos**, sobre um domínio fictício de reservas, e mostram apenas
o trecho que muda.

## Regras de execução

- **Onda é propriedade do finding, não do TR.** O rótulo de cada TR abaixo é o **padrão, não a
  atribuição**: a onda de um TR é a do finding de maior severidade que ele resolve — sobe (TR-14
  vai à Onda 1 quando existe AP-07) ou desce (TR-06 vai à Onda 2 quando há AP-13 e não há AP-06).
  **TR que nenhum finding aciona não é agendado em onda alguma.**
- **TR-01 e TR-06 primeiro, na onda que o plano lhes deu**, porque criam a estrutura de que os
  demais dependem. Aplicar TR-04 antes de haver camadas obriga a refazê-lo.
- **Boot após cada TR.** O commit é o ponto de retorno; o boot é o localizador do defeito. Um
  boot vermelho depois de um TR custa um conserto; depois de seis, uma investigação.
- **Smoke test e commit ao fim da onda**, nunca por TR. Ver `validation-protocol.md`.
- **Nada de mudança de shape não declarada.** Se um TR alterar o corpo de uma resposta sem que
  isso conste da seção Breaking changes aprovada, pare: é regressão, não melhoria.

---

## Índice

Localize a seção pelo cabeçalho literal `## TR-NN`.

| TR | Onda | Resolve | Transformação |
|---|---|---|---|
| TR-01 | 1 | AP-02 | Extrair configuração para módulo de ambiente com fail-fast |
| TR-02 | 1 | AP-01 | Vincular parâmetros e fechar a execução dinâmica |
| TR-03 | 1 | AP-04 | Derivar senha com primitiva lenta e migrar por reidratação |
| TR-04 | 1 | AP-03 | Separar entidade de DTO com allowlist de projeção |
| TR-05 | 1 | AP-05, AP-24 | Autenticar com credencial assinada e negar por padrão |
| TR-06 | 1 | AP-06, AP-13 | Decompor a god class nas cinco camadas |
| TR-07 | 2 | AP-08 | Mover regra e efeito colateral para o service |
| TR-08 | 2 | AP-12, AP-14 | Validador declarativo por entidade com allowlist de bind |
| TR-09 | 2 | AP-09, AP-10 | Inverter a resolução de dependências no composition root |
| TR-10 | 2 | AP-11 | Envolver as escritas relacionadas numa unidade de trabalho |
| TR-11 | 3 | AP-15 | Colapsar o laço de consultas numa ida só ao banco |
| TR-12 | 3 | AP-16 | Substituir a chamada deprecated e fixar a regra no linter |
| TR-13 | 3 | AP-18, AP-23 | Error handler centralizado com envelope único |
| TR-14 | 3 (ou 1) | AP-19, AP-07 | Logger com níveis, timestamp e redação de sensíveis |
| TR-15 | 3 | AP-17, AP-26 | Consolidar na abstração existente e remover o morto |
| TR-16 | 3 | AP-21 | Migração versionada, seed separado, constraints declaradas |
| TR-17 | 3 | AP-22 | Paginação com defaults explícitos |
| TR-18 | 4 | AP-25, AP-27, AP-20 | Nomear literais, renomear identificadores, restringir origem |

AP-28 não tem TR: é reportado e não corrigido.

## TR-01 — Extrair configuração para módulo de ambiente com fail-fast

**Onda 1 · Resolve AP-02 · Pré-condição:** os valores sensíveis foram inventariados na Fase 2,
com `arquivo:linha` de cada um.

**Passos.**
1. Crie o módulo de configuração: um leitor por chave, tipado, que **falha no boot** quando
   uma variável obrigatória está ausente.
2. Substitua cada literal sensível pela leitura correspondente; o composition root injeta o
   objeto de configuração adiante em vez de cada módulo lê-lo.
3. Publique um arquivo de exemplo com as chaves e **sem** valores reais; confirme que o de
   ambiente real está ignorado pelo VCS. Desligue debug fora de desenvolvimento e restrinja o
   bind de rede ao que o ambiente definir.

**Python [sintético]**
```python
# antes
app.config["SIGNING_KEY"] = "literal-value-123"
app.config["DEBUG"] = True
# depois
settings = load_settings()          # levanta ConfigError se faltar chave obrigatória
app.config["SIGNING_KEY"] = settings.signing_key
app.config["DEBUG"] = settings.debug
```

**JavaScript [sintético]**
```javascript
// antes
const SIGNING_KEY = "literal-value-123";
// depois
const settings = loadSettings();    // lança ConfigError se faltar chave obrigatória
const SIGNING_KEY = settings.signingKey;
```

**Risco.** Fail-fast transforma variável esquecida em aplicação que não sobe — é o
comportamento desejado, mas quebra o boot da validação se o ambiente local não tiver as chaves.
Defina os valores de desenvolvimento antes de rodar o primeiro boot pós-TR.

**Verificação.** A aplicação sobe com as variáveis definidas; sobe com erro **explícito** e
mensagem nomeando a chave quando você remove uma obrigatória; nenhum literal sensível
sobrevive à busca no código.

## TR-02 — Vincular parâmetros e fechar a execução dinâmica

**Onda 1 · Resolve AP-01 · Pré-condição:** todos os pontos de montagem por concatenação foram
listados; nenhum será deixado para depois.

**Passos.**
1. Converta cada consulta para parâmetros vinculados, passando os valores separados da string.
2. Onde o valor externo for identificador de estrutura (não vinculável), valide-o contra
   allowlist fechada antes de interpolar.
3. Remova por inteiro qualquer endpoint que aceite consulta ou comando arbitrário no payload.
   Operação administrativa legítima pertence a script fora da superfície HTTP.
4. Confirme que a remoção do endpoint consta da seção Breaking changes aprovada.

**Python [sintético]**
```python
# antes
cursor.execute("SELECT * FROM reservation WHERE code = '" + code + "'")
# depois
cursor.execute("SELECT * FROM reservation WHERE code = ?", (code,))
```

**JavaScript [sintético]**
```javascript
// antes
db.query(`SELECT * FROM reservation WHERE code = '${code}'`);
// depois
db.query("SELECT * FROM reservation WHERE code = $1", [code]);
```

**Risco.** Tipos que antes eram coagidos pela concatenação passam a ser vinculados como estão;
uma coluna numérica que recebia string agora pode divergir. Confira os tipos dos parâmetros nos
caminhos de busca.

**Verificação.** Nenhuma string de consulta contém operador de concatenação com variável; uma
entrada com aspas ou operador de comentário de SQL retorna resultado vazio em vez de erro ou
de dado extra.

## TR-03 — Derivar senha com primitiva lenta e migrar por reidratação

**Onda 1 · Resolve AP-04 · Pré-condição:** os caminhos de escrita e de verificação de
credencial estão identificados; existe dependência de hashing lento disponível para a stack.

**Passos.**
1. Adote uma primitiva de derivação lenta da plataforma, com salt por registro e fator de
   custo configurável — nunca uma função caseira.
2. Reescreva a verificação para comparar por função de tempo constante da própria primitiva.
3. Migre por **reidratação**: na próxima autenticação bem-sucedida contra o formato antigo,
   regrave a credencial no formato novo. Marque o formato no próprio valor armazenado.
4. Amplie a coluna de credencial se o formato novo for mais longo que o antigo.

**Python [sintético]**
```python
# antes
stored = fast_digest(password).hexdigest()
ok = stored == row["password"]
# depois
stored = password_hasher.hash(password)      # salt + fator de custo embutidos
ok = password_hasher.verify(row["password"], password)
```

**JavaScript [sintético]**
```javascript
// antes
const stored = fastDigest(password);
const ok = stored === row.password;
// depois
const stored = await passwordHasher.hash(password);
const ok = await passwordHasher.verify(row.password, password);
```

**Risco.** A derivação lenta custa centenas de milissegundos por chamada — é o objetivo. Se o
smoke test tiver timeout curto no endpoint de autenticação, ele passa a falhar por tempo e não
por defeito. Ajuste o timeout antes de concluir que a onda ficou vermelha.

**Verificação.** Credenciais persistidas não são legíveis; duas contas com a mesma senha
produzem valores armazenados diferentes; o login antigo continua funcionando e, após o
primeiro sucesso, o valor armazenado está no formato novo.

## TR-04 — Separar entidade de DTO com allowlist de projeção

**Onda 1 · Resolve AP-03 · Pré-condição:** a camada de controllers existe (TR-06 aplicado, se
o projeto era monolítico).

**Passos.**
1. Crie um serializador por contexto de saída, projetando uma **allowlist** explícita de
   campos. Espalhar o registro inteiro e depois remover chaves é frágil: o próximo campo
   sensível entra sozinho.
2. Aplique-o em todas as respostas que hoje serializam a entidade, inclusive a de autenticação.
3. Remova endpoints de diagnóstico que serializem configuração.
4. Registre cada campo removido da resposta na seção Breaking changes.

**Python [sintético]**
```python
# antes
return jsonify(dict(row))
# depois
def to_guest_dto(row):
    return {"id": row["id"], "name": row["name"]}   # credencial e documento não atravessam
return jsonify(to_guest_dto(row))
```

**JavaScript [sintético]**
```javascript
// antes
res.json(row);
// depois
const toGuestDto = (row) => ({ id: row.id, name: row.name });
res.json(toGuestDto(row));
```

**Risco.** Consumidores existentes que liam um campo removido quebram. É exatamente o que a
seção Breaking changes existe para declarar antes do gate.

**Verificação.** Nenhuma resposta contém campo de credencial, segredo ou documento; a resposta
de autenticação carrega apenas a credencial de sessão e a identificação mínima do sujeito.

## TR-05 — Autenticar com credencial assinada e negar por padrão

**Onda 1 · Resolve AP-05, AP-24 · Pré-condição:** o inventário de rotas da Fase 1 classifica
cada rota como pública, autenticada ou privilegiada.

**Passos.**
1. Emita, no login, uma credencial **assinada e expirável** com a chave que TR-01 trouxe do
   ambiente. Uma string derivada do identificador do sujeito não é credencial.
2. Crie o middleware de verificação e o de autorização por papel. Faça a decisão consultar o
   papel que o schema já modela — se ele existe e ninguém o lê, ligá-lo é parte deste TR.
3. Aplique **negar por padrão**: a rota declara que é pública; a ausência de declaração não
   libera.
4. Aplique limite de taxa por sujeito e por origem no endpoint de autenticação (AP-24). Sem
   ele, corrigir a autenticação apenas move o caminho mais barato de ataque para força bruta.

**Python [sintético]**
```python
# antes
app.add_url_rule("/reservations/purge", view_func=purge_reservations, methods=["POST"])
# depois
app.add_url_rule("/reservations/purge",
                 view_func=require_role("staff")(purge_reservations), methods=["POST"])
```

**JavaScript [sintético]**
```javascript
// antes
router.post("/reservations/purge", purgeReservations);
// depois
router.post("/reservations/purge", authenticate, requireRole("staff"), purgeReservations);
```

**Risco.** O smoke test do baseline foi capturado sem autenticação: depois deste TR, as rotas
protegidas passam a responder 401. Isso **não** é regressão — atualize o roteiro de smoke test
para autenticar antes de chamar as rotas protegidas, e registre a mudança de status como
breaking change declarada.

**Verificação.** Rota privilegiada sem credencial responde 401; com credencial de papel
insuficiente responde 403; com credencial válida responde como no baseline. Tentativas
repetidas de login são barradas após o limite.

## TR-06 — Decompor a god class nas cinco camadas

**Onda 1 · Resolve AP-06, AP-13 · Pré-condição:** `mvc-guidelines.md` lido; a variante
idiomática da stack e a granularidade de controller (§7) já decididas.

**Passos.**
1. **Extraia a persistência primeiro.** Mova toda montagem de consulta para repositórios por
   agregado. A camada de dados é a que tem menos dependências de saída, então move-se com o
   menor risco.
2. **Extraia a regra depois.** Mova as decisões de negócio para services que recebem os
   repositórios por parâmetro.
3. **Deixe o roteamento como casca fina.** O controller faz parse, chama o service, mapeia o
   resultado. Três linhas úteis.
4. **Monte o composition root**; o entry point só monta o grafo e sobe. Faça um TR por
   agregado quando houver mais de um, com boot entre eles.

**Python [sintético]**
```python
# antes — mesmo corpo: schema, consulta, regra e rota
@app.route("/reservations", methods=["POST"])
def create_reservation(): ...
# depois — quatro arquivos, uma responsabilidade cada
# repositories/reservation_repository.py → insert(), find_by_code()
# services/reservation_service.py        → create() decide e orquestra
# controllers/reservation_controller.py  → parse, chama service, mapeia resposta
# routes/reservation_routes.py           → método + path + middlewares
```

**JavaScript [sintético]**
```javascript
// antes — rota com consulta e regra no próprio callback
// depois
// src/repositories/reservationRepository.js → insert(), findByCode()
// src/services/reservationService.js        → create() decide e orquestra
// src/controllers/reservationController.js  → parse, chama service, mapeia resposta
// src/routes/reservationRoutes.js           → método + path + middlewares
```

**Risco.** É o TR de maior superfície e concentra o risco da Onda 1. Mover em uma tacada torna
qualquer quebra indepurável — vá agregado por agregado. Cuidado com import circular entre
service e repositório.

**Verificação.** Nenhum arquivo importa driver e framework web ao mesmo tempo; nenhum handler
menciona sessão, cursor ou dialeto; a aplicação sobe e todas as rotas do baseline continuam
registradas com o mesmo método e path.

## TR-07 — Mover regra e efeito colateral para o service

**Onda 2 · Resolve AP-08 · Pré-condição:** existe camada de service (TR-06, quando aplicável).

**Passos.**
1. Mova a decisão de negócio do handler para um método do service, nomeado pelo caso de uso.
2. Mova também o efeito colateral (notificação, integração) para o service, atrás de uma
   dependência injetada — não de uma chamada direta a cliente concreto.
3. Faça o service sinalizar o resultado com **tipo de erro de domínio**, não com forma do
   retorno. Um `None` que significa "não encontrado" força o controller a decidir regra.
4. Retire da camada de dados qualquer regra que tenha ido parar lá junto com agregação.

**Python [sintético]**
```python
# antes — no handler
if total > 500: total = total * 0.9
# depois — no service
def price(self, reservation):
    return self._discount_policy.apply(reservation.total)
```

**JavaScript [sintético]**
```javascript
// antes — no handler
if (total > 500) total = total * 0.9;
// depois — no service
price(reservation) {
  return this.discountPolicy.apply(reservation.total);
}
```

**Risco.** Mover a regra sem mover o teste do status code deixa o controller inspecionando a
forma do retorno — o sintoma volta com outra roupa. Introduza o erro de domínio no mesmo TR.

**Verificação.** Nenhum service importa símbolo de protocolo; nenhum handler contém condicional
sobre valor de negócio; os status codes do baseline não mudaram.

## TR-08 — Validador declarativo por entidade com allowlist de bind

**Onda 2 · Resolve AP-12, AP-14 · Pré-condição:** as invariantes foram inventariadas, com as
divergências entre criação e atualização já mapeadas na Fase 2.

**Passos.**
1. Declare as invariantes uma vez por entidade, num validador invocado pelo service.
2. Resolva cada divergência **explicitamente**: escolha a regra correta e registre a escolha.
   Duas regras que discordavam não podem virar uma por acidente.
3. Aplique allowlist de campos vinculáveis: o payload nunca vai inteiro para a entidade nem
   para o update.
4. Espelhe as invariantes como constraints no schema, junto com TR-16.

**Python [sintético]**
```python
# antes
if len(name) < 3 or nights > 30: return error(400)
entity = Reservation(**payload)
# depois
data = ReservationSchema.validate(payload)          # invariantes num lugar só
entity = Reservation(name=data.name, nights=data.nights)   # allowlist explícita
```

**JavaScript [sintético]**
```javascript
// antes
if (name.length < 3 || nights > 30) return res.status(400).json(...);
Object.assign(entity, req.body);
// depois
const data = reservationSchema.validate(req.body);
Object.assign(entity, { name: data.name, nights: data.nights });
```

**Risco.** Unificar duas regras divergentes muda o comportamento de um dos endpoints — entrada
antes aceita passa a ser rejeitada, ou o inverso. Declare no gate qual das duas venceu.

**Verificação.** A mesma entrada inválida é rejeitada com o mesmo status nas rotas de criação e
de atualização; um payload com campo extra não o grava; a constraint equivalente existe no
schema.

## TR-09 — Inverter a resolução de dependências no composition root

**Onda 2 · Resolve AP-09, AP-10 · Pré-condição:** existe um entry point identificado que pode
assumir o papel de composition root.

**Passos.**
1. Troque cada chamada a factory global no corpo por um parâmetro recebido no construtor ou na
   função.
2. Faça o composition root instanciar tudo, na ordem config → infraestrutura → repositórios →
   services → controllers → rotas.
3. Converta estado mutável de módulo em instância com ciclo de vida explícito, criada no
   composition root e injetada; se for handle compartilhado, use pool thread-safe em vez de
   variável de módulo com a proteção do driver desligada.
4. Remova acumuladores globais que a linguagem torna estruturalmente inoperantes.

**Python [sintético]**
```python
# antes
def find_reservation(code):
    db = shared_connection()            # dependência resolvida no corpo
# depois
class ReservationRepository:
    def __init__(self, db): self._db = db     # dependência recebida
```

**JavaScript [sintético]**
```javascript
// antes
const db = require("./db");             // dependência resolvida no import
function findReservation(code) { return db.query(...); }
// depois
const makeReservationRepository = (db) => ({ findByCode: (code) => db.query(...) });
```

**Risco.** Remover o singleton expõe ordem de inicialização que antes era acidental: algo que
funcionava porque o módulo era importado cedo pode passar a receber `undefined`. Suba a
aplicação após cada agregado convertido.

**Verificação.** Nenhum módulo abaixo do composition root instancia infraestrutura; um
repositório pode ser construído em isolamento com uma implementação alternativa de banco; a
aplicação sobe.

## TR-10 — Envolver as escritas relacionadas numa unidade de trabalho

**Onda 2 · Resolve AP-11 · Pré-condição:** as sequências de escrita e os pares check-then-act
foram identificados, com a interleaving que produz estado inválido descrita no relatório.

**Passos.**
1. Abra uma transação explícita no service (não no controller) e faça os repositórios operarem
   sobre ela.
2. Faça rollback em todo caminho de erro, inclusive nos retornos antecipados.
3. Substitua check-then-act por operação atômica — atualização condicional que retorna quantas
   linhas afetou — ou por constraint que torne a corrida impossível. Declare a integridade
   referencial no schema para que a deleção não deixe órfãos (junto com TR-16).

**Python [sintético]**
```python
# antes
repo.insert_reservation(r); repo.decrement_availability(r.slot)
# depois
with uow.transaction():
    repo.insert_reservation(r)
    if repo.decrement_availability_if_free(r.slot) == 0:
        raise SlotUnavailable()          # rollback automático na saída do bloco
```

**JavaScript [sintético]**
```javascript
// antes
await repo.insertReservation(r); await repo.decrementAvailability(r.slot);
// depois
await uow.transaction(async (tx) => {
  await repo.insertReservation(r, tx);
  if ((await repo.decrementAvailabilityIfFree(r.slot, tx)) === 0) throw new SlotUnavailable();
});
```

**Risco.** Transações longas seguram lock e mudam o comportamento sob concorrência; e uma
transação aberta no controller anula o ganho. Mantenha o bloco no service e curto.

**Verificação.** Um erro forçado no meio da sequência não deixa registro parcial; a consumação
concorrente do último recurso disponível falha para um dos chamadores em vez de estourar o
limite.

## TR-11 — Colapsar o laço de consultas numa ida só ao banco

**Onda 3 · Resolve AP-15 · Pré-condição:** existe camada de repositório onde a nova consulta
possa viver.

**Passos.**
1. Substitua o laço por uma junção, por eager loading declarado, ou por carga em lote a partir
   do conjunto de chaves — nesta ordem de preferência.
2. Mova agregação calculada em laço para a cláusula da consulta.
3. Reagrupe o resultado em memória depois da consulta única, preservando a **forma** de saída
   que o baseline tinha.
4. Reutilize um cursor por chamada em vez de alocar um por iteração.

**Python [sintético]**
```python
# antes
for r in reservations:
    r["items"] = db.execute("SELECT * FROM item WHERE reservation_id = ?", (r["id"],))
# depois
rows = db.execute("SELECT r.*, i.* FROM reservation r LEFT JOIN item i ON i.reservation_id = r.id")
reservations = group_items_by_reservation(rows)
```

**JavaScript [sintético]**
```javascript
// antes
for (const r of reservations) r.items = await db.query("... WHERE reservation_id = $1", [r.id]);
// depois
const rows = await db.query("SELECT r.*, i.* FROM reservation r LEFT JOIN item i ON i.reservation_id = r.id");
const reservations = groupItemsByReservation(rows);
```

**Risco.** A junção pode alterar a ordem dos itens e a presença de coleções vazias — um
`LEFT JOIN` sem item produz linha com colunas nulas. Se a forma do corpo mudar, é breaking
change e precisa estar declarada.

**Verificação.** A contagem de consultas executadas por requisição deixa de crescer com o
número de registros; o corpo da resposta é igual ao do baseline, item a item.

## TR-12 — Substituir a chamada deprecated e fixar a regra no linter

**Onda 3 · Resolve AP-16 · Pré-condição:** a versão **real** do runtime foi obtida na Fase 1 e
consta do relatório, junto com o equivalente moderno de cada chamada.

**Passos.**
1. Substitua cada ocorrência pelo equivalente da versão em uso, começando pelo caminho quente.
2. Verifique semântica, não apenas assinatura: substitutos frequentemente mudam o default
   (fuso, codificação, tratamento de nulo).
3. Fixe uma regra de linter que impeça a regressão. Sem isso, a chamada volta na próxima
   contribuição — e a ausência de linter é o que explica a sobrevivência dela até aqui.
4. Registre a versão de runtime mínima no manifesto, para que a checagem futura tenha âncora.

**Python [sintético]**
```python
# antes
import imp                                  # deprecated desde 3.4, removido em 3.12
module = imp.load_source(name, path)
# depois
import importlib.util
module = load_module_from_path(name, path)  # via importlib.util
```

**JavaScript [sintético]**
```javascript
// antes
const buf = new Buffer(input, "utf8");      // deprecated desde Node 6
// depois
const buf = Buffer.from(input, "utf8");
```

**Risco.** Substituto com default diferente muda comportamento silenciosamente — o caso clássico
é o de APIs de tempo, onde o equivalente moderno passa a exigir fuso explícito. Compare a saída
antes e depois em um valor conhecido.

**Verificação.** A execução não emite aviso de depreciação; o linter reprova uma reintrodução
proposital da chamada antiga; o comportamento observável do endpoint afetado é o do baseline.

## TR-13 — Error handler centralizado com envelope único

**Onda 3 · Resolve AP-18, AP-23 · Pré-condição:** existem tipos de erro de domínio (introduzidos
em TR-07) ou eles serão criados aqui.

**Passos.**
1. Defina o envelope único de erro: código estável, mensagem para humano, identificador de
   correlação. Um idioma só.
2. Instale o tratador na fronteira do processo, com mapa erro-de-domínio → status HTTP.
3. Remova os blocos de captura genérica dos handlers. O tratador registra o erro completo e
   devolve apenas o envelope — nunca a representação textual da exceção.
4. Separe o que estava colapsado: inexistente é 404, entrada inválida é 4xx, defeito é 5xx.

**Python [sintético]**
```python
# antes
except Exception as e: return jsonify({"erro": str(e)}), 500
# depois
@app.errorhandler(DomainError)
def handle(e):
    logger.warning("domain_error", extra={"code": e.code, "cid": correlation_id()})
    return jsonify({"error": {"code": e.code, "message": e.message}}), STATUS[type(e)]
```

**JavaScript [sintético]**
```javascript
// antes
catch (e) { res.status(500).json({ erro: e.message }); }
// depois
app.use((err, req, res, next) => {
  logger.warn("domain_error", { code: err.code, cid: req.correlationId });
  res.status(STATUS[err.constructor] ?? 500).json({ error: { code: err.code, message: err.message } });
});
```

**Risco.** Uniformizar o envelope é a breaking change mais frequente desta skill, e muda o
status de casos que antes eram 500. Enumere **cada endpoint** afetado na seção Breaking changes,
não a mudança em geral.

**Verificação.** Nenhum handler contém captura genérica; nenhuma resposta contém texto de
exceção nem caminho de arquivo; erro de cliente responde 4xx e o defeito aparece no log com o
mesmo identificador de correlação da resposta.

## TR-14 — Logger com níveis, timestamp e redação de sensíveis

**Onda 3 — antecipe para a Onda 1 quando existir AP-07 · Resolve AP-19, AP-07**
**Pré-condição:** a configuração do destino e do nível veio do ambiente (TR-01).

**Passos.**
1. Instale um logger com níveis, timestamp e destino configurável; injete-o em vez de importá-lo
   como global onde a camada já recebe dependências.
2. Substitua cada saída de console do caminho de requisição por chamada com nível apropriado.
3. Aplique **redação por allowlist de campos emitíveis** antes de qualquer emissão. Uma
   denylist de nomes sensíveis falha no primeiro campo novo.
4. Nunca emita o payload inteiro: é assim que campos sensíveis vazam sem ninguém os ter nomeado.

**Python [sintético]**
```python
# antes
print("charge for card " + card_number + " token " + token)
# depois
logger.info("charge_attempted", extra={"card_last4": card_number[-4:], "guest_id": guest_id})
```

**JavaScript [sintético]**
```javascript
// antes
console.log("charge for card " + cardNumber + " token " + token);
// depois
logger.info("charge_attempted", { cardLast4: cardNumber.slice(-4), guestId });
```

**Risco.** Trocar console por logger sem configurar destino em desenvolvimento faz o registro
sumir da saída, e a validação passa a rodar às cegas. Confirme que o nível de desenvolvimento
mostra o que você precisa ver durante a Fase 3.

**Verificação.** Nenhuma saída direta de console no caminho de requisição; uma busca por
credencial, token ou documento no log de um fluxo completo não retorna nada; todo registro tem
nível e timestamp.

## TR-15 — Consolidar na abstração existente e remover o morto

**Onda 3 · Resolve AP-17, AP-26 · Pré-condição:** a regra de alcançabilidade
(`mvc-guidelines.md` §6) foi aplicada, e o conteúdo do que será removido já está registrado
como finding no relatório aprovado.

**Passos.**
1. Para cada duplicação, verifique se a abstração correta **já existe** no repositório. Se
   existir, ligue os chamadores a ela em vez de criar outra — é a diferença entre ligar camadas
   e recriá-las.
2. Reconcilie as divergências entre as cópias antes de unificar; se divergirem em regra, não
   unifique (ver AP-17, contra-exemplo).
3. Remova símbolos mortos e dependências declaradas e não importadas.
4. Antes de remover uma dependência morta, confira se ela não corresponde a uma lacuna que
   outro TR desta sessão vai preencher — nesse caso, use-a em vez de removê-la.

**Python [sintético]**
```python
# antes — a mesma regra copiada em três handlers, e um método de domínio que ninguém chama
if reservation["status"] == "H": label = "held"
# depois
label = Reservation.status_label(reservation)   # método que já existia, agora alcançável
```

**JavaScript [sintético]**
```javascript
// antes
if (reservation.status === "H") label = "held";
// depois
const label = Reservation.statusLabel(reservation);
```

**Risco.** Remoção baseada em busca textual apaga símbolo alcançado por reflexão, por
carregamento dinâmico ou por configuração. Confirme a alcançabilidade pelo grafo de imports
**e** por busca no repositório inteiro antes de apagar.

**Verificação.** A abstração antes morta tem referências externas contadas maiores que zero; a
aplicação sobe após a remoção; o manifesto não declara dependência que nenhum arquivo importa.

## TR-16 — Migração versionada, seed separado, constraints declaradas

**Onda 3 · Resolve AP-21 · Pré-condição:** o schema efetivo foi capturado na Fase 1 e serve de
base para a primeira migração.

**Passos.**
1. Extraia a DDL do boot para uma migração versionada inicial que reproduza o schema atual.
2. Declare no schema as restrições que hoje só existem em código ou em lugar nenhum: chaves
   estrangeiras, unicidade, não-nulo, faixas — espelhando as invariantes de TR-08.
3. Mova o seed para um script separado, executável sob demanda e nunca no boot. Remova
   credencial de demonstração do seed de qualquer ambiente que não seja local.
4. Deixe o boot apenas **verificar** a versão de schema aplicada e falhar com mensagem clara se
   estiver defasada.

**Python [sintético]**
```python
# antes — no módulo de banco, roda em todo import
cursor.execute("CREATE TABLE IF NOT EXISTS reservation (...)")
# depois
# migrations/0001_initial.sql  → o mesmo DDL, com FK, UNIQUE e NOT NULL declarados
# scripts/seed_dev.py          → dados de demonstração, execução manual
```

**JavaScript [sintético]**
```javascript
// antes — no módulo de banco, roda em todo require
db.exec("CREATE TABLE IF NOT EXISTS reservation (...)");
// depois
// migrations/0001_initial.sql  → o mesmo DDL, com FK, UNIQUE e NOT NULL declarados
// scripts/seedDev.js           → dados de demonstração, execução manual
```

**Risco.** Adicionar constraint a um banco com dados existentes falha se os dados já violarem a
regra — e essa violação costuma existir justamente porque a constraint nunca existiu. Verifique
os dados antes; sem isso a onda fica vermelha por causa do banco, não do código.

**Verificação.** A aplicação sobe contra um banco já migrado sem executar DDL; um banco vazio
fica utilizável rodando a migração e o seed explicitamente; inserir registro que viola a
integridade agora falha no banco.

## TR-17 — Paginação com defaults explícitos

**Onda 3 · Resolve AP-22 · Pré-condição:** os endpoints de listagem estão inventariados, com a
forma exata do corpo do baseline.

**Passos.**
1. Aceite limite e offset (ou cursor) como parâmetros de query, com default explícito e teto
   máximo — o teto é o que impede que o cliente reintroduza o problema.
2. Aplique a cláusula na consulta do repositório, nunca fatiando em memória: fatiar depois de
   trazer tudo não resolve nada.
3. Preserve a **forma do item**. Se envolver a lista num envelope com metadados, isso é
   breaking change e precisa estar declarado e aprovado.
4. Valide os parâmetros com o validador de TR-08 em vez de condicionais no handler.

**Python [sintético]**
```python
# antes
rows = db.execute("SELECT * FROM reservation")
# depois
limit = min(int(query.get("limit", DEFAULT_LIMIT)), MAX_LIMIT)
rows = db.execute("SELECT * FROM reservation LIMIT ? OFFSET ?", (limit, offset))
```

**JavaScript [sintético]**
```javascript
// antes
const rows = await db.query("SELECT * FROM reservation");
// depois
const limit = Math.min(Number(req.query.limit ?? DEFAULT_LIMIT), MAX_LIMIT);
const rows = await db.query("SELECT * FROM reservation LIMIT $1 OFFSET $2", [limit, offset]);
```

**Risco.** Um consumidor que dependia de receber a coleção inteira passa a receber uma página.
O default é uma decisão de contrato: escolha-o alto o bastante para não quebrar o uso comum e
declare-o na seção Breaking changes.

**Verificação.** Sem parâmetros, a resposta tem no máximo o default de itens; com limite acima
do teto, o teto vence; o item individual tem exatamente a forma do baseline; a consulta traz
apenas a página.

## TR-18 — Nomear literais, renomear identificadores, restringir origem

**Onda 4 · Resolve AP-25, AP-27, AP-20 · Pré-condição:** as ondas anteriores que executaram estão
verdes e commitadas; as vazias não bloqueiam. Esta onda é a de menor risco e roda por último de
propósito.

**Passos.**
1. Promova cada literal com significado a constante nomeada ou enum, e mantenha o valor
   idêntico. Renomear e mudar valor no mesmo passo torna a quebra indepurável.
2. Renomeie identificadores para o vocabulário do domínio e elimine sombreamento de builtin.
   Agrupe parâmetros posicionais do mesmo tipo primitivo num objeto quando forem trocáveis
   sem erro.
3. Restrinja a política de origem cruzada a uma allowlist vinda do ambiente, por método e por
   rota, em vez do padrão permissivo global.
4. Não renomeie campo de contrato público sem declará-lo como breaking change.

**Python [sintético]**
```python
# antes
if nights > 30: ...
CORS(app)
# depois
MAX_NIGHTS_PER_RESERVATION = 30
if nights > MAX_NIGHTS_PER_RESERVATION: ...
CORS(app, origins=settings.allowed_origins, methods=["GET", "POST"])
```

**JavaScript [sintético]**
```javascript
// antes
if (nights > 30) { }
app.use(cors());
// depois
const MAX_NIGHTS_PER_RESERVATION = 30;
if (nights > MAX_NIGHTS_PER_RESERVATION) { }
app.use(cors({ origin: settings.allowedOrigins, methods: ["GET", "POST"] }));
```

**Risco.** Renomeação em massa por busca e substituição atinge strings e comentários, e altera
nome de coluna ou chave de resposta sem intenção. Renomeie por símbolo, não por texto.

**Verificação.** Nenhum literal de negócio solto em condicional; nenhum builtin sombreado; a
requisição de uma origem não listada é recusada e a de uma origem listada é aceita; o corpo de
todas as respostas é idêntico ao do baseline.
