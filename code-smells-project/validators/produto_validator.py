from models import produto as modelo_produto
from validators.schema import Campo, Schema

# Divergência resolvida explicitamente (TR-08 passo 2, breaking change BC-10):
# a criação validava tamanho de nome e vocabulário de categoria; a atualização não.
# **A regra da criação venceu** — é a mais restritiva e a que o schema de TR-16 declara
# como CHECK. O mesmo schema atende os dois casos de uso, então elas não podem divergir
# de novo.
PRODUTO = Schema(
    Campo("nome", str, rotulo="Nome",
          tamanho_min=modelo_produto.NOME_TAMANHO_MINIMO,
          tamanho_max=modelo_produto.NOME_TAMANHO_MAXIMO,
          mensagem_curto="Nome muito curto",
          mensagem_longo="Nome muito longo"),
    Campo("descricao", str, rotulo="Descrição", obrigatorio=False, default=""),
    Campo("preco", float, rotulo="Preço", minimo=0,
          mensagem_minimo="Preço não pode ser negativo"),
    Campo("estoque", int, rotulo="Estoque", minimo=0,
          mensagem_minimo="Estoque não pode ser negativo"),
    Campo("categoria", str, rotulo="Categoria",
          default=modelo_produto.CATEGORIA_PADRAO,
          escolhas=modelo_produto.CATEGORIAS_VALIDAS),
)
