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
// A resposta é montada aqui porque a Onda 1 ainda não tem tratador central;
// TR-13 (Onda 3) troca isto por `next(new UnauthorizedError())`.
const makeAuthenticate = ({ adminToken }) => (req, res, next) => {
    const token = extractToken(req);
    if (!token || !safeEquals(token, adminToken)) {
        return res.status(401).send(new UnauthorizedError().message);
    }
    req.principal = { role: 'admin' };
    next();
};

module.exports = { makeAuthenticate };
