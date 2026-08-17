'use strict';

const { scrypt, randomBytes, timingSafeEqual } = require('node:crypto');
const { promisify } = require('node:util');

const scryptAsync = promisify(scrypt);

const FORMAT = 'scrypt';        // marcador de formato no próprio valor armazenado
const SALT_BYTES = 16;
const KEY_BYTES = 64;

// ND-3: scrypt da biblioteca padrão — salt por registro e fator de custo real,
// sem adicionar dependência ao manifesto. Substitui a função caseira `badCrypto`,
// cuja saída era determinada pelos 2 primeiros caracteres do base64 da senha.
const makePasswordService = ({ costFactor }) => {
    const params = { N: costFactor, r: 8, p: 1, maxmem: 128 * costFactor * 8 * 2 };

    const derive = async (plaintext, salt) => {
        const key = await scryptAsync(plaintext, salt, KEY_BYTES, params);
        return key.toString('hex');
    };

    return {
        async hash(plaintext) {
            const salt = randomBytes(SALT_BYTES).toString('hex');
            const derived = await derive(plaintext, salt);
            return `${FORMAT}$${costFactor}$${salt}$${derived}`;
        },

        // Reidratação: credencial em formato legado é reconhecida como não-verificável
        // e sinalizada para regravação no primeiro sucesso de autenticação.
        async verify(stored, plaintext) {
            if (typeof stored !== 'string' || !stored.startsWith(`${FORMAT}$`)) {
                return { valid: false, needsRehash: true, reason: 'legacy-format' };
            }
            const [, storedCost, salt, expected] = stored.split('$');
            const actual = await derive(plaintext, salt);
            const a = Buffer.from(actual, 'hex');
            const b = Buffer.from(expected, 'hex');
            const valid = a.length === b.length && timingSafeEqual(a, b);
            return { valid, needsRehash: valid && Number(storedCost) !== costFactor };
        },
    };
};

module.exports = { makePasswordService, FORMAT };
