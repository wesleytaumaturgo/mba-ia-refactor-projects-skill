'use strict';

const { loadConfig } = require('../src/config');
const { createDatabase } = require('../src/db/connection');
const { migrate } = require('../src/db/migrate');
const { makeLogger } = require('../src/lib/logger');

(async () => {
    const config = loadConfig();
    const logger = makeLogger({ level: config.logLevel });
    const db = await createDatabase({ databaseFile: config.databaseFile, verbose: false });
    const { applied } = await migrate(db, { logger });
    logger.info('migrate_finished', { rowsAffected: applied });
    await db.close();
})().catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exit(1);
});
