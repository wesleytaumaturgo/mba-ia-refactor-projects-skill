"""Acesso a dados do agregado Task — único lugar que conhece o ORM para esta entidade."""

from utils.helpers import utc_now

from models.task import Task


class TaskRepository:
    def __init__(self, db):
        self._db = db

    # ── leitura ──────────────────────────────────────────────────────────────
    def get(self, task_id):
        return self._db.session.get(Task, task_id)

    def list_all(self, limit=None, offset=None):
        query = Task.query.order_by(Task.id)
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def list_by_user(self, user_id, limit=None, offset=None):
        query = Task.query.filter_by(user_id=user_id).order_by(Task.id)
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def search(self, text=None, status=None, priority=None, user_id=None,
               limit=None, offset=None):
        query = Task.query
        if text:
            query = query.filter(
                self._db.or_(Task.title.like(f'%{text}%'),
                             Task.description.like(f'%{text}%'))
            )
        if status:
            query = query.filter(Task.status == status)
        if priority is not None:
            query = query.filter(Task.priority == priority)
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        query = query.order_by(Task.id)
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    # ── agregações, expressas na própria consulta ────────────────────────────
    def count(self):
        return Task.query.count()

    def count_by_status(self):
        rows = (self._db.session.query(Task.status, self._db.func.count(Task.id))
                .group_by(Task.status).all())
        return {status: total for status, total in rows}

    def count_by_priority(self):
        rows = (self._db.session.query(Task.priority, self._db.func.count(Task.id))
                .group_by(Task.priority).all())
        return {priority: total for priority, total in rows}

    def count_by_category(self):
        rows = (self._db.session.query(Task.category_id, self._db.func.count(Task.id))
                .group_by(Task.category_id).all())
        return {category_id: total for category_id, total in rows}

    def count_by_user(self):
        rows = (self._db.session.query(Task.user_id, self._db.func.count(Task.id))
                .group_by(Task.user_id).all())
        return {user_id: total for user_id, total in rows}

    def count_done_by_user(self):
        rows = (self._db.session.query(Task.user_id, self._db.func.count(Task.id))
                .filter(Task.status == 'done').group_by(Task.user_id).all())
        return {user_id: total for user_id, total in rows}

    def _overdue_filter(self, now):
        return self._db.and_(Task.due_date.isnot(None),
                             Task.due_date < now,
                             Task.status.notin_(Task.TERMINAL_STATUSES))

    def count_overdue(self, now=None):
        now = now or utc_now()
        return Task.query.filter(self._overdue_filter(now)).count()

    def list_overdue(self, now=None):
        now = now or utc_now()
        return Task.query.filter(self._overdue_filter(now)).order_by(Task.due_date).all()

    def count_created_since(self, moment):
        return Task.query.filter(Task.created_at >= moment).count()

    def count_done_since(self, moment):
        return Task.query.filter(Task.status == 'done',
                                 Task.updated_at >= moment).count()

    # ── escrita ──────────────────────────────────────────────────────────────
    def add(self, task):
        self._db.session.add(task)
        return task

    def delete(self, task):
        self._db.session.delete(task)

    def delete_by_user(self, user_id):
        return Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)

    def clear_category(self, category_id):
        return (Task.query.filter_by(category_id=category_id)
                .update({'category_id': None}, synchronize_session=False))
