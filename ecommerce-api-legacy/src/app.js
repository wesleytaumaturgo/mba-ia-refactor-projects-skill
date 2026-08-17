'use strict';

const express = require('express');

const { loadConfig } = require('./config');
const { createDatabase } = require('./db/connection');
const { bootstrapSchema } = require('./db/bootstrapSchema');

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
const { makeAuthenticate } = require('./middlewares/auth');
const { makeRateLimiter } = require('./middlewares/rateLimit');

// Composition root: ÚNICO ponto autorizado a instanciar infraestrutura.
// Ordem: config → infraestrutura → repositórios → services → controllers → rotas.
async function main() {
    const config = loadConfig();
    const logger = makeLogger({ level: config.logLevel });

    const db = createDatabase({
        databaseFile: config.databaseFile,
        verbose: config.isDevelopment,
    });
    await bootstrapSchema(db);

    const courseRepository = makeCourseRepository(db);
    const userRepository = makeUserRepository(db);
    const enrollmentRepository = makeEnrollmentRepository(db);
    const paymentRepository = makePaymentRepository(db);
    const auditLogRepository = makeAuditLogRepository(db);

    const passwordService = makePasswordService({ costFactor: config.passwordCostFactor });
    const paymentGateway = makePaymentGateway({ apiKey: config.paymentGatewayKey, logger });

    const checkoutService = makeCheckoutService({
        courseRepository,
        userRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        paymentGateway,
        passwordService,
        logger,
    });
    const reportService = makeReportService({
        courseRepository,
        enrollmentRepository,
        userRepository,
        paymentRepository,
    });
    const userService = makeUserService({ userRepository });

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
