from helpdesk.enums import Permissao
from helpdesk.excecoes import (
    EmailEmUsoError,
    PermissaoNegadaError,
    TecnicoComChamadosError,
    UltimoAdministradorError,
    UsuarioNaoEncontradoError,
)
from helpdesk.usuarios import Administrador, Tecnico, Usuario, UsuarioComum


class HelpDesk:
    def __init__(self, nome_empresa: str, admin_inicial: Administrador):
        if not isinstance(admin_inicial, Administrador):
            raise ValueError("O sistema precisa começar com um administrador.")
        self.__nome_empresa = nome_empresa
        self.__usuarios = [admin_inicial]

    @property
    def nome_empresa(self) -> str:
        return self.__nome_empresa

    @property
    def usuarios(self) -> list[Usuario]:
        return list(self.__usuarios)

    def cadastrar_usuario_comum(self, nome: str, email: str, senha: str, setor: str) -> UsuarioComum:
        if not self.__email_disponivel(email):
            raise EmailEmUsoError(f"O e-mail {email} já está cadastrado.")
        usuario = UsuarioComum(nome, email, senha, setor)
        self.__usuarios.append(usuario)
        return usuario

    def cadastrar_tecnico(self, admin: Administrador, nome: str, email: str, senha: str,
                          especialidade: str) -> Tecnico:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_TECNICOS)
        if not self.__email_disponivel(email):
            raise EmailEmUsoError(f"O e-mail {email} já está cadastrado.")
        tecnico = Tecnico(nome, email, senha, especialidade)
        self.__usuarios.append(tecnico)
        return tecnico

    def cadastrar_administrador(self, admin: Administrador, nome: str, email: str, senha: str,
                                cargo: str) -> Administrador:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_ADMINISTRADORES)
        if not self.__email_disponivel(email):
            raise EmailEmUsoError(f"O e-mail {email} já está cadastrado.")
        novo_admin = Administrador(nome, email, senha, cargo)
        self.__usuarios.append(novo_admin)
        return novo_admin

    def autenticar(self, email: str, senha: str, acesso: Permissao) -> Usuario | None:
        for usuario in self.__usuarios:
            if usuario.email == email.strip().lower():
                if usuario.esta_ativo() and usuario.autenticar(senha) and usuario.possui_permissao(acesso):
                    return usuario
                return None
        return None

    def listar_tecnicos(self) -> list[Tecnico]:
        tecnicos = []
        for usuario in self.__usuarios:
            if isinstance(usuario, Tecnico):
                tecnicos.append(usuario)
        return tecnicos

    def atualizar_tecnico(self, admin: Administrador, tecnico: Tecnico, nome: str,
                          especialidade: str) -> None:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_TECNICOS)
        self.__verificar_cadastro(tecnico)
        tecnico.nome = nome
        tecnico.especialidade = especialidade

    def excluir_tecnico(self, admin: Administrador, tecnico: Tecnico) -> None:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_TECNICOS)
        self.__verificar_cadastro(tecnico)
        if tecnico.contar_em_atendimento() > 0:
            raise TecnicoComChamadosError(
                f"{tecnico.nome} ainda possui chamados em atendimento e não pode ser excluído."
            )
        self.__usuarios.remove(tecnico)

    def alterar_bloqueio(self, admin: Administrador, usuario: Usuario, bloquear: bool) -> None:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_USUARIOS)
        self.__verificar_cadastro(usuario)
        if bloquear:
            if usuario.possui_permissao(Permissao.GERENCIAR_ADMINISTRADORES) and usuario.esta_ativo():
                if self.__contar_admins_ativos() <= 1:
                    raise UltimoAdministradorError("O sistema precisa ter pelo menos um administrador ativo.")
            usuario.bloquear()
        else:
            usuario.desbloquear()

    def desativar_administrador(self, admin: Administrador, alvo: Administrador) -> None:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_ADMINISTRADORES)
        self.__verificar_cadastro(alvo)
        if not alvo.possui_permissao(Permissao.GERENCIAR_ADMINISTRADORES):
            raise ValueError(f"{alvo.nome} não é um administrador.")
        if alvo.esta_ativo() and self.__contar_admins_ativos() <= 1:
            raise UltimoAdministradorError("O sistema precisa ter pelo menos um administrador ativo.")
        alvo.bloquear()

    def resumir_atividades(self, admin: Administrador) -> dict[str, int]:
        self.__verificar_permissao(admin, Permissao.CONSULTAR_TODOS_CHAMADOS)
        resumo = {}
        for tecnico in self.listar_tecnicos():
            resumo[tecnico.nome] = tecnico.contar_em_atendimento()
        return resumo

    def __contar_admins_ativos(self) -> int:
        total = 0
        for usuario in self.__usuarios:
            if usuario.possui_permissao(Permissao.GERENCIAR_ADMINISTRADORES) and usuario.esta_ativo():
                total += 1
        return total

    def __email_disponivel(self, email: str) -> bool:
        for usuario in self.__usuarios:
            if usuario.email == email.strip().lower():
                return False
        return True

    def __verificar_permissao(self, usuario: Usuario, permissao: Permissao) -> None:
        if usuario not in self.__usuarios or not usuario.esta_ativo() or not usuario.possui_permissao(permissao):
            raise PermissaoNegadaError(f"{usuario.nome} não tem permissão para esta operação.")

    def __verificar_cadastro(self, usuario: Usuario) -> None:
        if usuario not in self.__usuarios:
            raise UsuarioNaoEncontradoError(f"{usuario.nome} não está cadastrado no sistema.")
