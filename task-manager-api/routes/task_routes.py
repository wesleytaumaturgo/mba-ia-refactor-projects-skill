"""Tabela de rotas do agregado Task — método + path → handler + middlewares. Sem lógica."""
from flask import Blueprint

from middlewares.auth import public

task_bp = Blueprint('tasks', __name__)


def register_task_routes(controller):
    task_bp.add_url_rule('/tasks', 'get_tasks',
                         public(controller.list_tasks), methods=['GET'])
    task_bp.add_url_rule('/tasks/search', 'search_tasks',
                         public(controller.search_tasks), methods=['GET'])
    task_bp.add_url_rule('/tasks/stats', 'task_stats',
                         public(controller.task_stats), methods=['GET'])
    task_bp.add_url_rule('/tasks/<int:task_id>', 'get_task',
                         public(controller.get_task), methods=['GET'])
    task_bp.add_url_rule('/tasks', 'create_task',
                         controller.create_task, methods=['POST'])
    task_bp.add_url_rule('/tasks/<int:task_id>', 'update_task',
                         controller.update_task, methods=['PUT'])
    task_bp.add_url_rule('/tasks/<int:task_id>', 'delete_task',
                         controller.delete_task, methods=['DELETE'])
    return task_bp
