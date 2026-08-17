"""Emissão e verificação de credencial assinada e expirável.

Formato compacto: ``<payload_b64url>.<assinatura_b64url>``, assinatura HMAC-SHA256 sobre o
payload com a chave que TR-01 trouxe do ambiente. Uma string derivada do identificador do
sujeito não é credencial: sem assinatura, qualquer chamador a forja.
"""

import base64
import hashlib
import hmac
import json
import time


class TokenInvalido(Exception):
    """Assinatura ausente, malformada ou que não confere."""


class TokenExpirado(Exception):
    """Assinatura válida, mas fora da janela de validade."""


def _b64(dados):
    return base64.urlsafe_b64encode(dados).decode("ascii").rstrip("=")


def _de_b64(texto):
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _assinar(secret, payload_b64):
    return hmac.new(
        secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256
    ).digest()


def emitir(secret, sujeito_id, papel, ttl_segundos, agora=None):
    agora = int(time.time()) if agora is None else int(agora)
    payload = {"sub": int(sujeito_id), "role": papel, "iat": agora, "exp": agora + int(ttl_segundos)}
    payload_b64 = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    return payload_b64 + "." + _b64(_assinar(secret, payload_b64))


def verificar(secret, token, agora=None):
    """Devolve o payload. Levanta TokenInvalido ou TokenExpirado."""
    if not token or not isinstance(token, str) or token.count(".") != 1:
        raise TokenInvalido("formato de credencial inválido")

    payload_b64, assinatura_b64 = token.split(".")
    try:
        assinatura = _de_b64(assinatura_b64)
    except (ValueError, TypeError):
        raise TokenInvalido("assinatura ilegível")

    if not hmac.compare_digest(assinatura, _assinar(secret, payload_b64)):
        raise TokenInvalido("assinatura não confere")

    try:
        payload = json.loads(_de_b64(payload_b64).decode("utf-8"))
    except (ValueError, TypeError):
        raise TokenInvalido("payload ilegível")

    agora = int(time.time()) if agora is None else int(agora)
    if int(payload.get("exp", 0)) <= agora:
        raise TokenExpirado("credencial expirada")

    return payload
