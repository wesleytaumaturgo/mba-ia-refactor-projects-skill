'use strict';

const makeUserRepository = (db) => ({
    findByEmail: (email) => db.get('SELECT id, name, email FROM users WHERE email = ?', [email]),

    findById: (id) => db.get('SELECT id, name FROM users WHERE id = ?', [id]),

    insert: async ({ name, email, passwordHash }) => {
        const { lastID } = await db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash]
        );
        return lastID;
    },

    deleteById: async (id) => {
        const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
        return changes;
    },
});

module.exports = { makeUserRepository };
