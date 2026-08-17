'use strict';

const fs = require('node:fs/promises');
const path = require('node:path');

const MIGRATIONS_DIR = path.join(__dirname, 'migrations');

// A stack não oferece ferramenta de migração própria (sqlite3 é só o driver),
// então este é o mínimo que versiona schema: um diretório de arquivos ordenados
// e uma tabela que registra o que já foi aplicado.
async function ensureMigrationsTable(db) {
    await db.exec(`
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    TEXT PRIMARY KEY,
            applied_at DATETIME NOT NULL
        );
    `);
}

async function listMigrations() {
    const files = await fs.readdir(MIGRATIONS_DIR);
    return files.filter((f) => f.endsWith('.sql')).sort();
}

async function appliedVersions(db) {
    const rows = await db.all('SELECT version FROM schema_migrations');
    return new Set(rows.map((r) => r.version));
}

async function migrate(db, { logger } = {}) {
    await ensureMigrationsTable(db);
    const applied = await appliedVersions(db);
    const pending = (await listMigrations()).filter((f) => !applied.has(f));

    for (const file of pending) {
        const sql = await fs.readFile(path.join(MIGRATIONS_DIR, file), 'utf8');
        await db.exec(sql);
        await db.run('INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime(\'now\'))', [file]);
        if (logger) logger.info('migration_applied', { code: file });
    }

    return { applied: pending.length };
}

// O boot só VERIFICA a versão aplicada; não executa DDL.
async function assertSchemaUpToDate(db) {
    await ensureMigrationsTable(db);
    const applied = await appliedVersions(db);
    const pending = (await listMigrations()).filter((f) => !applied.has(f));
    if (pending.length > 0) {
        throw new Error(
            `Schema desatualizado: ${pending.length} migração(ões) pendente(s): ${pending.join(', ')}. ` +
            `Rode "npm run migrate" antes de subir a aplicação.`
        );
    }
}

module.exports = { migrate, assertSchemaUpToDate, listMigrations };
