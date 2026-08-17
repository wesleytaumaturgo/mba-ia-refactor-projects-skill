from database import get_db
from security.password import hash_password, is_legacy, verify_password

def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    rows = cursor.fetchall()
    result = []
    for row in rows:

        result.append({
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "preco": row["preco"],
            "estoque": row["estoque"],
            "categoria": row["categoria"],
            "ativo": row["ativo"],
            "criado_em": row["criado_em"]
        })
    return result

def get_produto_por_id(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row:
        return {
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "preco": row["preco"],
            "estoque": row["estoque"],
            "categoria": row["categoria"],
            "ativo": row["ativo"],
            "criado_em": row["criado_em"]
        }
    return None

def criar_produto(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria)
    )
    db.commit()
    return cursor.lastrowid

def atualizar_produto(id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, id)
    )
    db.commit()
    return True

def deletar_produto(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
    db.commit()
    return True

def get_todos_usuarios():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "senha": row["senha"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"]
        })
    return result

def get_usuario_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row:
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "senha": row["senha"],
            "tipo": row["tipo"],
            "criado_em": row["criado_em"]
        }
    return None

def login_usuario(email, senha):
    """Verifica a credencial fora do SQL e reidrata o formato legado no primeiro sucesso."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row is None:
        return None

    armazenado = row["senha"]
    if not verify_password(armazenado, senha):
        return None

    if is_legacy(armazenado):
        cursor.execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            (hash_password(senha), row["id"])
        )
        db.commit()

    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"]
    }

def criar_usuario(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, hash_password(senha), tipo)
    )
    db.commit()
    return cursor.lastrowid

def get_usuario_por_email(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    return {"id": row["id"]} if row else None

def criar_pedido(usuario_id, itens):
    db = get_db()
    cursor = db.cursor()

    total = 0

    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": "Produto " + str(item["produto_id"]) + " não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": "Estoque insuficiente para " + produto["nome"]}
        total = total + (produto["preco"] * item["quantidade"])

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, "pendente", total)
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        cursor.execute("SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cursor.fetchone()
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
            "VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
        )

        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"])
        )

    db.commit()
    return {"pedido_id": pedido_id, "total": total}

def get_pedidos_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        pedido = {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": []
        }

        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],))
        itens = cursor2.fetchall()
        for item in itens:
            cursor3 = db.cursor()
            cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
            prod = cursor3.fetchone()
            pedido["itens"].append({
                "produto_id": item["produto_id"],
                "produto_nome": prod["nome"] if prod else "Desconhecido",
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"]
            })
        result.append(pedido)
    return result

def get_todos_pedidos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos")
    rows = cursor.fetchall()
    result = []
    for row in rows:

        pedido = {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": []
        }
        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],))
        itens = cursor2.fetchall()
        for item in itens:
            cursor3 = db.cursor()
            cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
            prod = cursor3.fetchone()
            pedido["itens"].append({
                "produto_id": item["produto_id"],
                "produto_nome": prod["nome"] if prod else "Desconhecido",
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"]
            })
        result.append(pedido)
    return result

def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0]
    if faturamento is None:
        faturamento = 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", ("pendente",))
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", ("aprovado",))
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", ("cancelado",))
    cancelados = cursor.fetchone()[0]

    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
    }

def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id)
    )
    db.commit()
    return True

def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    cursor = db.cursor()

    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.append("%" + termo + "%")
        params.append("%" + termo + "%")
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        query += " AND preco <= ?"
        params.append(preco_max)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    result = []
    for row in rows:

        result.append({
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "preco": row["preco"],
            "estoque": row["estoque"],
            "categoria": row["categoria"],
            "ativo": row["ativo"],
            "criado_em": row["criado_em"]
        })
    return result
