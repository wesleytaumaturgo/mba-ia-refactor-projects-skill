"""Tratador de erro centralizado, na fronteira do processo, com envelope único.

Um idioma só: `{"error": {"code", "message", "correlation_id"}}`. O service sinaliza
por **tipo**; este é o único lugar que decide o status. Nenhum handler captura
exceção genericamente, e nenhuma resposta carrega texto de exceção ou caminho de
arquivo — o defeito vai para o log, o cliente recebe o identificador de correlação.
"""
import logging
import uuid

from flask import g, jsonify, request
from werkzeug.exceptions import HTTPException

from services.errors import (Conflict, DomainError, NotFound, PermissionDenied,
                             ValidationError)

logger = logging.getLogger('task_manager.errors')

STATUS_BY_TYPE = (
    (ValidationError, 400),
    (NotFound, 404),
    (Conflict, 409),
    (PermissionDenied, 403),
)

# Alguns erros de autenticação têm status próprio, distinto do de autorização.
STATUS_BY_CODE = {
    'invalid_credentials': 401,
    'inactive_user': 403,
}

CODE_BY_STATUS = {
    400: 'bad_request', 401: 'unauthorized', 403: 'forbidden', 404: 'not_found',
    405: 'method_not_allowed', 409: 'conflict', 429: 'too_many_requests',
    500: 'internal_error',
}


def correlation_id():
    if not hasattr(g, 'correlation_id'):
        g.correlation_id = uuid.uuid4().hex[:12]
    return g.correlation_id


def status_for(error):
    if error.code in STATUS_BY_CODE:
        return STATUS_BY_CODE[error.code]
    for error_type, status in STATUS_BY_TYPE:
        if isinstance(error, error_type):
            return status
    return 400


def envelope(code, message, extra=None):
    body = {'error': {'code': code, 'message': message,
                      'correlation_id': correlation_id()}}
    if extra:
        body['error'].update(extra)
    return body


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def handle_domain_error(error):
        """Falha de domínio: esperada, 4xx, sem stack trace no log."""
        status = status_for(error)
        logger.warning('domain_error code=%s status=%s path=%s cid=%s',
                       error.code, status, request.path, correlation_id())
        extra = {'field': error.field} if error.field else None
        return jsonify(envelope(error.code, error.message, extra)), status

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Erro de protocolo (404 de rota, 405 de método): mesmo envelope."""
        code = CODE_BY_STATUS.get(error.code, 'http_error')
        return jsonify(envelope(code, error.description)), error.code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        """Defeito: 5xx. O erro completo vai para o log; o cliente recebe só o cid."""
        cid = correlation_id()
        logger.exception('unhandled_error path=%s cid=%s', request.path, cid)
        return jsonify(envelope('internal_error',
                                'Erro interno. Cite o correlation_id ao reportar.')), 500

    return app
