'use strict';

const makeEnrollmentRepository = (db) => ({
    insert: async ({ userId, courseId }) => {
        const { lastID } = await db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]
        );
        return lastID;
    },

    findByCourseId: (courseId) =>
        db.all('SELECT id, user_id, course_id FROM enrollments WHERE course_id = ? ORDER BY id', [courseId]),

    countByUserId: async (userId) => {
        const row = await db.get('SELECT COUNT(*) AS total FROM enrollments WHERE user_id = ?', [userId]);
        return row.total;
    },
});

module.exports = { makeEnrollmentRepository };
