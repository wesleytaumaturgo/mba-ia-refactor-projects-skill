'use strict';

const { CourseNotFoundError, PaymentDeclinedError } = require('../errors');

// Política de conta criada implicitamente pelo checkout. Preserva o comportamento
// original (F-003 registrou o literal); torná-la explícita aqui é o que permite
// discuti-la como decisão de produto em vez de encontrá-la num callback.
const IMPLICIT_ACCOUNT_DEFAULT_PASSWORD = '123456';

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
    unitOfWork,
    cache,
    logger,
}) => ({
    async execute({ name, email, password, courseId, card }) {
        const course = await courseRepository.findActiveById(courseId);
        if (!course) throw new CourseNotFoundError();

        const existing = await userRepository.findByEmail(email);

        // A autorização acontece FORA da transação, de propósito: manter uma
        // transação aberta durante uma chamada externa segura lock por tempo
        // indeterminado. Nada foi escrito ainda, então recusar aqui não deixa estado.
        const { status, approved } = await paymentGateway.authorize({ card, amount: course.price });
        if (!approved) throw new PaymentDeclinedError();

        // TR-10: as escritas relacionadas passam a ter fronteira transacional.
        // Antes, uma falha no INSERT de pagamento deixava o aluno matriculado
        // sem pagamento registrado, e o cliente recebia 500 como se nada tivesse
        // acontecido. Agora ou as quatro escritas acontecem, ou nenhuma acontece.
        const enrollmentId = await unitOfWork.run(async () => {
            const userId = existing
                ? existing.id
                : await userRepository.insert({
                      name,
                      email,
                      passwordHash: await passwordService.hash(password || IMPLICIT_ACCOUNT_DEFAULT_PASSWORD),
                  });

            const id = await enrollmentRepository.insert({ userId, courseId });
            await paymentRepository.insert({ enrollmentId: id, amount: course.price, status });
            await auditLogRepository.insert(`Checkout curso ${courseId} por ${userId}`);

            cache.set(`last_checkout_${userId}`, course.title);
            logger.info('checkout_completed', { userId, courseId, enrollmentId: id, amount: course.price, status });
            return id;
        });

        return { enrollmentId };
    },
});

module.exports = { makeCheckoutService };
