from flask import jsonify, request

from dto.serializers import pedidos_dto
from services.errors import EntradaInvalida


class PedidoController:
    def __init__(self, pedido_service, logger):
        self._service = pedido_service
        self._log = logger

    def listar_todos(self):
        pag = self._service.listar(**_parametros_de_pagina())
        return jsonify({
            "dados": pedidos_dto(pag["itens"]),
            "paginacao": pag["paginacao"],
            "sucesso": True,
        }), 200

    def listar_por_usuario(self, usuario_id):
        pag = self._service.listar_por_usuario(usuario_id, **_parametros_de_pagina())
        return jsonify({
            "dados": pedidos_dto(pag["itens"]),
            "paginacao": pag["paginacao"],
            "sucesso": True,
        }), 200

    def criar(self):
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            raise EntradaInvalida("Dados inválidos")
        resultado = self._service.criar(dados.get("usuario_id"), dados.get("itens", []))
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def atualizar_status(self, pedido_id):
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            raise EntradaInvalida("Status inválido")
        self._service.atualizar_status(pedido_id, dados.get("status", ""))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def _parametros_de_pagina():
    return {
        "limite": request.args.get("limite", None),
        "offset": request.args.get("offset", None),
    }
