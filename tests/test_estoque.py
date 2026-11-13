import unittest

from helpdesk.enums import Categoria, Prioridade, StatusChamado
from helpdesk.estoque import Equipamento
from helpdesk.excecoes import (
    EquipamentoBaixadoError, EstoqueInsuficienteError, PermissaoNegadaError,
)
from helpdesk.helpdesk import HelpDesk
from helpdesk.usuarios import Administrador, Tecnico


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


class TestEstoqueNoHelpDesk(unittest.TestCase):
    def setUp(self):
        self.admin = Administrador("Admin", "admin@empresa.com", "1234", "Gerente de TI")
        self.helpdesk = HelpDesk("Empresa", self.admin)
        self.usuario = self.helpdesk.cadastrar_usuario_comum(
            "Usuario", "usuario@empresa.com", "1234", "Financeiro"
        )
        self.tecnico = self.helpdesk.cadastrar_tecnico(
            self.admin, "Tecnico", "tecnico@empresa.com", "1234", "Hardware"
        )

    def cadastrar_mouse(self):
        return self.helpdesk.cadastrar_equipamento(
            self.tecnico, "EQ01", "Mouse USB", "Periférico", 10, 2
        )

    def abrir_chamado(self):
        return self.helpdesk.abrir_chamado(
            self.usuario, "Mouse quebrado", "Mouse não funciona",
            Categoria.HARDWARE, Prioridade.BAIXA
        )

    def test_uc12_cadastrar_equipamento(self):
        """UC12: Técnico cadastra equipamento e ele aparece no estoque"""
        mouse = self.cadastrar_mouse()
        self.assertEqual(self.helpdesk.listar_equipamentos(self.tecnico), [mouse])
        self.assertEqual(mouse.quantidade, 10)

    def test_uc12_recusar_codigo_duplicado(self):
        """UC12: Equipamento com código já cadastrado é recusado"""
        self.cadastrar_mouse()
        with self.assertRaises(ValueError):
            self.cadastrar_mouse()
        self.assertEqual(len(self.helpdesk.listar_equipamentos(self.tecnico)), 1)

    def test_uc12_recusar_cadastro_por_quem_nao_e_tecnico(self):
        """UC12: Usuário comum e administrador não cadastram equipamento"""
        for perfil in (self.usuario, self.admin):
            with self.assertRaises(PermissaoNegadaError):
                self.helpdesk.cadastrar_equipamento(perfil, "EQ01", "Mouse USB", "Periférico", 10, 2)
        self.assertEqual(self.helpdesk.listar_equipamentos(self.tecnico), [])

    def test_uc13_consultar_estoque(self):
        """UC13: Consulta lista equipamentos ativos e os abaixo do mínimo"""
        mouse = self.helpdesk.cadastrar_equipamento(
            self.tecnico, "EQ01", "Mouse USB", "Periférico", 1, 5
        )
        teclado = self.helpdesk.cadastrar_equipamento(
            self.tecnico, "EQ02", "Teclado", "Periférico", 10, 2
        )
        self.helpdesk.dar_baixa_equipamento(self.tecnico, "EQ02", "Equipamento danificado")
        self.assertEqual(self.helpdesk.listar_equipamentos(self.tecnico), [mouse])
        self.assertEqual(self.helpdesk.listar_equipamentos(self.tecnico, False), [mouse, teclado])
        self.assertEqual(self.helpdesk.listar_equipamentos_abaixo_do_minimo(self.tecnico), [mouse])

    def test_uc13_recusar_consulta_por_usuario_comum(self):
        """UC13: Usuário comum não consulta o estoque"""
        with self.assertRaises(PermissaoNegadaError):
            self.helpdesk.listar_equipamentos(self.usuario)

    def test_uc14_atualizar_dados_do_equipamento(self):
        """UC14: Técnico atualiza descrição e quantidade mínima sem alterar o saldo"""
        mouse = self.cadastrar_mouse()
        self.helpdesk.atualizar_equipamento(self.tecnico, "EQ01", "Mouse sem fio", 4)
        self.assertEqual(mouse.descricao, "Mouse sem fio")
        self.assertEqual(mouse.quantidade_minima, 4)
        self.assertEqual(mouse.quantidade, 10)

    def test_uc14_repor_equipamento(self):
        """UC14: Reposição aumenta o saldo e registra a movimentação"""
        mouse = self.cadastrar_mouse()
        self.helpdesk.repor_equipamento(self.tecnico, "EQ01", 5, "Compra")
        self.assertEqual(mouse.quantidade, 15)
        self.assertEqual(len(mouse.listar_movimentacoes()), 1)

    def test_uc11_registrar_saida_para_chamado(self):
        """UC11: Saída reduz o estoque e registra observação no chamado"""
        mouse = self.cadastrar_mouse()
        chamado = self.abrir_chamado()
        self.tecnico.assumir_chamado(chamado)
        self.helpdesk.registrar_saida_equipamento(self.tecnico, "EQ01", 2, chamado)
        self.assertEqual(mouse.quantidade, 8)
        self.assertIs(mouse.listar_movimentacoes()[0].chamado, chamado)
        self.assertEqual(len(chamado.listar_historico()), 2)
        self.assertEqual(chamado.status, StatusChamado.EM_ATENDIMENTO)

    def test_uc11_recusar_saida_por_tecnico_que_nao_e_responsavel(self):
        """UC11: Somente o técnico responsável pelo chamado registra a saída"""
        mouse = self.cadastrar_mouse()
        chamado = self.abrir_chamado()
        self.tecnico.assumir_chamado(chamado)
        outro = self.helpdesk.cadastrar_tecnico(
            self.admin, "Outro Tecnico", "outro.tecnico@empresa.com", "1234", "Redes"
        )
        with self.assertRaises(PermissaoNegadaError):
            self.helpdesk.registrar_saida_equipamento(outro, "EQ01", 2, chamado)
        self.assertEqual(mouse.quantidade, 10)
        self.assertEqual(len(chamado.listar_historico()), 1)

    def test_uc11_recusar_saida_para_chamado_nao_assumido(self):
        """UC11: Chamado ainda ABERTO não recebe saída de equipamento"""
        mouse = self.cadastrar_mouse()
        chamado = self.abrir_chamado()
        with self.assertRaises(PermissaoNegadaError):
            self.helpdesk.registrar_saida_equipamento(self.tecnico, "EQ01", 2, chamado)
        self.assertEqual(mouse.quantidade, 10)
        self.assertEqual(chamado.listar_historico(), [])

    def test_uc15_dar_baixa_em_equipamento(self):
        """UC15: Equipamento baixado sai da lista de ativos e registra a baixa"""
        mouse = self.cadastrar_mouse()
        self.helpdesk.dar_baixa_equipamento(self.tecnico, "EQ01", "Equipamento danificado")
        self.assertFalse(mouse.ativo)
        self.assertEqual(self.helpdesk.listar_equipamentos(self.tecnico), [])
        self.assertEqual(len(mouse.listar_movimentacoes()), 1)

    def test_uc15_recusar_baixa_de_equipamento_inexistente(self):
        """UC15: Baixa de equipamento não cadastrado é recusada"""
        with self.assertRaises(ValueError):
            self.helpdesk.dar_baixa_equipamento(self.tecnico, "EQ99", "Equipamento danificado")


if __name__ == "__main__":
    unittest.main()
