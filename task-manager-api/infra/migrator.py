"""Migrações versionadas, executadas por comando explícito — nunca no boot.

O boot apenas **verifica** a versão aplicada e falha com mensagem clara se o schema
estiver defasado. Isso devolve ao projeto um caminho de evolução de schema, que
`db.create_all()` não tinha: ele só criava tabelas ausentes e nunca alterava coluna.

uso:
    python -m infra.migrator upgrade   # aplica as migrações pendentes
    python -m infra.migrator status    # mostra aplicadas e pendentes
"""
import os
import sqlite3
import sys

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'migrations')


class PendingMigrations(RuntimeError):
    """Schema defasado em relação às migrações do repositório."""


def _database_path(database_uri):
    if not database_uri.startswith('sqlite:///'):
        raise RuntimeError(f'Migrador só suporta SQLite; recebido: {database_uri}')
    path = database_uri[len('sqlite:///'):]
    if os.path.isabs(path):
        return path
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, 'instance', path)


def _connect(database_uri):
    path = _database_path(database_uri)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute('PRAGMA foreign_keys = ON')
    connection.execute(
        'CREATE TABLE IF NOT EXISTS schema_migrations ('
        '  version TEXT PRIMARY KEY,'
        '  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)'
    )
    connection.commit()
    return connection


def available_migrations():
    if not os.path.isdir(MIGRATIONS_DIR):
        return []
    return sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql'))


def applied_migrations(database_uri):
    connection = _connect(database_uri)
    try:
        rows = connection.execute('SELECT version FROM schema_migrations ORDER BY version')
        return [row[0] for row in rows]
    finally:
        connection.close()


def pending_migrations(database_uri):
    applied = set(applied_migrations(database_uri))
    return [m for m in available_migrations() if m not in applied]


def upgrade(database_uri):
    """Aplica as migrações pendentes, cada uma na sua própria transação."""
    connection = _connect(database_uri)
    applied = []
    try:
        for name in pending_migrations(database_uri):
            sql = open(os.path.join(MIGRATIONS_DIR, name), encoding='utf-8').read()
            try:
                connection.executescript(sql)
                connection.execute('INSERT INTO schema_migrations (version) VALUES (?)', (name,))
                connection.commit()
                applied.append(name)
            except Exception:
                connection.rollback()
                raise
        return applied
    finally:
        connection.close()


def verify(database_uri):
    """Chamada no boot. Levanta PendingMigrations se o schema estiver defasado."""
    pending = pending_migrations(database_uri)
    if pending:
        raise PendingMigrations(
            'Schema desatualizado. Migrações pendentes: ' + ', '.join(pending) +
            '. Rode: python -m infra.migrator upgrade'
        )


def _main(argv):
    sys.path.insert(0, os.path.dirname(MIGRATIONS_DIR))
    from config import load_settings

    settings = load_settings()
    command = argv[1] if len(argv) > 1 else 'status'

    if command == 'upgrade':
        applied = upgrade(settings.database_uri)
        print('Migrações aplicadas:', ', '.join(applied) if applied else 'nenhuma (já atualizado)')
    elif command == 'status':
        print('Banco     :', _database_path(settings.database_uri))
        print('Aplicadas :', ', '.join(applied_migrations(settings.database_uri)) or 'nenhuma')
        print('Pendentes :', ', '.join(pending_migrations(settings.database_uri)) or 'nenhuma')
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(_main(sys.argv))
