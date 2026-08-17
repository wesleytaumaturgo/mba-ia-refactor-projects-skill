from flask import jsonify, request

from dto.serializers import usuario_dto, usuarios_dto
from services.errors import EntradaInvalida


class UsuarioController:
    def __init__(self, usuario_service, auth_service, logger):
        self._service = usuario_service
        self._auth = auth_service
        self._log = logger

    def listar(self):
        pag = self._service.listar(
            limite=request.args.get("limite", None),
            offset=request.args.get("offset", None),
        )
        return jsonify({
            "dados": usuarios_dto(pag["itens"]),
            "paginacao": pag["paginacao"],
            "sucesso": True,
        }), 200

    def buscar(self, usuario_id):
        usuario = self._service.buscar_por_id(usuario_id)
        return jsonify({"dados": usuario_dto(usuario), "sucesso": True}), 200

    def criar(self):
        usuario_id = self._service.criar(request.get_json(silent=True))
        self._log.info("usuario_criado", usuario_id=usuario_id)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            raise EntradaInvalida("Email e senha são obrigatórios")
        email = dados.get("email", "")
        chave = (email or "").lower() + "|" + (request.remote_addr or "-")
        sessao = self._auth.autenticar(email, dados.get("senha", ""), chave)
        return jsonify({"dados": sessao, "sucesso": True, "mensagem": "Login OK"}), 200
