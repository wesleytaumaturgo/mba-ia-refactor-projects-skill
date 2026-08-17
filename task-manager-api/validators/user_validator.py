"""Validação declarativa do agregado User, com allowlist de bind."""
import re

from models.user import User
from services.errors import ValidationError
from validators.base import require_text

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')

WRITABLE_FIELDS = ('name', 'email', 'password', 'role', 'active')
CREATE_REQUIRED = ('name', 'email', 'password')
DEFAULTS = {'role': 'user'}


def is_valid_email(email):
    """Única definição de validação de e-mail do projeto (consolida F-010)."""
    return isinstance(email, str) and bool(EMAIL_PATTERN.match(email))


class UserValidator:
    def _coerce(self, field, value):
        if field == 'name':
            return require_text(value, 'nome', 1, 100, message='Nome é obrigatório')
        if field == 'email':
            if not is_valid_email(value):
                raise ValidationError('Email inválido', field='email')
            return value
        if field == 'password':
            if not isinstance(value, str) or len(value) < User.MIN_PASSWORD_LENGTH:
                raise ValidationError(
                    f'Senha deve ter no mínimo {User.MIN_PASSWORD_LENGTH} caracteres',
                    field='password')
            return value
        if field == 'role':
            if not User.is_valid_role(value):
                raise ValidationError('Role inválido', field='role')
            return value
        if field == 'active':
            if not isinstance(value, bool):
                raise ValidationError('active deve ser booleano', field='active')
            return value
        raise ValidationError(f'Campo não gravável: {field}', field=field)

    def _require_payload(self, payload):
        if not isinstance(payload, dict) or not payload:
            raise ValidationError('Dados inválidos')

    def validate_create(self, payload):
        self._require_payload(payload)
        for field in CREATE_REQUIRED:
            if not payload.get(field):
                label = {'name': 'Nome', 'email': 'Email', 'password': 'Senha'}[field]
                article = 'é obrigatório' if field != 'password' else 'é obrigatória'
                raise ValidationError(f'{label} {article}', field=field)

        data = dict(DEFAULTS)
        for field in WRITABLE_FIELDS:
            if field in payload:
                data[field] = self._coerce(field, payload[field])
        data['role'] = self._coerce('role', data['role'])
        return data

    def validate_update(self, payload):
        self._require_payload(payload)
        return {field: self._coerce(field, payload[field])
                for field in WRITABLE_FIELDS if field in payload}
