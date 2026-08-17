from flask import jsonify, request

from dto.serializers import produto_dto, produtos_dto


class ProdutoController:
    """Tradução protocolo ↔ domínio: parse, chamada ao service, mapeamento da resposta.

    Não captura exceção nem escolhe status de erro — o erro de domínio sobe e o tratador
    centralizado de TR-13 o traduz.
    """

    def __init__(self, produto_service, logger):
        self._service = produto_service
        self._log = logger

    def listar(self):
        pag = self._service.listar(**_parametros_de_pagina())
        self._log.info("produtos_listados", item_count=len(pag["itens"]))
        return jsonify({
            "dados": produtos_dto(pag["itens"]),
            "paginacao": pag["paginacao"],
            "sucesso": True,
        }), 200

    def buscar(self, produto_id):
        produto = self._service.buscar_por_id(produto_id)
        return jsonify({"dados": produto_dto(produto), "sucesso": True}), 200

    def pesquisar(self):
        pag = self._service.buscar(
            termo=request.args.get("q", ""),
            categoria=request.args.get("categoria", None),
            preco_min=request.args.get("preco_min", None),
            preco_max=request.args.get("preco_max", None),
            **_parametros_de_pagina()
        )
        return jsonify({
            "dados": produtos_dto(pag["itens"]),
            "total": pag["paginacao"]["total"],
            "paginacao": pag["paginacao"],
            "sucesso": True,
        }), 200

    def criar(self):
        produto_id = self._service.criar(request.get_json(silent=True))
        self._log.info("produto_criado", produto_id=produto_id)
        return jsonify({
            "dados": {"id": produto_id},
            "sucesso": True,
            "mensagem": "Produto criado",
        }), 201

    def atualizar(self, produto_id):
        dados = request.get_json(silent=True)
        # A ordem preserva a do baseline: existência do recurso antes do formato do corpo.
        self._service.buscar_por_id(produto_id)
        self._service.atualizar(produto_id, dados)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        self._service.deletar(produto_id)
        self._log.info("produto_deletado", produto_id=produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def _parametros_de_pagina():
    return {
        "limite": request.args.get("limite", None),
        "offset": request.args.get("offset", None),
    }
