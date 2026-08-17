"""Limite de taxa para o endpoint de autenticação (AP-24).

Sem ele, corrigir a autenticação apenas move o caminho mais barato de ataque para
força bruta. Conta por sujeito **e** por origem, em janela deslizante.

O estado é compartilhado por construção e protegido por lock — não é o estado
global mutável e desprotegido que AP-10 descreve.
"""
import threading
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, limit, window_seconds):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits = defaultdict(list)
        self._lock = threading.Lock()

    def _prune(self, key, now):
        cutoff = now - self.window_seconds
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]

    def check(self, *keys):
        """Registra a tentativa. Devolve (permitido, segundos_para_liberar)."""
        now = time.time()
        with self._lock:
            worst_retry = 0
            allowed = True
            for key in keys:
                if key is None:
                    continue
                self._prune(key, now)
                if len(self._hits[key]) >= self.limit:
                    allowed = False
                    worst_retry = max(worst_retry,
                                      int(self.window_seconds - (now - self._hits[key][0])) + 1)
            if allowed:
                for key in keys:
                    if key is not None:
                        self._hits[key].append(now)
            return allowed, worst_retry

    def reset(self, *keys):
        """Zera o contador — chamado após autenticação bem-sucedida."""
        with self._lock:
            for key in keys:
                self._hits.pop(key, None)
