"""Leitura e validação do ambiente — única camada que conhece variáveis de ambiente.

Falha no boot quando uma chave obrigatória está ausente. O composition root lê estes
valores uma vez e os injeta adiante; nenhuma outra camada lê o ambiente.
"""
import os

from dotenv import load_dotenv

load_dotenv()

DEV_PLACEHOLDER_SECRET = 'dev-only-insecure-not-for-production'


class ConfigError(RuntimeError):
    """Variável obrigatória ausente ou inválida. Levantada no boot, nunca em requisição."""


def _str(key, default=None, required=False):
    value = os.environ.get(key, default)
    if required and not value:
        raise ConfigError(
            f"Variável de ambiente obrigatória ausente: {key}. "
            f"Copie .env.example para .env e preencha-a."
        )
    return value


def _int(key, default):
    raw = os.environ.get(key)
    if raw is None or raw == '':
        return default
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"Variável de ambiente {key} deve ser um inteiro; recebido: {raw!r}")


def _bool(key, default):
    raw = os.environ.get(key)
    if raw is None or raw == '':
        return default
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


class Settings:
    """Configuração imutável, tipada, resolvida uma vez no boot."""

    __slots__ = (
        'env', 'debug', 'host', 'port', 'secret_key', 'database_uri',
        'token_ttl_seconds', 'login_rate_limit', 'login_rate_window_seconds',
        'page_size_default', 'page_size_max', 'cors_origins',
        'password_hash_iterations',
        'smtp_host', 'smtp_port', 'smtp_user', 'smtp_password',
    )

    def __init__(self):
        self.env = _str('APP_ENV', 'development')
        is_production = self.env == 'production'

        # Em produção a chave é obrigatória e o boot falha sem ela. Em desenvolvimento
        # cai num placeholder declaradamente inválido, que nunca deve ir a produção.
        self.secret_key = _str('SECRET_KEY', required=is_production) or DEV_PLACEHOLDER_SECRET
        if is_production and self.secret_key == DEV_PLACEHOLDER_SECRET:
            raise ConfigError('SECRET_KEY de desenvolvimento não pode ser usada em produção.')

        self.debug = _bool('DEBUG', not is_production)
        if is_production and self.debug:
            raise ConfigError('DEBUG não pode ficar ligado em produção.')

        self.host = _str('HOST', '127.0.0.1')
        self.port = _int('PORT', 5000)
        self.database_uri = _str('DATABASE_URI', 'sqlite:///tasks.db')

        self.token_ttl_seconds = _int('TOKEN_TTL_SECONDS', 3600)
        self.login_rate_limit = _int('LOGIN_RATE_LIMIT', 10)
        self.login_rate_window_seconds = _int('LOGIN_RATE_WINDOW_SECONDS', 300)

        self.page_size_default = _int('PAGE_SIZE_DEFAULT', 50)
        self.page_size_max = _int('PAGE_SIZE_MAX', 200)

        origins = _str('CORS_ORIGINS', 'http://localhost:3000')
        self.cors_origins = [o.strip() for o in origins.split(',') if o.strip()]

        self.password_hash_iterations = _int('PASSWORD_HASH_ITERATIONS', 260000)

        self.smtp_host = _str('SMTP_HOST', 'localhost')
        self.smtp_port = _int('SMTP_PORT', 587)
        self.smtp_user = _str('SMTP_USER', '')
        self.smtp_password = _str('SMTP_PASSWORD', '')

    def __repr__(self):
        return f'<Settings env={self.env} debug={self.debug} host={self.host}:{self.port}>'


def load_settings():
    """Constrói a configuração. Levanta ConfigError no boot se algo obrigatório faltar."""
    return Settings()
