'use strict';

const { PAID } = require('./paymentGateway');

// Regra de reconhecimento de receita: só pagamento liquidado compõe o faturamento.
// TR-11 substitui a orquestração de consultas por uma ida só ao banco; a regra
// permanece aqui, porque é decisão de domínio e não de acesso a dados.
const makeReportService = ({ courseRepository, enrollmentRepository, userRepository, paymentRepository }) => ({
    async financialReport() {
        const courses = await courseRepository.findAll();

        return Promise.all(
            courses.map(async (course) => {
                const enrollments = await enrollmentRepository.findByCourseId(course.id);

                const students = await Promise.all(
                    enrollments.map(async (enrollment) => {
                        const [user, payment] = await Promise.all([
                            userRepository.findById(enrollment.user_id),
                            paymentRepository.findByEnrollmentId(enrollment.id),
                        ]);
                        return {
                            student: user ? user.name : 'Unknown',
                            paid: payment ? payment.amount : 0,
                            settled: Boolean(payment && payment.status === PAID),
                        };
                    })
                );

                const revenue = students
                    .filter((s) => s.settled)
                    .reduce((total, s) => total + s.paid, 0);

                return {
                    course: course.title,
                    revenue,
                    students: students.map(({ student, paid }) => ({ student, paid })),
                };
            })
        );
    },
});

module.exports = { makeReportService };
