"""Projeção de saída para Category — allowlist explícita."""
from utils.helpers import format_date


def category_public(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': format_date(category.created_at),
    }


def category_list_item(category, task_count):
    data = category_public(category)
    data['task_count'] = task_count
    return data
