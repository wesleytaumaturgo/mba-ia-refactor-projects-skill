from models import pedido as modelo_pedido
from validators.schema import Campo, Schema

ITEM = Schema(
    Campo("produto_id", int, rotulo="Produto ID"),
    Campo("quantidade", int, rotulo="Quantidade",
          minimo=modelo_pedido.QUANTIDADE_MINIMA_POR_ITEM,
          mensagem_minimo="Quantidade deve ser pelo menos 1"),
)

STATUS = Schema(
    Campo("status", str, rotulo="Status", escolhas=modelo_pedido.STATUS_VALIDOS),
)
