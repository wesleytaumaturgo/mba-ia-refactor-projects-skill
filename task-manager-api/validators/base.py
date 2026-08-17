"""Primitivas de validação compartilhadas.

Coerção de tipo explícita: entrada de tipo errado vira ValidationError (que o
controller traduz para 400), nunca exceção não tratada (que virava 500).
"""
from datetime import datetime

from services.errors import ValidationError

DATE_FORMATS = ('%Y-%m-%d', '%d/%m/%Y')


def optional_int(value, field):
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        raise ValidationError(f'{field} deve ser um número inteiro', field=field)
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(f'{field} deve ser um número inteiro', field=field)


def require_text(value, field, minimum, maximum, message=None):
    if not isinstance(value, str):
        raise ValidationError(message or f'{field} deve ser texto', field=field)
    text = value.strip()
    if len(text) < minimum or len(text) > maximum:
        raise ValidationError(
            message or f'{field} deve ter entre {minimum} e {maximum} caracteres',
            field=field)
    return text


def parse_date(value, field='due_date'):
    """Única definição de parsing de data do projeto (consolida F-010)."""
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        return value
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    raise ValidationError('Formato de data inválido. Use YYYY-MM-DD', field=field)


def normalize_tags(value, field='tags'):
    """Única definição de serialização de tags do projeto (consolida F-010)."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return ','.join(str(tag).strip() for tag in value)
    if isinstance(value, str):
        return value
    raise ValidationError('tags deve ser uma lista ou uma string', field=field)


def split_tags(raw):
    return raw.split(',') if raw else []
