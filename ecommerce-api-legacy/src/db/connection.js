'use strict';

const sqlite3base = require('sqlite3');

// Único ponto do projeto que conhece o driver. Devolve uma API baseada em Promise,
// o que elimina o `self = this` e os três referentes de `this` do código original:
// `lastID` e `changes` são lidos aqui dentro e devolvidos como dado.
async function createDatabase({ databaseFile, verbose = false }) {
    const sqlite3 = verbose ? sqlite3base.verbose() : sqlite3base;
    const driver = new sqlite3.Database(databaseFile);

    const run = (sql, params = []) =>
        new Promise((resolve, reject) => {
            driver.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });

    const get = (sql, params = []) =>
        new Promise((resolve, reject) => {
            driver.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });

    const all = (sql, params = []) =>
        new Promise((resolve, reject) => {
            driver.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });

    const exec = (sql) =>
        new Promise((resolve, reject) => {
            driver.exec(sql, (err) => (err ? reject(err) : resolve()));
        });

    const close = () =>
        new Promise((resolve, reject) => {
            driver.close((err) => (err ? reject(err) : resolve()));
        });

    // Unidade de trabalho. A conexão é única, então os repositórios já operam
    // sobre ela — não é preciso passar um handle de transação adiante.
    // Rollback em TODO caminho de erro, inclusive nos retornos antecipados: é a
    // saída do bloco que decide, não o autor do service lembrar de compensar.
    const transaction = async (work) => {
        await exec('BEGIN IMMEDIATE');
        try {
            const result = await work();
            await exec('COMMIT');
            return result;
        } catch (error) {
            await exec('ROLLBACK');
            throw error;
        }
    };

    // SQLite ignora FOREIGN KEY por padrão: sem este PRAGMA, as constraints
    // declaradas na migração 0001 não valeriam nada. É por CONEXÃO, não por schema.
    await exec('PRAGMA foreign_keys = ON');

    return { run, get, all, exec, transaction, close };
}

module.exports = { createDatabase };
