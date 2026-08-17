"""Aplica as migrações pendentes. Execução explícita, fora do boot da aplicação."""

import sys

from config import load_settings
from infra import migrator
from infra.connection import Database


def main():
    settings = load_settings()
    db = Database(settings.db_path)
    aplicadas = migrator.aplicar(db)
    if aplicadas:
        print("migracoes aplicadas: " + ", ".join(aplicadas))
    else:
        print("nenhuma migracao pendente")
    print("versao do schema: " + str(migrator.versao_aplicada(db)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
