from models import produto as modelo_produto


class ProdutoRepository:
    """Acesso a dados de produto. Toda consulta usa parâmetros vinculados (TR-02)."""

    def listar(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos")
        return [modelo_produto.de_registro(row) for row in cursor.fetchall()]

    def buscar_por_id(self, conn, produto_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        row = cursor.fetchone()
        return modelo_produto.de_registro(row) if row else None

    def inserir(self, conn, nome, descricao, preco, estoque, categoria):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        return cursor.lastrowid

    def atualizar(self, conn, produto_id, nome, descricao, preco, estoque, categoria):
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, "
            "categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        return cursor.rowcount

    def deletar(self, conn, produto_id):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        return cursor.rowcount

    def buscar(self, conn, termo=None, categoria=None, preco_min=None, preco_max=None):
        query = "SELECT * FROM produtos WHERE 1=1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            params.extend(["%" + termo + "%", "%" + termo + "%"])
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max is not None:
            query += " AND preco <= ?"
            params.append(preco_max)

        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        return [modelo_produto.de_registro(row) for row in cursor.fetchall()]

    def contar(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM produtos")
        return cursor.fetchone()[0]

    def baixar_estoque_se_disponivel(self, conn, produto_id, quantidade):
        """Consumação atômica: o UPDATE condicional devolve 0 quando não havia estoque."""
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
            (quantidade, produto_id, quantidade),
        )
        return cursor.rowcount
