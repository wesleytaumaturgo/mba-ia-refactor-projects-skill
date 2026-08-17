"""Leitura e validação do ambiente.

Única camada autorizada a ler variáveis de ambiente. Falha no boot quando uma
variável obrigatória está ausente — um segredo esquecido derruba a aplicação em
vez de virar um default silencioso.
"""

import os


class ConfigError(RuntimeError):
    """Levantada no boot quando uma variável obrigatória está ausente ou é inválida."""


OBRIGATORIAS = ("LOJA_SECRET_KEY",)


def _carregar_arquivo_env(caminho):
    """Popula os.environ a partir de um arquivo de ambiente, sem sobrescrever o que já existe.

    Evita uma dependência só para ler pares chave=valor. Ausência do arquivo não é erro:
    em produção as variáveis vêm do próprio ambiente.
    """
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, _, valor = linha.partition("=")
            os.environ.setdefault(chave.strip(), valor.strip())


def _texto(chave, default=None):
    valor = os.environ.get(chave, default)
    if valor is None:
        raise ConfigError(
            "Variável de ambiente obrigatória ausente: " + chave +
            ". Copie .env.example para .env e preencha os valores."
        )
    return valor


def _inteiro(chave, default):
    bruto = os.environ.get(chave)
    if bruto is None or bruto == "":
        return default
    try:
        return int(bruto)
    except ValueError:
        raise ConfigError("Variável de ambiente " + chave + " precisa ser inteira, recebido: " + bruto)


def _booleano(chave, default):
    bruto = os.environ.get(chave)
    if bruto is None or bruto == "":
        return default
    return bruto.strip().lower() in ("1", "true", "yes", "on")


def _lista(chave, default):
    bruto = os.environ.get(chave)
    if bruto is None or bruto.strip() == "":
        return list(default)
    return [item.strip() for item in bruto.split(",") if item.strip()]


class Settings:
    """Objeto de configuração imutável, construído uma vez no composition root."""

    __slots__ = (
        "secret_key", "db_path", "debug", "host", "port", "environment",
        "log_level", "allowed_origins", "token_ttl_seconds", "password_cost_log2",
        "login_rate_limit", "login_rate_window_seconds",
        "page_size_default", "page_size_max",
    )

    def __init__(self, **valores):
        for nome in self.__slots__:
            object.__setattr__(self, nome, valores[nome])

    def __setattr__(self, nome, valor):
        raise AttributeError("Settings é imutável após o boot")


def load_settings(caminho_env=".env"):
    """Constrói o objeto de configuração. Levanta ConfigError se faltar chave obrigatória."""
    _carregar_arquivo_env(caminho_env)

    for chave in OBRIGATORIAS:
        if not os.environ.get(chave):
            raise ConfigError(
                "Variável de ambiente obrigatória ausente: " + chave +
                ". Copie .env.example para .env e preencha os valores."
            )

    ambiente = _texto("LOJA_ENV", "development")

    return Settings(
        secret_key=_texto("LOJA_SECRET_KEY"),
        db_path=_texto("LOJA_DB_PATH", "loja.db"),
        environment=ambiente,
        debug=_booleano("LOJA_DEBUG", ambiente == "development"),
        host=_texto("LOJA_HOST", "127.0.0.1"),
        port=_inteiro("LOJA_PORT", 5000),
        log_level=_texto("LOJA_LOG_LEVEL", "INFO"),
        allowed_origins=_lista("LOJA_ALLOWED_ORIGINS", []),
        token_ttl_seconds=_inteiro("LOJA_TOKEN_TTL_SECONDS", 3600),
        password_cost_log2=_inteiro("LOJA_PASSWORD_COST_LOG2", 14),
        login_rate_limit=_inteiro("LOJA_LOGIN_RATE_LIMIT", 5),
        login_rate_window_seconds=_inteiro("LOJA_LOGIN_RATE_WINDOW_SECONDS", 300),
        page_size_default=_inteiro("LOJA_PAGE_SIZE_DEFAULT", 20),
        page_size_max=_inteiro("LOJA_PAGE_SIZE_MAX", 100),
    )
