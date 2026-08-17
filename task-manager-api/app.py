"""Composition root: lê a configuração, monta o grafo de objetos e sobe a aplicação.

É o único lugar do projeto autorizado a instanciar infraestrutura. Nenhuma camada
abaixo resolve dependência no próprio corpo — todas as recebem por parâmetro.
"""
from flask import Flask
from flask_cors import CORS
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import load_settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from infra.migrator import verify as verify_schema
from middlewares.auth import authenticate_request, public
from middlewares.error_handler import register_error_handlers
from middlewares.rate_limit import RateLimiter
from repositories.category_repository import CategoryRepository
from repositories.task_repository import TaskRepository
from repositories.unit_of_work import UnitOfWork
from repositories.user_repository import UserRepository
from routes.category_routes import register_category_routes
from routes.report_routes import register_report_routes
from routes.task_routes import register_task_routes
from routes.user_routes import register_user_routes
from security.tokens import issue_token
from services.category_service import CategoryService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService
from validators.category_validator import CategoryValidator
from validators.pagination import Pagination
from validators.task_validator import TaskValidator
from utils.helpers import format_date, utc_now
from validators.user_validator import UserValidator


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.secret_key
    app.config['SETTINGS'] = settings

    # Allowlist de origens vinda do ambiente, por método — não o padrão permissivo global.
    CORS(app,
         origins=settings.cors_origins,
         methods=['GET', 'POST', 'PUT', 'DELETE'],
         allow_headers=['Content-Type', 'Authorization'],
         supports_credentials=False)
    db.init_app(app)

    # SQLite não aplica chave estrangeira por padrão: ligar o pragma é o que torna a
    # integridade declarada em 0001_initial.sql efetiva em runtime (F-007).
    @event.listens_for(Engine, 'connect')
    def _enable_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.close()

    # config → infraestrutura → repositórios → services → controllers → rotas
    unit_of_work = UnitOfWork(db)
    task_repository = TaskRepository(db)
    user_repository = UserRepository(db)
    category_repository = CategoryRepository(db)

    rate_limiter = RateLimiter(settings.login_rate_limit,
                               settings.login_rate_window_seconds)
    app.config['LOGIN_RATE_LIMITER'] = rate_limiter

    task_service = TaskService(task_repository, user_repository, category_repository,
                               unit_of_work, TaskValidator())
    user_service = UserService(
        user_repository, task_repository, unit_of_work, UserValidator(),
        token_issuer=lambda user: issue_token(user, settings.secret_key,
                                              settings.token_ttl_seconds),
    )
    category_service = CategoryService(category_repository, task_repository,
                                       unit_of_work, CategoryValidator())
    report_service = ReportService(task_repository, user_repository, category_repository)

    pagination = Pagination(settings.page_size_default, settings.page_size_max)

    app.register_blueprint(register_task_routes(TaskController(task_service, pagination)))
    app.register_blueprint(register_user_routes(
        UserController(user_service, task_service, rate_limiter, pagination)))
    app.register_blueprint(register_category_routes(CategoryController(category_service, pagination)))
    app.register_blueprint(register_report_routes(ReportController(report_service)))

    # Negar por padrão: toda rota exige credencial, exceto as marcadas com @public.
    app.before_request(authenticate_request)

    # Erro de domínio → status HTTP, num só lugar.
    register_error_handlers(app)

    @app.route('/health')
    @public
    def health():
        return {'status': 'ok', 'timestamp': format_date(utc_now())}

    @app.route('/')
    @public
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    return app


settings = load_settings()

# O boot apenas VERIFICA a versão de schema aplicada. A DDL saiu do caminho de boot:
# quem cria ou evolui o schema é `python -m infra.migrator upgrade`.
verify_schema(settings.database_uri)

app = create_app(settings)

if __name__ == '__main__':
    app.run(debug=settings.debug, host=settings.host, port=settings.port)
