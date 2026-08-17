from flask import Flask, jsonify, request
from flask_cors import CORS
import controllers
import database
from config import load_settings
from database import get_db
from middlewares.auth import POLITICAS_PADRAO, PoliticaDeAcesso
from middlewares.rate_limit import LimitadorDeTaxa
from observability.logger import build_logger
from security import password

settings = load_settings()

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.secret_key
app.config["DEBUG"] = settings.debug
database.configure(settings)
password.configure(settings.password_cost_log2)

log = build_logger(settings.log_level)
limitador_login = LimitadorDeTaxa(settings.login_rate_limit, settings.login_rate_window_seconds)
politica_de_acesso = PoliticaDeAcesso(settings, POLITICAS_PADRAO)
controllers.configure(settings, limitador_login, log)

CORS(app)


@app.before_request
def _verificar_acesso():
    """Negar por padrão: nenhum handler roda antes desta verificação."""
    return politica_de_acesso.aplicar()

app.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
app.add_url_rule("/produtos/busca", "buscar_produtos", controllers.buscar_produtos, methods=["GET"])
app.add_url_rule("/produtos/<int:id>", "buscar_produto", controllers.buscar_produto, methods=["GET"])
app.add_url_rule("/produtos", "criar_produto", controllers.criar_produto, methods=["POST"])
app.add_url_rule("/produtos/<int:id>", "atualizar_produto", controllers.atualizar_produto, methods=["PUT"])
app.add_url_rule("/produtos/<int:id>", "deletar_produto", controllers.deletar_produto, methods=["DELETE"])

app.add_url_rule("/usuarios", "listar_usuarios", controllers.listar_usuarios, methods=["GET"])
app.add_url_rule("/usuarios/<int:id>", "buscar_usuario", controllers.buscar_usuario, methods=["GET"])
app.add_url_rule("/usuarios", "criar_usuario", controllers.criar_usuario, methods=["POST"])
app.add_url_rule("/login", "login", controllers.login, methods=["POST"])

app.add_url_rule("/pedidos", "criar_pedido", controllers.criar_pedido, methods=["POST"])
app.add_url_rule("/pedidos", "listar_todos_pedidos", controllers.listar_todos_pedidos, methods=["GET"])
app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", controllers.listar_pedidos_usuario, methods=["GET"])
app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", controllers.atualizar_status_pedido, methods=["PUT"])

app.add_url_rule("/relatorios/vendas", "relatorio_vendas", controllers.relatorio_vendas, methods=["GET"])

app.add_url_rule("/health", "health_check", controllers.health_check, methods=["GET"])

@app.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health"
        }
    })

@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    log.warning("banco_resetado", resultado="todas_as_tabelas_apagadas")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

# POST /admin/query foi REMOVIDO por TR-02 (finding F-008, breaking change BC-3).
# Executava SQL arbitrário recebido no corpo da requisição; a superfície era o defeito,
# então não havia como fechá-lo preservando a rota. Operação administrativa legítima
# pertence a script de manutenção fora da superfície HTTP.

if __name__ == "__main__":

    get_db()
    log.info("servidor_iniciado", host=settings.host, port=settings.port, ambiente=settings.environment)

    app.run(host=settings.host, port=settings.port, debug=settings.debug)
