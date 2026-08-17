from flask import Blueprint


def build(controller):
    """Rotas de infraestrutura: raiz e health check."""
    bp = Blueprint("sistema", __name__)
    bp.add_url_rule("/", "index", controller.index, methods=["GET"])
    bp.add_url_rule("/health", "health_check", controller.health, methods=["GET"])
    return bp


def build_admin(controller):
    bp = Blueprint("admin", __name__)
    bp.add_url_rule("/admin/reset-db", "reset_database", controller.resetar_banco, methods=["POST"])
    return bp
