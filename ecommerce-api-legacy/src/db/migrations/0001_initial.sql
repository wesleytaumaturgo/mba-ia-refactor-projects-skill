-- 0001_initial — reproduz o schema que a god class criava no boot, agora com as
-- restrições de integridade que nunca existiram (F-007).
--
-- ND-5: as chaves estrangeiras são ON DELETE RESTRICT. Registro de pagamento é
-- dado contábil; uma remoção de usuário não pode destruí-lo em cascata.

PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pass  TEXT NOT NULL
);

CREATE TABLE courses (
    id     INTEGER PRIMARY KEY,
    title  TEXT NOT NULL,
    price  REAL NOT NULL CHECK (price >= 0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE enrollments (
    id        INTEGER PRIMARY KEY,
    user_id   INTEGER NOT NULL REFERENCES users(id)   ON DELETE RESTRICT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    UNIQUE (user_id, course_id)
);

CREATE TABLE payments (
    id            INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE RESTRICT,
    amount        REAL NOT NULL CHECK (amount >= 0),
    status        TEXT NOT NULL CHECK (status IN ('PAID', 'DENIED'))
);

CREATE TABLE audit_logs (
    id         INTEGER PRIMARY KEY,
    action     TEXT NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_payments_enrollment ON payments(enrollment_id);
