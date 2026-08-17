from models import pedido as modelo_pedido


class PedidoRepository:
    """Acesso a dados de pedido e itens.

    O laço de consultas aninhadas foi movido para cá tal como estava: colapsá-lo é
    trabalho de TR-11 (finding F-019, Onda 3), não deste TR.
    """

    def _carregar_itens(self, conn, pedido_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido_id,))
        itens = []
        for item in cursor.fetchall():
            cursor_nome = conn.cursor()
            cursor_nome.execute(
                "SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],)
            )
            prod = cursor_nome.fetchone()
            itens.append(
                modelo_pedido.item_de_registro(
                    item, prod["nome"] if prod else "Desconhecido"
                )
            )
        return itens

    def listar(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos")
        pedidos = []
        for row in cursor.fetchall():
            pedido = modelo_pedido.de_registro(row)
            pedido["itens"] = self._carregar_itens(conn, row["id"])
            pedidos.append(pedido)
        return pedidos

    def listar_por_usuario(self, conn, usuario_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
        pedidos = []
        for row in cursor.fetchall():
            pedido = modelo_pedido.de_registro(row)
            pedido["itens"] = self._carregar_itens(conn, row["id"])
            pedidos.append(pedido)
        return pedidos

    def buscar_por_id(self, conn, pedido_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
        row = cursor.fetchone()
        return modelo_pedido.de_registro(row) if row else None

    def inserir(self, conn, usuario_id, status, total):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, status, total),
        )
        return cursor.lastrowid

    def inserir_item(self, conn, pedido_id, produto_id, quantidade, preco_unitario):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
            "VALUES (?, ?, ?, ?)",
            (pedido_id, produto_id, quantidade, preco_unitario),
        )
        return cursor.lastrowid

    def atualizar_status(self, conn, pedido_id, novo_status):
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
        )
        return cursor.rowcount

    def contar(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        return cursor.fetchone()[0]

    def agregados_de_vendas(self, conn):
        """Agrega no banco e devolve números crus. Nenhuma regra de negócio aqui."""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        total_pedidos = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total) FROM pedidos")
        faturamento = cursor.fetchone()[0] or 0

        contagens = {}
        for status in ("pendente", "aprovado", "cancelado"):
            cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", (status,))
            contagens[status] = cursor.fetchone()[0]

        return {
            "total_pedidos": total_pedidos,
            "faturamento": faturamento,
            "por_status": contagens,
        }
