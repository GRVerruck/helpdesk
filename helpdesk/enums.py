from enum import Enum


class StatusChamado(Enum):
    ABERTO = "Aberto"
    EM_ATENDIMENTO = "Em atendimento"
    PENDENTE = "Pendente"
    RESOLVIDO = "Resolvido"
    CANCELADO = "Cancelado"


class Prioridade(Enum):
    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"
    CRITICA = "Crítica"


class Categoria(Enum):
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    REDE = "Rede"
    ACESSO = "Acesso"
    OUTROS = "Outros"


class TipoAtendimento(Enum):
    DIAGNOSTICO = "Diagnóstico"
    SOLUCAO = "Solução"
    OBSERVACAO = "Observação"


class TipoMovimentacao(Enum):
    ENTRADA = "Entrada"
    SAIDA = "Saída"
    BAIXA = "Baixa"


class Permissao(Enum):
    ACESSAR_APLICATIVO = "Acessar aplicativo"
    ACESSAR_PAINEL_ADMIN = "Acessar painel administrativo"
    ABRIR_CHAMADO = "Abrir chamado"
    CONSULTAR_PROPRIOS_CHAMADOS = "Consultar próprios chamados"
    CANCELAR_CHAMADO = "Cancelar chamado"
    ATENDER_CHAMADO = "Atender chamado"
    CONSULTAR_TODOS_CHAMADOS = "Consultar todos os chamados"
    GERENCIAR_ESTOQUE = "Gerenciar estoque"
    GERENCIAR_TECNICOS = "Gerenciar técnicos"
    GERENCIAR_USUARIOS = "Gerenciar usuários"
    GERENCIAR_ADMINISTRADORES = "Gerenciar administradores"
