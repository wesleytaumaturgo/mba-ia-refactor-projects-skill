'use strict';

const sqlite3base = require('sqlite3');

// Único ponto do projeto que conhece o driver. Devolve uma API baseada em Promise,
// o que elimina o `self = this` e os três referentes de `this` do código original:
// `lastID` e `changes` são lidos aqui dentro e devolvidos como dado.
function createDatabase({ databaseFile, verbose = false }) {
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

    return { run, get, all, exec, close };
}

module.exports = { createDatabase };
