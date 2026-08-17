"""Serializadores de saída.

Cada função projeta uma **allowlist** explícita de campos. Espalhar o registro inteiro e
depois remover chaves é frágil: o próximo campo sensível entra sozinho na resposta. Aqui,
um campo só atravessa a fronteira de saída se estiver nomeado abaixo.

`senha` não aparece em nenhuma allowlist deste módulo — é o que sustenta BC-1.
"""

CAMPOS_PRODUTO = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")
CAMPOS_USUARIO = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_USUARIO_AUTENTICADO = ("id", "nome", "email", "tipo")
CAMPOS_PEDIDO = ("id", "usuario_id", "status", "total", "criado_em")
CAMPOS_ITEM_PEDIDO = ("produto_id", "produto_nome", "quantidade", "preco_unitario")


def _projetar(registro, campos):
    return {campo: registro[campo] for campo in campos if campo in registro}


def produto_dto(registro):
    return _projetar(registro, CAMPOS_PRODUTO)


def produtos_dto(registros):
    return [produto_dto(registro) for registro in registros]


def usuario_dto(registro):
    """Projeção pública de usuário. `senha` fica de fora por construção."""
    return _projetar(registro, CAMPOS_USUARIO)


def usuarios_dto(registros):
    return [usuario_dto(registro) for registro in registros]


def usuario_autenticado_dto(registro):
    """Identificação mínima do sujeito devolvida no fluxo de autenticação."""
    return _projetar(registro, CAMPOS_USUARIO_AUTENTICADO)


def item_pedido_dto(registro):
    return _projetar(registro, CAMPOS_ITEM_PEDIDO)


def pedido_dto(registro):
    corpo = _projetar(registro, CAMPOS_PEDIDO)
    corpo["itens"] = [item_pedido_dto(item) for item in registro.get("itens", [])]
    return corpo


def pedidos_dto(registros):
    return [pedido_dto(registro) for registro in registros]


def health_dto(contagens, versao):
    """Diagnóstico sem valor de configuração. Sustenta BC-2.

    `secret_key`, `debug`, `db_path` e `ambiente` foram removidos: eram configuração
    interna servida por rota pública (finding F-007).
    """
    return {
        "status": "ok",
        "database": "connected",
        "counts": contagens,
        "versao": versao,
    }
