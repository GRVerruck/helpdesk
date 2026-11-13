import unittest

from helpdesk.enums import Categoria, Prioridade
from helpdesk.excecoes import (
    EmailEmUsoError, PermissaoNegadaError, TecnicoComChamadosError, UltimoAdministradorError,
)
from helpdesk.helpdesk import HelpDesk
from helpdesk.usuarios import Administrador, Tecnico, UsuarioComum


class TestHelpDesk(unittest.TestCase):
    def setUp(self):
        self.admin = Administrador("Admin", "admin@empresa.com", "1234", "Gerente de TI")
        self.helpdesk = HelpDesk("Empresa", self.admin)
        self.usuario = self.helpdesk.cadastrar_usuario_comum(
            "Usuario", "usuario@empresa.com", "1234", "Financeiro"
        )
        self.tecnico = self.helpdesk.cadastrar_tecnico(
            self.admin, "Tecnico", "tecnico@empresa.com", "1234", "Redes"
        )

    def test_rn05_excluir_tecnico_sem_chamados_em_atendimento(self):
        """RN05: Técnico sem chamados em atendimento pode ser excluído"""
        self.helpdesk.excluir_tecnico(self.admin, self.tecnico)
        self.assertNotIn(self.tecnico, self.helpdesk.listar_tecnicos())

    def test_rn05_recusar_exclusao_com_chamados_em_atendimento(self):
        """RN05: Técnico com chamados EM_ATENDIMENTO não pode ser excluído"""
        chamado = self.helpdesk.abrir_chamado(
            self.usuario, "Sem rede", "Computador sem acesso à rede",
            Categoria.REDE, Prioridade.ALTA
        )
        self.tecnico.assumir_chamado(chamado)
        with self.assertRaises(TecnicoComChamadosError):
            self.helpdesk.excluir_tecnico(self.admin, self.tecnico)
        self.assertIn(self.tecnico, self.helpdesk.listar_tecnicos())

    def test_rn06_autocadastro_gera_apenas_usuario_comum(self):
        """RN06: Autocadastro gera apenas Usuário Comum"""
        novo = self.helpdesk.cadastrar_usuario_comum(
            "Novo", "novo@empresa.com", "1234", "Compras"
        )
        self.assertIsInstance(novo, UsuarioComum)
        self.assertNotIsInstance(novo, (Tecnico, Administrador))

    def test_rn06_recusar_cadastro_de_tecnico_por_nao_administrador(self):
        """RN06: Usuário que não é administrador não cadastra técnico"""
        with self.assertRaises(PermissaoNegadaError):
            self.helpdesk.cadastrar_tecnico(
                self.usuario, "Intruso", "intruso@empresa.com", "1234", "Redes"
            )
        self.assertEqual(self.helpdesk.listar_tecnicos(), [self.tecnico])

    def test_rn06_manter_ao_menos_um_administrador_ativo(self):
        """RN06: O sistema mantém ao menos um administrador ativo"""
        segundo_admin = self.helpdesk.cadastrar_administrador(
            self.admin, "Segundo", "segundo@empresa.com", "1234", "Coordenador"
        )
        self.helpdesk.desativar_administrador(self.admin, segundo_admin)
        self.assertFalse(segundo_admin.esta_ativo())
        with self.assertRaises(UltimoAdministradorError):
            self.helpdesk.desativar_administrador(self.admin, self.admin)
        self.assertTrue(self.admin.esta_ativo())

    def test_uc17_administrador_cadastra_tecnico(self):
        """UC17: Administrador cadastra técnico"""
        novo = self.helpdesk.cadastrar_tecnico(
            self.admin, "Novo Tecnico", "novo.tecnico@empresa.com", "1234", "Hardware"
        )
        self.assertIsInstance(novo, Tecnico)
        self.assertIn(novo, self.helpdesk.listar_tecnicos())

    def test_uc17_recusar_email_ja_cadastrado(self):
        """UC17: E-mail já cadastrado é recusado"""
        with self.assertRaises(EmailEmUsoError):
            self.helpdesk.cadastrar_tecnico(
                self.admin, "Copia", "TECNICO@empresa.com", "1234", "Redes"
            )
        self.assertEqual(self.helpdesk.listar_tecnicos(), [self.tecnico])

    def test_uc18_consultar_tecnicos_lista_somente_tecnicos(self):
        """UC18: Consulta de técnicos lista somente técnicos"""
        segundo = self.helpdesk.cadastrar_tecnico(
            self.admin, "Segundo Tecnico", "segundo.tecnico@empresa.com", "1234", "Hardware"
        )
        self.assertEqual(self.helpdesk.listar_tecnicos(), [self.tecnico, segundo])

    def test_uc19_atualizar_nome_e_especialidade_do_tecnico(self):
        """UC19: Administrador atualiza nome e especialidade do técnico"""
        self.helpdesk.atualizar_tecnico(self.admin, self.tecnico, "Tecnico Senior", "Servidores")
        self.assertEqual(self.tecnico.nome, "Tecnico Senior")
        self.assertEqual(self.tecnico.especialidade, "Servidores")

    def test_uc19_recusar_atualizacao_por_nao_administrador(self):
        """UC19: Usuário que não é administrador não atualiza técnico"""
        with self.assertRaises(PermissaoNegadaError):
            self.helpdesk.atualizar_tecnico(self.usuario, self.tecnico, "Outro Nome", "Servidores")
        self.assertEqual(self.tecnico.nome, "Tecnico")
        self.assertEqual(self.tecnico.especialidade, "Redes")

    def test_uc22_administrador_cadastra_outro_administrador(self):
        """UC22: Administrador cadastra outro administrador"""
        novo = self.helpdesk.cadastrar_administrador(
            self.admin, "Segundo", "segundo@empresa.com", "1234", "Coordenador"
        )
        self.assertIsInstance(novo, Administrador)
        self.assertIn(novo, self.helpdesk.usuarios)

    def test_uc22_recusar_cadastro_de_administrador_por_nao_administrador(self):
        """UC22: Usuário que não é administrador não cadastra administrador"""
        total = len(self.helpdesk.usuarios)
        with self.assertRaises(PermissaoNegadaError):
            self.helpdesk.cadastrar_administrador(
                self.usuario, "Intruso", "intruso@empresa.com", "1234", "Diretor"
            )
        self.assertEqual(len(self.helpdesk.usuarios), total)

    def test_uc24_resumir_atividades_dos_tecnicos(self):
        """UC24: Resumo mostra quantos chamados cada técnico atende"""
        self.helpdesk.cadastrar_tecnico(
            self.admin, "Segundo Tecnico", "segundo.tecnico@empresa.com", "1234", "Hardware"
        )
        for numero in range(2):
            chamado = self.helpdesk.abrir_chamado(
                self.usuario, f"Chamado {numero}", "Descrição", Categoria.SOFTWARE, Prioridade.BAIXA
            )
            self.tecnico.assumir_chamado(chamado)
        resumo = self.helpdesk.resumir_atividades(self.admin)
        self.assertEqual(resumo, {"Tecnico": 2, "Segundo Tecnico": 0})

    def test_uc24_recusar_resumo_por_quem_nao_e_administrador(self):
        """UC24: Somente o administrador acompanha atividades dos técnicos"""
        for perfil in (self.usuario, self.tecnico):
            with self.assertRaises(PermissaoNegadaError):
                self.helpdesk.resumir_atividades(perfil)
        self.assertEqual(self.helpdesk.resumir_atividades(self.admin), {"Tecnico": 0})


if __name__ == "__main__":
    unittest.main()
