"""Unidade de trabalho — fronteira transacional explícita, aberta pelo service.

O bloco é curto e vive no service, nunca no controller: transação aberta na camada de
apresentação anula o ganho (TR-10).
"""
from contextlib import contextmanager


class UnitOfWork:
    def __init__(self, db):
        self._db = db

    @contextmanager
    def transaction(self):
        """Comita ao sair sem erro; faz rollback em QUALQUER caminho de erro."""
        try:
            yield self._db.session
            self._db.session.commit()
        except Exception:
            self._db.session.rollback()
            raise
