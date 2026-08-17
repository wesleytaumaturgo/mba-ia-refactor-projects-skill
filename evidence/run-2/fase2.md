# run-2 · Fase 2 — Auditoria · `ecommerce-api-legacy`

Auditoria somente leitura. **Nenhum arquivo do projeto foi modificado.**
Relatório completo gravado pela skill em:

```
/home/wesley/Github/MBA/Desafio/mba-ia-refactor-projects-skill/reports/audit-ecommerce-api-legacy.md
```

Este arquivo é o registro de **execução** da fase: como a varredura foi feita, o que ela produziu
e onde parou. Os findings em si, com evidência literal, estão no relatório acima.

---

## Varredura dos 28 APs

Ordem do catálogo, entrada a entrada, sem pular. Resultado por AP:

| AP | Sinal | Resultado | Finding |
|---|---|---|---|
| AP-01 Injection | Query montada por concatenação de entrada externa? | **não encontrado** | — |
| AP-02 Hardcoded secret | Literal sensível no bootstrap sem leitura de ambiente? | CRITICAL | F-001 |
| AP-03 PII na serialização | Mapeamento registro→DTO projeta credencial/PII? | **não encontrado** | — |
| AP-04 Derivação de senha | Hash caseiro sem salt e sem custo? | CRITICAL | F-003 |
| AP-05 Rota privilegiada sem auth | Rota destrutiva/admin sem verificação? | CRITICAL | F-002 |
| AP-06 God class | Conexão + schema + rota + regra no mesmo corpo? | CRITICAL | F-004 |
| AP-07 Segredo/PII em log | Log interpola PAN ou segredo? | CRITICAL | F-005 |
| AP-08 Regra fora do service | Decisão de domínio dentro do handler? | HIGH | F-008 |
| AP-09 Acoplamento concreto | Infra instanciada no construtor, sem injeção? | HIGH | F-009 |
| AP-10 Estado global mutável | Variável de módulo escrita pelo caminho de requisição? | HIGH | F-011 |
| AP-11 Escrita sem transação | Escritas relacionadas sem fronteira e sem compensação? | HIGH | F-010 |
| AP-12 Validação inline | Invariante de domínio como condicional no handler? | **não encontrado** | — |
| AP-13 Rota → driver | Handler manipula o driver diretamente? | HIGH | F-006 |
| AP-14 Mass assignment | Payload repassado inteiro ao update/construtor? | **não encontrado** | — |
| AP-15 N+1 aninhado | Consulta dentro de laço sobre resultado anterior? | MEDIUM | F-014 |
| AP-16 Deprecated API | Chamada deprecated **na versão real do runtime**? | **não encontrado** | — |
| AP-17 Duplicação com abstração morta | 3+ cópias **e** a abstração correta morta no repo? | **não encontrado** | — |
| AP-18 Captura genérica | Erro descartado sem registro, detalhe vazado? | MEDIUM | F-012 |
| AP-19 Console como log | stdout como registro, sem nível nem timestamp? | LOW | F-019 |
| AP-20 CORS permissivo | Middleware de origem cruzada permissivo? | **não encontrado** | — |
| AP-21 DDL/seed no boot | Schema criado como efeito colateral do boot? | HIGH | F-007 |
| AP-22 Sem paginação | Listagem devolve o conjunto completo? | MEDIUM | F-015 |
| AP-23 Contrato inconsistente | Envelopes divergentes entre handlers equivalentes? | MEDIUM | F-013 |
| AP-24 Rate limiting | Endpoint de autenticação sem limite? | **não aplicável** | — |
| AP-25 Magic literals | Vocabulário fechado reconstruído inline? | LOW | F-017 |
| AP-26 Código morto | Símbolo exportado/importado sem consumidor? | LOW | F-018 |
| AP-27 Nomenclatura pobre | Identificadores de 1–3 letras em handler extenso? | LOW | F-016 |
| AP-28 Infra de qualidade | Sem dev deps, teste, lint, CI, `engines`? | LOW | F-020 |

**Cobertura: 28/28.** 20 viraram finding, 7 saíram como *não encontrado*, 1 como *não aplicável*.
Nenhum ficou *não verificável* — em particular AP-16, que era o candidato natural a esse estado,
foi resolvido executando o runtime.

---

## Verificações executadas (não apenas leitura)

O catálogo exige procedimento executado para três entradas. Todos foram feitos:

### AP-16 — contra o runtime real, não o manifesto

```console
$ node --pending-deprecation --trace-deprecation src/app.js
  (+ os 3 endpoints exercitados)
--- saida literal ---
Frankenstein LMS rodando na porta 3000...
Processando cartão 4111 na chave pk_live_1234567890abcdef
[LOG] Salvando no cache: last_checkout_2
--- grep -i deprecat ---
(nenhuma linha com 'deprecat')
```

```console
$ grep -nE "new Buffer\(|util\.(isArray|_extend|isNullOrUndefined|print)|url\.parse\(|crypto\.createCipher\(|require\('domain'\)|process\.binding|GLOBAL|require\.extensions" src/*.js
(nenhuma ocorrencia)
```

Verificado contra **Node.js v24.12.0** — a versão obtida executando o runtime na Fase 1.
"Não encontrado" com a versão citada; sem ela não provaria nada.

### AP-04 — verificação decisiva de colisão

```console
$ node -e "const { badCrypto } = require('./src/utils'); ..."
"senhaforte"   -> c2c2c2c2c2
"senha123"     -> c2c2c2c2c2
"sorvete"      -> c2c2c2c2c2
"s"            -> cwcwcwcwcw
"12345678"     -> MTMTMTMTMT
"admin"        -> YWYWYWYWYW
--- colisoes ---
c2c2c2c2c2 <- senhaforte, senha123, sorvete
```

Colisão demonstrada, não presumida.

### AP-02 — ausência de leitura de ambiente

```console
$ grep -rn "process\.env\|dotenv" src/ package.json
(nenhuma leitura de ambiente em todo o projeto)
```

É essa ausência que fecha o limite superior do AP: nenhum literal pode ser "default de
desenvolvimento com precedência do ambiente" se ambiente algum é lido.

### Evidências que sustentam os *não encontrados*

```console
$ grep -nE 'db\.(run|get|all)\(`|\+ *(req|u|e|p|cid|cc|id)\b' src/*.js
(nenhuma: 100% das queries usam ? com array de valores)                    # AP-01

$ grep -nE 'Object\.assign|\.\.\.req\.body|\[req\.body\]' src/*.js
(nenhum: campos lidos individualmente)                                     # AP-14

$ grep -rn "cors\|Access-Control" src/ package.json
(nenhum middleware de origem cruzada registrado)                           # AP-20

$ grep -rniE "login|signin|auth|token|session|jwt|passport" src/ package.json
(nenhuma rota nem dependencia de autenticacao)                             # AP-24

$ grep -nE "FOREIGN KEY|REFERENCES|UNIQUE|NOT NULL|CHECK" src/AppManager.js
(zero constraints em todas as 5 tabelas)                                   # sinal estrutural de AP-21
```

### AP-28 — verificação um nível acima (regra do monorepo)

```console
$ ls -a . | grep -iE "test|spec|lint|eslint|prettier|\.env|jest|mocha|vitest|\.github|Makefile|Dockerfile|tsconfig|editorconfig|package.json"
(nenhum artefato de qualidade na raiz do repositorio)
```

A isenção "a infraestrutura existe fora do diretório analisado" foi checada e **não** se aplica.

---

## Decisões de classificação que evitaram inflar a contagem

Registradas aqui porque são o que separa uma auditoria falsificável de um preenchimento de cota:

1. **AP-03 descartado, e o defeito realocado.** A exposição de nome de aluno e valor pago a um
   chamador anônimo é real — mas a causa é a ausência de controle de acesso (AP-05 / F-002), não a
   projeção. A projeção em `src/AppManager.js:112-115` é campo a campo e **exclui** `pass` e
   `email`. Reportar os dois seria contar o mesmo defeito duas vezes.
2. **AP-17 descartado apesar de 5 cópias.** O AP exige **duas** condições; a segunda falha — não
   existe no repositório a abstração correta que ninguém invoca. As 5 cópias do retorno de erro
   pertencem a F-012 e F-013.
3. **AP-12 descartado.** A única verificação pré-lógica (`src/AppManager.js:35`) é de protocolo —
   campo obrigatório ausente —, caso que o próprio AP exclui.
4. **O literal `"4"` de `src/AppManager.js:46` não abriu finding LOW próprio.** Ele vive dentro do
   bloco que já é F-008. O mesmo condicional não é dois findings.
5. **O nome `AppManager` não abriu finding de AP-27.** É o *sinal de nome* de AP-06, citado em
   F-004.

---

## Resultado

| Severidade | Findings | Ocorrências |
|---|---|---|
| CRITICAL | 5 | 12 |
| HIGH | 6 | 35 |
| MEDIUM | 4 | 24 |
| LOW | 5 | 26 |
| **Total** | **20** | **97** |

Breaking changes previstas: **8** (BC-1 a BC-8), todas enumeradas por endpoint.
Plano: **4 ondas, todas com TR atribuído — nenhuma onda vazia.**
TRs não agendados por falta de finding que os acione: TR-02, TR-04, TR-08, TR-12.
Itens NEEDS-DECISION: **6** (ND-1 a ND-6), cada um com recomendação e alternativa.

---

## Estado do repositório ao fim da Fase 2

```console
$ git status --porcelain
?? reports/audit-ecommerce-api-legacy.md
?? reports/baseline-ecommerce-api-legacy.json

$ git status --porcelain ecommerce-api-legacy/
[fim - vazio significa projeto intocado]
```

Exatamente as duas escritas que a skill autoriza antes do gate: relatório e baseline. Nenhum
arquivo de código, manifesto, configuração ou diretório do projeto foi criado, movido ou alterado.

---

## Gate

Prompt emitido, execução **parada**, aguardando resposta explícita do humano:

```console
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**Não respondido por este operador.** A Fase 3 não foi iniciada.
