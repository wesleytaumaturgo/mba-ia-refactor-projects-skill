'use strict';

const { randomUUID } = require('node:crypto');

const {
    DomainError,
    CourseNotFoundError,
    PaymentDeclinedError,
    InvalidRequestError,
    UserHasEnrollmentsError,
    UserNotFoundError,
    UnauthorizedError,
    RateLimitExceededError,
} = require('../errors');

// Mapa erro-de-domínio → status HTTP. Um lugar só, e legível de cima a baixo.
// Separa o que o código original colapsava: recurso inexistente é 404, entrada
// recusada é 4xx, e defeito é 5xx — nunca mais um erro de driver virando 404.
const STATUS_BY_ERROR = new Map([
    [InvalidRequestError, 400],
    [PaymentDeclinedError, 400],
    [UnauthorizedError, 401],
    [CourseNotFoundError, 404],
    [UserNotFoundError, 404],
    [UserHasEnrollmentsError, 409],
    [RateLimitExceededError, 429],
]);

const correlationId = () => (req, res, next) => {
    req.correlationId = req.get('x-correlation-id') || randomUUID();
    res.set('X-Correlation-Id', req.correlationId);
    next();
};

// Envelope único, um idioma só, código de erro estável. O texto da exceção e o
// caminho de arquivo NUNCA atravessam a fronteira: o cliente recebe o código de
// correlação, e o log recebe o erro completo com o mesmo código.
const makeErrorHandler = ({ logger }) => (error, req, res, next) => {
    if (res.headersSent) return next(error);

    const isDomain = error instanceof DomainError;
    const status = isDomain ? (STATUS_BY_ERROR.get(error.constructor) ?? 400) : 500;

    if (status >= 500) {
        logger.error('unhandled_error', {
            code: error.code || error.name,
            correlationId: req.correlationId,
            method: req.method,
            path: req.path,
            statusCode: status,
        });
        // Detalhe completo só no destino do log, nunca na resposta.
        process.stderr.write(`${req.correlationId} ${error.stack || error.message}\n`);
    } else {
        logger.warn('domain_error', {
            code: error.code,
            correlationId: req.correlationId,
            method: req.method,
            path: req.path,
            statusCode: status,
        });
    }

    res.status(status).json({
        error: {
            code: isDomain ? error.code : 'INTERNAL_ERROR',
            message: isDomain ? error.message : 'Erro interno',
            correlationId: req.correlationId,
        },
    });
};

// 404 de rota inexistente também passa pelo envelope, em vez do HTML do framework.
const notFoundHandler = () => (req, res) => {
    res.status(404).json({
        error: {
            code: 'ROUTE_NOT_FOUND',
            message: 'Rota não encontrada',
            correlationId: req.correlationId,
        },
    });
};

module.exports = { makeErrorHandler, notFoundHandler, correlationId, STATUS_BY_ERROR };
