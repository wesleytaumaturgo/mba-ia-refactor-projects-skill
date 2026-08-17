"""Validação declarativa do agregado Category, com allowlist de bind."""
from models.category import Category
from services.errors import ValidationError
from validators.base import require_text

WRITABLE_FIELDS = ('name', 'description', 'color')
DEFAULTS = {'description': '', 'color': Category.DEFAULT_COLOR}


def is_valid_color(color):
    """Única definição de validação de cor do projeto (consolida F-010)."""
    return isinstance(color, str) and len(color) == 7 and color.startswith('#')


class CategoryValidator:
    def _coerce(self, field, value):
        if field == 'name':
            return require_text(value, 'nome', 1, 100, message='Nome é obrigatório')
        if field == 'description':
            return '' if value is None else str(value)
        if field == 'color':
            if not is_valid_color(value):
                raise ValidationError('Cor deve estar no formato #RRGGBB', field='color')
            return value
        raise ValidationError(f'Campo não gravável: {field}', field=field)

    def _require_payload(self, payload):
        if not isinstance(payload, dict) or not payload:
            raise ValidationError('Dados inválidos')

    def validate_create(self, payload):
        self._require_payload(payload)
        if not payload.get('name'):
            raise ValidationError('Nome é obrigatório', field='name')
        data = dict(DEFAULTS)
        for field in WRITABLE_FIELDS:
            if field in payload:
                data[field] = self._coerce(field, payload[field])
        return data

    def validate_update(self, payload):
        self._require_payload(payload)
        return {field: self._coerce(field, payload[field])
                for field in WRITABLE_FIELDS if field in payload}
