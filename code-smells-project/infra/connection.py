"""Conexão com o banco, com ciclo de vida explícito.

Substitui o handle global mutável de `database.py` (findings F-009 e F-014): a conexão
deixa de ser variável de módulo criada sob demanda e passa a ser construída pelo
composition root e aberta por uso, com fechamento garantido.

Como cada uso abre a sua própria conexão, `check_same_thread=False` deixa de ser
necessário — a proteção de concorrência do driver volta a valer.
"""

import sqlite3
from contextlib import contextmanager


class Database:
    def __init__(self, db_path):
        self._db_path = db_path

    @property
    def db_path(self):
        return self._db_path

    def _conectar(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def connection(self):
        """Conexão para leitura. Fecha ao sair; não comita."""
        conn = self._conectar()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        """Unidade de trabalho: comita na saída limpa, desfaz em qualquer erro, sempre fecha."""
        conn = self._conectar()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
