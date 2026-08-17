-- Migração inicial: reproduz o schema efetivo capturado na Fase 1 e declara as
-- restrições de integridade que só existiam em código, ou em lugar nenhum (finding F-013).
-- As invariantes espelham as de `models/` e as do validador de TR-08.

CREATE TABLE produtos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nome       TEXT    NOT NULL CHECK (length(nome) BETWEEN 2 AND 200),
    descricao  TEXT    NOT NULL DEFAULT '',
    preco      REAL    NOT NULL CHECK (preco >= 0),
    estoque    INTEGER NOT NULL CHECK (estoque >= 0),
    categoria  TEXT    NOT NULL CHECK (categoria IN
                   ('informatica', 'moveis', 'vestuario', 'geral', 'eletronicos', 'livros')),
    ativo      INTEGER NOT NULL DEFAULT 1,
    criado_em  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE usuarios (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nome       TEXT    NOT NULL,
    email      TEXT    NOT NULL UNIQUE,
    senha      TEXT    NOT NULL,
    tipo       TEXT    NOT NULL DEFAULT 'cliente' CHECK (tipo IN ('admin', 'cliente')),
    criado_em  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pedidos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    status     TEXT    NOT NULL DEFAULT 'pendente' CHECK (status IN
                   ('pendente', 'aprovado', 'enviado', 'entregue', 'cancelado')),
    total      REAL    NOT NULL CHECK (total >= 0),
    criado_em  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE itens_pedido (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id      INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    produto_id     INTEGER NOT NULL REFERENCES produtos(id),
    quantidade     INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario REAL    NOT NULL CHECK (preco_unitario >= 0)
);

CREATE INDEX idx_pedidos_usuario ON pedidos(usuario_id);
CREATE INDEX idx_itens_pedido ON itens_pedido(pedido_id);
