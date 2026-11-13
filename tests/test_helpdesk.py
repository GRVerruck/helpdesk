import unittest

from helpdesk.enums import Categoria, Prioridade
from helpdesk.excecoes import (
    PermissaoNegadaError, TecnicoComChamadosError, UltimoAdministradorError,
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


if __name__ == "__main__":
    unittest.main()
