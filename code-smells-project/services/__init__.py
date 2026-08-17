"""Regra de negócio e orquestração de efeitos colaterais.

Único lugar que decide *o quê* acontece. Nenhum módulo aqui importa símbolo de protocolo
(request, response, status) — a regra precisa valer com ou sem HTTP.
"""
