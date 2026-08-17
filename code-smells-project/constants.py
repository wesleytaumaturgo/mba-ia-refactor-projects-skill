"""Metadados da API declarados uma vez.

A versão estava duplicada como literal em dois arquivos (`app.py` e `controllers.py` no
código original) — dois lugares que divergem sem que nada detecte.
"""

VERSAO_API = "1.0.0"

MENSAGEM_BOAS_VINDAS = "Bem-vindo à API da Loja"

ENDPOINTS_PUBLICADOS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}
