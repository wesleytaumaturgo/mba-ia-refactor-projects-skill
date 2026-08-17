"""Superfície pública do pacote de models.

O reexport não é decoração: importar `models` registra os três mappers de uma vez,
que é o que permite ao SQLAlchemy resolver os relacionamentos declarados por nome
(`db.relationship('User', ...)`) independentemente da ordem de import dos módulos.
"""
from models.category import Category as Category
from models.task import Task as Task
from models.user import User as User

__all__ = ['Category', 'Task', 'User']
