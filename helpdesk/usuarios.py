import hashlib
from abc import ABC, abstractmethod
from datetime import datetime

from helpdesk.enums import Permissao
from helpdesk.excecoes import LimiteChamadosError, SenhaIncorretaError


class Usuario(ABC):
    _proximo_id = 1

    def __init__(self, nome: str, email: str, senha: str):
        self.nome = nome
        self.email = email
        self.__senha_hash = self.__gerar_hash(senha)
        self._ativo = True
        self.__data_cadastro = datetime.now()
        self.__id = Usuario._proximo_id
        Usuario._proximo_id += 1

    @property
    def id(self) -> int:
        return self.__id

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str):
        if not valor or not valor.strip():
            raise ValueError("O nome não pode ser vazio.")
        self._nome = valor.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, valor: str):
        if not self._validar_email(valor):
            raise ValueError(f"E-mail inválido: {valor}")
        self._email = valor.strip().lower()

    @property
    def data_cadastro(self) -> datetime:
        return self.__data_cadastro

    def autenticar(self, senha: str) -> bool:
        return self.__senha_hash == self.__gerar_hash(senha)

    def alterar_senha(self, senha_atual: str, nova_senha: str) -> None:
        if not self.autenticar(senha_atual):
            raise SenhaIncorretaError("A senha atual está incorreta.")
        self.__senha_hash = self.__gerar_hash(nova_senha)

    def atualizar_dados(self, nome: str, email: str) -> None:
        self.nome = nome
        self.email = email

    def bloquear(self) -> None:
        self._ativo = False

    def desbloquear(self) -> None:
        self._ativo = True

    def esta_ativo(self) -> bool:
        return self._ativo

    def possui_permissao(self, permissao: Permissao) -> bool:
        return permissao in self.listar_permissoes()

    @abstractmethod
    def obter_perfil(self) -> str:
        pass

    @abstractmethod
    def listar_permissoes(self) -> set[Permissao]:
        pass

    @abstractmethod
    def pode_visualizar(self, chamado) -> bool:
        pass

    def _validar_email(self, email: str) -> bool:
        if not email or " " in email.strip():
            return False
        partes = email.strip().split("@")
        return len(partes) == 2 and partes[0] != "" and "." in partes[1]

    def __gerar_hash(self, senha: str) -> str:
        if not senha or len(senha) < 4:
            raise ValueError("A senha deve ter pelo menos 4 caracteres.")
        return hashlib.sha256(senha.encode()).hexdigest()

    def __str__(self) -> str:
        situacao = "ativo" if self._ativo else "bloqueado"
        return f"[{self.__id}] {self._nome} <{self._email}> - {self.obter_perfil()} ({situacao})"


class UsuarioComum(Usuario):
    def __init__(self, nome: str, email: str, senha: str, setor: str, ramal: str = ""):
        super().__init__(nome, email, senha)
        self.__setor = setor
        self.__ramal = ramal
        self.__chamados = []

    @property
    def setor(self) -> str:
        return self.__setor

    @setor.setter
    def setor(self, valor: str):
        self.__setor = valor

    @property
    def ramal(self) -> str:
        return self.__ramal

    @ramal.setter
    def ramal(self, valor: str):
        self.__ramal = valor

    def adicionar_chamado(self, chamado) -> None:
        self.__chamados.append(chamado)

    def listar_meus_chamados(self) -> list:
        return list(self.__chamados)

    def cancelar_chamado(self, chamado) -> None:
        chamado.cancelar(self)

    def obter_perfil(self) -> str:
        return "Usuário Comum"

    def listar_permissoes(self) -> set[Permissao]:
        return {
            Permissao.ACESSAR_APLICATIVO,
            Permissao.ABRIR_CHAMADO,
            Permissao.CONSULTAR_PROPRIOS_CHAMADOS,
            Permissao.CANCELAR_CHAMADO,
        }

    def pode_visualizar(self, chamado) -> bool:
        return chamado.solicitante is self


class Tecnico(Usuario):
    def __init__(self, nome: str, email: str, senha: str, especialidade: str):
        super().__init__(nome, email, senha)
        self.especialidade = especialidade
        self.__limite_chamados = 5
        self.__chamados_atribuidos = []

    @property
    def especialidade(self) -> str:
        return self.__especialidade

    @especialidade.setter
    def especialidade(self, valor: str):
        if not valor or not valor.strip():
            raise ValueError("A especialidade não pode ser vazia.")
        self.__especialidade = valor.strip()

    @property
    def limite_chamados(self) -> int:
        return self.__limite_chamados

    @property
    def chamados_atribuidos(self) -> list:
        return list(self.__chamados_atribuidos)

    def assumir_chamado(self, chamado) -> None:
        if not self.pode_assumir():
            raise LimiteChamadosError(
                f"{self.nome} já possui {self.__limite_chamados} chamados em atendimento."
            )
        chamado.atribuir_tecnico(self)
        self.__chamados_atribuidos.append(chamado)

    def registrar_atendimento(self, chamado, tipo, descricao: str, novo_status=None):
        return chamado.registrar_atendimento(self, tipo, descricao, novo_status)

    def contar_em_atendimento(self) -> int:
        total = 0
        for chamado in self.__chamados_atribuidos:
            if chamado.esta_em_atendimento():
                total += 1
        return total

    def pode_assumir(self) -> bool:
        return self.esta_ativo() and self.contar_em_atendimento() < self.__limite_chamados

    def obter_perfil(self) -> str:
        return "Técnico de TI"

    def listar_permissoes(self) -> set[Permissao]:
        return {
            Permissao.ACESSAR_APLICATIVO,
            Permissao.ATENDER_CHAMADO,
            Permissao.CONSULTAR_TODOS_CHAMADOS,
            Permissao.GERENCIAR_ESTOQUE,
        }

    def pode_visualizar(self, chamado) -> bool:
        return True


class Administrador(Usuario):
    def __init__(self, nome: str, email: str, senha: str, cargo: str):
        super().__init__(nome, email, senha)
        self.__cargo = cargo

    @property
    def cargo(self) -> str:
        return self.__cargo

    @cargo.setter
    def cargo(self, valor: str):
        self.__cargo = valor

    def obter_perfil(self) -> str:
        return "Administrador"

    def listar_permissoes(self) -> set[Permissao]:
        return {
            Permissao.ACESSAR_PAINEL_ADMIN,
            Permissao.CONSULTAR_TODOS_CHAMADOS,
            Permissao.GERENCIAR_TECNICOS,
            Permissao.GERENCIAR_USUARIOS,
            Permissao.GERENCIAR_ADMINISTRADORES,
        }

    def pode_visualizar(self, chamado) -> bool:
        return True
