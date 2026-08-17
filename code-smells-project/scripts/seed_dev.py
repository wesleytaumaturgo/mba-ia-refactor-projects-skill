"""Carga de dados de demonstração. Execução manual, **nunca** no boot.

Recusa-se a rodar fora de ambiente de desenvolvimento: as credenciais de exemplo são
conhecidas e não podem ser inseridas em produção (finding F-013).
"""

import sys

from config import load_settings
from infra.connection import Database
from security import password

PRODUTOS = (
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
)

USUARIOS = (
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
)


def main():
    settings = load_settings()
    if settings.environment != "development":
        print("recusado: seed de demonstracao so roda com LOJA_ENV=development "
              "(atual: " + settings.environment + ")", file=sys.stderr)
        return 1

    password.configure(settings.password_cost_log2)
    db = Database(settings.db_path)

    with db.transaction() as conn:
        if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
            print("banco ja populado; nada a fazer")
            return 0
        conn.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)", PRODUTOS)
        conn.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [(n, e, password.hash_password(s), t) for n, e, s, t in USUARIOS])
    print("seed aplicado: " + str(len(PRODUTOS)) + " produtos, " + str(len(USUARIOS)) + " usuarios")
    return 0


if __name__ == "__main__":
    sys.exit(main())
