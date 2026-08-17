"""Logger com níveis, timestamp e destino configurável.

**Redação por allowlist**, não por denylist: um campo só é emitido se estiver nomeado em
`CAMPOS_EMITIVEIS`. Uma denylist de nomes sensíveis falha no primeiro campo novo — e foi
exatamente assim que o e-mail dos usuários acabou no stdout (finding F-005).

O identificador do sujeito substitui o e-mail em todas as mensagens de autenticação.
"""

import logging
import sys

REDIGIDO = "<redigido>"

# Allowlist de campos que podem atravessar para o log. Nada fora daqui é emitido.
CAMPOS_EMITIVEIS = frozenset({
    "usuario_id", "produto_id", "pedido_id", "item_count",
    "total", "quantidade", "status", "canal", "resultado",
    "erro_tipo", "correlation_id", "endpoint", "metodo", "status_code",
    "limite", "janela_segundos", "versao_schema", "host", "port", "ambiente",
})


class Logger:
    def __init__(self, subjacente):
        self._log = subjacente

    def _formatar(self, evento, campos):
        partes = [evento]
        for chave in sorted(campos):
            valor = campos[chave] if chave in CAMPOS_EMITIVEIS else REDIGIDO
            partes.append(str(chave) + "=" + str(valor))
        return " ".join(partes)

    def info(self, evento, **campos):
        self._log.info(self._formatar(evento, campos))

    def warning(self, evento, **campos):
        self._log.warning(self._formatar(evento, campos))

    def error(self, evento, **campos):
        self._log.error(self._formatar(evento, campos))

    def exception(self, evento, **campos):
        self._log.exception(self._formatar(evento, campos))


def build_logger(nivel="INFO", nome="loja", destino=None):
    """Constrói o logger no composition root. O destino padrão é stdout."""
    subjacente = logging.getLogger(nome)
    subjacente.setLevel(getattr(logging, str(nivel).upper(), logging.INFO))
    subjacente.propagate = False
    if not subjacente.handlers:
        handler = logging.StreamHandler(destino or sys.stdout)
        handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        ))
        subjacente.addHandler(handler)
    return Logger(subjacente)
