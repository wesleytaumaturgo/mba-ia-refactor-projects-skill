'use strict';

const { UserNotFoundError, UserHasEnrollmentsError } = require('../errors');

const makeUserController = ({ userService }) => ({
    async remove(req, res) {
        try {
            await userService.remove(req.params.id);
            return res.status(200).send('Usuário removido.');
        } catch (error) {
            // BC-9 (ND-5): usuário com matrícula passa a responder 409.
            if (error instanceof UserHasEnrollmentsError) return res.status(409).send(error.message);
            if (error instanceof UserNotFoundError) return res.status(404).send(error.message);
            throw error;
        }
    },
});

module.exports = { makeUserController };
