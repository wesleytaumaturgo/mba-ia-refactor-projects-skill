// TR-09 removeu o estado global mutável de módulo:
//   - `globalCache` virou instância injetada em src/lib/cache.js
//   - `totalRevenue` era primitivo exportado por valor em CommonJS: reatribuições
//     nunca chegariam aos consumidores. Acumulador estruturalmente inoperante, removido.
// O que restou aqui é código legado sem consumidor, removido por TR-15 na Onda 4.

function logAndCache(key, data) {
    console.log(`[LOG] Salvando no cache: ${key}`);
}

function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}

module.exports = { logAndCache, badCrypto };
