"""Derivação e verificação de senha.

Primitiva lenta da plataforma (PBKDF2-HMAC-SHA256), com salt por registro e fator de
custo configurável. Comparação em tempo constante.

Migração por reidratação: o formato antigo (MD5 sem salt, 32 hex) continua sendo
aceito na verificação e é regravado no formato novo no primeiro login bem-sucedido.
O formato fica marcado no próprio valor armazenado.
"""
import hashlib
import hmac
import os
import re

ALGORITHM = 'pbkdf2_sha256'
SALT_BYTES = 16
DEFAULT_ITERATIONS = 260000

_LEGACY_MD5 = re.compile(r'^[0-9a-f]{32}$')


def hash_password(password, iterations=DEFAULT_ITERATIONS):
    """Deriva a senha. Formato: pbkdf2_sha256$<iterações>$<salt hex>$<digest hex>."""
    salt = os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f'{ALGORITHM}${iterations}${salt.hex()}${digest.hex()}'


def is_legacy(stored):
    """True quando o valor armazenado está no formato antigo (MD5 sem salt)."""
    return bool(stored) and bool(_LEGACY_MD5.match(stored))


def verify_password(stored, password):
    """Verifica a senha contra o valor armazenado, em qualquer um dos dois formatos."""
    if not stored:
        return False

    if is_legacy(stored):
        legacy = hashlib.md5(password.encode('utf-8')).hexdigest()
        return hmac.compare_digest(stored, legacy)

    try:
        algorithm, raw_iterations, salt_hex, digest_hex = stored.split('$')
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False

    try:
        iterations = int(raw_iterations)
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return hmac.compare_digest(bytes.fromhex(digest_hex), candidate)


def needs_rehash(stored, iterations=DEFAULT_ITERATIONS):
    """True quando o valor deve ser regravado — formato antigo ou fator de custo defasado."""
    if is_legacy(stored):
        return True
    try:
        algorithm, raw_iterations, _, _ = stored.split('$')
    except (ValueError, AttributeError):
        return True
    return algorithm != ALGORITHM or int(raw_iterations) < iterations
