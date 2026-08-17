from flask import jsonify, request

from dto.serializers import usuario_dto, usuarios_dto
from services.errors import (
    Conflito,
    CredencialInvalida,
    EntradaInvalida,
    LimiteDeTaxaExcedido,
    NaoEncontrado,
)


class UsuarioController:
    def __init__(self, usuario_service, auth_service, logger):
        self._service = usuario_service
        self._auth = auth_service
        self._log = logger

    def listar(self):
        usuarios = self._service.listar()
        return jsonify({"dados": usuarios_dto(usuarios), "sucesso": True}), 200

    def buscar(self, id):
        try:
            usuario = self._service.buscar_por_id(id)
        except NaoEncontrado as erro:
            return jsonify({"erro": erro.mensagem}), 404
        return jsonify({"dados": usuario_dto(usuario), "sucesso": True}), 200

    def criar(self):
        dados = request.get_json(silent=True)
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        try:
            usuario_id = self._service.criar(
                dados.get("nome", ""), dados.get("email", ""), dados.get("senha", "")
            )
        except EntradaInvalida as erro:
            return jsonify({"erro": erro.mensagem}), 400
        except Conflito as erro:
            return jsonify({"erro": erro.mensagem, "sucesso": False}), 409

        self._log.info("usuario_criado", usuario_id=usuario_id)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        dados = request.get_json(silent=True) or {}
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        chave = (email or "").lower() + "|" + (request.remote_addr or "-")

        try:
            sessao = self._auth.autenticar(email, senha, chave)
        except EntradaInvalida as erro:
            return jsonify({"erro": erro.mensagem}), 400
        except LimiteDeTaxaExcedido as erro:
            return jsonify({"erro": erro.mensagem, "sucesso": False}), 429
        except CredencialInvalida as erro:
            return jsonify({"erro": erro.mensagem, "sucesso": False}), 401

        return jsonify({"dados": sessao, "sucesso": True, "mensagem": "Login OK"}), 200
