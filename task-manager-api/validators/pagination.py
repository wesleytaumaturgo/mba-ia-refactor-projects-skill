"""Validação dos parâmetros de paginação, no validador — não em condicional no handler.

O teto é o que impede o cliente de reintroduzir o problema pedindo `limit` arbitrário.
A cláusula é aplicada na consulta do repositório, nunca fatiando em memória.
"""
from services.errors import ValidationError
from validators.base import optional_int


class Pagination:
    def __init__(self, default_size, max_size):
        self.default_size = default_size
        self.max_size = max_size

    def from_request(self, args):
        """Devolve (limit, offset) já coagidos, com default e teto aplicados."""
        limit = optional_int(args.get('limit'), 'limit')
        offset = optional_int(args.get('offset'), 'offset')

        if limit is None:
            limit = self.default_size
        elif limit < 1:
            raise ValidationError('limit deve ser maior que zero', field='limit')
        else:
            limit = min(limit, self.max_size)

        if offset is None:
            offset = 0
        elif offset < 0:
            raise ValidationError('offset não pode ser negativo', field='offset')

        return limit, offset
