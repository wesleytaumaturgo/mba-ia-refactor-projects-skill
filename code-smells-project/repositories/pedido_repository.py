from models import pedido as modelo_pedido


class PedidoRepository:
    """Acesso a dados de pedido e itens.

    O laço de consultas aninhadas foi movido para cá tal como estava: colapsá-lo é
    trabalho de TR-11 (finding F-019, Onda 3), não deste TR.
    """

    def _itens_em_lote(self, conn, pedido_ids, cursor):
        """Carrega os itens de TODOS os pedidos da página numa única ida ao banco.

        Substitui o laço aninhado que disparava `1 + P + Σitens` consultas (finding F-019).
        O `IN` recebe um placeholder por chave — os valores continuam vinculados, e a
        quantidade de marcadores vem do tamanho da lista interna, não de entrada externa.
        """
        if not pedido_ids:
            return {}

        marcadores = ",".join(["?"] * len(pedido_ids))
        cursor.execute(
            "SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, "
            "       p.nome AS produto_nome "
            "FROM itens_pedido i "
            "LEFT JOIN produtos p ON p.id = i.produto_id "
            "WHERE i.pedido_id IN (" + marcadores + ") "
            "ORDER BY i.id",
            tuple(pedido_ids),
        )

        agrupado = {}
        for row in cursor.fetchall():
            agrupado.setdefault(row["pedido_id"], []).append(
                modelo_pedido.item_de_registro(row, row["produto_nome"] or "Desconhecido")
            )
        return agrupado

    def _montar(self, conn, linhas, cursor):
        pedidos = [modelo_pedido.de_registro(row) for row in linhas]
        itens = self._itens_em_lote(conn, [p["id"] for p in pedidos], cursor)
        for pedido in pedidos:
            pedido["itens"] = itens.get(pedido["id"], [])
        return pedidos

    def listar(self, conn, limite, offset):
        # Um cursor por chamada, não um por iteração.
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM pedidos ORDER BY id LIMIT ? OFFSET ?", (limite, offset)
        )
        return self._montar(conn, cursor.fetchall(), cursor)

    def listar_por_usuario(self, conn, usuario_id, limite, offset):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY id LIMIT ? OFFSET ?",
            (usuario_id, limite, offset),
        )
        return self._montar(conn, cursor.fetchall(), cursor)

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

    def contar(self, conn, usuario_id=None):
        cursor = conn.cursor()
        if usuario_id is None:
            cursor.execute("SELECT COUNT(*) FROM pedidos")
        else:
            cursor.execute("SELECT COUNT(*) FROM pedidos WHERE usuario_id = ?", (usuario_id,))
        return cursor.fetchone()[0]

    def agregados_de_vendas(self, conn):
        """Agrega no banco e devolve números crus. Nenhuma regra de negócio aqui."""
        # Cinco consultas de agregação sobre a mesma tabela viraram uma
        # (variante correlata de F-019).
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS total_pedidos, "
            "       COALESCE(SUM(total), 0) AS faturamento, "
            "       SUM(CASE WHEN status = 'pendente'  THEN 1 ELSE 0 END) AS pendente, "
            "       SUM(CASE WHEN status = 'aprovado'  THEN 1 ELSE 0 END) AS aprovado, "
            "       SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelado "
            "FROM pedidos"
        )
        linha = cursor.fetchone()
        total_pedidos = linha["total_pedidos"]
        faturamento = linha["faturamento"] or 0
        contagens = {
            "pendente": linha["pendente"] or 0,
            "aprovado": linha["aprovado"] or 0,
            "cancelado": linha["cancelado"] or 0,
        }

        return {
            "total_pedidos": total_pedidos,
            "faturamento": faturamento,
            "por_status": contagens,
        }
