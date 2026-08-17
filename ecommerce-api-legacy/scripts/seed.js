'use strict';

const { loadConfig } = require('../src/config');
const { createDatabase } = require('../src/db/connection');
const { seedDevelopment } = require('../src/db/seed');
const { makePasswordService } = require('../src/services/passwordService');
const { makeLogger } = require('../src/lib/logger');

(async () => {
    const config = loadConfig();
    const logger = makeLogger({ level: config.logLevel });
    const db = await createDatabase({ databaseFile: config.databaseFile, verbose: false });
    const passwordService = makePasswordService({ costFactor: config.passwordCostFactor });
    await seedDevelopment(db, { passwordService, nodeEnv: config.nodeEnv, logger });
    await db.close();
})().catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exit(1);
});
