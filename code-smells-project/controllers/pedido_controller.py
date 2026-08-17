from flask import jsonify, request

from dto.serializers import pedidos_dto
from services.errors import EntradaInvalida, NaoEncontrado, RegraDeNegocioViolada


class PedidoController:
    def __init__(self, pedido_service, logger):
        self._service = pedido_service
        self._log = logger

    def listar_todos(self):
        pedidos = self._service.listar()
        return jsonify({"dados": pedidos_dto(pedidos), "sucesso": True}), 200

    def listar_por_usuario(self, usuario_id):
        pedidos = self._service.listar_por_usuario(usuario_id)
        return jsonify({"dados": pedidos_dto(pedidos), "sucesso": True}), 200

    def criar(self):
        dados = request.get_json(silent=True)
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        try:
            resultado = self._service.criar(
                dados.get("usuario_id"), dados.get("itens", [])
            )
        except EntradaInvalida as erro:
            return jsonify({"erro": erro.mensagem}), 400
        except (NaoEncontrado, RegraDeNegocioViolada) as erro:
            # O baseline responde 400 para item inexistente e para estoque insuficiente.
            return jsonify({"erro": erro.mensagem, "sucesso": False}), 400

        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def atualizar_status(self, pedido_id):
        dados = request.get_json(silent=True) or {}
        try:
            self._service.atualizar_status(pedido_id, dados.get("status", ""))
        except EntradaInvalida as erro:
            return jsonify({"erro": erro.mensagem}), 400
        except NaoEncontrado as erro:
            return jsonify({"erro": erro.mensagem}), 404

        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
