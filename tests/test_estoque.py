import unittest

from helpdesk.estoque import Equipamento
from helpdesk.excecoes import EquipamentoBaixadoError, EstoqueInsuficienteError
from helpdesk.usuarios import Tecnico


class TestEstoque(unittest.TestCase):
    def setUp(self):
        self.tecnico = Tecnico("Tecnico", "tecnico@empresa.com", "1234", "Hardware")
        self.equipamento = Equipamento("EQ01", "Mouse USB", "Periférico", 10, 2)

    def test_rn04_saida_com_quantidade_suficiente(self):
        """RN04: Saída com quantidade suficiente reduz o estoque"""
        self.equipamento.registrar_saida(3, self.tecnico, None)
        self.assertEqual(self.equipamento.quantidade, 7)
        self.assertEqual(len(self.equipamento.listar_movimentacoes()), 1)

    def test_rn04_recusar_saida_que_deixaria_estoque_negativo(self):
        """RN04: Saída maior que o saldo não deixa o estoque negativo"""
        with self.assertRaises(EstoqueInsuficienteError):
            self.equipamento.registrar_saida(11, self.tecnico, None)
        self.assertEqual(self.equipamento.quantidade, 10)
        self.assertEqual(self.equipamento.listar_movimentacoes(), [])

    def test_rn04_recusar_movimentacao_de_equipamento_baixado(self):
        """RN04: Equipamento baixado não pode ser movimentado"""
        self.equipamento.dar_baixa(self.tecnico, "Equipamento danificado")
        with self.assertRaises(EquipamentoBaixadoError):
            self.equipamento.registrar_saida(1, self.tecnico, None)
        with self.assertRaises(EquipamentoBaixadoError):
            self.equipamento.registrar_entrada(1, self.tecnico, "Reposição")
        self.assertFalse(self.equipamento.ativo)
        self.assertEqual(len(self.equipamento.listar_movimentacoes()), 1)


if __name__ == "__main__":
    unittest.main()
