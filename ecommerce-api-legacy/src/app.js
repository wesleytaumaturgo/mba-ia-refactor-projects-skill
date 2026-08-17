'use strict';

const express = require('express');

const { loadConfig } = require('./config');
const { createDatabase } = require('./db/connection');
const { migrate, assertSchemaUpToDate } = require('./db/migrate');
const { seedDevelopment } = require('./db/seed');

const { makeCourseRepository } = require('./repositories/courseRepository');
const { makeUserRepository } = require('./repositories/userRepository');
const { makeEnrollmentRepository } = require('./repositories/enrollmentRepository');
const { makePaymentRepository } = require('./repositories/paymentRepository');
const { makeAuditLogRepository } = require('./repositories/auditLogRepository');

const { makePasswordService } = require('./services/passwordService');
const { makePaymentGateway } = require('./services/paymentGateway');
const { makeCheckoutService } = require('./services/checkoutService');
const { makeReportService } = require('./services/reportService');
const { makeUserService } = require('./services/userService');

const { makeCheckoutController } = require('./controllers/checkoutController');
const { makeReportController } = require('./controllers/reportController');
const { makeUserController } = require('./controllers/userController');

const { buildRoutes } = require('./routes');
const { makeLogger } = require('./lib/logger');
const { makeCache } = require('./lib/cache');
const { makeAuthenticate } = require('./middlewares/auth');
const { makeRateLimiter } = require('./middlewares/rateLimit');

// Composition root: ÚNICO ponto autorizado a instanciar infraestrutura.
// Ordem: config → infraestrutura → repositórios → services → controllers → rotas.
async function main() {
    const config = loadConfig();
    const logger = makeLogger({ level: config.logLevel });

    const db = await createDatabase({
        databaseFile: config.databaseFile,
        verbose: config.isDevelopment,
    });

    const courseRepository = makeCourseRepository(db);
    const userRepository = makeUserRepository(db);
    const enrollmentRepository = makeEnrollmentRepository(db);
    const paymentRepository = makePaymentRepository(db);
    const auditLogRepository = makeAuditLogRepository(db);

    const cache = makeCache({ ttlMs: 300000, maxEntries: 1000 });
    const passwordService = makePasswordService({ costFactor: config.passwordCostFactor });

    // TR-16: o boot NÃO executa DDL — apenas verifica a versão de schema aplicada.
    // Exceção declarada: um banco ':memory:' deixa de existir quando o processo
    // morre, então não há como pré-migrá-lo por script. Nesse caso, e só em
    // desenvolvimento, o boot aplica migração e seed e diz que fez isso.
    if (config.databaseFile === ':memory:' && config.isDevelopment) {
        logger.warn('ephemeral_database', { code: 'in-memory-bootstrap' });
        await migrate(db, { logger });
        await seedDevelopment(db, { passwordService, nodeEnv: config.nodeEnv, logger });
    } else {
        await assertSchemaUpToDate(db);
    }
    const paymentGateway = makePaymentGateway({ apiKey: config.paymentGatewayKey, logger });

    const checkoutService = makeCheckoutService({
        courseRepository,
        userRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        paymentGateway,
        passwordService,
        unitOfWork: { run: db.transaction },
        cache,
        logger,
    });
    const reportService = makeReportService({
        courseRepository,
        enrollmentRepository,
        userRepository,
        paymentRepository,
    });
    const userService = makeUserService({
        userRepository,
        enrollmentRepository,
        unitOfWork: { run: db.transaction },
        logger,
    });

    const checkoutController = makeCheckoutController({ checkoutService });
    const reportController = makeReportController({ reportService });
    const userController = makeUserController({ userService });

    const authenticate = makeAuthenticate({ adminToken: config.adminToken });
    const rateLimit = makeRateLimiter({ max: config.rateLimitMax, windowMs: config.rateLimitWindowMs });

    const app = express();
    app.use(express.json());
    app.use(buildRoutes({ checkoutController, reportController, userController, authenticate, rateLimit }));

    app.listen(config.port, config.host, () => {
        logger.info('server_started', { port: config.port, host: config.host, environment: config.nodeEnv });
    });
}

main().catch((error) => {
    // Fronteira do processo: falha de bootstrap não tem logger garantido.
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exit(1);
});
