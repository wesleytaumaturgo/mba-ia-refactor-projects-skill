from flask import jsonify, request

from dto.serializers import produto_dto, produtos_dto
from services.errors import Conflito, EntradaInvalida, NaoEncontrado


class ProdutoController:
    """Tradução protocolo ↔ domínio. Parse, chamada ao service, mapeamento da resposta."""

    def __init__(self, produto_service, logger):
        self._service = produto_service
        self._log = logger

    def listar(self):
        produtos = self._service.listar()
        self._log.info("produtos_listados", item_count=len(produtos))
        return jsonify({"dados": produtos_dto(produtos), "sucesso": True}), 200

    def buscar(self, id):
        try:
            produto = self._service.buscar_por_id(id)
        except NaoEncontrado as erro:
            return jsonify({"erro": erro.mensagem, "sucesso": False}), 404
        return jsonify({"dados": produto_dto(produto), "sucesso": True}), 200

    def pesquisar(self):
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)

        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)

        resultados = self._service.buscar(termo, categoria, preco_min, preco_max)
        return jsonify({
            "dados": produtos_dto(resultados),
            "total": len(resultados),
            "sucesso": True,
        }), 200

    def _extrair_payload(self, dados):
        """Allowlist de campos vinculáveis: o payload nunca vai inteiro para a entidade.

        O campo ausente vira `None`; qual é o default de categoria é decisão de domínio e
        pertence ao service, não a esta borda.
        """
        return {
            "nome": dados["nome"],
            "descricao": dados.get("descricao", ""),
            "preco": dados["preco"],
            "estoque": dados["estoque"],
            "categoria": dados.get("categoria"),
        }

    def _validar_protocolo(self, dados):
        """Verificação de protocolo — campo ausente no corpo. Pertence à borda."""
        if not dados:
            return "Dados inválidos"
        for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
            if campo not in dados:
                return rotulo + " é obrigatório"
        return None

    def criar(self):
        dados = request.get_json(silent=True)
        problema = self._validar_protocolo(dados)
        if problema:
            return jsonify({"erro": problema}), 400

        try:
            produto_id = self._service.criar(**self._extrair_payload(dados))
        except EntradaInvalida as erro:
            return jsonify({"erro": erro.mensagem}), 400

        self._log.info("produto_criado", produto_id=produto_id)
        return jsonify({
            "dados": {"id": produto_id},
            "sucesso": True,
            "mensagem": "Produto criado",
        }), 201

    def atualizar(self, id):
        dados = request.get_json(silent=True)

        # A ordem preserva a do baseline: existência do recurso antes do formato do corpo.
        try:
            self._service.buscar_por_id(id)
        except NaoEncontrado as erro:
            return jsonify({"erro": erro.mensagem}), 404

        problema = self._validar_protocolo(dados)
        if problema:
            return jsonify({"erro": problema}), 400

        try:
            self._service.atualizar(id, **self._extrair_payload(dados))
        except NaoEncontrado as erro:
            return jsonify({"erro": erro.mensagem}), 404
        except EntradaInvalida as erro:
            return jsonify({"erro": erro.mensagem}), 400

        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, id):
        try:
            self._service.deletar(id)
        except NaoEncontrado as erro:
            return jsonify({"erro": erro.mensagem}), 404
        except Conflito as erro:
            return jsonify({"erro": erro.mensagem, "sucesso": False}), 409
        self._log.info("produto_deletado", produto_id=id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
