'use strict';

const { InvalidRequestError } = require('../errors');

// Casca fina: parse da entrada, chamada ao service, mapeamento do RESULTADO.
// Nenhuma captura genérica e nenhum mapeamento de erro — TR-13 centralizou isso.
const makeCheckoutController = ({ checkoutService }) => ({
    async create(req, res) {
        const { usr, eml, pwd, c_id: courseId, card } = req.body;

        if (!usr || !eml || !courseId || !card) throw new InvalidRequestError();

        const { enrollmentId } = await checkoutService.execute({
            name: usr,
            email: eml,
            password: pwd,
            courseId,
            card,
        });

        return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    },
});

module.exports = { makeCheckoutController };
