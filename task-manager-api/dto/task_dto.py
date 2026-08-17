"""Projeção de saída para Task — allowlist explícita, por contexto de resposta."""
from utils.helpers import format_date


def _tags(task):
    return task.tags.split(',') if task.tags else []


def task_public(task):
    """Forma canônica de uma task na saída."""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': format_date(task.created_at),
        'updated_at': format_date(task.updated_at),
        'due_date': format_date(task.due_date),
        'tags': _tags(task),
    }


def task_with_overdue(task, now=None):
    data = task_public(task)
    data['overdue'] = task.is_overdue(now)
    return data


def task_list_item(task, now=None):
    """Item da coleção — MESMA forma do detalhe (BC-5).

    Os campos derivados `user_name` e `category_name` saíam daqui e não do detalhe,
    o que dava duas representações do mesmo recurso (F-014). ND-4 escolheu alinhar a
    coleção ao detalhe: elimina a divergência e o custo por item no mesmo movimento.
    """
    return task_with_overdue(task, now)


def task_summary_for_user(task, now=None):
    """Recorte usado na listagem de tasks de um usuário."""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': format_date(task.created_at),
        'due_date': format_date(task.due_date),
        'overdue': task.is_overdue(now),
    }


def task_overdue_entry(task, now):
    return {
        'id': task.id,
        'title': task.title,
        'due_date': format_date(task.due_date),
        'days_overdue': (now - task.due_date).days,
    }
