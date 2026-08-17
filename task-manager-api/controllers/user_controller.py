"""Tradução protocolo ↔ domínio para User, incluindo o fluxo de autenticação."""

from utils.helpers import utc_now

from flask import jsonify, request

from dto.task_dto import task_summary_for_user
from dto.user_dto import user_detail, user_identity, user_list_item, user_public
from middlewares.auth import is_admin
from middlewares.error_handler import envelope


class UserController:
    def __init__(self, user_service, task_service, rate_limiter, pagination):
        self._users = user_service
        self._tasks = task_service
        self._rate_limiter = rate_limiter
        self._pagination = pagination

    def list_users(self):
        limit, offset = self._pagination.from_request(request.args)
        return jsonify([user_list_item(u)
                        for u in self._users.list_users(limit=limit, offset=offset)]), 200

    def get_user(self, user_id):
        user = self._users.get_user(user_id)
        tasks = self._tasks.list_tasks_of_user(user_id)
        now = utc_now()
        return jsonify(user_detail(user, [_task_detail(t, now) for t in tasks])), 200

    def create_user(self):
        user = self._users.create_user(request.get_json(silent=True),
                                       actor_is_admin=is_admin())
        return jsonify(user_public(user)), 201

    def update_user(self, user_id):
        user = self._users.update_user(user_id, request.get_json(silent=True),
                                       actor_is_admin=is_admin())
        return jsonify(user_public(user)), 200

    def delete_user(self, user_id):
        self._users.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    def list_user_tasks(self, user_id):
        limit, offset = self._pagination.from_request(request.args)
        self._users.get_user(user_id)
        now = utc_now()
        tasks = self._tasks.list_tasks_of_user(user_id, limit=limit, offset=offset)
        return jsonify([task_summary_for_user(t, now) for t in tasks]), 200

    def login(self):
        payload = request.get_json(silent=True) or {}
        email = payload.get('email')
        password = payload.get('password')

        subject_key = f'user:{email}'
        origin_key = f'ip:{request.remote_addr}'
        allowed, retry_after = self._rate_limiter.check(subject_key, origin_key)
        if not allowed:
            response = jsonify(envelope('too_many_requests',
                                        'Muitas tentativas de login. '
                                        'Tente novamente mais tarde.'))
            response.headers['Retry-After'] = str(retry_after)
            return response, 429

        user = self._users.authenticate(email, password)
        self._rate_limiter.reset(subject_key, origin_key)

        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user_identity(user),
            'token': self._users.issue_token(user),
        }), 200


def _task_detail(task, now):
    """Forma da task dentro do detalhe de usuário — igual à forma canônica."""
    from dto.task_dto import task_public
    return task_public(task)
