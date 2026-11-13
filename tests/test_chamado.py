import unittest

from helpdesk.enums import Categoria, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.excecoes import (
    CancelamentoNaoPermitidoError, ChamadoNaoAbertoError, LimiteChamadosError,
    SolucaoObrigatoriaError,
)
from helpdesk.helpdesk import HelpDesk
from helpdesk.usuarios import Administrador


class TestChamado(unittest.TestCase):
    def setUp(self):
        self.admin = Administrador("Admin", "admin@empresa.com", "1234", "Gerente de TI")
        self.helpdesk = HelpDesk("Empresa", self.admin)
        self.solicitante = self.helpdesk.cadastrar_usuario_comum(
            "Solicitante", "solicitante@empresa.com", "1234", "RH"
        )
        self.tecnico = self.helpdesk.cadastrar_tecnico(
            self.admin, "Tecnico", "tecnico@empresa.com", "1234", "Redes"
        )
        self.chamado = self.helpdesk.abrir_chamado(
            self.solicitante, "Sem rede", "Computador sem acesso à rede",
            Categoria.REDE, Prioridade.ALTA
        )

    def test_rn01_cancelar_com_status_aberto_pelo_solicitante(self):
        """RN01: Solicitante cancela chamado com status ABERTO"""
        self.solicitante.cancelar_chamado(self.chamado)
        self.assertEqual(self.chamado.status, StatusChamado.CANCELADO)
        self.assertIsNotNone(self.chamado.data_encerramento)
        self.assertEqual(len(self.chamado.listar_historico()), 1)

    def test_rn01_recusar_cancelamento_por_outro_usuario(self):
        """RN01: Outro usuário não pode cancelar o chamado"""
        outro_usuario = self.helpdesk.cadastrar_usuario_comum(
            "Outro", "outro@empresa.com", "1234", "Financeiro"
        )
        with self.assertRaises(CancelamentoNaoPermitidoError):
            outro_usuario.cancelar_chamado(self.chamado)
        self.assertEqual(self.chamado.status, StatusChamado.ABERTO)
        self.assertEqual(self.chamado.listar_historico(), [])

    def test_rn01_recusar_cancelamento_com_status_diferente_de_aberto(self):
        """RN01: Chamado que não está ABERTO não pode ser cancelado"""
        self.tecnico.assumir_chamado(self.chamado)
        with self.assertRaises(CancelamentoNaoPermitidoError):
            self.solicitante.cancelar_chamado(self.chamado)
        self.assertEqual(self.chamado.status, StatusChamado.EM_ATENDIMENTO)
        self.assertIsNone(self.chamado.data_encerramento)

    def test_rn02_assumir_chamado_aberto(self):
        """RN02: Técnico assume chamado ABERTO"""
        self.tecnico.assumir_chamado(self.chamado)
        self.assertEqual(self.chamado.status, StatusChamado.EM_ATENDIMENTO)
        self.assertIs(self.chamado.responsavel, self.tecnico)
        self.assertEqual(self.tecnico.contar_em_atendimento(), 1)

    def test_rn02_recusar_assumir_chamado_em_outro_status(self):
        """RN02: Chamado que não está ABERTO não pode ser assumido"""
        outro_tecnico = self.helpdesk.cadastrar_tecnico(
            self.admin, "Outro Tecnico", "outro.tecnico@empresa.com", "1234", "Hardware"
        )
        self.tecnico.assumir_chamado(self.chamado)
        with self.assertRaises(ChamadoNaoAbertoError):
            outro_tecnico.assumir_chamado(self.chamado)
        self.assertIs(self.chamado.responsavel, self.tecnico)
        self.assertEqual(outro_tecnico.contar_em_atendimento(), 0)

    def test_rn02_recusar_sexto_chamado_simultaneo(self):
        """RN02: Técnico não pode ter mais de 5 chamados EM_ATENDIMENTO"""
        chamados = [self.chamado]
        for i in range(4):
            chamados.append(self.helpdesk.abrir_chamado(
                self.solicitante, f"Chamado {i}", "Descrição", Categoria.SOFTWARE, Prioridade.BAIXA
            ))
        for chamado in chamados:
            self.tecnico.assumir_chamado(chamado)
        sexto = self.helpdesk.abrir_chamado(
            self.solicitante, "Sexto", "Descrição", Categoria.SOFTWARE, Prioridade.BAIXA
        )
        with self.assertRaises(LimiteChamadosError):
            self.tecnico.assumir_chamado(sexto)
        self.assertEqual(sexto.status, StatusChamado.ABERTO)
        self.assertIsNone(sexto.responsavel)
        self.assertEqual(self.tecnico.contar_em_atendimento(), 5)

    def test_rn03_mudanca_de_status_gera_registro(self):
        """RN03: Mudança de status gera um registro de atendimento"""
        self.tecnico.assumir_chamado(self.chamado)
        registro = self.tecnico.registrar_atendimento(
            self.chamado, TipoAtendimento.OBSERVACAO, "Aguardando peça", StatusChamado.PENDENTE
        )
        self.assertEqual(self.chamado.status, StatusChamado.PENDENTE)
        self.assertEqual(len(self.chamado.listar_historico()), 2)
        self.assertEqual(registro.status_anterior, StatusChamado.EM_ATENDIMENTO)
        self.assertEqual(registro.status_novo, StatusChamado.PENDENTE)

    def test_rn03_recusar_resolvido_sem_registro_de_solucao(self):
        """RN03: Chamado não vai para RESOLVIDO sem registro de SOLUCAO"""
        self.tecnico.assumir_chamado(self.chamado)
        with self.assertRaises(SolucaoObrigatoriaError):
            self.tecnico.registrar_atendimento(
                self.chamado, TipoAtendimento.DIAGNOSTICO, "Problema identificado",
                StatusChamado.RESOLVIDO
            )
        self.assertEqual(self.chamado.status, StatusChamado.EM_ATENDIMENTO)
        self.assertEqual(len(self.chamado.listar_historico()), 1)


if __name__ == "__main__":
    unittest.main()
