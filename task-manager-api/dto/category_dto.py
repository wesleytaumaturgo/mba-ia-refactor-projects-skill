"""Projeção de saída para Category — allowlist explícita."""


def category_public(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': str(category.created_at),
    }


def category_list_item(category, task_count):
    data = category_public(category)
    data['task_count'] = task_count
    return data
