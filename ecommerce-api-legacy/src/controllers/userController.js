'use strict';

const makeUserController = ({ userService }) => ({
    async remove(req, res) {
        await userService.remove(req.params.id);
        return res.status(200).send('Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.');
    },
});

module.exports = { makeUserController };
