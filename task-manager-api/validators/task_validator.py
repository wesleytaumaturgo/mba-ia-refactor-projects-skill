"""Validação declarativa do agregado Task.

Allowlist de bind: só os campos declarados aqui são gravados. Campo desconhecido no
payload é descartado, não repassado à entidade.

As MESMAS invariantes valem na criação e na atualização — a divergência entre os dois
caminhos era F-011.
"""
from models.task import Task
from services.errors import ValidationError
from validators.base import normalize_tags, optional_int, parse_date, require_text

# Allowlist de bind: campo do payload → como coagir/validar.
WRITABLE_FIELDS = ('title', 'description', 'status', 'priority',
                   'user_id', 'category_id', 'due_date', 'tags')

DEFAULTS = {'description': '', 'status': 'pending', 'priority': 3}


class TaskValidator:
    optional_int = staticmethod(optional_int)

    def _coerce(self, field, value):
        if field == 'title':
            return require_text(value, 'título', Task.MIN_TITLE_LENGTH, Task.MAX_TITLE_LENGTH,
                                message=f'Título deve ter entre {Task.MIN_TITLE_LENGTH} e '
                                        f'{Task.MAX_TITLE_LENGTH} caracteres')
        if field == 'description':
            return '' if value is None else str(value)
        if field == 'status':
            if not Task.is_valid_status(value):
                raise ValidationError('Status inválido', field='status')
            return value
        if field == 'priority':
            priority = optional_int(value, 'priority')
            if not Task.is_valid_priority(priority):
                raise ValidationError(
                    f'Prioridade deve ser entre {Task.MIN_PRIORITY} e {Task.MAX_PRIORITY}',
                    field='priority')
            return priority
        if field in ('user_id', 'category_id'):
            return optional_int(value, field)
        if field == 'due_date':
            return parse_date(value)
        if field == 'tags':
            return normalize_tags(value)
        raise ValidationError(f'Campo não gravável: {field}', field=field)

    def _require_payload(self, payload):
        if not isinstance(payload, dict) or not payload:
            raise ValidationError('Dados inválidos')

    def validate_create(self, payload):
        self._require_payload(payload)
        if not payload.get('title'):
            raise ValidationError('Título é obrigatório', field='title')

        data = dict(DEFAULTS)
        for field in WRITABLE_FIELDS:
            if field in payload:
                data[field] = self._coerce(field, payload[field])
        # Reaplica as invariantes sobre os defaults, para que criar e atualizar
        # apliquem exatamente a mesma regra.
        for field in ('status', 'priority'):
            data[field] = self._coerce(field, data[field])
        return data

    def validate_update(self, payload):
        self._require_payload(payload)
        return {field: self._coerce(field, payload[field])
                for field in WRITABLE_FIELDS if field in payload}
