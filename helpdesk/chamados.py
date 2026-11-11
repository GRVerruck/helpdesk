from datetime import datetime

from helpdesk.enums import Categoria, Prioridade, StatusChamado


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
