'use strict';

const express = require('express');

// Encaminha a rejeição de um handler assíncrono para a cadeia de erro do Express.
// Sem isto, uma promessa rejeitada em Express 4 escapa do processo.
const asyncHandler = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);

// Tabela de rotas: método + path → middlewares + handler. Sem lógica.
//
// TR-05, negar por padrão: cada rota declara explicitamente seu regime de acesso.
// `PUBLIC` é uma declaração, não uma omissão — rota sem declaração não existe aqui,
// e acrescentar uma sem decidir o regime é um erro visível na revisão desta tabela.
function buildRoutes({ checkoutController, reportController, userController, authenticate, rateLimit }) {
    const router = express.Router();
    const PUBLIC = [];

    // Pública por decisão de produto (ND-1): o próprio checkout cria a conta do aluno.
    // Público não significa ilimitado — daí o limite de taxa.
    router.post('/api/checkout', ...PUBLIC, rateLimit, asyncHandler(checkoutController.create));

    // Privilegiada: expõe faturamento e dados de terceiros.
    router.get('/api/admin/financial-report', authenticate, asyncHandler(reportController.financial));

    // Destrutiva.
    router.delete('/api/users/:id', authenticate, asyncHandler(userController.remove));

    return router;
}

module.exports = { buildRoutes, asyncHandler };
