"""Erros de domínio.

O service sinaliza o resultado com **tipo**, nunca com a forma do retorno. Um `None`
que significa "não encontrado" obrigaria o controller a decidir regra de domínio —
que é exatamente o AP-08 que TR-07 remove.

Nenhum símbolo de protocolo aqui: a tradução para status HTTP é do controller.
"""


class DomainError(Exception):
    code = 'domain_error'

    def __init__(self, message, code=None, field=None):
        super().__init__(message)
        self.message = message
        self.field = field
        if code:
            self.code = code


class NotFound(DomainError):
    code = 'not_found'


class ValidationError(DomainError):
    code = 'validation_error'


class Conflict(DomainError):
    code = 'conflict'


class PermissionDenied(DomainError):
    code = 'permission_denied'
