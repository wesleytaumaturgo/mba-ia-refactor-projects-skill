# Review de prontidão — desafio Skills / `refactor-arch`

> **Postura:** avaliador do enunciado (`docs/enunciado.md`). Sem benefício da dúvida.
> Somente leitura, exceto este arquivo. Nada foi consertado.
> **HEAD auditado:** `df646d0` (`docs(reports): add audit-project-{1,2,3}.md as required by the challenge`).
> **Branch:** `main` = `origin/main` = `df646d0effb0fea80d5ddbbb7e4f16d378912a84`.
> **Data:** 2026-08-17.

**Veredito:** PRONTO PARA ENTREGA.

Nenhum entregável obrigatório falta. As 12 células de aceite têm evidência no disco que
confirma a afirmação. O README mente em dois números secundários (inventário 25≠23;
comentário `200 = teto` ≠ saída 10) e acerta nos números que o enunciado cobra. Isso
não derruba a entrega; está na §3 e na §4.

---

## 1. MATRIZ DE ENTREGA

| Item exigido | Presente? | Caminho | Observação |
|---|---|---|---|
| Skill `refactor-arch` no projeto 1 | SIM | `code-smells-project/.claude/skills/refactor-arch/SKILL.md` + 6 references | Nome e `SKILL.md` intactos. 293 + 3057 linhas no pacote (conferido por `wc -l`). Slash command extra em `code-smells-project/.claude/commands/refactor-arch.md` (37 linhas). |
| Skill no projeto 2 | SIM | `ecommerce-api-legacy/.claude/skills/refactor-arch/` | `diff -rq` contra o projeto 1: vazio. Cópia literal. |
| Skill no projeto 3 | SIM | `task-manager-api/.claude/skills/refactor-arch/` | `diff -rq` contra o projeto 1: vazio. Cópia literal. |
| Código refatorado commitado — projeto 1 | SIM | commits `5e0591b` `dc0e74c` `222bb9a` `d1b9b8e` `48b6f7b` | Baseline `ec6d1d4`. `controllers.py` / `models.py` da raiz sumiram (esperado). Árvore MVC em disco. |
| Código refatorado commitado — projeto 2 | SIM | commits `4701894` `fb19464` `0d1eacc` `cc8d8a5` | Baseline `5d02287`. `src/AppManager.js` e `src/utils.js` não existem mais. |
| Código refatorado commitado — projeto 3 | SIM | commits `7fd2012` `9e81e4d` `3235b4b` `303c1f9` `e86217f` | Baseline `f580ee5`. Camadas novas + `utils/` religado. |
| `reports/audit-project-1.md` | SIM | `reports/audit-project-1.md` | md5 idêntico a `reports/audit-code-smells-project.md` (`954189804125379dcacf416e8d5eb3bc`). 26 cabeçalhos `### [`. Rodapé `:1088`. |
| `reports/audit-project-2.md` | SIM | `reports/audit-project-2.md` | md5 idêntico a `reports/audit-ecommerce-api-legacy.md`. 20 findings. Rodapé `:969`. |
| `reports/audit-project-3.md` | SIM | `reports/audit-project-3.md` | md5 idêntico a `reports/audit-task-manager-api.md`. 23 findings. Rodapé `:1670`. |
| README seção A — Análise Manual | SIM | `README.md:11-142` | 3 tabelas + consolidado 75. Dossiês em `.planning/analise-manual/{code-smells-project,ecommerce-api-legacy,task-manager-api}.md`. Mix C/H/M/L existe nos dossiês; o recorte do README não lista 2 LOW por projeto (ver §3). |
| README seção B — Construção da Skill | SIM | `README.md:144-481` | 5 áreas mapeadas + 6º arquivo justificado. Catálogo 28 APs (7/7/9/5). Playbook 18 TRs, 18 `python` + 18 `javascript`. |
| README seção C — Resultados | SIM | `README.md:485-840` | Placar 12 células, totais 26/20/23, árvores antes/depois, checklist, logs de boot, limitações. |
| README seção D — Como Executar | SIM | `README.md:844-1012` | Pré-requisitos, 3 blocos de boot, curls de validação, invocação da skill. |
| Estrutura vs diagrama do enunciado | SIM, com desvio esperado | raiz + 3 projetos + `reports/` | O diagrama do enunciado (`docs/enunciado.md:291-337`) mostra o **antes**. O depois é MVC. A skill está no path exigido nos 3. `reports/audit-project-{1,2,3}.md` existem (commit `df646d0`). Extras permitidos: `evidence/`, `.planning/`, `docs/enunciado.md`, baselines JSON, cópias `audit-<projeto>.md`. |
| 5 áreas de conhecimento na skill | SIM | `SKILL.md:23-32` + `references/` | Análise, catálogo, template, MVC, playbook. `validation-protocol.md` é +1 declarado. |
| ≥8 anti-patterns, severidade distribuída | SIM | `references/antipattern-catalog.md` | 28 cabeçalhos `## AP-NN`. Linha `:85`: `CRITICAL 7 · HIGH 7 · MEDIUM 9 · LOW 5`. README cita `:80` — número de linha velho; o texto está em `:85`. |
| Detecção de API deprecated | SIM | `antipattern-catalog.md` AP-16; `reports/audit-project-3.md` F-016 | Encontrado no projeto 3 (34 chamadas). Projetos 1 e 2: "não encontrado", declarado. |
| ≥8 TRs com antes/depois | SIM | `references/refactor-playbook.md` | 18 cabeçalhos `## TR-NN`. 18+18 blocos. |
| Fase 2 pede confirmação | SIM | `SKILL.md` gate; rodapé dos 3 reports | Prompt literal `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` em `reports/audit-project-1.md:1093` e `audit-project-3.md:1675`. |
| Fase 3 valida boot + endpoints | SIM | `SKILL.md` + `validation-protocol.md` + `evidence/run-*/validacao.md` | Reexecutado nesta auditoria (seção 4). |

---

## 2. CRITÉRIOS DE ACEITE

Fonte da afirmação: `README.md:489-494`. Cada célula foi aberta no arquivo que o README cita.
Contagem de findings refeita por `grep` sobre `reports/audit-project-{1,2,3}.md`.
CA-4 reexecutado nesta sessão (seção 4).

| Critério | `code-smells-project` | `ecommerce-api-legacy` | `task-manager-api` |
|---|---|---|---|
| **CA-1** Fase 1 detecta stack | **PASSA.** `evidence/run-1/checagem.md:14-26` — 5/5 campos. Runtime 3.12.3 e Flask 3.1.1 conferidos nesta máquina (`python3 --version`, `pip show flask`). Relatório `reports/audit-project-1.md:10-11`. | **PASSA.** `evidence/run-2/checagem.md:10-30` — 13/13. Nesta máquina: Node v24.12.0, npm 11.6.2, Express 4.22.1, sqlite3 5.1.7. Relatório `reports/audit-project-2.md:10-11`. | **PASSA.** `evidence/run-3/checagem.md:16-41` — 15/15. Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 + Flask-CORS 4.0.0 (`pip show`). Relatório `reports/audit-project-3.md:10-14`. |
| **CA-2** Fase 2 ≥ 5 findings | **PASSA.** `grep -c '^### \[' reports/audit-project-1.md` = **26**. `evidence/run-1/checagem.md:50-65`. Mínimo 5. | **PASSA.** Mesmo `grep` = **20**. `evidence/run-2/checagem.md:48-66`. | **PASSA.** Mesmo `grep` = **23**. `evidence/run-3/checagem.md:65-79`. |
| **CA-3** ≥ 1 CRITICAL ou HIGH | **PASSA.** 8 CRITICAL + 6 HIGH = **14**. `evidence/run-1/checagem.md:69-71`. Cabeçalhos em `reports/audit-project-1.md:81-502`. | **PASSA.** 5 + 6 = **11**. `evidence/run-2/checagem.md:70-80`. | **PASSA.** 4 + 5 = **9**. `evidence/run-3/checagem.md:107` e cabeçalhos `reports/audit-project-3.md:120-627`. |
| **CA-4** aplicação funciona após refatoração | **PASSA.** Evidência citada: `evidence/run-1/validacao.md:281-286` (19/19). Reexecução: boot em `127.0.0.1:5000`, `/health` 200 sem `secret_key`, login 200, `/relatorios/vendas` 401, `POST /admin/query` 404. Saída na §4. | **PASSA.** `evidence/run-2/validacao.md:310-315` (4/4). Reexecução: boot porta 3000, checkout `{"msg":"Sucesso","enrollment_id":2}`, report anônimo 401, report autenticado 200 envelope, DELETE anônimo 401. | **PASSA.** `evidence/run-3/validacao.md:481-499` (22/22). Reexecução: boot, `/health` 200, login emite token, `/users` 401 sem credencial e 200 com token (sem campo `password`), `fake-jwt-token-1` → 401. |

**12/12 passam.** Nenhuma célula afirma o que o arquivo citado nega.

Ressalva que o próprio README já declara (`README.md:749-756`): o CA-4 do projeto 2 assenta em `M = 4`. A evidência confirma 4/4; o peso é menor. Não é mentira.

---

## 3. CONSISTÊNCIA README × DISCO

Amostragem do que o README afirma com número, path ou árvore.

### 3.1 O que confere

| Afirmação (README) | Disco | Veredito |
|---|---|---|
| Skill 7 arquivos, 3.057 linhas; SKILL.md 293; command 37 | `wc -l` no pacote = 293+830+334+225+819+238+318 = **3057**; command = 37 | Confere |
| `diff -r` das três `.claude/` vazio | `diff -rq` nesta sessão: vazio | Confere |
| Catálogo 28 APs, 7/7/9/5 | 28 `## AP-NN`; `:85` declara 7/7/9/5 | Confere (linha citada `:80` está deslocada; ver 3.2) |
| 18 TRs, 18 python + 18 javascript | `grep -c '```python'` / `'```javascript'` = 18/18; 18 `## TR-NN` | Confere |
| Totais Fase 2: 26 / 20 / 23 e 8·6·7·5 / 5·6·4·5 / 4·5·9·5 | `grep` dos cabeçalhos + rodapés `:1088`, `:969`, `:1670` | Confere |
| Análise manual 27+22+26 = 75 | Dossiês: AM-001–027, AM-028–049, AM-050–075 | Confere |
| Cobertura 85,2% / 77,3%·86,4%·95,5% / 96,2%·98,1% | `evidence/run-1/checagem.md:134-135`; `run-2/checagem.md:125-127`; `run-3/checagem.md:191-192` | Confere com a evidência citada (não recontada finding a finding nesta auditoria) |
| LOC antes: 780 / 180 / 1.158 | `git show` dos baselines: 88+292+314+86=780; 14+141+25=180; 15 `.py` = 1158 | Confere |
| LOC depois: 2.155 / 1.157 / 2.286 | `find`+`wc -l` em `.py`/`.js` excluindo `.venv`/`node_modules`/`.claude` | Confere |
| Arquivos-fonte depois P1: 58 `.py`; P3: 53 `.py` | `find … -name '*.py'` = 58 e 53 | Confere |
| `routes/` P1 = 66 LOC; P3 = 85 LOC | `wc -l` = 66 e 85 | Confere |
| `utils/` 0 → 25 sítios | 16 `utc_now(` + 9 `format_date(` fora de `helpers.py` = 25 | Confere |
| SHAs de onda e baseline | `git cat-file -t` em todos os 16 SHAs da tabela `README.md:633-635` | Confere |
| `git ls-files \| grep -i smoke` vazio | vazio | Confere — harness **não** está no repo |
| Sem `CLAUDE.md` | `git ls-files` sem `CLAUDE.md` | Confere |
| Placares 7✅/2⚠️ (r2) e 9✅ (r4); r3 = 9/0 citada | `.planning/02-review-rodada2.md:35`; `.planning/02-review-interno.md:65` | Confere |
| C-A14/16/17/20/23 ainda abertos | AP-08 `:285-288` sem isenção de model da stack; AP-02 `:123` ainda fala "variável de ambiente"; AP-06 `:224-226` ainda exige as quatro; TR-06 título `:277` "cinco camadas"; `project-analysis.md:125` ainda tem "alto valor" | Confere — o README **não esconde** o que existe |
| `express` = 1 no grep da skill | `antipattern-catalog.md:96` = palavra **expressão** | Confere |

### 3.2 O que não fecha

| Afirmação | Disco | Gravidade |
|---|---|---|
| Inventário de acoplamento tem **25** linhas (`README.md:839`) | Tabela em `.planning/03-review-agnosticismo.md:104-126` = **23** linhas de dado | README × disco. Número usado para sustentar que "15" é o único irreconstruível. 12 e 10 fecham; 25 não. |
| `antipattern-catalog.md:80` declara 7/7/9/5 (`README.md:205`) | A frase está na **linha 85** | Referência de linha velha. O fato existe. |
| Depois do projeto 2: **33 arquivos** · 1.157 LOC (`README.md:533`, `:588`) | 29 `.js` (LOC 1.157); 35 tracked sem `.claude`; 33 = tracked sem `README.md` e `api.http` | 33 só fecha com exclusão não declarada. LOC confere. Não é o mesmo critério de "58 arquivos-fonte" do projeto 1. |
| `/tasks?limit=999` imprime **200** (`README.md:959`) | Seed documentado cria 10 tasks (`task-manager-api/seed.py`, `task-manager-api/README.md`). Comando real imprime **10** | Comentário da seção D falso. Comando roda. Ver §4. |
| Decisão: numeração `audit-project-{1,2,3}` **não** foi acoplada (`README.md:381`) | Os três arquivos existem, cópias byte a byte, commit `df646d0` | A skill de fato escreve `audit-<projeto>.md`. O humano acrescentou as cópias depois e o README não atualiza a decisão. Não esconde o arquivo — esconde que ele passou a existir. |

### 3.3 `[ausente]` e a nota das rodadas

O briefing desta auditoria dizia "quatro lugares". No disco há **um** token literal:

```
README.md:840    O número 15: `[ausente]`.
```

`git log -S '[ausente]'` aponta só `ca13fcf`. Não há outros três placeholders.

Quatro *declarações de ausência* em prosa, sem o token:

1. **Número 15 do review externo** (`README.md:835-840`). O arquivo `.planning/03-review-agnosticismo.md` foi sobrescrito pela segunda passagem. Seção 5 atual tem **12** itens numerados; seção 6 tem **10** correções C-A14…C-A23; inventário tem **23** linhas. O 15 não é reconstruível. Declaração **honesta**. Não esconde um "15" que exista.
2. **Divisão 5 internas + 1 externa** (`README.md:321-322`). No disco: `.planning/02-review-rodada2.md` (rodada 2) e `.planning/02-review-interno.md` (rodada 4, que cita rodadas 1 e 3 como séries `A-n`/`D-n`). Rodadas 1 e 3 **não** têm arquivo próprio. `.planning/03-review-agnosticismo.md` é uma passagem externa sobrescrita. 4 internas + 2 passagens externas = 6. A nota **corrige** a conta velha. Honesta.
3. **Harness de smoke** (`README.md:1007-1012`). `git ls-files \| grep -i smoke` vazio. Honesta.
4. **C-A14…C-A23 não aplicadas** (`README.md:474-481`, `:805-819`). Confirmado no texto da skill (amostra na tabela 3.1). Honesta — e o contrário de esconder: o dado existe e o README admite que não mexeu.

Nenhuma das quatro esconde arquivo, finding ou número que o disco tenha.

### 3.4 Recorte da seção A vs mínimo do enunciado

O enunciado (`docs/enunciado.md:135-140`) pede, **no README**, ≥5 problemas por projeto com ≥1 C/H, ≥2 MEDIUM, ≥2 LOW.

Tabelas publicadas em `README.md:46-99`:

| Projeto | C | H | M | L no recorte |
|---|---|---|---|---|
| P1 | 7 | 7 | 2 | **0** |
| P2 | 4 | 7 | 3 | **1** (AM-045) |
| P3 | 5 | 3 | 3 | **1** (AM-069) |

Os dossiês têm 5 / 5 / 7 LOW. O consolidado (`README.md:103-108`) declara esses totais e aponta `.planning/analise-manual/`. O dado existe; o recorte do README **não cumpre sozinho** o mix de 2 LOW. Não classifico como bloqueador porque a mesma seção A incorpora os dossiês por referência e o consolidado. Registro como recorte incompleto.

---

## 4. TESTE DA SEÇÃO D

Comandos de `README.md:868-962`, executados nesta máquina (Python 3.12.3, Node v24.12.0, npm 11.6.2).
`claude "/refactor-arch"` **não** foi reinvocado — alteraria o working tree e exige sessão autenticada.
Os blocos de boot e os curls de validação foram.

Pré-passo comum, como escrito: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (P1, P3) e `npm install` (P2). Os três instalaram. Flask 3.1.1 / Express 4.22.1 / Flask 3.0.0 conferidos.

### 4.1 Projeto 1 — `code-smells-project`

**Como escrito, sem preencher `LOJA_SECRET_KEY`:** os três comandos seguintes a `cp .env.example .env` falham. O comentário do bloco avisa. Confirmado:

```
config.settings.ConfigError: Variável de ambiente obrigatória ausente: LOJA_SECRET_KEY. Copie .env.example para .env e preencha os valores.
```

(`scripts.migrate`, `scripts.seed_dev`, `python app.py` — exit 1 nos três.)

**Depois de preencher a chave** (passo do comentário, não um comando):

```
$ python -m scripts.migrate
nenhuma migracao pendente
versao do schema: 1

$ python -m scripts.seed_dev
banco ja populado; nada a fazer

$ python app.py
2026-08-17T19:07:24-0300 INFO     loja servidor_iniciado ambiente=development host=127.0.0.1 port=5000
 * Tip: There are .env files present. Install python-dotenv to use them.
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
127.0.0.1 - - [17/Aug/2026 19:07:25] "GET / HTTP/1.1" 200 -
```

(`loja.db` local já existia; por isso o migrate não reimprimiu `migracoes aplicadas: 0001_initial.sql` do README. Comportamento correto, texto diferente.)

Curls (`README.md:922-928`). Senha do seed **não** está no bloco — está em `scripts/seed_dev.py:27` (`admin123`):

```
$ curl -s localhost:5000/health
{"counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}

$ curl -s localhost:5000/produtos | head -c 200
{"dados":[{"ativo":1,"categoria":"informatica",...}]}

$ curl -s -X POST localhost:5000/login ... '{"email":"admin@loja.com","senha":"admin123"}'
{"dados":{"expira_em":3600,"token":"eyJ…","token_type":"Bearer","usuario":{"id":1,"tipo":"admin"}},"mensagem":"Login OK","sucesso":true}

$ curl -s -o /dev/null -w '%{http_code}\n' localhost:5000/relatorios/vendas
401

$ curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:5000/admin/query
404
```

Sinais da refatoração: `/health` sem `secret_key`/`db_path`/`debug`; rota admin 404. **Funciona após o fill.**

### 4.2 Projeto 2 — `ecommerce-api-legacy`

**Como escrito, sem preencher as obrigatórias:**

```
ConfigError: Variável de ambiente obrigatória ausente: PAYMENT_GATEWAY_KEY. Veja .env.example para a lista completa.
```

**Depois de preencher `PAYMENT_GATEWAY_KEY` e `ADMIN_TOKEN`** (o `.env.example:8` documenta o gerador do token):

```
> desafio-arquitetura-ia-boilerplate@1.0.0 start
> node --env-file-if-exists=.env src/app.js

{"timestamp":"2026-08-17T22:07:39.007Z","level":"warn","event":"ephemeral_database","code":"in-memory-bootstrap"}
{"timestamp":"2026-08-17T22:07:39.011Z","level":"info","event":"migration_applied","code":"0001_initial.sql"}
{"timestamp":"2026-08-17T22:07:39.048Z","level":"info","event":"seed_applied","environment":"development"}
{"timestamp":"2026-08-17T22:07:39.054Z","level":"info","event":"server_started","port":3000,"host":"127.0.0.1","environment":"development"}
```

Curls:

```
$ curl -s -X POST localhost:3000/api/checkout ... courseId:2 card:4111…
{"msg":"Sucesso","enrollment_id":2}

$ curl -s -o /dev/null -w '%{http_code}\n' localhost:3000/api/admin/financial-report
401

$ curl -s localhost:3000/api/admin/financial-report -H "Authorization: Bearer $ADMIN"
{"items":[{"course":"Clean Architecture","revenue":997,…},{"course":"Docker","revenue":497,…}],"total":2,"limit":50,"offset":0}

$ curl -s -o /dev/null -w '%{http_code}\n' -X DELETE localhost:3000/api/users/1
401
```

O bloco usa `$ADMIN_TOKEN` e **não** exporta a variável. Copy-paste do curl autenticado com a shell limpa manda `Bearer ` vazio e leva 401. O valor precisa ser o mesmo gravado no `.env`. Depois desse passo, **funciona**.

### 4.3 Projeto 3 — `task-manager-api`

`SECRET_KEY` vazia é aceita em `APP_ENV=development` (`config/settings.py:61-63`). O bloco roda **sem fill**:

```
$ python -m infra.migrator upgrade
Migrações aplicadas: nenhuma (já atualizado)

$ python seed.py
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks

$ python app.py
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Debugger is active!
 * Debugger PIN: 121-623-934
127.0.0.1 - - [17/Aug/2026 19:07:52] "GET /health HTTP/1.1" 200 -
```

Curls:

```
TOKEN=… (122 chars)

$ curl -s localhost:5000/health
{"status": "ok", "timestamp": "2026-08-17 22:07:52.754124"}

$ curl -s localhost:5000/users -H "Authorization: Bearer $TOKEN" | head -c 200
[{"active": true, "email": "joao@email.com", "id": 5, "name": "João Silva", "role": "admin"}, …]
  → campo "password" ausente (False)

$ curl -s -o /dev/null -w '%{http_code}\n' localhost:5000/users
401

$ curl -s "localhost:5000/tasks?limit=999" | python3 -c '…print(len(json.load(sys.stdin)))'
10

$ curl … -H "Authorization: Bearer fake-jwt-token-1"
401
```

O comentário `# 200 = teto` é falso neste setup. O seed cria 10 tasks; `len` devolve 10. O teto `PAGE_SIZE_MAX=200` só apareceria com ≥200 linhas. **Comando funciona; resultado esperado documentado não.**

### 4.4 Síntese da seção D

| Projeto | Copy-paste do bloco bash | Após o fill documentado em comentário | Curls |
|---|---|---|---|
| 1 | Falha (obrigatória vazia) | Sobe | 5/5 sinais ok |
| 2 | Falha (obrigatória vazia) | Sobe | 4/4 ok; `$ADMIN_TOKEN` exige export manual |
| 3 | Sobe | — | 4/5 sinais ok; `len==200` não |

Os três projetos **sobem e respondem** quando o avaliador faz o que o comentário pede. Não é entrega quebrada. É documentação que não é um script único copy-paste.

---

## 5. HIGIENE

| Checagem | Resultado |
|---|---|
| Working tree em `df646d0` | Limpo (`git status --porcelain` vazio) antes desta auditoria criar `.venv`/`.env` locais (gitignored) |
| `main` atualizada | `main` = `origin/main` = `df646d0` |
| Histórico | Linear, mensagens no padrão `refactor(onda-N)`, `chore(baseline)`, `chore(skill)`, `docs(evidence)`. Legível. |
| `.gitignore` | Ignora `.env`, `node_modules/`, `.venv/`, `*.db`. Override `!.claude/` / `!**/.claude/` com exclusão de `hooks/` e `settings.local.json`. Condiz com `README.md:384`. |
| Skill versionada | `git ls-files` lista as 8 vias (SKILL + 6 refs + command) × 3 projetos |
| Segredos no tree atual | Nenhum `.env` tracked. SMTP de fixture permanece no **histórico** (`git log -S taskmanager@gmail.com`); o README declara ND-3 / AE-07. Não é omissão. |
| Arquivos indevidos tracked | Nenhum `node_modules`, `__pycache__`, `.venv`, `.idea`. `.idea/` existe no disco e está ignorado. |
| `.claude/` na raiz do repo | Só `hooks/*.sh` locais, **não** tracked — o workaround que o `.gitignore` descreve. |
| Extras além do diagrama | `evidence/`, `.planning/`, `docs/`, baselines JSON, READMEs por projeto. Não violam o enunciado. |
| `package.json` ainda se chama `desafio-arquitetura-ia-boilerplate` | Resíduo do boilerplate. Cosmético. |

---

## 6. VEREDITO

**PRONTO PARA ENTREGA.**

Não há bloqueador de enunciado. Skill nos 3, código refatorado commitado nos 3, reports no nome exigido, README A/B/C/D, 12/12 células com evidência que confirma a afirmação, seção D executável após o fill que ela mesma pede.

Itens que um avaliador pode marcar e que **não** derrubam:

1. `README.md:839` diz 25 linhas no inventário; o arquivo tem 23.
2. `README.md:959` promete `200` em `/tasks?limit=999`; a saída é `10`.
3. Recorte da seção A não lista 2 LOW por projeto (os dossiês listam).
4. Referência `antipattern-catalog.md:80` deveria ser `:85`.
5. "33 arquivos" do projeto 2 depende de exclusão não escrita.
6. Seção D não é copy-paste: P1/P2 exigem editar `.env`; o curl do report usa `$ADMIN_TOKEN` sem `export`.
7. `README.md:381` não registra que `audit-project-{1,2,3}.md` passaram a existir em `df646d0`.

Nenhum desses esconde entregável. O `[ausente]` do 15 e a nota das rodadas são declarações honestas.
