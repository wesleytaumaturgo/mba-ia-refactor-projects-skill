'use strict';

const { UserNotFoundError, UserHasEnrollmentsError } = require('../errors');

// TR-07: a regra de remoção passa a viver no service e a sinalizar por TIPO de
// erro de domínio — não pela forma do retorno. O controller deixa de decidir
// regra inspecionando `null` ou contagem de linhas afetadas.
//
// ND-5: usuário com matrícula NÃO é removido. O registro de pagamento é dado
// contábil, e a alternativa (cascata) deixaria uma chamada destruir histórico
// financeiro. A regra é imposta em dois níveis: aqui, com erro de domínio
// legível; e no schema, pela FK ON DELETE RESTRICT de TR-16 — que é o que
// impede a regra de ser contornada por qualquer outro caminho de escrita.
const makeUserService = ({ userRepository, enrollmentRepository, unitOfWork, logger }) => ({
    async remove(id) {
        return unitOfWork.run(async () => {
            const user = await userRepository.findById(id);
            if (!user) throw new UserNotFoundError();

            const enrollments = await enrollmentRepository.countByUserId(id);
            if (enrollments > 0) throw new UserHasEnrollmentsError();

            const rowsAffected = await userRepository.deleteById(id);
            logger.info('user_removed', { userId: Number(id), rowsAffected });
            return { rowsAffected };
        });
    },
});

module.exports = { makeUserService };
