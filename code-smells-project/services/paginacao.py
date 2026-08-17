"""Envelope de paginação, comum a todas as listagens."""

from validators.paginacao_validator import normalizar


def pagina(settings, limite, offset, carregar, contar):
    """Normaliza os parâmetros, carrega apenas a página e devolve itens + metadados."""
    limite, offset = normalizar(
        limite, offset, settings.page_size_default, settings.page_size_max
    )
    return {
        "itens": carregar(limite, offset),
        "paginacao": {"limite": limite, "offset": offset, "total": contar()},
    }
