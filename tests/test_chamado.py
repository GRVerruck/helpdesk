import unittest

from helpdesk.enums import Categoria, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.excecoes import (
    CancelamentoNaoPermitidoError, ChamadoNaoAbertoError, LimiteChamadosError,
    PermissaoNegadaError, SolucaoObrigatoriaError,
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

    def test_uc02_chamado_aberto_nasce_aberto_sem_responsavel(self):
        """UC02: Chamado aberto nasce ABERTO, sem responsável e com id sequencial"""
        segundo = self.helpdesk.abrir_chamado(
            self.solicitante, "Mouse quebrado", "Mouse não funciona",
            Categoria.HARDWARE, Prioridade.BAIXA
        )
        self.assertEqual(segundo.status, StatusChamado.ABERTO)
        self.assertIs(segundo.solicitante, self.solicitante)
        self.assertIsNone(segundo.responsavel)
        self.assertEqual(segundo.id, self.chamado.id + 1)
        self.assertIn(segundo, self.solicitante.listar_meus_chamados())

    def test_uc02_recusar_abertura_por_quem_nao_e_usuario_comum(self):
        """UC02: Técnico e administrador não abrem chamados"""
        for perfil in (self.tecnico, self.admin):
            with self.assertRaises(PermissaoNegadaError):
                self.helpdesk.abrir_chamado(
                    perfil, "Teste", "Descrição", Categoria.OUTROS, Prioridade.BAIXA
                )
        self.assertEqual(self.helpdesk.listar_chamados(self.admin), [self.chamado])

    def test_uc02_recusar_chamado_com_titulo_ou_descricao_vazios(self):
        """UC02: Chamado sem título ou sem descrição é recusado"""
        with self.assertRaises(ValueError):
            self.helpdesk.abrir_chamado(
                self.solicitante, "  ", "Descrição", Categoria.REDE, Prioridade.ALTA
            )
        with self.assertRaises(ValueError):
            self.helpdesk.abrir_chamado(
                self.solicitante, "Título", "", Categoria.REDE, Prioridade.ALTA
            )
        self.assertEqual(self.helpdesk.listar_chamados(self.admin), [self.chamado])

    def test_uc05_historico_lista_registros_em_ordem(self):
        """UC05: Histórico do chamado lista os registros em ordem cronológica"""
        self.tecnico.assumir_chamado(self.chamado)
        self.tecnico.registrar_atendimento(
            self.chamado, TipoAtendimento.OBSERVACAO, "Aguardando peça", StatusChamado.PENDENTE
        )
        historico = self.chamado.listar_historico()
        self.assertEqual(
            [registro.status_novo for registro in historico],
            [StatusChamado.EM_ATENDIMENTO, StatusChamado.PENDENTE]
        )
        self.assertIn("Aguardando peça", historico[1].resumir())
        self.assertIn(self.tecnico.nome, historico[1].resumir())

    def test_uc05_historico_retornado_nao_altera_o_chamado(self):
        """UC05: Alterar a lista de histórico retornada não altera o chamado"""
        self.tecnico.assumir_chamado(self.chamado)
        self.chamado.listar_historico().clear()
        self.assertEqual(len(self.chamado.listar_historico()), 1)

    def test_uc07_fila_lista_apenas_chamados_abertos(self):
        """UC07: Fila de chamados contém apenas chamados ABERTO"""
        segundo = self.helpdesk.abrir_chamado(
            self.solicitante, "Mouse quebrado", "Mouse não funciona",
            Categoria.HARDWARE, Prioridade.BAIXA
        )
        terceiro = self.helpdesk.abrir_chamado(
            self.solicitante, "Teclado quebrado", "Teclado não funciona",
            Categoria.HARDWARE, Prioridade.BAIXA
        )
        self.tecnico.assumir_chamado(self.chamado)
        self.solicitante.cancelar_chamado(terceiro)
        self.assertEqual(self.helpdesk.listar_fila(), [segundo])

    def test_uc09_resolver_chamado_com_registro_de_solucao(self):
        """UC09: Técnico responsável resolve o chamado com registro de SOLUCAO"""
        self.tecnico.assumir_chamado(self.chamado)
        self.tecnico.registrar_atendimento(
            self.chamado, TipoAtendimento.SOLUCAO, "Cabo de rede trocado", StatusChamado.RESOLVIDO
        )
        self.assertEqual(self.chamado.status, StatusChamado.RESOLVIDO)
        self.assertTrue(self.chamado.possui_solucao())
        self.assertIsNotNone(self.chamado.data_encerramento)
        self.assertEqual(self.tecnico.contar_em_atendimento(), 0)


if __name__ == "__main__":
    unittest.main()
