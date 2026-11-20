import tkinter as tk
from tkinter import messagebox, ttk

from helpdesk.enums import Categoria, Permissao, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.excecoes import HelpDeskError
from helpdesk.usuarios import Tecnico
from telas.componentes import CINZA, VERDE_ESCURO, Formulario, campo, criar_tabela, escolha, mostrar_erro

EM_ANDAMENTO = (StatusChamado.EM_ATENDIMENTO, StatusChamado.PENDENTE)


def formatar_data(data):
    if data is None:
        return "-"
    return data.strftime("%d/%m/%Y %H:%M")


def nome_responsavel(chamado):
    if chamado.responsavel is None:
        return "Não atribuído"
    return chamado.responsavel.nome


def caixa_texto(pai, altura, conteudo=None):
    texto = tk.Text(pai, height=altura, width=64, wrap="word", relief="solid", borderwidth=1, font="TkDefaultFont")
    texto.pack(fill="both", expand=True)
    if conteudo is not None:
        texto.insert("1.0", conteudo)
        texto.configure(state="disabled")
    return texto


class NovoChamado(Formulario):
    def __init__(self, app, ao_salvar):
        super().__init__(app, "Abrir chamado")
        self.ao_salvar = ao_salvar
        ttk.Label(self.corpo, text="Conte o que aconteceu para que a equipe possa ajudar.",
                  style="Discreto.TLabel").pack(anchor="w")
        self.titulo = campo(self.corpo, "Título")
        self.categoria = escolha(self.corpo, "Categoria", [categoria.value for categoria in Categoria])
        self.categoria.current(1)
        self.prioridade = escolha(self.corpo, "Prioridade", [prioridade.value for prioridade in Prioridade])
        self.prioridade.current(1)
        ttk.Label(self.corpo, text="Descrição do problema").pack(anchor="w", pady=(10, 0))
        ttk.Label(self.corpo, text="Informe a tela, a mensagem de erro e o que estava tentando fazer.",
                  style="Discreto.TLabel").pack(anchor="w", pady=(2, 4))
        self.descricao = caixa_texto(self.corpo, 6)
        self.adicionar_botoes(self.salvar, "Abrir chamado")
        self.unbind("<Return>")
        self.titulo.focus_set()

    def salvar(self):
        try:
            chamado = self.app.sistema.abrir_chamado(
                self.app.usuario, self.titulo.get(), self.descricao.get("1.0", "end"),
                Categoria(self.categoria.get()), Prioridade(self.prioridade.get()))
        except (HelpDeskError, ValueError) as erro:
            mostrar_erro(self, erro)
            return
        self.destroy()
        messagebox.showinfo("Chamado aberto", f"Seu chamado foi registrado com o número #{chamado.id}.",
                            parent=self.app)
        self.ao_salvar()


class DetalheChamado(Formulario):
    def __init__(self, app, chamado, ao_salvar):
        super().__init__(app, f"Chamado #{chamado.id}")
        self.chamado = chamado
        self.ao_salvar = ao_salvar
        usuario = app.usuario
        aberto = chamado.status == StatusChamado.ABERTO
        atendendo = usuario is chamado.responsavel and chamado.status in EM_ANDAMENTO

        resumo = (f"{chamado.titulo}\n\n"
                  f"{chamado.status.value}  |  Prioridade {chamado.prioridade.value.lower()}  |  "
                  f"{chamado.categoria.value}\n"
                  f"Solicitante: {chamado.solicitante.nome}  |  Responsável: {nome_responsavel(chamado)}\n"
                  f"Abertura: {formatar_data(chamado.data_abertura)}  |  "
                  f"Encerramento: {formatar_data(chamado.data_encerramento)}")
        ttk.Label(self.corpo, text=resumo, justify="left").pack(anchor="w", pady=(0, 12))

        botoes = ttk.Frame(self.corpo)
        botoes.pack(side="bottom", fill="x", pady=(14, 0))
        ttk.Button(botoes, text="Fechar", command=self.destroy).pack(side="right")
        if aberto and isinstance(usuario, Tecnico):
            ttk.Button(botoes, text="Assumir chamado", style="Principal.TButton",
                       command=self.assumir).pack(side="left")
        if aberto and usuario is chamado.solicitante:
            ttk.Button(botoes, text="Cancelar chamado", command=self.cancelar).pack(side="left")

        abas = ttk.Notebook(self.corpo)
        abas.pack(fill="both", expand=True)
        descricao = ttk.Frame(abas, padding=14)
        abas.add(descricao, text="Descrição")
        ttk.Label(descricao, text="Problema informado", style="Subtitulo.TLabel").pack(anchor="w", pady=(0, 6))
        caixa_texto(descricao, 10, chamado.descricao)

        historico = ttk.Frame(abas, padding=14)
        abas.add(historico, text="Histórico")
        ttk.Label(historico, text="Registros do atendimento", style="Subtitulo.TLabel").pack(anchor="w", pady=(0, 6))
        registros = [registro.resumir() for registro in chamado.listar_historico()]
        caixa_texto(historico, 10, "\n\n".join(registros) or "Ainda não há registros de atendimento neste chamado.")

        if atendendo:
            atendimento = ttk.Frame(abas, padding=14)
            abas.add(atendimento, text="Registrar atendimento")
            linha = ttk.Frame(atendimento)
            linha.pack(fill="x")
            esquerda = ttk.Frame(linha)
            esquerda.pack(side="left", fill="x", expand=True, padx=(0, 12))
            direita = ttk.Frame(linha)
            direita.pack(side="right", fill="x", expand=True)
            self.tipo = escolha(esquerda, "Tipo de registro", [tipo.value for tipo in TipoAtendimento])
            self.novo_status = escolha(direita, "Situação após o registro",
                                       ["Manter status", "Em atendimento", "Pendente", "Resolvido"])
            ttk.Label(atendimento, text="Descrição do atendimento").pack(anchor="w", pady=(12, 4))
            self.descricao = caixa_texto(atendimento, 4)
            ttk.Button(atendimento, text="Registrar atendimento", style="Principal.TButton",
                       command=self.registrar).pack(anchor="e", pady=(8, 0))
        self.grab_set()

    def executar(self, acao):
        try:
            acao()
        except (HelpDeskError, ValueError) as erro:
            mostrar_erro(self, erro)
            return
        self.destroy()
        self.ao_salvar()
        DetalheChamado(self.app, self.chamado, self.ao_salvar)

    def assumir(self):
        if messagebox.askyesno("Assumir chamado", "Deseja assumir este atendimento?", parent=self):
            self.executar(lambda: self.app.usuario.assumir_chamado(self.chamado))

    def cancelar(self):
        if messagebox.askyesno("Cancelar chamado", "Deseja cancelar este chamado?", parent=self):
            self.executar(lambda: self.app.usuario.cancelar_chamado(self.chamado))

    def registrar(self):
        situacao = self.novo_status.get()
        novo_status = None
        if situacao != "Manter status":
            novo_status = StatusChamado(situacao)
        if novo_status == StatusChamado.RESOLVIDO and not messagebox.askyesno(
                "Resolver chamado", "Deseja encerrar o chamado como resolvido?", parent=self):
            return
        self.executar(lambda: self.app.usuario.registrar_atendimento(
            self.chamado, TipoAtendimento(self.tipo.get()), self.descricao.get("1.0", "end"), novo_status))


class TelaChamados(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai, padding=16)
        self.app = app
        self.chamados = {}
        usuario = app.usuario
        pode_abrir = usuario.possui_permissao(Permissao.ABRIR_CHAMADO)

        topo = ttk.Frame(self)
        topo.pack(fill="x")
        ttk.Label(topo, text="Meus chamados" if pode_abrir else "Central de chamados",
                  style="Subtitulo.TLabel").pack(side="left")
        if pode_abrir:
            ttk.Button(topo, text="+ Novo chamado", style="Principal.TButton",
                       command=lambda: NovoChamado(app, self.atualizar)).pack(side="right")
        orientacao = {
            "Usuário Comum": "Acompanhe suas solicitações e consulte o histórico de cada atendimento.",
            "Técnico de TI": "Confira a fila de chamados abertos e os atendimentos sob sua responsabilidade.",
            "Administrador": "Acompanhe todos os chamados da equipe.",
        }
        ttk.Label(self, text=orientacao[usuario.obter_perfil()], style="Discreto.TLabel").pack(anchor="w", pady=(4, 12))

        resumo = ttk.Frame(self)
        resumo.pack(fill="x", pady=(0, 12))
        self.contadores = []
        for coluna, rotulo in enumerate(["Total de chamados", "Abertos", "Em atendimento / pendentes", "Resolvidos"]):
            resumo.columnconfigure(coluna, weight=1, uniform="cartoes")
            cartao = tk.Frame(resumo, background="white", padx=16, pady=10)
            cartao.grid(row=0, column=coluna, sticky="nsew", padx=(0, 8))
            contador = tk.Label(cartao, font=("", 22, "bold"), foreground=VERDE_ESCURO, background="white")
            contador.pack(anchor="w")
            tk.Label(cartao, text=rotulo, foreground=CINZA, background="white").pack(anchor="w")
            self.contadores.append(contador)

        filtros = ttk.Frame(self)
        filtros.pack(fill="x", pady=(0, 8))
        ttk.Label(filtros, text="Buscar:").pack(side="left")
        self.busca = tk.StringVar()
        self.busca.trace_add("write", self.atualizar)
        ttk.Entry(filtros, textvariable=self.busca).pack(side="left", fill="x", expand=True, padx=(6, 12))
        self.filtro_status = ttk.Combobox(filtros, state="readonly", width=18,
                                          values=["Todos os status"] + [status.value for status in StatusChamado])
        self.filtro_status.current(0)
        self.filtro_status.pack(side="left", padx=(0, 8))
        self.filtro_prioridade = ttk.Combobox(filtros, state="readonly", width=18,
                                              values=["Todas as prioridades"] + [p.value for p in Prioridade])
        self.filtro_prioridade.current(0)
        self.filtro_prioridade.pack(side="left")
        self.filtro_status.bind("<<ComboboxSelected>>", self.atualizar)
        self.filtro_prioridade.bind("<<ComboboxSelected>>", self.atualizar)
        self.somente_meus = tk.BooleanVar()
        if isinstance(usuario, Tecnico):
            ttk.Checkbutton(self, text="Somente os chamados que assumi", variable=self.somente_meus,
                            command=self.atualizar).pack(anchor="w", pady=(0, 8))

        rodape = ttk.Frame(self)
        rodape.pack(side="bottom", fill="x", pady=(12, 0))
        self.total = ttk.Label(rodape, style="Discreto.TLabel")
        self.total.pack(side="left")
        ttk.Button(rodape, text="Ver chamado", command=self.abrir).pack(side="right")

        self.tabela = criar_tabela(self, [
            ("id", "Nº", 50),
            ("titulo", "Título", 230),
            ("status", "Status", 120),
            ("prioridade", "Prioridade", 90),
            ("solicitante", "Solicitante", 130),
            ("responsavel", "Responsável", 130),
            ("abertura", "Abertura", 130),
        ])
        self.tabela.bind("<Double-1>", lambda evento: self.abrir())
        self.atualizar()

    def atualizar(self, *args):
        self.tabela.delete(*self.tabela.get_children())
        self.chamados = {}
        busca = self.busca.get().strip().lower()
        status = self.filtro_status.get()
        prioridade = self.filtro_prioridade.get()
        todos = self.app.sistema.listar_chamados(self.app.usuario)
        for chamado in reversed(todos):
            texto = f"{chamado.id} {chamado.titulo} {chamado.solicitante.nome} {nome_responsavel(chamado)}".lower()
            if busca and busca not in texto:
                continue
            if status != "Todos os status" and chamado.status.value != status:
                continue
            if prioridade != "Todas as prioridades" and chamado.prioridade.value != prioridade:
                continue
            if self.somente_meus.get() and chamado.responsavel is not self.app.usuario:
                continue
            chave = str(chamado.id)
            self.chamados[chave] = chamado
            self.tabela.insert("", "end", iid=chave, values=(
                chamado.id, chamado.titulo, chamado.status.value, chamado.prioridade.value,
                chamado.solicitante.nome, nome_responsavel(chamado), formatar_data(chamado.data_abertura),
            ))

        situacoes = [chamado.status for chamado in todos]
        totais = [
            len(todos),
            situacoes.count(StatusChamado.ABERTO),
            situacoes.count(StatusChamado.EM_ATENDIMENTO) + situacoes.count(StatusChamado.PENDENTE),
            situacoes.count(StatusChamado.RESOLVIDO),
        ]
        for contador, total in zip(self.contadores, totais):
            contador.configure(text=total)
        self.total.configure(text=f"{len(self.chamados)} de {len(todos)} chamados")

    def abrir(self):
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showinfo("Selecione um chamado", "Selecione uma linha para ver os detalhes.", parent=self)
            return
        DetalheChamado(self.app, self.chamados[selecao[0]], self.atualizar)
