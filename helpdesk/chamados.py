from datetime import datetime

from helpdesk.enums import Categoria, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.excecoes import ChamadoNaoAbertoError, LimiteChamadosError, PermissaoNegadaError
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
        if not tecnico.pode_assumir():
            raise LimiteChamadosError(
                f"{tecnico.nome} já possui {tecnico.limite_chamados} chamados em atendimento."
            )

        registro = RegistroAtendimento(
            tecnico, TipoAtendimento.OBSERVACAO, "Chamado assumido pelo técnico.",
            self.__status, StatusChamado.EM_ATENDIMENTO
        )
        self.__responsavel = tecnico
        self.__status = StatusChamado.EM_ATENDIMENTO
        self.__registros.append(registro)
        tecnico._adicionar_chamado(self)

    def listar_historico(self) -> list[RegistroAtendimento]:
        return list(self.__registros)

    def esta_em_atendimento(self) -> bool:
        return self.__status == StatusChamado.EM_ATENDIMENTO
