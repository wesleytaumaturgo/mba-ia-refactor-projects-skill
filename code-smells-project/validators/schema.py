"""Mini-schema declarativo.

A invariante é declarada **uma vez por entidade** e o mesmo schema atende criação e
atualização — que era exatamente onde as duas cópias divergiam (finding F-018).

Cumpre também a allowlist de bind: o resultado contém apenas os campos declarados, então
um payload com campo extra não o propaga.
"""

from services.errors import EntradaInvalida

FALTANDO = object()


class Campo:
    def __init__(self, nome, tipo, rotulo=None, obrigatorio=True, default=FALTANDO,
                 minimo=None, tamanho_min=None, tamanho_max=None, escolhas=None,
                 mensagem_curto=None, mensagem_longo=None, mensagem_minimo=None):
        self.nome = nome
        self.tipo = tipo
        self.rotulo = rotulo or nome.capitalize()
        self.obrigatorio = obrigatorio
        self.default = default
        self.minimo = minimo
        self.tamanho_min = tamanho_min
        self.tamanho_max = tamanho_max
        self.escolhas = escolhas
        self.mensagem_curto = mensagem_curto
        self.mensagem_longo = mensagem_longo
        self.mensagem_minimo = mensagem_minimo

    def _coagir(self, valor):
        """Verifica o tipo antes de qualquer comparação numérica.

        Sem isto, um `preco` textual chega a `preco < 0` e vira TypeError → 500. É a
        causa de um dos casos de BC-8.
        """
        if self.tipo is str:
            if not isinstance(valor, str):
                raise EntradaInvalida(self.rotulo + " deve ser texto")
            return valor
        if self.tipo is float:
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise EntradaInvalida(self.rotulo + " deve ser numérico")
            return float(valor)
        if self.tipo is int:
            if isinstance(valor, bool) or not isinstance(valor, int):
                raise EntradaInvalida(self.rotulo + " deve ser um número inteiro")
            return valor
        return valor

    def validar(self, payload):
        valor = payload.get(self.nome, FALTANDO)

        if valor is FALTANDO or valor is None:
            if self.default is not FALTANDO:
                return self.default
            if self.obrigatorio:
                raise EntradaInvalida(self.rotulo + " é obrigatório")
            return None

        valor = self._coagir(valor)

        if self.minimo is not None and valor < self.minimo:
            raise EntradaInvalida(self.mensagem_minimo or (self.rotulo + " inválido"))
        if self.tamanho_min is not None and len(valor) < self.tamanho_min:
            raise EntradaInvalida(self.mensagem_curto or (self.rotulo + " muito curto"))
        if self.tamanho_max is not None and len(valor) > self.tamanho_max:
            raise EntradaInvalida(self.mensagem_longo or (self.rotulo + " muito longo"))
        if self.escolhas is not None and valor not in self.escolhas:
            raise EntradaInvalida(
                self.rotulo + " inválida. Válidas: " + str(list(self.escolhas))
            )
        return valor


class Schema:
    def __init__(self, *campos):
        self._campos = campos

    def validate(self, payload):
        if not isinstance(payload, dict):
            raise EntradaInvalida("Dados inválidos")
        return {campo.nome: campo.validar(payload) for campo in self._campos}
