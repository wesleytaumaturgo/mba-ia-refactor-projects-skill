'use strict';

class ConfigError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ConfigError';
    }
}

function required(key) {
    const value = process.env[key];
    if (value === undefined || value === '') {
        throw new ConfigError(
            `Variável de ambiente obrigatória ausente: ${key}. ` +
            `Veja .env.example para a lista completa.`
        );
    }
    return value;
}

function optional(key, fallback) {
    const value = process.env[key];
    return value === undefined || value === '' ? fallback : value;
}

function toInt(key, value) {
    const parsed = Number(value);
    if (!Number.isInteger(parsed)) {
        throw new ConfigError(`Variável de ambiente ${key} precisa ser um inteiro, recebido: ${value}`);
    }
    return parsed;
}

// Falha no boot quando falta chave obrigatória. É o comportamento desejado de TR-01:
// variável esquecida vira aplicação que não sobe, não aplicação que sobe insegura.
function loadConfig(env = process.env) {
    const nodeEnv = optional('NODE_ENV', 'development');

    return Object.freeze({
        nodeEnv,
        isDevelopment: nodeEnv === 'development',
        port: toInt('PORT', optional('PORT', '3000')),
        host: optional('HOST', '127.0.0.1'),
        logLevel: optional('LOG_LEVEL', 'info'),
        databaseFile: optional('DATABASE_FILE', ':memory:'),
        paymentGatewayKey: required('PAYMENT_GATEWAY_KEY'),
        adminToken: required('ADMIN_TOKEN'),
        passwordCostFactor: toInt('PASSWORD_COST_FACTOR', optional('PASSWORD_COST_FACTOR', '16384')),
        rateLimitMax: toInt('RATE_LIMIT_MAX', optional('RATE_LIMIT_MAX', '30')),
        rateLimitWindowMs: toInt('RATE_LIMIT_WINDOW_MS', optional('RATE_LIMIT_WINDOW_MS', '60000')),
    });
}

module.exports = { loadConfig, ConfigError };
