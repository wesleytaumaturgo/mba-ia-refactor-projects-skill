"""Tabela de rotas do agregado Category — método + path → handler + middlewares.

Estas rotas moravam em `report_routes.py`, cujo blueprint se chamava `reports`
(F-022). Path e verbo são preservados; o que muda é o lugar e o nome do blueprint.
"""
from flask import Blueprint

from middlewares.auth import public

category_bp = Blueprint('categories', __name__)


def register_category_routes(controller):
    category_bp.add_url_rule('/categories', 'get_categories',
                             public(controller.list_categories), methods=['GET'])
    category_bp.add_url_rule('/categories', 'create_category',
                             controller.create_category, methods=['POST'])
    category_bp.add_url_rule('/categories/<int:cat_id>', 'update_category',
                             controller.update_category, methods=['PUT'])
    category_bp.add_url_rule('/categories/<int:cat_id>', 'delete_category',
                             controller.delete_category, methods=['DELETE'])
    return category_bp
