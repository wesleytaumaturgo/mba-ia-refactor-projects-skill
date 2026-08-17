"""Regra de negócio do agregado User, incluindo autenticação."""
from models.user import User
from observability.logger import get_logger, info, warning
from services.errors import Conflict, NotFound, PermissionDenied, ValidationError


logger = get_logger('users')


class UserService:
    def __init__(self, user_repository, task_repository, unit_of_work, validator,
                 token_issuer=None):
        self._users = user_repository
        self._tasks = task_repository
        self._uow = unit_of_work
        self._validator = validator
        self._token_issuer = token_issuer

    # ── leitura ──────────────────────────────────────────────────────────────
    def list_users(self, limit=None, offset=None):
        return self._users.list_all(limit=limit, offset=offset)

    def get_user(self, user_id):
        user = self._users.get(user_id)
        if user is None:
            raise NotFound('Usuário não encontrado')
        return user

    # ── escrita ──────────────────────────────────────────────────────────────
    def create_user(self, payload, actor_is_admin=False):
        data = self._validator.validate_create(payload)

        if data['role'] != 'user' and not actor_is_admin:
            raise PermissionDenied('Permissão insuficiente para atribuir este papel')

        password = data.pop('password')
        user = User()
        for field, value in data.items():
            setattr(user, field, value)
        user.set_password(password)

        # A unicidade é imposta pelo índice UNIQUE do schema, não por check-then-act.
        try:
            with self._uow.transaction():
                self._users.add(user)
        except Exception as exc:
            if _is_unique_violation(exc):
                raise Conflict('Email já cadastrado', field='email')
            raise
        info(logger, 'user_created', user_id=user.id, role=user.role)
        return user

    def update_user(self, user_id, payload, actor_is_admin=False):
        user = self.get_user(user_id)
        data = self._validator.validate_update(payload)

        if 'role' in data and not actor_is_admin:
            raise PermissionDenied('Permissão insuficiente para alterar o papel')

        password = data.pop('password', None)
        try:
            with self._uow.transaction():
                for field, value in data.items():
                    setattr(user, field, value)
                if password is not None:
                    user.set_password(password)
        except Exception as exc:
            if _is_unique_violation(exc):
                raise Conflict('Email já cadastrado', field='email')
            raise
        return user

    def delete_user(self, user_id):
        """Usuário e suas tasks caem na MESMA transação — ou tudo, ou nada."""
        user = self.get_user(user_id)
        with self._uow.transaction():
            self._tasks.delete_by_user(user_id)
            self._users.delete(user)
        info(logger, 'user_deleted', user_id=user_id)

    # ── autenticação ─────────────────────────────────────────────────────────
    def authenticate(self, email, password):
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = self._users.find_by_email(email)
        if user is None or not user.check_password(password):
            # NUNCA o e-mail nem a senha: só o evento e o resultado.
            warning(logger, 'login_failed', code='invalid_credentials')
            raise PermissionDenied('Credenciais inválidas', code='invalid_credentials')
        if not user.active:
            raise PermissionDenied('Usuário inativo', code='inactive_user')

        # Reidratação: formato antigo regravado no primeiro login bem-sucedido.
        if user.password_needs_rehash():
            with self._uow.transaction():
                user.set_password(password)
            info(logger, 'password_rehashed', user_id=user.id)
        info(logger, 'login_succeeded', user_id=user.id, role=user.role)
        return user

    def issue_token(self, user):
        return self._token_issuer(user)


def _is_unique_violation(exc):
    text = str(getattr(exc, 'orig', exc)).lower()
    return 'unique' in text and 'email' in text
