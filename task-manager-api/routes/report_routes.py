"""Tabela de rotas dos relatórios — método + path → handler + middlewares. Sem lógica."""
from flask import Blueprint

from middlewares.auth import public

report_bp = Blueprint('reports', __name__)


def register_report_routes(controller):
    report_bp.add_url_rule('/reports/summary', 'summary_report',
                           public(controller.summary), methods=['GET'])
    report_bp.add_url_rule('/reports/user/<int:user_id>', 'user_report',
                           public(controller.user_report), methods=['GET'])
    return report_bp
