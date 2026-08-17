class AdminRepository:
    """Operações administrativas que atravessam agregados."""

    # Allowlist fechada de identificadores de estrutura. Nome de tabela não é vinculável
    # como parâmetro pelo driver, então a allowlist é o que fecha o caminho (AP-01).
    TABELAS_DO_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")

    def apagar_todas_as_tabelas(self, conn):
        cursor = conn.cursor()
        for tabela in self.TABELAS_DO_RESET:
            cursor.execute("DELETE FROM " + tabela)
        return len(self.TABELAS_DO_RESET)
