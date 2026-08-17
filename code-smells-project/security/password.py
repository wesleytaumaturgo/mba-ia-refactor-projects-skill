"""Derivação de credencial por primitiva lenta, com salt por registro e fator de custo.

Formato armazenado: ``scrypt$<n_log2>$<r>$<p>$<salt_b64>$<dk_b64>``

O esquema é marcado no próprio valor, o que permite migrar por **reidratação**: uma
credencial no formato legado (texto simples) continua autenticando e é regravada no
formato novo no primeiro login bem-sucedido.
"""

import base64
import hashlib
import hmac
import os

ESQUEMA = "scrypt"
_CUSTO_LOG2_PADRAO = 14
_R = 8
_P = 1
_TAMANHO_DK = 32
_TAMANHO_SALT = 16

_custo_log2 = _CUSTO_LOG2_PADRAO


def configure(custo_log2):
    """Recebe do composition root o fator de custo. Nenhuma leitura de ambiente aqui."""
    global _custo_log2
    _custo_log2 = int(custo_log2)


def _b64(dados):
    return base64.urlsafe_b64encode(dados).decode("ascii").rstrip("=")


def _de_b64(texto):
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _derivar(senha, salt, custo_log2, r, p):
    n = 2 ** custo_log2
    # scrypt consome ~128*n*r bytes; a margem de 2x cobre o overhead interno do OpenSSL.
    maxmem = 128 * n * r * p * 2
    return hashlib.scrypt(
        senha.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=_TAMANHO_DK,
        maxmem=maxmem,
    )


def hash_password(senha, custo_log2=None):
    """Deriva a credencial com salt novo. Duas contas com a mesma senha geram valores distintos."""
    custo = _custo_log2 if custo_log2 is None else int(custo_log2)
    salt = os.urandom(_TAMANHO_SALT)
    dk = _derivar(senha, salt, custo, _R, _P)
    return "$".join([ESQUEMA, str(custo), str(_R), str(_P), _b64(salt), _b64(dk)])


def is_legacy(armazenado):
    """True quando o valor persistido não está no formato derivado (texto simples legado)."""
    return not (isinstance(armazenado, str) and armazenado.startswith(ESQUEMA + "$"))


def verify_password(armazenado, senha):
    """Compara em tempo constante. Aceita o formato legado para permitir a reidratação."""
    if armazenado is None or senha is None:
        return False

    if is_legacy(armazenado):
        return hmac.compare_digest(str(armazenado), str(senha))

    try:
        esquema, custo, r, p, salt_b64, dk_b64 = armazenado.split("$")
        if esquema != ESQUEMA:
            return False
        esperado = _de_b64(dk_b64)
        obtido = _derivar(senha, _de_b64(salt_b64), int(custo), int(r), int(p))
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(esperado, obtido)
