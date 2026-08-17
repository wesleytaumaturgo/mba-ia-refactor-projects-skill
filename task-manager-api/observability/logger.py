"""Logger com níveis, timestamp e destino configurável.

Substitui as 11 chamadas de `print()` que serviam de registro de eventos, sem nível,
sem timestamp e sem destino (F-019) — e o helper `log_action` que o próprio projeto
definia e nunca chamava.

**Redação por allowlist**, não por denylist: só os campos nomeados em EMITTABLE_FIELDS
atravessam. Uma denylist de nomes sensíveis falha no primeiro campo novo, e o payload
inteiro nunca é emitido.
"""
import logging
import sys

LOG_FORMAT = '%(asctime)s %(levelname)-8s %(name)s %(message)s'

# Allowlist do que pode ser emitido. Nada fora desta lista atravessa.
EMITTABLE_FIELDS = frozenset({
    'task_id', 'user_id', 'category_id', 'correlation_id', 'status',
    'priority', 'role', 'count', 'path', 'method', 'code', 'event',
})


def configure(settings):
    """Instala o logger raiz da aplicação. Chamado uma vez, no composition root."""
    level = logging.DEBUG if settings.debug else logging.INFO
    root = logging.getLogger('task_manager')
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root.addHandler(handler)
    return root


def get_logger(name):
    return logging.getLogger(f'task_manager.{name}')


def redact(fields):
    """Projeta apenas os campos da allowlist. Descarta o resto silenciosamente."""
    return {k: v for k, v in fields.items() if k in EMITTABLE_FIELDS}


def emit(logger, level, event, **fields):
    """Emite um evento nomeado com os campos permitidos — nunca o payload inteiro."""
    safe = redact(fields)
    detail = ' '.join(f'{k}={v}' for k, v in sorted(safe.items()))
    logger.log(level, '%s %s', event, detail)


def info(logger, event, **fields):
    emit(logger, logging.INFO, event, **fields)


def warning(logger, event, **fields):
    emit(logger, logging.WARNING, event, **fields)
