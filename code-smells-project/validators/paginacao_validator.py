"""Validação dos parâmetros de página, com default explícito e teto máximo.

O teto é o que impede que o cliente reintroduza o problema que TR-17 corrige.
"""

from services.errors import EntradaInvalida


def normalizar(limite, offset, default, maximo):
    limite = _inteiro_nao_negativo(limite, "limite", default)
    offset = _inteiro_nao_negativo(offset, "offset", 0)
    return min(limite, maximo) if limite > 0 else default, offset


def _inteiro_nao_negativo(bruto, rotulo, default):
    if bruto is None or bruto == "":
        return default
    try:
        valor = int(bruto)
    except (TypeError, ValueError):
        raise EntradaInvalida("Parâmetro " + rotulo + " deve ser um número inteiro")
    if valor < 0:
        raise EntradaInvalida("Parâmetro " + rotulo + " não pode ser negativo")
    return valor
