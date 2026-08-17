"""Entidade Usuario: forma dos dados e vocabulário de papéis."""

CAMPOS = ("id", "nome", "email", "senha", "tipo", "criado_em")

PAPEL_ADMIN = "admin"
PAPEL_CLIENTE = "cliente"


def de_registro(row):
    return {campo: row[campo] for campo in CAMPOS}
