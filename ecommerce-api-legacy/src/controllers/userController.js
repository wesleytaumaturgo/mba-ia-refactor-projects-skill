'use strict';

const makeUserController = ({ userService }) => ({
    async remove(req, res) {
        const { rowsAffected } = await userService.remove(req.params.id);
        // BC-7: o corpo de sucesso deixa de ser texto e passa a application/json.
        // O texto confessional original ("...ficaram sujos no banco") sumiu porque
        // deixou de ser verdadeiro: a FK ON DELETE RESTRICT de TR-16 impede órfãos.
        return res.status(200).json({ removed: true, rowsAffected });
    },
});

module.exports = { makeUserController };
