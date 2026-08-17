from flask import request, jsonify
import models
from security.tokens import emitir
from database import get_db
_settings = None
_limitador_login = None
_log = None


def configure(settings, limitador_login, logger):
    """Recebe do composition root a configuração, o limitador de taxa e o logger."""
    global _settings, _limitador_login, _log
    _settings = settings
    _limitador_login = limitador_login
    _log = logger


from dto.serializers import (
    health_dto,
    pedidos_dto,
    produto_dto,
    produtos_dto,
    usuario_autenticado_dto,
    usuario_dto,
    usuarios_dto,
)

def listar_produtos():
    try:
        produtos = models.get_todos_produtos()
        _log.info("produtos_listados", item_count=len(produtos))
        return jsonify({"dados": produtos_dto(produtos), "sucesso": True}), 200
    except Exception as e:
        _log.exception("falha_ao_listar_produtos", erro_tipo=type(e).__name__)
        return jsonify({"erro": str(e)}), 500

def buscar_produto(id):
    try:
        produto = models.get_produto_por_id(id)
        if produto:
            return jsonify({"dados": produto_dto(produto), "sucesso": True}), 200
        else:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def criar_produto():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        if "nome" not in dados:
            return jsonify({"erro": "Nome é obrigatório"}), 400
        if "preco" not in dados:
            return jsonify({"erro": "Preço é obrigatório"}), 400
        if "estoque" not in dados:
            return jsonify({"erro": "Estoque é obrigatório"}), 400

        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")

        if preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        if estoque < 0:
            return jsonify({"erro": "Estoque não pode ser negativo"}), 400
        if len(nome) < 2:
            return jsonify({"erro": "Nome muito curto"}), 400
        if len(nome) > 200:
            return jsonify({"erro": "Nome muito longo"}), 400

        categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
        if categoria not in categorias_validas:
            return jsonify({"erro": "Categoria inválida. Válidas: " + str(categorias_validas)}), 400

        id = models.criar_produto(nome, descricao, preco, estoque, categoria)
        _log.info("produto_criado", produto_id=id)
        return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    except Exception as e:
        _log.exception("falha_ao_criar_produto", erro_tipo=type(e).__name__)
        return jsonify({"erro": str(e)}), 500

def atualizar_produto(id):
    try:
        dados = request.get_json()

        produto_existente = models.get_produto_por_id(id)
        if not produto_existente:
            return jsonify({"erro": "Produto não encontrado"}), 404

        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        if "nome" not in dados:
            return jsonify({"erro": "Nome é obrigatório"}), 400
        if "preco" not in dados:
            return jsonify({"erro": "Preço é obrigatório"}), 400
        if "estoque" not in dados:
            return jsonify({"erro": "Estoque é obrigatório"}), 400

        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")

        if preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        if estoque < 0:
            return jsonify({"erro": "Estoque não pode ser negativo"}), 400

        models.atualizar_produto(id, nome, descricao, preco, estoque, categoria)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def deletar_produto(id):
    try:

        produto = models.get_produto_por_id(id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404

        models.deletar_produto(id)
        _log.info("produto_deletado", produto_id=id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def buscar_produtos():
    try:
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)

        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)

        resultados = models.buscar_produtos(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": produtos_dto(resultados), "total": len(resultados), "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def listar_usuarios():
    try:
        usuarios = models.get_todos_usuarios()

        return jsonify({"dados": usuarios_dto(usuarios), "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def buscar_usuario(id):
    try:
        usuario = models.get_usuario_por_id(id)
        if usuario:
            return jsonify({"dados": usuario_dto(usuario), "sucesso": True}), 200
        else:
            return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def criar_usuario():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not nome or not email or not senha:
            return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

        id = models.criar_usuario(nome, email, senha)
        _log.info("usuario_criado", usuario_id=id)
        return jsonify({"dados": {"id": id}, "sucesso": True}), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def login():
    try:
        dados = request.get_json()
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        chave = (email or "").lower() + "|" + (request.remote_addr or "-")
        permitido, liberar_em = _limitador_login.registrar_e_verificar(chave)
        if not permitido:
            _log.warning("login_bloqueado", limite=_settings.login_rate_limit, janela_segundos=_settings.login_rate_window_seconds)
            return jsonify({
                "erro": "Muitas tentativas de autenticação. Tente novamente em " + str(liberar_em) + "s",
                "sucesso": False
            }), 429

        usuario = models.login_usuario(email, senha)
        if usuario:
            _limitador_login.limpar(chave)
            token = emitir(
                _settings.secret_key,
                usuario["id"],
                usuario["tipo"],
                _settings.token_ttl_seconds,
            )
            _log.info("login_sucesso", usuario_id=usuario["id"])
            return jsonify({
                "dados": {
                    "token": token,
                    "token_type": "Bearer",
                    "expira_em": _settings.token_ttl_seconds,
                    "usuario": {"id": usuario["id"], "tipo": usuario["tipo"]},
                },
                "sucesso": True,
                "mensagem": "Login OK",
            }), 200
        else:
            _log.warning("login_falhou", resultado="credencial_invalida")
            return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def criar_pedido():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens or len(itens) == 0:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        resultado = models.criar_pedido(usuario_id, itens)

        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        _log.info("notificacao_enviada", canal="email", pedido_id=resultado["pedido_id"], usuario_id=usuario_id)
        _log.info("notificacao_enviada", canal="sms", pedido_id=resultado["pedido_id"], usuario_id=usuario_id)
        _log.info("notificacao_enviada", canal="push", pedido_id=resultado["pedido_id"], usuario_id=usuario_id)

        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso"
        }), 201

    except Exception as e:
        _log.exception("falha_ao_criar_pedido", erro_tipo=type(e).__name__)
        return jsonify({"erro": str(e)}), 500

def listar_pedidos_usuario(usuario_id):
    try:
        pedidos = models.get_pedidos_usuario(usuario_id)
        return jsonify({"dados": pedidos_dto(pedidos), "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def listar_todos_pedidos():
    try:

        pedidos = models.get_todos_pedidos()
        return jsonify({"dados": pedidos_dto(pedidos), "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def atualizar_status_pedido(pedido_id):
    try:
        dados = request.get_json()
        novo_status = dados.get("status", "")

        if novo_status not in ["pendente", "aprovado", "enviado", "entregue", "cancelado"]:
            return jsonify({"erro": "Status inválido"}), 400

        models.atualizar_status_pedido(pedido_id, novo_status)

        if novo_status == "aprovado":
            _log.info("pedido_aprovado", pedido_id=pedido_id, status=novo_status)
        if novo_status == "cancelado":
            _log.info("pedido_cancelado", pedido_id=pedido_id, status=novo_status)

        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def relatorio_vendas():
    try:
        relatorio = models.relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

def health_check():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cursor.fetchone()[0]

        return jsonify(health_dto(
            {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
            "1.0.0"
        )), 200
    except Exception as e:
        return jsonify({"status": "erro", "detalhes": str(e)}), 500
