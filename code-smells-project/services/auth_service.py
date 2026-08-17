from services.errors import CredencialInvalida, EntradaInvalida, LimiteDeTaxaExcedido


class AuthService:
    """Autenticação: verifica a credencial, reidrata o formato legado e emite o token.

    A regra vale com ou sem HTTP — o limitador de taxa recebe a chave já montada pelo
    controller, e não o objeto de requisição.
    """

    def __init__(self, db, usuario_repository, password_hasher, emissor_de_token, settings, limitador, logger):
        self._db = db
        self._repo = usuario_repository
        self._hasher = password_hasher
        self._emitir = emissor_de_token
        self._settings = settings
        self._limitador = limitador
        self._log = logger

    def autenticar(self, email, senha, chave_de_taxa):
        if not email or not senha:
            raise EntradaInvalida("Email e senha são obrigatórios")

        permitido, liberar_em = self._limitador.registrar_e_verificar(chave_de_taxa)
        if not permitido:
            self._log.warning(
                "login_bloqueado",
                limite=self._settings.login_rate_limit,
                janela_segundos=self._settings.login_rate_window_seconds,
            )
            raise LimiteDeTaxaExcedido(
                "Muitas tentativas de autenticação. Tente novamente em " + str(liberar_em) + "s"
            )

        with self._db.connection() as conn:
            usuario = self._repo.buscar_por_email(conn, email)

        if usuario is None or not self._hasher.verify_password(usuario["senha"], senha):
            self._log.warning("login_falhou", resultado="credencial_invalida")
            raise CredencialInvalida("Email ou senha inválidos")

        if self._hasher.is_legacy(usuario["senha"]):
            with self._db.transaction() as conn:
                self._repo.atualizar_credencial(
                    conn, usuario["id"], self._hasher.hash_password(senha)
                )

        self._limitador.limpar(chave_de_taxa)
        self._log.info("login_sucesso", usuario_id=usuario["id"])

        token = self._emitir(
            self._settings.secret_key,
            usuario["id"],
            usuario["tipo"],
            self._settings.token_ttl_seconds,
        )
        return {
            "token": token,
            "token_type": "Bearer",
            "expira_em": self._settings.token_ttl_seconds,
            "usuario": {"id": usuario["id"], "tipo": usuario["tipo"]},
        }
