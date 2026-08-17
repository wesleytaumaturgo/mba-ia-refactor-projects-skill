"""Entidade Produto: forma dos dados e invariantes válidas em qualquer caso de uso."""

CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")

NOME_TAMANHO_MINIMO = 2
NOME_TAMANHO_MAXIMO = 200
CATEGORIA_PADRAO = "geral"
CATEGORIAS_VALIDAS = (
    "informatica", "moveis", "vestuario", "geral", "eletronicos", "livros",
)


def de_registro(row):
    """Mapeia uma linha da persistência para a forma canônica da entidade.

    Único lugar do projeto que conhece essa correspondência — antes ela estava copiada
    em três funções de `models.py` (findings AM-016 / F-019 do relatório).
    """
    return {campo: row[campo] for campo in CAMPOS}
