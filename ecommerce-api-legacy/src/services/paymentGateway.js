'use strict';

const { PaymentStatus } = require('../models/paymentStatus');

// Prefixo de bandeira aceito pelo gateway simulado. Era o literal "4" solto
// dentro do ternário de autorização.
const APPROVED_CARD_PREFIX = '4';

// Adapter da integração de pagamento. É o único lugar que conhece a chave do
// gateway e o formato do cartão — o service de checkout orquestra, não integra.
//
// TR-14: o PAN completo e a chave do gateway NUNCA são emitidos. Só os quatro
// últimos dígitos atravessam, e a chave não é sequer passada ao logger.
const makePaymentGateway = ({ apiKey, logger }) => ({
    authorize: async ({ card, amount }) => {
        logger.info('payment_authorization_requested', {
            cardLast4: String(card).slice(-4),
            amount,
        });

        const status = card.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;

        logger.info('payment_authorization_settled', { status, amount });
        return { status, approved: status === PaymentStatus.PAID };
    },
});

module.exports = { makePaymentGateway, APPROVED_CARD_PREFIX };
