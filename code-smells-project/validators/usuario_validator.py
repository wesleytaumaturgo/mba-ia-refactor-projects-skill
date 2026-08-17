from validators.schema import Campo, Schema

USUARIO = Schema(
    Campo("nome", str, rotulo="Nome"),
    Campo("email", str, rotulo="Email", tamanho_min=3, mensagem_curto="Email inválido"),
    Campo("senha", str, rotulo="Senha"),
)

CREDENCIAL = Schema(
    Campo("email", str, rotulo="Email"),
    Campo("senha", str, rotulo="Senha"),
)
