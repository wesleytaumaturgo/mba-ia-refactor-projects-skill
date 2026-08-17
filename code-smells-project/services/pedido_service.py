import sqlite3

from models import pedido as modelo_pedido
from services.errors import EntradaInvalida, NaoEncontrado, RegraDeNegocioViolada
from services.paginacao import pagina
from validators.pedido_validator import ITEM, STATUS


class PedidoService:
    """Regra de negócio do pedido e orquestração dos efeitos colaterais.

    A notificação vem por dependência injetada, não por chamada direta a um cliente
    concreto: qualquer gatilho que crie pedido — job, importação em lote — passa por aqui
    e notifica, o que não acontecia quando as três linhas viviam no handler HTTP.
    """

    def __init__(self, db, pedido_repository, produto_repository, notificacao_service,
                 settings):
        self._db = db
        self._repo = pedido_repository
        self._produtos = produto_repository
        self._notificacao = notificacao_service
        self._settings = settings

    def listar(self, limite=None, offset=None):
        with self._db.connection() as conn:
            return pagina(
                self._settings, limite, offset,
                lambda lim, off: self._repo.listar(conn, lim, off),
                lambda: self._repo.contar(conn),
            )

    def listar_por_usuario(self, usuario_id, limite=None, offset=None):
        with self._db.connection() as conn:
            return pagina(
                self._settings, limite, offset,
                lambda lim, off: self._repo.listar_por_usuario(conn, usuario_id, lim, off),
                lambda: self._repo.contar(conn, usuario_id),
            )

    def criar(self, usuario_id, itens):
        if not usuario_id:
            raise EntradaInvalida("Usuario ID é obrigatório")
        if not itens or len(itens) < modelo_pedido.ITENS_MINIMOS_POR_PEDIDO:
            raise EntradaInvalida("Pedido deve ter pelo menos 1 item")
        itens = [ITEM.validate(item) for item in itens]

        # Uma única unidade de trabalho cobre a leitura dos produtos, a criação do pedido,
        # a inserção dos itens e a baixa de estoque. Qualquer erro desfaz tudo — antes,
        # o retorno antecipado no meio da sequência deixava estado parcial (finding F-012).
        try:
            pedido_id, total = self._gravar(usuario_id, itens)
        except sqlite3.IntegrityError:
            # A FK de TR-16 recusa pedido de usuário inexistente. Sem esta tradução o
            # erro subiria como defeito e viraria 500 — que é o colapso que o passo 4 de
            # TR-13 existe para desfazer.
            raise NaoEncontrado("Usuário " + str(usuario_id) + " não encontrado")

        self._notificacao.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def _gravar(self, usuario_id, itens):
        with self._db.transaction() as conn:
            total = 0
            linhas = []
            for item in itens:
                produto = self._produtos.buscar_por_id(conn, item["produto_id"])
                if produto is None:
                    raise NaoEncontrado(
                        "Produto " + str(item["produto_id"]) + " não encontrado"
                    )
                linhas.append((produto, item))
                total += produto["preco"] * item["quantidade"]

            pedido_id = self._repo.inserir(
                conn, usuario_id, modelo_pedido.STATUS_INICIAL, total
            )

            for produto, item in linhas:
                self._repo.inserir_item(
                    conn, pedido_id, produto["id"], item["quantidade"], produto["preco"]
                )
                # Consumação atômica: o UPDATE condicional afeta 0 linhas quando o estoque
                # já não cobre a quantidade. Substitui o par check-then-act, em que dois
                # pedidos concorrentes do último item passavam ambos na verificação.
                if self._produtos.baixar_estoque_se_disponivel(
                    conn, produto["id"], item["quantidade"]
                ) == 0:
                    raise RegraDeNegocioViolada(
                        "Estoque insuficiente para " + produto["nome"]
                    )

        return pedido_id, total

    def atualizar_status(self, pedido_id, novo_status):
        novo_status = STATUS.validate({"status": novo_status})["status"]

        with self._db.transaction() as conn:
            self._repo.atualizar_status(conn, pedido_id, novo_status)

        self._notificacao.pedido_mudou_de_status(pedido_id, novo_status)
        return True
