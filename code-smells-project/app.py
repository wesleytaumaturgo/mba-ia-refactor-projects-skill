"""Composition root e entry point.

Único ponto do projeto autorizado a instanciar infraestrutura. Lê a configuração,
constrói a conexão, os repositórios, os serviços e os controllers, registra as rotas e
sobe o servidor. Nenhuma camada abaixo chama fábrica global.
"""

from flask import Flask
from flask_cors import CORS

from config import load_settings
from controllers.admin_controller import AdminController
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
from controllers.relatorio_controller import RelatorioController
from controllers.usuario_controller import UsuarioController
from infra import migrator
from infra.connection import Database
from middlewares.auth import POLITICAS_PADRAO, PoliticaDeAcesso
from middlewares.rate_limit import LimitadorDeTaxa
from observability.logger import build_logger
from repositories.admin_repository import AdminRepository
from repositories.pedido_repository import PedidoRepository
from repositories.produto_repository import ProdutoRepository
from repositories.usuario_repository import UsuarioRepository
from routes import (
    pedido_routes,
    produto_routes,
    relatorio_routes,
    sistema_routes,
    usuario_routes,
)
from security import password
from security.tokens import emitir
from services.admin_service import AdminService
from services.auth_service import AuthService
from services.notificacao_service import NotificacaoService
from services.pedido_service import PedidoService
from services.produto_service import ProdutoService
from services.relatorio_service import PoliticaDeDesconto, RelatorioService
from services.usuario_service import UsuarioService


def build_app(settings):
    """Monta o grafo de objetos: config → infra → repositórios → services → controllers → rotas."""
    log = build_logger(settings.log_level)

    password.configure(settings.password_cost_log2)
    db = Database(settings.db_path)
    # O boot apenas VERIFICA a versão do schema. Criar tabela e inserir seed passaram a ser
    # `python -m scripts.migrate` e `python -m scripts.seed_dev` (finding F-013).
    migrator.verificar(db)

    produto_repository = ProdutoRepository()
    usuario_repository = UsuarioRepository()
    pedido_repository = PedidoRepository()
    admin_repository = AdminRepository()

    limitador_login = LimitadorDeTaxa(
        settings.login_rate_limit, settings.login_rate_window_seconds
    )
    notificacao_service = NotificacaoService(log)

    produto_service = ProdutoService(db, produto_repository)
    usuario_service = UsuarioService(db, usuario_repository, password)
    auth_service = AuthService(
        db, usuario_repository, password, emitir, settings, limitador_login, log
    )
    pedido_service = PedidoService(
        db, pedido_repository, produto_repository, notificacao_service
    )
    relatorio_service = RelatorioService(db, pedido_repository, PoliticaDeDesconto())
    admin_service = AdminService(
        db, admin_repository, produto_repository, usuario_repository, pedido_repository, log
    )

    produto_controller = ProdutoController(produto_service, log)
    usuario_controller = UsuarioController(usuario_service, auth_service, log)
    pedido_controller = PedidoController(pedido_service, log)
    relatorio_controller = RelatorioController(relatorio_service)
    admin_controller = AdminController(admin_service)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug

    CORS(app)

    politica_de_acesso = PoliticaDeAcesso(settings, POLITICAS_PADRAO)

    @app.before_request
    def _verificar_acesso():
        """Negar por padrão: nenhum handler roda antes desta verificação."""
        return politica_de_acesso.aplicar()

    app.register_blueprint(sistema_routes.build(admin_controller))
    app.register_blueprint(sistema_routes.build_admin(admin_controller))
    app.register_blueprint(produto_routes.build(produto_controller))
    app.register_blueprint(usuario_routes.build(usuario_controller))
    app.register_blueprint(usuario_routes.build_auth(usuario_controller))
    app.register_blueprint(pedido_routes.build(pedido_controller))
    app.register_blueprint(relatorio_routes.build(relatorio_controller))

    app.logger_loja = log
    return app


settings = load_settings()
app = build_app(settings)

if __name__ == "__main__":
    app.logger_loja.info(
        "servidor_iniciado",
        host=settings.host,
        port=settings.port,
        ambiente=settings.environment,
    )
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
