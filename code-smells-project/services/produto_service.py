import sqlite3
from services.errors import Conflito, NaoEncontrado
from services.paginacao import pagina
from validators.produto_validator import PRODUTO


class ProdutoService:
    """Regra de negócio de produto. Recebe o repositório e a fonte de conexão por parâmetro."""

    def __init__(self, db, produto_repository, settings):
        self._db = db
        self._repo = produto_repository
        self._settings = settings

    # ---- leitura ----

    def listar(self, limite=None, offset=None):
        with self._db.connection() as conn:
            return pagina(
                self._settings, limite, offset,
                lambda lim, off: self._repo.listar(conn, lim, off),
                lambda: self._repo.contar(conn),
            )

    def buscar_por_id(self, produto_id):
        with self._db.connection() as conn:
            produto = self._repo.buscar_por_id(conn, produto_id)
        if produto is None:
            raise NaoEncontrado("Produto não encontrado")
        return produto

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None,
               limite=None, offset=None):
        with self._db.connection() as conn:
            return pagina(
                self._settings, limite, offset,
                lambda lim, off: self._repo.buscar(
                    conn, termo, categoria, preco_min, preco_max, lim, off),
                lambda: self._repo.buscar(
                    conn, termo, categoria, preco_min, preco_max, apenas_contagem=True),
            )

    # ---- escrita ----

    def criar(self, payload):
        dados = PRODUTO.validate(payload)
        with self._db.transaction() as conn:
            return self._repo.inserir(
                conn, dados["nome"], dados["descricao"], dados["preco"],
                dados["estoque"], dados["categoria"],
            )

    def atualizar(self, produto_id, payload):
        with self._db.connection() as conn:
            if self._repo.buscar_por_id(conn, produto_id) is None:
                raise NaoEncontrado("Produto não encontrado")
        # Mesmo schema da criação: a divergência de F-018 deixa de ser possível.
        dados = PRODUTO.validate(payload)
        with self._db.transaction() as conn:
            self._repo.atualizar(
                conn, produto_id, dados["nome"], dados["descricao"], dados["preco"],
                dados["estoque"], dados["categoria"],
            )
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
