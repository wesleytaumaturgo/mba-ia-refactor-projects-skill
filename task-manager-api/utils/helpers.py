"""Utilitários efetivamente usados pelo projeto.

Este módulo era 100% não-invocado (F-010/F-020): dois símbolos importados e nunca
chamados, catorze sequer importados. TR-15 consolidou cada regra na sua camada e
manteve **aqui apenas o que tem chamador real**, listado em cada docstring.

As constantes de vocabulário que viviam soltas aqui migraram para as entidades que
as governam (`Task.VALID_STATUSES`, `User.VALID_ROLES`, `Category.DEFAULT_COLOR`) —
lugar único, ao lado da invariante.
"""
from datetime import datetime, timezone


def utc_now():
    """Instante atual em UTC, sem fuso anexado.

    Substitui `datetime.utcnow()`, deprecado no Python 3.12 (a versão em uso).
    Preserva deliberadamente a semântica **naive**: as colunas DATETIME do schema
    guardam UTC sem fuso, e devolver um valor aware quebraria toda comparação com
    elas com `TypeError: can't compare offset-naive and offset-aware datetimes`.

    Chamadores: models/task.py, services/, repositories/, controllers/, seed.py.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(value):
    """Serializa um instante para o corpo da resposta.

    Chamadores: dto/task_dto.py, dto/user_dto.py, dto/category_dto.py.
    """
    return str(value) if value is not None else None
