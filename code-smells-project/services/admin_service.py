class AdminService:
    """Operações administrativas e diagnóstico de liveness/readiness."""

    VERSAO = "1.0.0"

    def __init__(self, db, admin_repository, produto_repository, usuario_repository,
                 pedido_repository, logger):
        self._db = db
        self._admin = admin_repository
        self._produtos = produto_repository
        self._usuarios = usuario_repository
        self._pedidos = pedido_repository
        self._log = logger

    def resetar_banco(self):
        with self._db.transaction() as conn:
            tabelas = self._admin.apagar_todas_as_tabelas(conn)
        self._log.warning("banco_resetado", resultado="todas_as_tabelas_apagadas")
        return tabelas

    def health(self):
        """Liveness + readiness. Nenhum valor de configuração atravessa a fronteira (BC-2)."""
        with self._db.connection() as conn:
            conn.execute("SELECT 1")
            contagens = {
                "produtos": self._produtos.contar(conn),
                "usuarios": self._usuarios.contar(conn),
                "pedidos": self._pedidos.contar(conn),
            }
        return contagens, self.VERSAO
