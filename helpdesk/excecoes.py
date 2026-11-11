class HelpDeskError(Exception):
    pass


class PermissaoNegadaError(HelpDeskError):
    pass


class EmailEmUsoError(HelpDeskError):
    pass


class SenhaIncorretaError(HelpDeskError):
    pass


class UsuarioNaoEncontradoError(HelpDeskError):
    pass


class TecnicoComChamadosError(HelpDeskError):
    pass


class UltimoAdministradorError(HelpDeskError):
    pass


class LimiteChamadosError(HelpDeskError):
    pass


class ChamadoNaoAbertoError(HelpDeskError):
    pass


class CancelamentoNaoPermitidoError(HelpDeskError):
    pass


class TransicaoInvalidaError(HelpDeskError):
    pass


class SolucaoObrigatoriaError(HelpDeskError):
    pass


class EstoqueInsuficienteError(HelpDeskError):
    pass


class EquipamentoBaixadoError(HelpDeskError):
    pass
