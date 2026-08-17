import sqlite3

from models import produto as modelo_produto
from services.errors import Conflito, EntradaInvalida, NaoEncontrado


class ProdutoService:
    """Regra de negócio de produto. Recebe o repositório e a fonte de conexão por parâmetro."""

    def __init__(self, db, produto_repository):
        self._db = db
        self._repo = produto_repository

    # ---- leitura ----

    def listar(self):
        with self._db.connection() as conn:
            return self._repo.listar(conn)

    def buscar_por_id(self, produto_id):
        with self._db.connection() as conn:
            produto = self._repo.buscar_por_id(conn, produto_id)
        if produto is None:
            raise NaoEncontrado("Produto não encontrado")
        return produto

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        with self._db.connection() as conn:
            return self._repo.buscar(conn, termo, categoria, preco_min, preco_max)

    # ---- escrita ----

    def _com_defaults_de_dominio(self, categoria):
        return categoria if categoria else modelo_produto.CATEGORIA_PADRAO

    def _validar(self, nome, preco, estoque, categoria):
        if preco < 0:
            raise EntradaInvalida("Preço não pode ser negativo")
        if estoque < 0:
            raise EntradaInvalida("Estoque não pode ser negativo")
        if len(nome) < modelo_produto.NOME_TAMANHO_MINIMO:
            raise EntradaInvalida("Nome muito curto")
        if len(nome) > modelo_produto.NOME_TAMANHO_MAXIMO:
            raise EntradaInvalida("Nome muito longo")
        if categoria not in modelo_produto.CATEGORIAS_VALIDAS:
            raise EntradaInvalida(
                "Categoria inválida. Válidas: " + str(list(modelo_produto.CATEGORIAS_VALIDAS))
            )

    def criar(self, nome, descricao, preco, estoque, categoria):
        categoria = self._com_defaults_de_dominio(categoria)
        self._validar(nome, preco, estoque, categoria)
        with self._db.transaction() as conn:
            return self._repo.inserir(conn, nome, descricao, preco, estoque, categoria)

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        with self._db.connection() as conn:
            if self._repo.buscar_por_id(conn, produto_id) is None:
                raise NaoEncontrado("Produto não encontrado")
        categoria = self._com_defaults_de_dominio(categoria)
        self._validar(nome, preco, estoque, categoria)
        with self._db.transaction() as conn:
            self._repo.atualizar(conn, produto_id, nome, descricao, preco, estoque, categoria)
        return True

    def deletar(self, produto_id):
        with self._db.connection() as conn:
            if self._repo.buscar_por_id(conn, produto_id) is None:
                raise NaoEncontrado("Produto não encontrado")
        try:
            with self._db.transaction() as conn:
                self._repo.deletar(conn, produto_id)
        except sqlite3.IntegrityError:
            # A chave estrangeira de TR-16 impede a deleção que deixava itens_pedido órfãos
            # (finding F-012). Antes, o produto sumia e o item ficava apontando para o nada.
            raise Conflito("Produto referenciado por pedidos existentes")
        return True
