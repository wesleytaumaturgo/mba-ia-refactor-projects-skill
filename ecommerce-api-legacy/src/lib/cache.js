'use strict';

// Substitui o `globalCache` de escopo de módulo por uma instância com ciclo de
// vida explícito, criada no composition root e injetada em quem a usa.
// Ganha o que faltava ao original: política de expiração e teto de tamanho —
// sem eles, um processo de vida longa acumulava uma entrada por usuário, para sempre.
const makeCache = ({ ttlMs = 300000, maxEntries = 1000, clock = Date.now } = {}) => {
    const entries = new Map();

    const isExpired = (entry, now) => now - entry.storedAt >= ttlMs;

    const evictIfNeeded = () => {
        while (entries.size > maxEntries) {
            const oldest = entries.keys().next().value;
            entries.delete(oldest);
        }
    };

    return {
        set(key, value) {
            entries.delete(key);            // reinsere no fim: ordem de inserção = ordem de despejo
            entries.set(key, { value, storedAt: clock() });
            evictIfNeeded();
        },

        get(key) {
            const entry = entries.get(key);
            if (!entry) return undefined;
            if (isExpired(entry, clock())) {
                entries.delete(key);
                return undefined;
            }
            return entry.value;
        },

        get size() {
            return entries.size;
        },
    };
};

module.exports = { makeCache };
