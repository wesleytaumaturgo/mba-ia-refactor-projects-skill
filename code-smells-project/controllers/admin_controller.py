from flask import jsonify

from dto.serializers import health_dto


class AdminController:
    """Rotas de infraestrutura e administração — fora dos controllers de domínio (§7)."""

    def __init__(self, admin_service):
        self._service = admin_service

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }), 200

    def health(self):
        contagens, versao = self._service.health()
        return jsonify(health_dto(contagens, versao)), 200

    def resetar_banco(self):
        self._service.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
