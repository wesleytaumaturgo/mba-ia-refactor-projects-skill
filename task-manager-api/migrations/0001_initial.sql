-- 0001_initial — schema inicial versionado.
-- Reproduz o schema que `db.create_all()` produzia no boot, acrescentando as
-- restrições de integridade que só existiam em código Python (ou em lugar nenhum).

CREATE TABLE users (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    role        VARCHAR(50)  NOT NULL DEFAULT 'user',
    active      BOOLEAN      NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_users_role  CHECK (role IN ('user', 'admin', 'manager')),
    CONSTRAINT ck_users_name  CHECK (length(trim(name)) > 0)
);

CREATE TABLE categories (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(300),
    color       VARCHAR(7)   NOT NULL DEFAULT '#000000',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_categories_name  CHECK (length(trim(name)) > 0),
    CONSTRAINT ck_categories_color CHECK (color LIKE '#______')
);

CREATE TABLE tasks (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    status      VARCHAR(50)  NOT NULL DEFAULT 'pending',
    priority    INTEGER      NOT NULL DEFAULT 3,
    user_id     INTEGER,
    category_id INTEGER,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date    DATETIME,
    tags        VARCHAR(500),
    CONSTRAINT ck_tasks_status   CHECK (status IN ('pending', 'in_progress', 'done', 'cancelled')),
    CONSTRAINT ck_tasks_priority CHECK (priority BETWEEN 1 AND 5),
    CONSTRAINT ck_tasks_title    CHECK (length(trim(title)) BETWEEN 3 AND 200),
    -- A política de deleção passa a ser declarada no schema, não só no service:
    -- apagar um usuário leva as tasks dele; apagar uma categoria apenas desassocia.
    CONSTRAINT fk_tasks_user     FOREIGN KEY (user_id)     REFERENCES users(id)      ON DELETE CASCADE,
    CONSTRAINT fk_tasks_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- Índices nas colunas que as consultas efetivamente filtram.
CREATE INDEX ix_tasks_user_id     ON tasks (user_id);
CREATE INDEX ix_tasks_category_id ON tasks (category_id);
CREATE INDEX ix_tasks_status      ON tasks (status);
CREATE INDEX ix_tasks_due_date    ON tasks (due_date);
