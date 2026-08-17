"""Projeção de saída para Task — allowlist explícita, por contexto de resposta."""


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
        'created_at': str(task.created_at),
        'updated_at': str(task.updated_at),
        'due_date': str(task.due_date) if task.due_date else None,
        'tags': _tags(task),
    }


def task_with_overdue(task, now=None):
    data = task_public(task)
    data['overdue'] = task.is_overdue(now)
    return data


def task_list_item(task, now=None):
    """Item da coleção: forma canônica + atraso + nomes das entidades relacionadas."""
    data = task_with_overdue(task, now)
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def task_summary_for_user(task, now=None):
    """Recorte usado na listagem de tasks de um usuário."""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': str(task.due_date) if task.due_date else None,
        'overdue': task.is_overdue(now),
    }


def task_overdue_entry(task, now):
    return {
        'id': task.id,
        'title': task.title,
        'due_date': str(task.due_date),
        'days_overdue': (now - task.due_date).days,
    }
