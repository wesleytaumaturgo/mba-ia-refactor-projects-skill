"""Autenticação e autorização por papel, com política **negar por padrão**.

A rota declara que é pública; a ausência de declaração não libera. O registro de políticas
é a lista completa dos endpoints do projeto — um endpoint novo que ninguém declarar é
recusado, que é o comportamento desejado.

A decisão de autorização consulta o papel que o schema já modelava (`usuarios.tipo`) e que,
antes de TR-05, nenhuma decisão lia (finding F-002).
"""

from flask import g, jsonify, request

from security.tokens import TokenExpirado, TokenInvalido, verificar

PUBLICA = "publica"
AUTENTICADA = "autenticada"
ADMIN = "admin"


class PoliticaDeAcesso:
    """Mapa endpoint → nível exigido, consultado antes de cada requisição."""

    def __init__(self, settings, politicas):
        self._settings = settings
        self._politicas = dict(politicas)

    def nivel_de(self, endpoint):
        return self._politicas.get(endpoint)

    def _credencial_da_requisicao(self):
        cabecalho = request.headers.get("Authorization", "")
        if not cabecalho.startswith("Bearer "):
            return None
        return cabecalho[len("Bearer "):].strip()

    def aplicar(self):
        """before_request: devolve resposta de recusa, ou None para seguir ao handler."""
        endpoint = request.endpoint

        # Requisição a rota inexistente e preflight de origem cruzada seguem para o Flask.
        if endpoint is None or request.method == "OPTIONS":
            return None

        nivel = self.nivel_de(endpoint)

        if nivel is None:
            # Negar por padrão: endpoint sem política declarada não é liberado.
            return jsonify({
                "erro": "Endpoint sem política de acesso declarada",
                "sucesso": False
            }), 403

        if nivel == PUBLICA:
            return None

        token = self._credencial_da_requisicao()
        if not token:
            return jsonify({"erro": "Credencial ausente", "sucesso": False}), 401

        try:
            payload = verificar(self._settings.secret_key, token)
        except TokenExpirado:
            return jsonify({"erro": "Credencial expirada", "sucesso": False}), 401
        except TokenInvalido:
            return jsonify({"erro": "Credencial inválida", "sucesso": False}), 401

        g.usuario_id = payload["sub"]
        g.usuario_papel = payload.get("role")

        if nivel == ADMIN and g.usuario_papel != ADMIN:
            return jsonify({"erro": "Permissão insuficiente", "sucesso": False}), 403

        return None


# Política por endpoint. O nome é o do registro da rota, não o do path.
#
# Os 10 endpoints ADMIN são exatamente os declarados em BC-4 no relatório aprovado.
# `criar_pedido`, `criar_usuario` e `login` permanecem públicos porque o finding F-002 não
# os listou — alterar isso seria executar um plano diferente do aprovado no gate.
POLITICAS_PADRAO = {
    "sistema.index": PUBLICA,
    "sistema.health_check": PUBLICA,
    "produtos.listar_produtos": PUBLICA,
    "produtos.buscar_produtos": PUBLICA,
    "produtos.buscar_produto": PUBLICA,
    "usuarios.criar_usuario": PUBLICA,
    "auth.login": PUBLICA,
    "pedidos.criar_pedido": PUBLICA,

    "produtos.criar_produto": ADMIN,
    "produtos.atualizar_produto": ADMIN,
    "produtos.deletar_produto": ADMIN,
    "usuarios.listar_usuarios": ADMIN,
    "usuarios.buscar_usuario": ADMIN,
    "pedidos.listar_todos_pedidos": ADMIN,
    "pedidos.listar_pedidos_usuario": AUTENTICADA,
    "pedidos.atualizar_status_pedido": ADMIN,
    "relatorios.relatorio_vendas": ADMIN,
    "admin.reset_database": ADMIN,
}
