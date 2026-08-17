from models import pedido as modelo_pedido


class NotificacaoService:
    """Efeito colateral de negócio, atrás de dependência injetada.

    Antes de TR-07 as notificações eram três `print` dentro do handler HTTP (F-010):
    nenhum outro gatilho — job, importação em lote — as disparava.
    """

    CANAIS = ("email", "sms", "push")

    def __init__(self, logger):
        self._log = logger

    def pedido_criado(self, pedido_id, usuario_id):
        for canal in self.CANAIS:
            self._log.info(
                "notificacao_enviada", canal=canal, pedido_id=pedido_id, usuario_id=usuario_id
            )

    def pedido_mudou_de_status(self, pedido_id, novo_status):
        if novo_status == modelo_pedido.STATUS_APROVADO:
            self._log.info("pedido_aprovado", pedido_id=pedido_id, status=novo_status)
        if novo_status == modelo_pedido.STATUS_CANCELADO:
            self._log.info("pedido_cancelado", pedido_id=pedido_id, status=novo_status)
