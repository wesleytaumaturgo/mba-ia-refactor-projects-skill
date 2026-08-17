from models import usuario as modelo_usuario


class UsuarioRepository:
    def listar(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios")
        return [modelo_usuario.de_registro(row) for row in cursor.fetchall()]

    def buscar_por_id(self, conn, usuario_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        row = cursor.fetchone()
        return modelo_usuario.de_registro(row) if row else None

    def buscar_por_email(self, conn, email):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        row = cursor.fetchone()
        return modelo_usuario.de_registro(row) if row else None

    def inserir(self, conn, nome, email, senha_derivada, tipo):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_derivada, tipo),
        )
        return cursor.lastrowid

    def atualizar_credencial(self, conn, usuario_id, senha_derivada):
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?", (senha_derivada, usuario_id)
        )
        return cursor.rowcount

    def contar(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        return cursor.fetchone()[0]
