'use strict';

const makePaymentRepository = (db) => ({
    insert: async ({ enrollmentId, amount, status }) => {
        const { lastID } = await db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
        return lastID;
    },

    findByEnrollmentId: (enrollmentId) =>
        db.get('SELECT amount, status FROM payments WHERE enrollment_id = ?', [enrollmentId]),
});

module.exports = { makePaymentRepository };
