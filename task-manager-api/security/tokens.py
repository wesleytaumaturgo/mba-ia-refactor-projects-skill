"""Emissão e verificação de credencial assinada, com expiração.

A assinatura usa a chave que TR-01 trouxe do ambiente. Uma string derivada do
identificador do sujeito não é credencial — esta é.
"""
import base64
import hashlib
import hmac
import json
import time


class TokenError(Exception):
    """Credencial ausente, malformada, com assinatura inválida ou expirada."""


def _b64encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def _b64decode(text):
    padding = '=' * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _sign(payload_b64, secret_key):
    return _b64encode(hmac.new(secret_key.encode('utf-8'),
                               payload_b64.encode('ascii'),
                               hashlib.sha256).digest())


def issue_token(user, secret_key, ttl_seconds):
    """Emite credencial assinada para o sujeito, expirando em ttl_seconds."""
    payload = {
        'sub': user.id,
        'role': user.role,
        'iat': int(time.time()),
        'exp': int(time.time()) + ttl_seconds,
    }
    payload_b64 = _b64encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    return f'{payload_b64}.{_sign(payload_b64, secret_key)}'


def verify_token(token, secret_key):
    """Devolve o payload se a assinatura confere e não expirou. Senão, TokenError."""
    if not token:
        raise TokenError('Credencial ausente')

    parts = token.split('.')
    if len(parts) != 2:
        raise TokenError('Credencial malformada')

    payload_b64, signature = parts
    if not hmac.compare_digest(signature, _sign(payload_b64, secret_key)):
        raise TokenError('Assinatura inválida')

    try:
        payload = json.loads(_b64decode(payload_b64))
    except (ValueError, TypeError):
        raise TokenError('Credencial malformada')

    if payload.get('exp', 0) < int(time.time()):
        raise TokenError('Credencial expirada')

    return payload
