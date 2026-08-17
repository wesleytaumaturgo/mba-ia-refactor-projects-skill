"""Tratador de erro centralizado, com envelope único.

Substitui os 17 blocos `except Exception as e: return jsonify({"erro": str(e)}), 500`
(findings F-015 e F-017). Três mudanças de comportamento, todas declaradas em BC-7 e BC-8:

- o envelope passa a ser um só, com **código estável**, em todos os caminhos de erro;
- a representação textual da exceção **não** atravessa mais a fronteira — o cliente recebe
  um identificador de correlação, e o detalhe completo vai para o log;
- o que estava colapsado se separa: inexistente é 404, entrada inválida é 4xx, defeito é 5xx.
"""

import uuid

from flask import jsonify

from services.errors import (
    Conflito,
    CredencialInvalida,
    DomainError,
    EntradaInvalida,
    LimiteDeTaxaExcedido,
    NaoEncontrado,
    RegraDeNegocioViolada,
)

STATUS_POR_ERRO = {
    NaoEncontrado: 404,
    EntradaInvalida: 400,
    RegraDeNegocioViolada: 400,
    Conflito: 409,
    CredencialInvalida: 401,
    LimiteDeTaxaExcedido: 429,
}

CODIGO_DEFEITO_INTERNO = "erro_interno"
MENSAGEM_DEFEITO_INTERNO = "Erro interno. Use o identificador de correlação ao reportar."


def envelope(codigo, mensagem, correlation_id):
    return {"error": {"code": codigo, "message": mensagem, "correlation_id": correlation_id}}


def registrar(app, logger):
    @app.errorhandler(DomainError)
    def _erro_de_dominio(erro):
        correlation_id = str(uuid.uuid4())
        status = STATUS_POR_ERRO.get(type(erro), 400)
        logger.warning(
            "erro_de_dominio",
            erro_tipo=type(erro).__name__,
            status_code=status,
            correlation_id=correlation_id,
        )
        return jsonify(envelope(erro.codigo, erro.mensagem, correlation_id)), status

    @app.errorhandler(404)
    def _rota_inexistente(_erro):
        correlation_id = str(uuid.uuid4())
        return jsonify(envelope("rota_inexistente", "Recurso não encontrado", correlation_id)), 404

    @app.errorhandler(405)
    def _metodo_nao_permitido(_erro):
        correlation_id = str(uuid.uuid4())
        return jsonify(envelope("metodo_nao_permitido", "Método não permitido", correlation_id)), 405

    @app.errorhandler(Exception)
    def _defeito(erro):
        """Defeito inesperado: registra o erro completo, devolve apenas o identificador."""
        correlation_id = str(uuid.uuid4())
        logger.exception(
            "defeito_nao_tratado",
            erro_tipo=type(erro).__name__,
            status_code=500,
            correlation_id=correlation_id,
        )
        return jsonify(
            envelope(CODIGO_DEFEITO_INTERNO, MENSAGEM_DEFEITO_INTERNO, correlation_id)
        ), 500

    return app


def resposta_de_erro(codigo, mensagem, status):
    """Envelope único para recusas emitidas fora do fluxo de exceção (middlewares)."""
    return jsonify(envelope(codigo, mensagem, str(uuid.uuid4()))), status
