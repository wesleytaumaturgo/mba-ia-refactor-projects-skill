"""Autenticação e autorização — preocupação transversal, aplicada antes do handler.

Negar por padrão: a rota **declara** que é pública com @public. A ausência de
declaração não libera — uma rota nova nasce protegida.
"""
from functools import wraps

from flask import current_app, g, jsonify, request

from models.user import User
from security.tokens import TokenError, verify_token


def public(view):
    """Marca a rota como deliberadamente pública. Sem esta marca, a rota exige credencial.

    O view pode ser um método vinculado de controller, que não aceita atribuição de
    atributo — por isso a marca vai numa função que o envolve.
    """
    @wraps(view)
    def wrapper(*args, **kwargs):
        return view(*args, **kwargs)

    wrapper.is_public = True
    return wrapper


def _unauthorized(message):
    return jsonify({'error': message}), 401


def _forbidden(message):
    return jsonify({'error': message}), 403


def _bearer_token():
    header = request.headers.get('Authorization', '')
    if header.startswith('Bearer '):
        return header[7:].strip()
    return None


def authenticate_request():
    """before_request global: aplica negar-por-padrão a toda rota não declarada pública."""
    if request.method == 'OPTIONS':
        return None

    view = current_app.view_functions.get(request.endpoint)
    if view is None:
        return None
    if getattr(view, 'is_public', False):
        return None

    settings = current_app.config['SETTINGS']
    try:
        payload = verify_token(_bearer_token(), settings.secret_key)
    except TokenError as exc:
        return _unauthorized(str(exc))

    user = User.query.get(payload['sub'])
    if user is None:
        return _unauthorized('Credencial inválida')
    if not user.active:
        return _forbidden('Usuário inativo')

    g.current_user = user
    return None


def require_role(*roles):
    """Exige que o sujeito autenticado tenha um dos papéis — lê o `role` que o schema modela."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if user is None:
                return _unauthorized('Credencial ausente')
            if user.role not in roles:
                return _forbidden('Permissão insuficiente')
            return view(*args, **kwargs)
        return wrapper
    return decorator


def current_user():
    return getattr(g, 'current_user', None)


def is_admin():
    user = current_user()
    return user is not None and user.is_admin()
