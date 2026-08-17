"""Entidade Pedido: forma dos dados e vocabulário de status."""

CAMPOS = ("id", "usuario_id", "status", "total", "criado_em")
CAMPOS_ITEM = ("produto_id", "produto_nome", "quantidade", "preco_unitario")

STATUS_INICIAL = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")

QUANTIDADE_MINIMA_POR_ITEM = 1
ITENS_MINIMOS_POR_PEDIDO = 1


def de_registro(row):
    pedido = {campo: row[campo] for campo in CAMPOS}
    pedido["itens"] = []
    return pedido


def item_de_registro(row, produto_nome):
    return {
        "produto_id": row["produto_id"],
        "produto_nome": produto_nome,
        "quantidade": row["quantidade"],
        "preco_unitario": row["preco_unitario"],
    }
