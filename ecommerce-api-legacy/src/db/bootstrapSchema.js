'use strict';

// TR-06 apenas MOVE a DDL e o seed para fora da god class, sem mudar quando eles
// rodam: continuam no caminho de boot, que é o finding F-007 (AP-21) e pertence à
// Onda 2. É TR-16 que os substitui por migração versionada e seed sob demanda.
async function bootstrapSchema(db) {
    await db.exec(`
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
        CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
        CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
        CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
        CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
    `);

    await db.exec(`
        INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123');
        INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1);
        INSERT INTO enrollments (user_id, course_id) VALUES (1, 1);
        INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID');
    `);
}

module.exports = { bootstrapSchema };
