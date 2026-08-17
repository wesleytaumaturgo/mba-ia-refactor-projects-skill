"""Limite de taxa para o endpoint de autenticação (finding F-021, AP-24).

Janela deslizante por sujeito e por origem. Instância com ciclo de vida explícito, criada
no composition root e injetada — não é variável global de módulo.

Corrigir a autenticação sem isto apenas move o caminho mais barato de ataque para a força
bruta, que era o motivo de o finding ser registrado agora e não depois.
"""

import threading
import time


class LimitadorDeTaxa:
    def __init__(self, limite, janela_segundos, relogio=time.time):
        self._limite = int(limite)
        self._janela = int(janela_segundos)
        self._relogio = relogio
        self._tentativas = {}
        self._lock = threading.Lock()

    def registrar_e_verificar(self, chave):
        """Registra a tentativa. Devolve (permitido, segundos_para_liberar)."""
        agora = self._relogio()
        corte = agora - self._janela
        with self._lock:
            recentes = [t for t in self._tentativas.get(chave, []) if t > corte]
            if len(recentes) >= self._limite:
                self._tentativas[chave] = recentes
                return False, int(recentes[0] + self._janela - agora) + 1
            recentes.append(agora)
            self._tentativas[chave] = recentes
            return True, 0

    def limpar(self, chave):
        """Zera o contador após uma autenticação bem-sucedida."""
        with self._lock:
            self._tentativas.pop(chave, None)
