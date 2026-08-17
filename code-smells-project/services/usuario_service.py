import sqlite3

from models import usuario as modelo_usuario
from services.errors import Conflito, NaoEncontrado
from services.paginacao import pagina
from validators.usuario_validator import USUARIO


class UsuarioService:
    def __init__(self, db, usuario_repository, password_hasher, settings):
        self._db = db
        self._repo = usuario_repository
        self._hasher = password_hasher
        self._settings = settings

    def listar(self, limite=None, offset=None):
        with self._db.connection() as conn:
            return pagina(
                self._settings, limite, offset,
                lambda lim, off: self._repo.listar(conn, lim, off),
                lambda: self._repo.contar(conn),
            )

    def buscar_por_id(self, usuario_id):
        with self._db.connection() as conn:
            usuario = self._repo.buscar_por_id(conn, usuario_id)
        if usuario is None:
            raise NaoEncontrado("Usuário não encontrado")
        return usuario

    def criar(self, payload):
        dados = USUARIO.validate(payload)
        nome, email, senha = dados["nome"], dados["email"], dados["senha"]

        with self._db.connection() as conn:
            if self._repo.buscar_por_email(conn, email) is not None:
                raise Conflito("E-mail já cadastrado")

        try:
            with self._db.transaction() as conn:
                return self._repo.inserir(
                    conn, nome, email, self._hasher.hash_password(senha),
                    modelo_usuario.PAPEL_CLIENTE,
                )
        except sqlite3.IntegrityError:
            # A constraint UNIQUE de TR-16 fecha a corrida que a verificação acima sozinha
            # não fecha: dois cadastros simultâneos do mesmo e-mail.
            raise Conflito("E-mail já cadastrado")
