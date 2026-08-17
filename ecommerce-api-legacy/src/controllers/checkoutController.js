'use strict';

const { InvalidRequestError } = require('../errors');

// BC-8 / ND-6: o contrato público passa a aceitar o vocabulário do domínio e
// CONTINUA aceitando os nomes abreviados originais. Renomear sem compatibilidade
// quebraria todo cliente existente; aceitar os dois torna BC-8 uma adição.
const FIELD_ALIASES = Object.freeze({
    name:     ['name', 'usr'],
    email:    ['email', 'eml'],
    password: ['password', 'pwd'],
    courseId: ['courseId', 'c_id'],
    card:     ['card'],
});

const readField = (body, aliases) => {
    for (const alias of aliases) {
        if (body[alias] !== undefined) return body[alias];
    }
    return undefined;
};

const parseCheckoutRequest = (body = {}) =>
    Object.fromEntries(
        Object.entries(FIELD_ALIASES).map(([field, aliases]) => [field, readField(body, aliases)])
    );

// Casca fina: parse da entrada, chamada ao service, mapeamento do RESULTADO.
// Nenhuma captura genérica e nenhum mapeamento de erro — TR-13 centralizou isso.
const makeCheckoutController = ({ checkoutService }) => ({
    async create(req, res) {
        const { name, email, password, courseId, card } = parseCheckoutRequest(req.body);

        if (!name || !email || !courseId || !card) throw new InvalidRequestError();

        const { enrollmentId } = await checkoutService.execute({ name, email, password, courseId, card });

        return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    },
});

module.exports = { makeCheckoutController, parseCheckoutRequest, FIELD_ALIASES };
