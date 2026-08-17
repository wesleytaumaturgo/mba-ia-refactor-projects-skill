'use strict';

const { timingSafeEqual } = require('node:crypto');
const { UnauthorizedError } = require('../errors');

function safeEquals(a, b) {
    const bufA = Buffer.from(String(a));
    const bufB = Buffer.from(String(b));
    // timingSafeEqual exige mesmo comprimento; comparar tamanho antes não vaza o segredo.
    return bufA.length === bufB.length && timingSafeEqual(bufA, bufB);
}

function extractToken(req) {
    const header = req.get('authorization');
    if (!header) return null;
    const [scheme, value] = header.split(' ');
    return scheme && scheme.toLowerCase() === 'bearer' && value ? value : null;
}

// ND-2: token administrativo vindo do ambiente (TR-01), comparado em tempo constante.
// TR-13: a resposta deixa de ser montada aqui e passa pelo tratador central.
const makeAuthenticate = ({ adminToken }) => (req, res, next) => {
    const token = extractToken(req);
    if (!token || !safeEquals(token, adminToken)) {
        return next(new UnauthorizedError());
    }
    req.principal = { role: 'admin' };
    next();
};

module.exports = { makeAuthenticate };
