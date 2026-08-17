"""Tradução centralizada de erro de domínio → status HTTP.

O service sinaliza por **tipo**; este é o único lugar que decide o status. Nenhum
controller inspeciona a forma do valor retornado para escolher o código.
"""
from services.errors import (Conflict, DomainError, NotFound, PermissionDenied,
                             ValidationError)

STATUS_BY_TYPE = {
    ValidationError: 400,
    NotFound: 404,
    Conflict: 409,
    PermissionDenied: 403,
}

# Alguns erros de autenticação têm status próprio, distinto do de autorização.
STATUS_BY_CODE = {
    'invalid_credentials': 401,
    'inactive_user': 403,
}


def status_for(error):
    if error.code in STATUS_BY_CODE:
        return STATUS_BY_CODE[error.code]
    for error_type, status in STATUS_BY_TYPE.items():
        if isinstance(error, error_type):
            return status
    return 400


def register_error_handlers(app):
    from flask import jsonify

    @app.errorhandler(DomainError)
    def handle_domain_error(error):
        return jsonify({'error': error.message}), status_for(error)

    return app
