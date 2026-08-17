'use strict';

const { CourseNotFoundError, PaymentDeclinedError } = require('../errors');
const { globalCache } = require('../utils');

const DEFAULT_PASSWORD = '123456';

// Único lugar que decide O QUE acontece no checkout. Não importa nenhum símbolo
// de protocolo: nada aqui sabe que existe HTTP.
const makeCheckoutService = ({
    courseRepository,
    userRepository,
    enrollmentRepository,
    paymentRepository,
    auditLogRepository,
    paymentGateway,
    passwordService,
    logger,
}) => ({
    async execute({ name, email, password, courseId, card }) {
        const course = await courseRepository.findActiveById(courseId);
        if (!course) throw new CourseNotFoundError();

        const existing = await userRepository.findByEmail(email);
        const userId = existing
            ? existing.id
            : await userRepository.insert({
                  name,
                  email,
                  passwordHash: await passwordService.hash(password || DEFAULT_PASSWORD),
              });

        const { status, approved } = await paymentGateway.authorize({ card, amount: course.price });
        if (!approved) throw new PaymentDeclinedError();

        const enrollmentId = await enrollmentRepository.insert({ userId, courseId });
        await paymentRepository.insert({ enrollmentId, amount: course.price, status });
        await auditLogRepository.insert(`Checkout curso ${courseId} por ${userId}`);

        // TR-14: o registro de evento passa pelo logger com nível e timestamp;
        // a escrita no cache global permanece (F-011 é finding da Onda 2, TR-09).
        globalCache[`last_checkout_${userId}`] = course.title;
        logger.info('checkout_completed', { userId, courseId, enrollmentId, amount: course.price, status });

        return { enrollmentId };
    },
});

module.exports = { makeCheckoutService };
