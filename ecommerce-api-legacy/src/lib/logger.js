'use strict';

const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

// Redação por ALLOWLIST de campos emitíveis. Uma denylist de nomes sensíveis
// falha no primeiro campo novo; esta falha fechada — o que não está listado
// nunca chega ao destino.
const EMITTABLE = new Set([
    'event',
    'level',
    'timestamp',
    'amount',
    'status',
    'courseId',
    'userId',
    'enrollmentId',
    'cardLast4',
    'durationMs',
    'code',
    'correlationId',
    'method',
    'path',
    'statusCode',
    'rowsAffected',
    'port',
    'host',
    'environment',
]);

function redact(fields) {
    const safe = {};
    for (const [key, value] of Object.entries(fields || {})) {
        if (EMITTABLE.has(key)) safe[key] = value;
        else safe[key] = '[redacted]';
    }
    return safe;
}

const makeLogger = ({ level = 'info', destination = process.stdout } = {}) => {
    const threshold = LEVELS[level] ?? LEVELS.info;

    const emit = (levelName, event, fields) => {
        if (LEVELS[levelName] < threshold) return;
        const record = {
            timestamp: new Date().toISOString(),
            level: levelName,
            event,
            ...redact(fields),
        };
        destination.write(`${JSON.stringify(record)}\n`);
    };

    return {
        debug: (event, fields) => emit('debug', event, fields),
        info: (event, fields) => emit('info', event, fields),
        warn: (event, fields) => emit('warn', event, fields),
        error: (event, fields) => emit('error', event, fields),
    };
};

module.exports = { makeLogger, EMITTABLE };
