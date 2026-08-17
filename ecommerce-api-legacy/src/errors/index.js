'use strict';

// Erros de domínio. Sinalizam POR TIPO, nunca pela forma do valor de retorno —
// é isso que impede o controller de voltar a decidir regra inspecionando `null`.
class DomainError extends Error {
    constructor(code, message) {
        super(message);
        this.name = new.target.name;
        this.code = code;
    }
}

class CourseNotFoundError extends DomainError {
    constructor() {
        super('COURSE_NOT_FOUND', 'Curso não encontrado');
    }
}

class PaymentDeclinedError extends DomainError {
    constructor() {
        super('PAYMENT_DECLINED', 'Pagamento recusado');
    }
}

class InvalidRequestError extends DomainError {
    constructor(message = 'Requisição inválida') {
        super('INVALID_REQUEST', message);
    }
}

class UserHasEnrollmentsError extends DomainError {
    constructor() {
        super('USER_HAS_ENROLLMENTS', 'Usuário possui matrículas e não pode ser removido');
    }
}

class UserNotFoundError extends DomainError {
    constructor() {
        super('USER_NOT_FOUND', 'Usuário não encontrado');
    }
}

class UnauthorizedError extends DomainError {
    constructor() {
        super('UNAUTHORIZED', 'Credencial ausente ou inválida');
    }
}

class RateLimitExceededError extends DomainError {
    constructor() {
        super('RATE_LIMIT_EXCEEDED', 'Limite de requisições excedido');
    }
}

module.exports = {
    DomainError,
    CourseNotFoundError,
    PaymentDeclinedError,
    InvalidRequestError,
    UserHasEnrollmentsError,
    UserNotFoundError,
    UnauthorizedError,
    RateLimitExceededError,
};
