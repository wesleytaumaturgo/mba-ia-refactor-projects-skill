class PoliticaDeDesconto:
    """Política comercial de desconto por faixa de faturamento.

    Estava dentro de `models.relatorio_vendas`, misturada às agregações de consulta
    (finding F-010). Aqui é um objeto de domínio puro: exercitável sem banco.
    """

    # Faixas em ordem decrescente: (piso de faturamento, alíquota).
    FAIXAS = (
        (10000, 0.10),
        (5000, 0.05),
        (1000, 0.02),
    )

    def aplicar(self, faturamento):
        for piso, aliquota in self.FAIXAS:
            if faturamento > piso:
                return faturamento * aliquota
        return 0


class RelatorioService:
    def __init__(self, db, pedido_repository, politica_de_desconto):
        self._db = db
        self._repo = pedido_repository
        self._desconto = politica_de_desconto

    def vendas(self):
        with self._db.connection() as conn:
            agregados = self._repo.agregados_de_vendas(conn)

        total_pedidos = agregados["total_pedidos"]
        faturamento = agregados["faturamento"]
        desconto = self._desconto.aplicar(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": agregados["por_status"]["pendente"],
            "pedidos_aprovados": agregados["por_status"]["aprovado"],
            "pedidos_cancelados": agregados["por_status"]["cancelado"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
