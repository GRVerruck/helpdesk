import unittest

from helpdesk.enums import Categoria, Permissao, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.excecoes import SenhaIncorretaError
from helpdesk.helpdesk import HelpDesk
from helpdesk.usuarios import Administrador


class TestUsuarios(unittest.TestCase):
    def setUp(self):
        self.admin = Administrador("Admin", "admin@empresa.com", "1234", "Gerente de TI")
        self.helpdesk = HelpDesk("Empresa", self.admin)
        self.usuario = self.helpdesk.cadastrar_usuario_comum(
            "Usuario", "usuario@empresa.com", "1234", "Financeiro"
        )
        self.tecnico = self.helpdesk.cadastrar_tecnico(
            self.admin, "Tecnico", "tecnico@empresa.com", "1234", "Redes"
        )

    def test_uc06_login_no_aplicativo_para_usuario_comum_e_tecnico(self):
        """UC06: Usuário comum e técnico entram no aplicativo, administrador não"""
        acesso = Permissao.ACESSAR_APLICATIVO
        self.assertIs(self.helpdesk.autenticar("usuario@empresa.com", "1234", acesso), self.usuario)
        self.assertIs(self.helpdesk.autenticar("tecnico@empresa.com", "1234", acesso), self.tecnico)
        self.assertIsNone(self.helpdesk.autenticar("admin@empresa.com", "1234", acesso))

    def test_uc16_login_no_painel_apenas_para_administrador(self):
        """UC16: Somente o administrador entra no painel administrativo"""
        acesso = Permissao.ACESSAR_PAINEL_ADMIN
        self.assertIs(self.helpdesk.autenticar("admin@empresa.com", "1234", acesso), self.admin)
        self.assertIsNone(self.helpdesk.autenticar("usuario@empresa.com", "1234", acesso))
        self.assertIsNone(self.helpdesk.autenticar("tecnico@empresa.com", "1234", acesso))

    def test_uc06_recusar_login_com_senha_incorreta(self):
        """UC06: Login é recusado com senha incorreta"""
        acesso = Permissao.ACESSAR_APLICATIVO
        self.assertIsNone(self.helpdesk.autenticar("usuario@empresa.com", "senha-errada", acesso))

    def test_uc21_usuario_bloqueado_nao_faz_login(self):
        """UC21: Usuário bloqueado não entra e volta a entrar ao ser desbloqueado"""
        acesso = Permissao.ACESSAR_APLICATIVO
        self.helpdesk.alterar_bloqueio(self.admin, self.usuario, True)
        self.assertIsNone(self.helpdesk.autenticar("usuario@empresa.com", "1234", acesso))
        self.helpdesk.alterar_bloqueio(self.admin, self.usuario, False)
        self.assertIs(self.helpdesk.autenticar("usuario@empresa.com", "1234", acesso), self.usuario)

    def test_uc03_usuario_comum_ve_apenas_os_proprios_chamados(self):
        """UC03: Usuário comum visualiza apenas os próprios chamados"""
        outro = self.helpdesk.cadastrar_usuario_comum(
            "Outro", "outro@empresa.com", "1234", "Compras"
        )
        meu_chamado = self.helpdesk.abrir_chamado(
            self.usuario, "Sem rede", "Computador sem acesso à rede",
            Categoria.REDE, Prioridade.ALTA
        )
        self.helpdesk.abrir_chamado(
            outro, "Mouse quebrado", "Mouse não funciona", Categoria.HARDWARE, Prioridade.BAIXA
        )
        self.assertEqual(self.helpdesk.listar_chamados(self.usuario), [meu_chamado])

    def test_uc23_administrador_ve_todos_os_chamados(self):
        """UC23: Administrador visualiza os chamados de todos"""
        outro = self.helpdesk.cadastrar_usuario_comum(
            "Outro", "outro@empresa.com", "1234", "Compras"
        )
        self.helpdesk.abrir_chamado(
            self.usuario, "Sem rede", "Computador sem acesso à rede",
            Categoria.REDE, Prioridade.ALTA
        )
        cancelado = self.helpdesk.abrir_chamado(
            outro, "Mouse quebrado", "Mouse não funciona", Categoria.HARDWARE, Prioridade.BAIXA
        )
        outro.cancelar_chamado(cancelado)
        self.assertEqual(len(self.helpdesk.listar_chamados(self.admin)), 2)

    def test_uc23_tecnico_nao_ve_chamados_encerrados_de_outros(self):
        """UC23: Técnico não consulta os chamados da empresa, só a fila e os que atende"""
        outro = self.helpdesk.cadastrar_usuario_comum(
            "Outro", "outro@empresa.com", "1234", "Compras"
        )
        segundo_tecnico = self.helpdesk.cadastrar_tecnico(
            self.admin, "Segundo Tecnico", "segundo.tecnico@empresa.com", "1234", "Hardware"
        )
        cancelado = self.helpdesk.abrir_chamado(
            outro, "Mouse quebrado", "Mouse não funciona", Categoria.HARDWARE, Prioridade.BAIXA
        )
        outro.cancelar_chamado(cancelado)
        resolvido = self.helpdesk.abrir_chamado(
            self.usuario, "Sem rede", "Computador sem acesso à rede",
            Categoria.REDE, Prioridade.ALTA
        )
        segundo_tecnico.assumir_chamado(resolvido)
        segundo_tecnico.registrar_atendimento(
            resolvido, TipoAtendimento.SOLUCAO, "Cabo de rede trocado", StatusChamado.RESOLVIDO
        )
        aberto = self.helpdesk.abrir_chamado(
            self.usuario, "Teclado quebrado", "Teclado não funciona",
            Categoria.HARDWARE, Prioridade.BAIXA
        )
        self.assertEqual(self.helpdesk.listar_chamados(self.tecnico), [aberto])

    def test_uc23_tecnico_ve_os_chamados_que_atende(self):
        """UC23: Técnico continua vendo os chamados que ele atende"""
        chamado = self.helpdesk.abrir_chamado(
            self.usuario, "Sem rede", "Computador sem acesso à rede",
            Categoria.REDE, Prioridade.ALTA
        )
        self.tecnico.assumir_chamado(chamado)
        self.assertIn(chamado, self.helpdesk.listar_chamados(self.tecnico))

    def test_senha_recusar_alteracao_com_senha_atual_incorreta(self):
        """Senha: Senha atual incorreta impede a alteração"""
        with self.assertRaises(SenhaIncorretaError):
            self.usuario.alterar_senha("senha-errada", "nova-senha")
        self.assertTrue(self.usuario.autenticar("1234"))

    def test_senha_nova_senha_substitui_a_anterior(self):
        """Senha: Nova senha passa a valer no lugar da anterior"""
        self.usuario.alterar_senha("1234", "nova-senha")
        self.assertTrue(self.usuario.autenticar("nova-senha"))
        self.assertFalse(self.usuario.autenticar("1234"))

    def test_validacao_recusar_dados_invalidos_no_cadastro(self):
        """Validação: Cadastro recusa nome vazio, e-mail inválido e senha curta"""
        total = len(self.helpdesk.usuarios)
        with self.assertRaises(ValueError):
            self.helpdesk.cadastrar_usuario_comum("  ", "a@empresa.com", "1234", "RH")
        with self.assertRaises(ValueError):
            self.helpdesk.cadastrar_usuario_comum("Ana", "email-invalido", "1234", "RH")
        with self.assertRaises(ValueError):
            self.helpdesk.cadastrar_usuario_comum("Ana", "ana@empresa.com", "123", "RH")
        self.assertEqual(len(self.helpdesk.usuarios), total)


if __name__ == "__main__":
    unittest.main()
