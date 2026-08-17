"""Regra de negócio do agregado Task. Único lugar que decide o que acontece.

Não importa nenhum símbolo de protocolo — a regra vale igual sob HTTP ou sob uma fila.
"""
from datetime import datetime

from models.task import Task
from services.errors import NotFound, ValidationError


class TaskService:
    def __init__(self, task_repository, user_repository, category_repository,
                 unit_of_work, validator):
        self._tasks = task_repository
        self._users = user_repository
        self._categories = category_repository
        self._uow = unit_of_work
        self._validator = validator

    # ── leitura ──────────────────────────────────────────────────────────────
    def list_tasks(self, limit=None, offset=None):
        return self._tasks.list_all(limit=limit, offset=offset)

    def get_task(self, task_id):
        task = self._tasks.get(task_id)
        if task is None:
            raise NotFound('Task não encontrada')
        return task

    def list_tasks_of_user(self, user_id, limit=None, offset=None):
        return self._tasks.list_by_user(user_id, limit=limit, offset=offset)

    def search(self, text=None, status=None, priority=None, user_id=None,
               limit=None, offset=None):
        return self._tasks.search(
            text=text,
            status=status,
            priority=self._validator.optional_int(priority, 'priority'),
            user_id=self._validator.optional_int(user_id, 'user_id'),
            limit=limit, offset=offset,
        )

    def statistics(self, now=None):
        now = now or datetime.utcnow()
        by_status = self._tasks.count_by_status()
        total = self._tasks.count()
        done = by_status.get('done', 0)
        return {
            'total': total,
            'pending': by_status.get('pending', 0),
            'in_progress': by_status.get('in_progress', 0),
            'done': done,
            'cancelled': by_status.get('cancelled', 0),
            'overdue': self._tasks.count_overdue(now),
            'completion_rate': completion_rate(done, total),
        }

    # ── escrita ──────────────────────────────────────────────────────────────
    def _check_relations(self, data):
        if data.get('user_id') is not None and self._users.get(data['user_id']) is None:
            raise NotFound('Usuário não encontrado', field='user_id')
        if data.get('category_id') is not None and self._categories.get(data['category_id']) is None:
            raise NotFound('Categoria não encontrada', field='category_id')

    def create_task(self, payload):
        data = self._validator.validate_create(payload)
        self._check_relations(data)

        task = Task()
        for field, value in data.items():
            setattr(task, field, value)

        with self._uow.transaction():
            self._tasks.add(task)
        return task

    def update_task(self, task_id, payload):
        task = self.get_task(task_id)
        data = self._validator.validate_update(payload)
        self._check_relations(data)

        with self._uow.transaction():
            for field, value in data.items():
                setattr(task, field, value)
            task.updated_at = datetime.utcnow()
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        with self._uow.transaction():
            self._tasks.delete(task)


def completion_rate(done, total):
    """Única definição de taxa de conclusão no projeto (consolida F-010)."""
    if not total:
        return 0
    return round((done / total) * 100, 2)
