'use strict';

// TR-18: o vocabulário fechado de status de pagamento deixa de ser um literal
// reconstruído em três pontos do código. Os VALORES são idênticos aos originais —
// renomear e mudar valor no mesmo passo tornaria a quebra indepurável.
//
// A constraint equivalente vive no schema (migração 0001: CHECK (status IN (...))),
// então a regra existe nos dois lugares e não pode divergir em silêncio.
const PaymentStatus = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

const SETTLED = PaymentStatus.PAID;
const ALL = Object.freeze(Object.values(PaymentStatus));

const isSettled = (status) => status === SETTLED;

module.exports = { PaymentStatus, SETTLED, ALL, isSettled };
