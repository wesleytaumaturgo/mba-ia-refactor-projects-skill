'use strict';

const { CourseNotFoundError, PaymentDeclinedError } = require('../errors');

// Casca fina: parse da entrada, chamada ao service, mapeamento do resultado.
// Nenhuma decisão de negócio; o mapeamento é por TIPO de erro de domínio, não
// pela forma do valor devolvido.
const makeCheckoutController = ({ checkoutService }) => ({
    async create(req, res) {
        const { usr, eml, pwd, c_id: courseId, card } = req.body;

        if (!usr || !eml || !courseId || !card) return res.status(400).send('Bad Request');

        try {
            const { enrollmentId } = await checkoutService.execute({
                name: usr,
                email: eml,
                password: pwd,
                courseId,
                card,
            });
            return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        } catch (error) {
            if (error instanceof CourseNotFoundError) return res.status(404).send('Curso não encontrado');
            if (error instanceof PaymentDeclinedError) return res.status(400).send('Pagamento recusado');
            throw error;
        }
    },
});

module.exports = { makeCheckoutController };
