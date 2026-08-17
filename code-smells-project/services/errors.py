"""Erros de domínio.

O service sinaliza o resultado pelo **tipo do erro**, não pela forma do retorno. Um `None`
que significa "não encontrado" força o controller a decidir regra — que era exatamente o
sintoma de F-010 (o controller inspecionando a forma do valor para escolher o status).
"""


class DomainError(Exception):
    codigo = "erro_de_dominio"

    def __init__(self, mensagem, codigo=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if codigo:
            self.codigo = codigo


class NaoEncontrado(DomainError):
    codigo = "nao_encontrado"


class EntradaInvalida(DomainError):
    codigo = "entrada_invalida"


class RegraDeNegocioViolada(DomainError):
    codigo = "regra_violada"


class Conflito(DomainError):
    codigo = "conflito"


class CredencialInvalida(DomainError):
    codigo = "credencial_invalida"


class LimiteDeTaxaExcedido(DomainError):
    codigo = "limite_de_taxa"
