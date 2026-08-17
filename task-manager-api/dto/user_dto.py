"""Projeção de saída para User — allowlist explícita de campos.

A credencial NUNCA atravessa esta fronteira. A projeção é por allowlist e não por
remoção de chaves: assim o próximo campo sensível adicionado à entidade não entra
sozinho na resposta.
"""
from utils.helpers import format_date


def user_public(user):
    """Projeção base — a única forma de User que sai da aplicação."""
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': format_date(user.created_at),
    }


def user_list_item(user):
    """Item da coleção — MESMA forma do detalhe, sem o derivado `task_count` (BC-6)."""
    return user_public(user)


def user_detail(user, tasks):
    data = user_public(user)
    data['tasks'] = tasks
    return data


def user_identity(user):
    """Identificação mínima do sujeito, para a resposta de autenticação."""
    return user_public(user)
