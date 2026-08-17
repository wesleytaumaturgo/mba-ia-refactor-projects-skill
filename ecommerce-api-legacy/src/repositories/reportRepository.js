'use strict';

// TR-11: a cascata de `1 + C + 2·E` consultas vira UMA ida ao banco.
// A agregação de receita, que era um laço em JavaScript sobre todos os pagamentos,
// passa para a cláusula da consulta — o banco soma, a aplicação apenas reagrupa.
//
// BC-6: a ordenação é EXPLÍCITA. O código original emitia os cursos na ordem em
// que cada cadeia de callbacks terminava, e duas execuções davam ordens diferentes.
const FINANCIAL_REPORT_SQL = `
    SELECT
        c.id                                        AS course_id,
        c.title                                     AS course_title,
        u.name                                      AS student_name,
        p.amount                                    AS paid_amount,
        (
            SELECT COALESCE(SUM(p2.amount), 0)
              FROM enrollments e2
              JOIN payments    p2 ON p2.enrollment_id = e2.id
             WHERE e2.course_id = c.id
               AND p2.status    = ?
        )                                           AS course_revenue
      FROM courses      c
      LEFT JOIN enrollments e ON e.course_id     = c.id
      LEFT JOIN users       u ON u.id            = e.user_id
      LEFT JOIN payments    p ON p.enrollment_id = e.id
     WHERE c.id IN (SELECT id FROM courses ORDER BY title, id LIMIT ? OFFSET ?)
     ORDER BY c.title, c.id, e.id
`;

const makeReportRepository = (db) => ({
    // Uma consulta, independentemente de quantos cursos e matrículas existam.
    financialRows: ({ settledStatus, limit, offset }) =>
        db.all(FINANCIAL_REPORT_SQL, [settledStatus, limit, offset]),

    countCourses: async () => {
        const row = await db.get('SELECT COUNT(*) AS total FROM courses');
        return row.total;
    },
});

module.exports = { makeReportRepository, FINANCIAL_REPORT_SQL };
