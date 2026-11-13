from helpdesk.chamados import Chamado
from helpdesk.enums import Categoria, Permissao, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.estoque import Equipamento, Estoque
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
        self.__chamados = []
        self.__estoque = Estoque()
        self.__proximo_id_chamado = 1

    @property
    def nome_empresa(self) -> str:
        return self.__nome_empresa

    @property
    def usuarios(self) -> list[Usuario]:
        return list(self.__usuarios)

    # UC01
    def cadastrar_usuario_comum(self, nome: str, email: str, senha: str, setor: str) -> UsuarioComum:
        if not self.__email_disponivel(email):
            raise EmailEmUsoError(f"O e-mail {email} já está cadastrado.")
        usuario = UsuarioComum(nome, email, senha, setor)
        self.__usuarios.append(usuario)
        return usuario

    # UC17
    def cadastrar_tecnico(self, admin: Administrador, nome: str, email: str, senha: str,
                          especialidade: str) -> Tecnico:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_TECNICOS)
        if not self.__email_disponivel(email):
            raise EmailEmUsoError(f"O e-mail {email} já está cadastrado.")
        tecnico = Tecnico(nome, email, senha, especialidade)
        self.__usuarios.append(tecnico)
        return tecnico

    # UC22
    def cadastrar_administrador(self, admin: Administrador, nome: str, email: str, senha: str,
                                cargo: str) -> Administrador:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_ADMINISTRADORES)
        if not self.__email_disponivel(email):
            raise EmailEmUsoError(f"O e-mail {email} já está cadastrado.")
        novo_admin = Administrador(nome, email, senha, cargo)
        self.__usuarios.append(novo_admin)
        return novo_admin

    # UC06 e UC16 
    def autenticar(self, email: str, senha: str, acesso: Permissao) -> Usuario | None:
        for usuario in self.__usuarios:
            if usuario.email == email.strip().lower():
                if usuario.esta_ativo() and usuario.autenticar(senha) and usuario.possui_permissao(acesso):
                    return usuario
                return None
        return None

    # UC02
    def abrir_chamado(self, solicitante: UsuarioComum, titulo: str, descricao: str,
                      categoria: Categoria, prioridade: Prioridade) -> Chamado:
        self.__verificar_permissao(solicitante, Permissao.ABRIR_CHAMADO)
        chamado = Chamado(
            self.__proximo_id_chamado, titulo, descricao, categoria, prioridade, solicitante
        )
        self.__chamados.append(chamado)
        solicitante.adicionar_chamado(chamado)
        self.__proximo_id_chamado += 1
        return chamado

    # UC03 e UC23
    def listar_chamados(self, usuario: Usuario) -> list[Chamado]:
        permissao = Permissao.CONSULTAR_PROPRIOS_CHAMADOS
        if usuario.possui_permissao(Permissao.CONSULTAR_TODOS_CHAMADOS):
            permissao = Permissao.CONSULTAR_TODOS_CHAMADOS
        self.__verificar_permissao(usuario, permissao)

        chamados = []
        for chamado in self.__chamados:
            if usuario.pode_visualizar(chamado):
                chamados.append(chamado)
        return chamados

    # UC07
    def listar_fila(self) -> list[Chamado]:
        fila = []
        for chamado in self.__chamados:
            if chamado.status == StatusChamado.ABERTO:
                fila.append(chamado)
        return fila

    # UC18
    def listar_tecnicos(self) -> list[Tecnico]:
        tecnicos = []
        for usuario in self.__usuarios:
            if isinstance(usuario, Tecnico):
                tecnicos.append(usuario)
        return tecnicos

    # UC19
    def atualizar_tecnico(self, admin: Administrador, tecnico: Tecnico, nome: str,
                          especialidade: str) -> None:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_TECNICOS)
        self.__verificar_cadastro(tecnico)
        tecnico.nome = nome
        tecnico.especialidade = especialidade

    # UC20 (RN05)
    def excluir_tecnico(self, admin: Administrador, tecnico: Tecnico) -> None:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_TECNICOS)
        self.__verificar_cadastro(tecnico)
        if tecnico.contar_em_atendimento() > 0:
            raise TecnicoComChamadosError(
                f"{tecnico.nome} ainda possui chamados em atendimento e não pode ser excluído."
            )
        self.__usuarios.remove(tecnico)

    # UC21 (RN06)
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

    # UC22 (RN06)
    def desativar_administrador(self, admin: Administrador, alvo: Administrador) -> None:
        self.__verificar_permissao(admin, Permissao.GERENCIAR_ADMINISTRADORES)
        self.__verificar_cadastro(alvo)
        if not alvo.possui_permissao(Permissao.GERENCIAR_ADMINISTRADORES):
            raise ValueError(f"{alvo.nome} não é um administrador.")
        if alvo.esta_ativo() and self.__contar_admins_ativos() <= 1:
            raise UltimoAdministradorError("O sistema precisa ter pelo menos um administrador ativo.")
        alvo.bloquear()

    # UC24
    def resumir_atividades(self, admin: Administrador) -> dict[str, int]:
        self.__verificar_permissao(admin, Permissao.CONSULTAR_TODOS_CHAMADOS)
        resumo = {}
        for tecnico in self.listar_tecnicos():
            resumo[tecnico.nome] = tecnico.contar_em_atendimento()
        return resumo

    # UC12
    def cadastrar_equipamento(self, tecnico: Tecnico, codigo: str, descricao: str, tipo: str,
                              quantidade: int = 0, quantidade_minima: int = 0) -> Equipamento:
        self.__verificar_permissao(tecnico, Permissao.GERENCIAR_ESTOQUE)
        equipamento = Equipamento(codigo, descricao, tipo, quantidade, quantidade_minima)
        self.__estoque.cadastrar_equipamento(equipamento)
        return equipamento

    # UC13
    def listar_equipamentos(self, tecnico: Tecnico, apenas_ativos: bool = True) -> list[Equipamento]:
        self.__verificar_permissao(tecnico, Permissao.GERENCIAR_ESTOQUE)
        return self.__estoque.listar(apenas_ativos)

    def listar_equipamentos_abaixo_do_minimo(self, tecnico: Tecnico) -> list[Equipamento]:
        self.__verificar_permissao(tecnico, Permissao.GERENCIAR_ESTOQUE)
        return self.__estoque.listar_abaixo_do_minimo()

    # UC14 
    def atualizar_equipamento(self, tecnico: Tecnico, codigo: str, descricao: str,
                              quantidade_minima: int) -> None:
        self.__verificar_permissao(tecnico, Permissao.GERENCIAR_ESTOQUE)
        self.__obter_equipamento(codigo).atualizar_dados(descricao, quantidade_minima)

    # UC14 
    def repor_equipamento(self, tecnico: Tecnico, codigo: str, quantidade: int, motivo: str) -> None:
        self.__verificar_permissao(tecnico, Permissao.GERENCIAR_ESTOQUE)
        self.__obter_equipamento(codigo).registrar_entrada(quantidade, tecnico, motivo)

    # UC11
    def registrar_saida_equipamento(self, tecnico: Tecnico, codigo: str, quantidade: int,
                                    chamado: Chamado) -> None:
        self.__verificar_permissao(tecnico, Permissao.GERENCIAR_ESTOQUE)
        equipamento = self.__obter_equipamento(codigo)
        if chamado not in self.__chamados:
            raise ValueError("O chamado não pertence a este sistema.")
        if chamado.responsavel is not tecnico or chamado.status not in (
                StatusChamado.EM_ATENDIMENTO, StatusChamado.PENDENTE):
            raise PermissaoNegadaError(
                "Somente o técnico responsável por um chamado em andamento pode registrar saída."
            )
        equipamento.registrar_saida(quantidade, tecnico, chamado)
        chamado.registrar_atendimento(
            tecnico, TipoAtendimento.OBSERVACAO,
            f"Saída de {quantidade} un. de {equipamento.descricao} ({equipamento.codigo}).",
        )

    # UC15
    def dar_baixa_equipamento(self, tecnico: Tecnico, codigo: str, motivo: str) -> None:
        self.__verificar_permissao(tecnico, Permissao.GERENCIAR_ESTOQUE)
        self.__obter_equipamento(codigo).dar_baixa(tecnico, motivo)

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

    def __obter_equipamento(self, codigo: str) -> Equipamento:
        equipamento = self.__estoque.buscar(codigo)
        if equipamento is None:
            raise ValueError(f"Equipamento {codigo} não encontrado.")
        return equipamento

    def __verificar_cadastro(self, usuario: Usuario) -> None:
        if usuario not in self.__usuarios:
            raise UsuarioNaoEncontradoError(f"{usuario.nome} não está cadastrado no sistema.")
