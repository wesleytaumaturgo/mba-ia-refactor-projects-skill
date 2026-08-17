# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para MVC pela skill
`refactor-arch`.

## Como rodar

```bash
npm install
cp .env.example .env      # preencha PAYMENT_GATEWAY_KEY e ADMIN_TOKEN (obrigatórias)
npm start
```

A aplicação sobe em `http://127.0.0.1:3000` (mude com `HOST`/`PORT` no `.env`). Por padrão
`DATABASE_FILE=:memory:` — volátil, e por isso o boot aplica migração e seed automaticamente
quando roda nessa configuração em desenvolvimento (loga `ephemeral_database` ao fazer isso).

Trocando por um arquivo real, o boot deixa de migrar sozinho e passa apenas a **verificar** a
versão de schema aplicada, falhando com mensagem clara se houver migração pendente:

```bash
# .env: DATABASE_FILE=./data/app.db
npm run migrate           # aplica o schema — a DDL não roda mais no boot com arquivo real
npm run seed               # dados de demonstração
npm start
```

Exemplos de requisições estão em `api.http`.

### Autenticação

As rotas administrativas exigem o token do operador, enviado como `Authorization: Bearer
<token>` e comparado em tempo constante contra `ADMIN_TOKEN`:

```bash
curl localhost:3000/api/admin/financial-report -H "Authorization: Bearer $ADMIN_TOKEN"
```

Pública: `POST /api/checkout` (com limite de taxa). Toda rota nova nasce **protegida** — a
exceção é declarada explicitamente em `src/routes/index.js`.

## Estrutura

| Diretório | Responsabilidade única |
|---|---|
| `src/config/` | Ler o ambiente, validar o obrigatório, expor valores tipados. Falha no boot se faltar. |
| `src/models/` | Forma dos dados e invariantes que valem sempre. |
| `src/repositories/` | Traduzir entre entidade e persistência. Único lugar que conhece o driver do banco. |
| `src/services/` | Regra de negócio e orquestração — checkout, pagamento, relatório, usuário. |
| `src/controllers/` | Traduzir entre protocolo HTTP e domínio. |
| `src/routes/` | Declarar `método + path → middlewares + handler`. Sem lógica. |
| `src/middlewares/` | Autenticação, tratamento de erro, correlação, limite de taxa. |
| `src/errors/` | Vocabulário de erro de domínio, mapeado a status HTTP no tratador central. |
| `src/lib/` | Logger e cache com chamador real. |
| `src/db/` | Conexão, migração versionada (`src/db/migrations/`) e seed. |

`src/app.js` é o composition root: o único ponto autorizado a instanciar infraestrutura.

## Erros

Envelope único em todos os caminhos de erro:

```json
{"error": {"code": "INVALID_REQUEST", "message": "...", "correlationId": "e166135d2c89"}}
```

Cite o `correlationId` ao reportar um problema — ele acompanha a resposta no cabeçalho
`X-Correlation-Id` e aparece no log do servidor.
