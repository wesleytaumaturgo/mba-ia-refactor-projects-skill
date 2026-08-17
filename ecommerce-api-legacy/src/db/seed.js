'use strict';

// ND-4: o seed sai do boot e vira script sob demanda, atrás de guarda de ambiente.
// A senha do usuário de demonstração deixa de ser o literal '123' em texto puro:
// passa pela mesma derivação lenta que o fluxo de produção usa (TR-03).
async function seedDevelopment(db, { passwordService, nodeEnv, logger }) {
    if (nodeEnv !== 'development') {
        throw new Error(`Seed de demonstração recusado em NODE_ENV="${nodeEnv}". Só roda em development.`);
    }

    const existing = await db.get('SELECT COUNT(*) AS total FROM courses');
    if (existing.total > 0) {
        if (logger) logger.info('seed_skipped', { code: 'already-seeded' });
        return { seeded: false };
    }

    const passwordHash = await passwordService.hash('123');

    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        'Leonan',
        'leonan@fullcycle.com.br',
        passwordHash,
    ]);
    await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)', [
        'Clean Architecture', 997.0, 1,
        'Docker', 497.0, 1,
    ]);
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
    await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [1, 997.0, 'PAID']);

    if (logger) logger.info('seed_applied', { environment: nodeEnv });
    return { seeded: true };
}

module.exports = { seedDevelopment };
