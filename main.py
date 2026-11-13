from helpdesk.enums import Categoria, Permissao, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.excecoes import HelpDeskError
from helpdesk.helpdesk import HelpDesk
from helpdesk.usuarios import Administrador


def secao(titulo):
    print(f"\n{'=' * 72}\n{titulo}\n{'=' * 72}")


def descrever_chamado(chamado):
    responsavel = chamado.responsavel.nome if chamado.responsavel else "sem responsável"
    return (f"#{chamado.id} [{chamado.status.value}] {chamado.titulo} "
            f"- {chamado.prioridade.value} ({responsavel})")


def descrever_equipamento(equipamento):
    situacao = "ativo" if equipamento.ativo else "baixado"
    return (f"{equipamento.codigo} - {equipamento.descricao}: {equipamento.quantidade} un. "
            f"(mínimo {equipamento.quantidade_minima}, {situacao})")


def executar(descricao, acao):
    acao()
    print(f"[OK] {descricao}")


def tentar(regra, acao):
    try:
        acao()
    except (HelpDeskError, ValueError) as erro:
        print(f"[BLOQUEADO] {regra}\n            {type(erro).__name__}: {erro}")
    else:
        print(f"[FALHA] {regra}: a operação deveria ter sido recusada")


def main():
    secao("1. Criação do sistema")
    admin = Administrador("Marina Souza", "marina@empresa.com", "admin123", "Gerente de TI")
    helpdesk = HelpDesk("Empresa de Teste", admin)
    print(f"Empresa: {helpdesk.nome_empresa}")
    print(f"Administrador inicial: {admin}")

    secao("2. Cadastro de usuários (UC01, UC17, UC22)")
    ana = helpdesk.cadastrar_usuario_comum("Ana Lima", "ana@empresa.com", "ana123", "Financeiro")
    bruno = helpdesk.cadastrar_usuario_comum("Bruno Reis", "bruno@empresa.com", "bruno123", "RH")
    carlos = helpdesk.cadastrar_tecnico(
        admin, "Carlos Dias", "carlos@empresa.com", "carlos123", "Redes"
    )
    diana = helpdesk.cadastrar_tecnico(
        admin, "Diana Alves", "diana@empresa.com", "diana123", "Hardware"
    )
    helena = helpdesk.cadastrar_administrador(
        admin, "Helena Costa", "helena@empresa.com", "helena123", "Coordenadora"
    )
    for usuario in helpdesk.usuarios:
        print(usuario)

    secao("3. Login por perfil (UC06, UC16)")
    tentativas = [
        ("ana@empresa.com", "ana123", Permissao.ACESSAR_APLICATIVO, "Ana no aplicativo"),
        ("carlos@empresa.com", "carlos123", Permissao.ACESSAR_APLICATIVO, "Carlos no aplicativo"),
        ("marina@empresa.com", "admin123", Permissao.ACESSAR_PAINEL_ADMIN, "Marina no painel"),
        ("ana@empresa.com", "ana123", Permissao.ACESSAR_PAINEL_ADMIN, "Ana no painel"),
        ("marina@empresa.com", "admin123", Permissao.ACESSAR_APLICATIVO, "Marina no aplicativo"),
        ("ana@empresa.com", "errada", Permissao.ACESSAR_APLICATIVO, "Ana com senha errada"),
    ]
    for email, senha, acesso, descricao in tentativas:
        usuario = helpdesk.autenticar(email, senha, acesso)
        print(f"{descricao}: {'acesso liberado' if usuario else 'acesso negado'}")

    secao("4. Abertura de chamados e fila (UC02, UC03, UC07)")
    chamado1 = helpdesk.abrir_chamado(
        ana, "Computador sem rede", "Sem acesso à rede desde cedo.",
        Categoria.REDE, Prioridade.ALTA
    )
    chamado2 = helpdesk.abrir_chamado(
        bruno, "Monitor piscando", "A tela pisca a cada poucos segundos.",
        Categoria.HARDWARE, Prioridade.MEDIA
    )
    chamado3 = helpdesk.abrir_chamado(
        ana, "Instalar planilhas", "Preciso do pacote de planilhas instalado.",
        Categoria.SOFTWARE, Prioridade.BAIXA
    )
    print("Chamados da Ana:")
    for chamado in helpdesk.listar_chamados(ana):
        print(f"  {descrever_chamado(chamado)}")
    print("Fila de chamados abertos:")
    for chamado in helpdesk.listar_fila():
        print(f"  {descrever_chamado(chamado)}")

    secao("5. Atendimento de um chamado (UC08, UC09, UC10, UC05)")
    carlos.assumir_chamado(chamado1)
    carlos.registrar_atendimento(
        chamado1, TipoAtendimento.DIAGNOSTICO, "Cabo de rede com defeito."
    )
    carlos.registrar_atendimento(
        chamado1, TipoAtendimento.OBSERVACAO, "Aguardando cabo novo do almoxarifado.",
        StatusChamado.PENDENTE
    )
    carlos.registrar_atendimento(
        chamado1, TipoAtendimento.OBSERVACAO, "Cabo recebido, retomando o atendimento.",
        StatusChamado.EM_ATENDIMENTO
    )
    carlos.registrar_atendimento(
        chamado1, TipoAtendimento.SOLUCAO, "Cabo de rede substituído.", StatusChamado.RESOLVIDO
    )
    print(descrever_chamado(chamado1))
    print("Histórico:")
    for registro in chamado1.listar_historico():
        print(f"  {registro.resumir()}")

    secao("6. Estoque (UC12, UC13, UC14, UC11, UC15)")
    diana.assumir_chamado(chamado2)
    helpdesk.cadastrar_equipamento(diana, "CAB-HDMI", "Cabo HDMI", "Cabo", 4, 3)
    helpdesk.cadastrar_equipamento(diana, "TEC-01", "Teclado USB", "Periférico", 10, 2)
    print("Estoque inicial:")
    for equipamento in helpdesk.listar_equipamentos(diana):
        print(f"  {descrever_equipamento(equipamento)}")

    helpdesk.registrar_saida_equipamento(diana, "CAB-HDMI", 2, chamado2)
    print(f"\nSaída de 2 cabos HDMI para o chamado #{chamado2.id}")
    print("Abaixo do mínimo:")
    for equipamento in helpdesk.listar_equipamentos_abaixo_do_minimo(diana):
        print(f"  {descrever_equipamento(equipamento)}")

    helpdesk.repor_equipamento(diana, "CAB-HDMI", 5, "Compra mensal")
    helpdesk.atualizar_equipamento(diana, "CAB-HDMI", "Cabo HDMI 2m", 3)
    helpdesk.dar_baixa_equipamento(diana, "TEC-01", "Teclado com teclas quebradas")
    print("\nEstoque final (incluindo baixados):")
    for equipamento in helpdesk.listar_equipamentos(diana, False):
        print(f"  {descrever_equipamento(equipamento)}")
    print(f"Histórico do chamado #{chamado2.id}:")
    for registro in chamado2.listar_historico():
        print(f"  {registro.resumir()}")

    secao("7. Administração (UC18, UC19, UC21, UC23, UC24)")
    helpdesk.atualizar_tecnico(admin, diana, "Diana Alves Pereira", "Hardware e Servidores")
    print("Técnicos cadastrados:")
    for tecnico in helpdesk.listar_tecnicos():
        print(f"  {tecnico} | especialidade: {tecnico.especialidade}")

    helpdesk.alterar_bloqueio(admin, bruno, True)
    print(f"\nBruno bloqueado. Login: "
          f"{'liberado' if helpdesk.autenticar('bruno@empresa.com', 'bruno123', Permissao.ACESSAR_APLICATIVO) else 'negado'}")
    helpdesk.alterar_bloqueio(admin, bruno, False)
    print(f"Bruno desbloqueado. Login: "
          f"{'liberado' if helpdesk.autenticar('bruno@empresa.com', 'bruno123', Permissao.ACESSAR_APLICATIVO) else 'negado'}")

    print("\nChamados da empresa:")
    for chamado in helpdesk.listar_chamados(admin):
        print(f"  {descrever_chamado(chamado)}")
    print("Atividades dos técnicos (chamados em atendimento):")
    for nome, total in helpdesk.resumir_atividades(admin).items():
        print(f"  {nome}: {total}")

    secao("8. Regras de negócio (violações recusadas)")
    print("-- RN01: cancelamento")
    tentar("RN01: outro usuário tenta cancelar o chamado da Ana",
           lambda: bruno.cancelar_chamado(chamado3))
    tentar("RN01: cancelar chamado que já está em atendimento",
           lambda: bruno.cancelar_chamado(chamado2))
    executar("RN01: a própria Ana cancela o chamado ainda aberto",
             lambda: ana.cancelar_chamado(chamado3))

    print("\n-- RN02: assumir chamados")
    extras = [
        helpdesk.abrir_chamado(
            ana, f"Chamado extra {numero}", "Chamado criado para o teste de limite.",
            Categoria.OUTROS, Prioridade.BAIXA
        )
        for numero in range(1, 7)
    ]
    for extra in extras[:5]:
        carlos.assumir_chamado(extra)
    print(f"Carlos tem {carlos.contar_em_atendimento()} chamados em atendimento")
    tentar("RN02: Carlos tenta assumir o sexto chamado",
           lambda: carlos.assumir_chamado(extras[5]))
    tentar("RN02: Diana tenta assumir chamado que já está em atendimento",
           lambda: diana.assumir_chamado(extras[0]))

    print("\n-- RN03: resolução do chamado")
    tentar("RN03: resolver chamado sem registro de solução",
           lambda: carlos.registrar_atendimento(
               extras[0], TipoAtendimento.DIAGNOSTICO, "Verificado.", StatusChamado.RESOLVIDO))

    print("\n-- RN04: estoque")
    tentar("RN04: saída maior que o saldo do estoque",
           lambda: helpdesk.registrar_saida_equipamento(diana, "CAB-HDMI", 100, chamado2))
    tentar("RN04: reposição em equipamento baixado",
           lambda: helpdesk.repor_equipamento(diana, "TEC-01", 5, "Compra"))

    print("\n-- RN05: exclusão de técnico")
    tentar("RN05: excluir técnico com chamado em atendimento",
           lambda: helpdesk.excluir_tecnico(admin, diana))

    print("\n-- RN06: hierarquia de cadastro")
    tentar("RN06: usuário comum tenta cadastrar técnico",
           lambda: helpdesk.cadastrar_tecnico(
               ana, "Intruso", "intruso@empresa.com", "1234", "Redes"))
    executar("RN06: Marina desativa a administradora Helena",
             lambda: helpdesk.desativar_administrador(admin, helena))
    tentar("RN06: desativar o único administrador ativo",
           lambda: helpdesk.desativar_administrador(admin, admin))


if __name__ == "__main__":
    main()
