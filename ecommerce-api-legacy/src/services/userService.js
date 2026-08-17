'use strict';

// TR-06 extrai a remoção de usuário sem alterar comportamento: o texto confessional
// da resposta original ainda descreve o que acontece. TR-10 e TR-16 introduzem a
// integridade referencial que torna o defeito impossível (ND-5, RESTRICT).
const makeUserService = ({ userRepository }) => ({
    async remove(id) {
        await userRepository.deleteById(id);
    },
});

module.exports = { makeUserService };
