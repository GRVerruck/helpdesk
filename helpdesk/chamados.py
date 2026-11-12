from datetime import datetime

from helpdesk.enums import Categoria, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.excecoes import (
    CancelamentoNaoPermitidoError, ChamadoNaoAbertoError, LimiteChamadosError,
    PermissaoNegadaError, SolucaoObrigatoriaError, TransicaoInvalidaError,
)
from helpdesk.usuarios import Tecnico, Usuario


class RegistroAtendimento:
    def __init__(self, autor: Usuario, tipo: TipoAtendimento, descricao: str,
                 status_anterior: StatusChamado, status_novo: StatusChamado):
        self.__data_hora = datetime.now()
        self.__autor = autor
        self.__tipo = tipo
        self.__descricao = descricao
        self.__status_anterior = status_anterior
        self.__status_novo = status_novo

    @property
    def data_hora(self) -> datetime:
        return self.__data_hora

    @property
    def autor(self) -> Usuario:
        return self.__autor

    @property
    def tipo(self) -> TipoAtendimento:
        return self.__tipo

    @property
    def descricao(self) -> str:
        return self.__descricao

    @property
    def status_anterior(self) -> StatusChamado:
        return self.__status_anterior

    @property
    def status_novo(self) -> StatusChamado:
        return self.__status_novo

    def eh_solucao(self) -> bool:
        return self.__tipo == TipoAtendimento.SOLUCAO

    def resumir(self) -> str:
        return (
            f"{self.__data_hora:%d/%m/%Y %H:%M} - {self.__autor.nome}: "
            f"{self.__tipo.value} - {self.__descricao} "
            f"({self.__status_anterior.value} -> {self.__status_novo.value})"
        )


class Chamado:
    def __init__(self, id: int, titulo: str, descricao: str, categoria: Categoria,
                 prioridade: Prioridade, solicitante):
        if not isinstance(titulo, str) or not titulo.strip():
            raise ValueError("O título não pode ser vazio.")
        if not isinstance(descricao, str) or not descricao.strip():
            raise ValueError("A descrição não pode ser vazia.")
        if not isinstance(categoria, Categoria):
            raise ValueError("A categoria do chamado é inválida.")
        if not isinstance(prioridade, Prioridade):
            raise ValueError("A prioridade do chamado é inválida.")

        self.__id = id
        self.__titulo = titulo.strip()
        self.__descricao = descricao.strip()
        self.__categoria = categoria
        self.__prioridade = prioridade
        self.__status = StatusChamado.ABERTO
        self.__data_abertura = datetime.now()
        self.__data_encerramento = None
        self.__solicitante = solicitante
        self.__responsavel = None
        self.__registros = []

    @property
    def id(self) -> int:
        return self.__id

    @property
    def titulo(self) -> str:
        return self.__titulo

    @property
    def descricao(self) -> str:
        return self.__descricao

    @property
    def categoria(self) -> Categoria:
        return self.__categoria

    @property
    def prioridade(self) -> Prioridade:
        return self.__prioridade

    @property
    def status(self) -> StatusChamado:
        return self.__status

    @property
    def data_abertura(self) -> datetime:
        return self.__data_abertura

    @property
    def data_encerramento(self) -> datetime | None:
        return self.__data_encerramento

    @property
    def solicitante(self):
        return self.__solicitante

    @property
    def responsavel(self):
        return self.__responsavel

    def atribuir_tecnico(self, tecnico: Tecnico) -> None:
        if not isinstance(tecnico, Tecnico) or not tecnico.esta_ativo():
            raise PermissaoNegadaError("Somente um técnico ativo pode assumir o chamado.")
        if self.__status != StatusChamado.ABERTO:
            raise ChamadoNaoAbertoError("Somente chamados abertos podem ser assumidos.")
        self.registrar_atendimento(
            tecnico, TipoAtendimento.OBSERVACAO, "Chamado assumido pelo técnico.",
            StatusChamado.EM_ATENDIMENTO
        )

    def registrar_atendimento(self, autor: Usuario, tipo: TipoAtendimento, descricao: str,
                             novo_status: StatusChamado | None = None) -> RegistroAtendimento:
        if not isinstance(autor, Usuario) or not autor.esta_ativo():
            raise PermissaoNegadaError("Somente usuários ativos podem registrar atendimentos.")
        if not isinstance(tipo, TipoAtendimento):
            raise ValueError("O tipo de atendimento é inválido.")
        if not isinstance(descricao, str) or not descricao.strip():
            raise ValueError("A descrição não pode ser vazia.")
        if novo_status is None:
            novo_status = self.__status
        if not isinstance(novo_status, StatusChamado):
            raise ValueError("O status do chamado é inválido.")

        if novo_status == StatusChamado.CANCELADO:
            if autor is not self.__solicitante or self.__status != StatusChamado.ABERTO:
                raise CancelamentoNaoPermitidoError(
                    "Somente o solicitante pode cancelar um chamado ainda aberto."
                )
            if tipo != TipoAtendimento.OBSERVACAO:
                raise PermissaoNegadaError("O cancelamento deve gerar uma observação.")
        elif self.__status == StatusChamado.ABERTO:
            if (not isinstance(autor, Tecnico) or novo_status != StatusChamado.EM_ATENDIMENTO
                    or tipo != TipoAtendimento.OBSERVACAO):
                raise PermissaoNegadaError("O chamado deve ser assumido por um técnico.")
        elif not isinstance(autor, Tecnico) or autor is not self.__responsavel:
            raise PermissaoNegadaError("Somente o técnico responsável pode registrar atendimentos.")

        if not self.__validar_transicao(novo_status):
            raise TransicaoInvalidaError("A mudança de status não é permitida.")
        if novo_status == StatusChamado.EM_ATENDIMENTO and not self.esta_em_atendimento():
            if not autor.pode_assumir():
                raise LimiteChamadosError(
                    f"{autor.nome} já possui {autor.limite_chamados} chamados em atendimento."
                )
        if novo_status == StatusChamado.RESOLVIDO:
            if tipo != TipoAtendimento.SOLUCAO and not self.possui_solucao():
                raise SolucaoObrigatoriaError("É necessário registrar uma solução para resolver o chamado.")

        registro = RegistroAtendimento(autor, tipo, descricao.strip(), self.__status, novo_status)
        if self.__status == StatusChamado.ABERTO and novo_status == StatusChamado.EM_ATENDIMENTO:
            self.__responsavel = autor
            autor._adicionar_chamado(self)
        self.__status = novo_status
        self.__registros.append(registro)
        if novo_status in (StatusChamado.RESOLVIDO, StatusChamado.CANCELADO):
            self.__data_encerramento = registro.data_hora
        return registro

    def cancelar(self, usuario: Usuario) -> None:
        self.registrar_atendimento(
            usuario, TipoAtendimento.OBSERVACAO, "Chamado cancelado pelo solicitante.",
            StatusChamado.CANCELADO
        )

    def possui_solucao(self) -> bool:
        for registro in self.__registros:
            if registro.eh_solucao():
                return True
        return False

    def __validar_transicao(self, novo_status: StatusChamado) -> bool:
        if self.__status == StatusChamado.ABERTO:
            return novo_status in (StatusChamado.EM_ATENDIMENTO, StatusChamado.CANCELADO)
        if self.__status in (StatusChamado.EM_ATENDIMENTO, StatusChamado.PENDENTE):
            return novo_status in (
                StatusChamado.EM_ATENDIMENTO, StatusChamado.PENDENTE, StatusChamado.RESOLVIDO
            )
        return False

    def listar_historico(self) -> list[RegistroAtendimento]:
        return list(self.__registros)

    def esta_em_atendimento(self) -> bool:
        return self.__status == StatusChamado.EM_ATENDIMENTO
