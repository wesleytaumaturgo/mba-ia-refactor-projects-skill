'use strict';

const { PAID } = require('./paymentGateway');

const DEFAULT_LIMIT = 50;
const MAX_LIMIT = 200;
const UNKNOWN_STUDENT = 'Unknown';

// Reagrupa em memória o resultado da consulta única, preservando a FORMA de saída
// que o baseline tinha: { course, revenue, students: [{ student, paid }] }.
function groupByCourse(rows) {
    const byCourse = new Map();

    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            byCourse.set(row.course_id, {
                course: row.course_title,
                revenue: row.course_revenue,
                students: [],
            });
        }
        // LEFT JOIN sem matrícula produz linha com colunas nulas: curso sem aluno
        // tem `students: []`, e não um aluno fantasma.
        if (row.student_name !== null || row.paid_amount !== null) {
            byCourse.get(row.course_id).students.push({
                student: row.student_name ?? UNKNOWN_STUDENT,
                paid: row.paid_amount ?? 0,
            });
        }
    }

    return [...byCourse.values()];
}

const makeReportService = ({ reportRepository }) => ({
    // TR-17 / BC-6: a resposta passa a ser envelope paginado. A FORMA DO ITEM é
    // preservada — { course, revenue, students: [{ student, paid }] } —, o que muda
    // é o envoltório. O teto MAX_LIMIT é o que impede o cliente de reintroduzir o
    // problema pedindo `limit=999999`; a página é aplicada na consulta, não fatiada
    // em memória depois de trazer tudo.
    async financialReport({ limit, offset } = {}) {
        const effectiveLimit = Math.min(
            Number.isInteger(limit) && limit > 0 ? limit : DEFAULT_LIMIT,
            MAX_LIMIT
        );
        const effectiveOffset = Number.isInteger(offset) && offset >= 0 ? offset : 0;

        const [rows, total] = await Promise.all([
            reportRepository.financialRows({
                settledStatus: PAID,
                limit: effectiveLimit,
                offset: effectiveOffset,
            }),
            reportRepository.countCourses(),
        ]);

        return { items: groupByCourse(rows), total, limit: effectiveLimit, offset: effectiveOffset };
    },
});

module.exports = { makeReportService, DEFAULT_LIMIT, MAX_LIMIT };
