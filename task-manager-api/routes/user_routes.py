"""Tabela de rotas do agregado User — método + path → handler + middlewares. Sem lógica."""
from flask import Blueprint

from middlewares.auth import public, require_role

user_bp = Blueprint('users', __name__)


def register_user_routes(controller):
    user_bp.add_url_rule('/users', 'get_users',
                         controller.list_users, methods=['GET'])
    user_bp.add_url_rule('/users/<int:user_id>', 'get_user',
                         controller.get_user, methods=['GET'])
    user_bp.add_url_rule('/users/<int:user_id>/tasks', 'get_user_tasks',
                         controller.list_user_tasks, methods=['GET'])
    user_bp.add_url_rule('/users', 'create_user',
                         controller.create_user, methods=['POST'])
    user_bp.add_url_rule('/users/<int:user_id>', 'update_user',
                         controller.update_user, methods=['PUT'])
    user_bp.add_url_rule('/users/<int:user_id>', 'delete_user',
                         require_role('admin')(controller.delete_user), methods=['DELETE'])
    user_bp.add_url_rule('/login', 'login',
                         public(controller.login), methods=['POST'])
    return user_bp
