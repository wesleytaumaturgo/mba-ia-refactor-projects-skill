"""Migração versionada de schema.

A DDL sai do caminho de boot (finding F-013) e passa a viver em arquivos numerados,
aplicados uma vez e registrados em `PRAGMA user_version`. O boot apenas **verifica** a
versão aplicada e falha com mensagem clara se estiver defasada.
"""

import os

DIRETORIO_MIGRACOES = os.path.join(os.path.dirname(__file__), "migrations")


class SchemaDesatualizado(RuntimeError):
    """O banco não está na versão que o código espera."""


def migracoes_disponiveis():
    if not os.path.isdir(DIRETORIO_MIGRACOES):
        return []
    arquivos = [f for f in os.listdir(DIRETORIO_MIGRACOES) if f.endswith(".sql")]
    return sorted(arquivos)


def versao_esperada():
    return len(migracoes_disponiveis())


def versao_aplicada(db):
    with db.connection() as conn:
        return conn.execute("PRAGMA user_version").fetchone()[0]


def aplicar(db):
    """Aplica as migrações pendentes. Idempotente: nada acontece se já estiver em dia."""
    atual = versao_aplicada(db)
    aplicadas = []
    for indice, arquivo in enumerate(migracoes_disponiveis(), start=1):
        if indice <= atual:
            continue
        caminho = os.path.join(DIRETORIO_MIGRACOES, arquivo)
        with open(caminho, encoding="utf-8") as origem:
            sql = origem.read()
        with db.transaction() as conn:
            conn.executescript(sql)
            conn.execute("PRAGMA user_version = " + str(indice))
        aplicadas.append(arquivo)
    return aplicadas


def verificar(db):
    """Chamado no boot. Não cria nada — só confere e falha com mensagem acionável."""
    atual = versao_aplicada(db)
    esperada = versao_esperada()
    if atual != esperada:
        raise SchemaDesatualizado(
            "Schema do banco na versão " + str(atual) + ", esperada " + str(esperada) +
            ". Rode `python -m scripts.migrate` antes de subir a aplicação."
        )
    return atual
