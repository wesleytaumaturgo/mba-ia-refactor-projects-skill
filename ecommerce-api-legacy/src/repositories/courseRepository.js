'use strict';

const ACTIVE = 1;

// Recebe o handle por parâmetro; não instancia infraestrutura, não conhece HTTP.
const makeCourseRepository = (db) => ({
    findActiveById: (id) =>
        db.get('SELECT id, title, price, active FROM courses WHERE id = ? AND active = ?', [id, ACTIVE]),

    findAll: (limit, offset) =>
        limit === undefined
            ? db.all('SELECT id, title, price, active FROM courses ORDER BY id')
            : db.all('SELECT id, title, price, active FROM courses ORDER BY id LIMIT ? OFFSET ?', [limit, offset]),

    countAll: async () => {
        const row = await db.get('SELECT COUNT(*) AS total FROM courses');
        return row.total;
    },
});

module.exports = { makeCourseRepository };
