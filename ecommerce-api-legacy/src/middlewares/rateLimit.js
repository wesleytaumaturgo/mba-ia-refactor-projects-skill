'use strict';

const { RateLimitExceededError } = require('../errors');

// AP-24 por composição: a rota de checkout permanece pública (ND-1), então o
// limite de taxa é o que impede que "público" signifique "ilimitado".
// Janela deslizante simples, por origem, com ciclo de vida explícito — não é
// estado global de módulo: a instância nasce no composition root.
const makeRateLimiter = ({ max, windowMs }) => {
    const hits = new Map();

    const prune = (now) => {
        for (const [key, timestamps] of hits) {
            const alive = timestamps.filter((t) => now - t < windowMs);
            if (alive.length === 0) hits.delete(key);
            else hits.set(key, alive);
        }
    };

    return (req, res, next) => {
        const now = Date.now();
        prune(now);

        const key = req.ip || 'unknown';
        const timestamps = (hits.get(key) || []).filter((t) => now - t < windowMs);

        if (timestamps.length >= max) return next(new RateLimitExceededError());

        timestamps.push(now);
        hits.set(key, timestamps);
        next();
    };
};

module.exports = { makeRateLimiter };
