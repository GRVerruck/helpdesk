import tkinter as tk
from tkinter import messagebox, ttk

from helpdesk.excecoes import HelpDeskError
from helpdesk.usuarios import Administrador, Tecnico
from telas.componentes import PERFIS, Formulario, campo, criar_tabela, escolha, mostrar_erro

DETALHES = {"Usuário Comum": "Setor", "Técnico de TI": "Especialidade", "Administrador": "Cargo"}


def detalhe_do_perfil(usuario):
    if isinstance(usuario, Tecnico):
        return usuario.especialidade
    if isinstance(usuario, Administrador):
        return usuario.cargo
    return usuario.setor


class CadastroUsuario(Formulario):
    def __init__(self, app, ao_salvar, autocadastro=False):
        super().__init__(app, "Criar minha conta" if autocadastro else "Cadastrar usuário")
        self.ao_salvar = ao_salvar
        self.autocadastro = autocadastro
        if autocadastro:
            ttk.Label(self.corpo, text="A conta criada aqui é de Usuário Comum.", style="Discreto.TLabel").pack(anchor="w")
        self.nome = campo(self.corpo, "Nome completo")
        self.email = campo(self.corpo, "E-mail")
        self.perfil = None
        if not autocadastro:
            self.perfil = escolha(self.corpo, "Perfil", PERFIS)
            self.perfil.bind("<<ComboboxSelected>>", self.trocar_perfil)
        self.rotulo_detalhe = ttk.Label(self.corpo, text="Setor")
        self.rotulo_detalhe.pack(anchor="w", pady=(10, 4))
        self.detalhe = ttk.Entry(self.corpo, width=40)
        self.detalhe.pack(fill="x")
        self.senha = campo(self.corpo, "Senha (mínimo de 4 caracteres)", senha=True)
        self.confirmacao = campo(self.corpo, "Confirmar senha", senha=True)
        self.adicionar_botoes(self.salvar, "Cadastrar")
        self.nome.focus_set()

    def perfil_escolhido(self):
        if self.perfil is None:
            return "Usuário Comum"
        return self.perfil.get()

    def trocar_perfil(self, evento=None):
        self.rotulo_detalhe.configure(text=DETALHES[self.perfil_escolhido()])

    def salvar(self):
        nome = self.nome.get()
        email = self.email.get()
        detalhe = self.detalhe.get().strip()
        senha = self.senha.get()
        if not nome.strip() or not email.strip() or not detalhe or not senha:
            messagebox.showwarning("Campos obrigatórios", "Preencha todos os campos.", parent=self)
            return
        if senha != self.confirmacao.get():
            messagebox.showwarning("Senhas diferentes", "A confirmação não é igual à senha.", parent=self)
            return
        sistema = self.app.sistema
        perfil = self.perfil_escolhido()
        try:
            if perfil == "Técnico de TI":
                usuario = sistema.cadastrar_tecnico(self.app.usuario, nome, email, senha, detalhe)
            elif perfil == "Administrador":
                usuario = sistema.cadastrar_administrador(self.app.usuario, nome, email, senha, detalhe)
            else:
                usuario = sistema.cadastrar_usuario_comum(nome, email, senha, detalhe)
        except (HelpDeskError, ValueError) as erro:
            mostrar_erro(self, erro)
            return
        self.destroy()
        messagebox.showinfo("Cadastro concluído", f"{usuario.nome} já pode entrar com o e-mail {usuario.email}.",
                            parent=self.app)
        self.ao_salvar(usuario)


class EditarTecnico(Formulario):
    def __init__(self, app, tecnico, ao_salvar):
        super().__init__(app, "Editar técnico")
        self.tecnico = tecnico
        self.ao_salvar = ao_salvar
        ttk.Label(self.corpo, text=tecnico.email, style="Discreto.TLabel").pack(anchor="w")
        self.nome = campo(self.corpo, "Nome completo")
        self.nome.insert(0, tecnico.nome)
        self.especialidade = campo(self.corpo, "Especialidade")
        self.especialidade.insert(0, tecnico.especialidade)
        self.adicionar_botoes(self.salvar)
        self.nome.focus_set()

    def salvar(self):
        try:
            self.app.sistema.atualizar_tecnico(self.app.usuario, self.tecnico, self.nome.get(),
                                               self.especialidade.get())
        except (HelpDeskError, ValueError) as erro:
            mostrar_erro(self, erro)
            return
        self.destroy()
        self.ao_salvar(self.tecnico)


class AlterarSenha(Formulario):
    def __init__(self, app):
        super().__init__(app, "Alterar minha senha")
        self.atual = campo(self.corpo, "Senha atual", senha=True)
        self.nova = campo(self.corpo, "Nova senha (mínimo de 4 caracteres)", senha=True)
        self.confirmacao = campo(self.corpo, "Confirmar nova senha", senha=True)
        self.adicionar_botoes(self.salvar)
        self.atual.focus_set()

    def salvar(self):
        if self.nova.get() != self.confirmacao.get():
            messagebox.showwarning("Senhas diferentes", "A confirmação não é igual à nova senha.", parent=self)
            return
        try:
            self.app.usuario.alterar_senha(self.atual.get(), self.nova.get())
        except (HelpDeskError, ValueError) as erro:
            mostrar_erro(self, erro)
            return
        self.destroy()
        messagebox.showinfo("Senha alterada", "Use a nova senha no próximo acesso.", parent=self.app)


class MinhaConta(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai, padding=24)
        usuario = app.usuario
        ttk.Label(self, text="Meus dados", style="Subtitulo.TLabel").pack(anchor="w", pady=(0, 12))
        dados = ttk.Frame(self)
        dados.pack(anchor="w")
        linhas = [
            ("Nome", usuario.nome),
            ("E-mail", usuario.email),
            ("Perfil", usuario.obter_perfil()),
            (DETALHES[usuario.obter_perfil()], detalhe_do_perfil(usuario)),
            ("Cadastrado em", usuario.data_cadastro.strftime("%d/%m/%Y %H:%M")),
        ]
        for linha, (rotulo, valor) in enumerate(linhas):
            ttk.Label(dados, text=f"{rotulo}:", style="Discreto.TLabel").grid(row=linha, column=0, sticky="w", pady=3)
            ttk.Label(dados, text=valor).grid(row=linha, column=1, sticky="w", padx=(12, 0), pady=3)
        ttk.Label(self, text="O que posso fazer no sistema", style="Subtitulo.TLabel").pack(anchor="w", pady=(24, 8))
        permissoes = sorted(permissao.value for permissao in usuario.listar_permissoes())
        for permissao in permissoes:
            ttk.Label(self, text=f"•  {permissao}").pack(anchor="w", pady=1)
        ttk.Button(self, text="Alterar minha senha", command=lambda: AlterarSenha(app)).pack(anchor="w", pady=(24, 0))


class TelaUsuarios(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai, padding=16)
        self.app = app
        self.usuarios = {}

        topo = ttk.Frame(self)
        topo.pack(fill="x", pady=(0, 12))
        ttk.Label(topo, text="Usuários do sistema", style="Subtitulo.TLabel").pack(side="left")
        ttk.Button(topo, text="+ Cadastrar usuário", style="Principal.TButton",
                   command=self.cadastrar).pack(side="right")

        filtros = ttk.Frame(self)
        filtros.pack(fill="x", pady=(0, 8))
        ttk.Label(filtros, text="Buscar:").pack(side="left")
        self.busca = tk.StringVar()
        self.busca.trace_add("write", self.atualizar)
        ttk.Entry(filtros, textvariable=self.busca).pack(side="left", fill="x", expand=True, padx=(6, 12))
        self.filtro_perfil = ttk.Combobox(filtros, values=["Todos os perfis"] + PERFIS, state="readonly", width=16)
        self.filtro_perfil.current(0)
        self.filtro_perfil.pack(side="left", padx=(0, 8))
        self.filtro_situacao = ttk.Combobox(filtros, values=["Todas as situações", "Ativos", "Bloqueados"],
                                            state="readonly", width=17)
        self.filtro_situacao.current(0)
        self.filtro_situacao.pack(side="left")
        self.filtro_perfil.bind("<<ComboboxSelected>>", self.atualizar)
        self.filtro_situacao.bind("<<ComboboxSelected>>", self.atualizar)

        botoes = ttk.Frame(self)
        botoes.pack(side="bottom", fill="x", pady=(12, 0))
        self.botao_editar = ttk.Button(botoes, text="Editar técnico", command=self.editar)
        self.botao_editar.pack(side="left", padx=(0, 8))
        self.botao_bloquear = ttk.Button(botoes, text="Bloquear", command=self.bloquear)
        self.botao_bloquear.pack(side="left", padx=(0, 8))
        self.botao_excluir = ttk.Button(botoes, text="Excluir técnico", command=self.excluir)
        self.botao_excluir.pack(side="left", padx=(0, 8))
        self.botao_desativar = ttk.Button(botoes, text="Desativar administrador", command=self.desativar)
        self.botao_desativar.pack(side="left")

        self.total = ttk.Label(self, style="Discreto.TLabel")
        self.total.pack(anchor="w", pady=(0, 6))
        self.tabela = criar_tabela(self, [
            ("id", "Nº", 50),
            ("nome", "Nome", 180),
            ("email", "E-mail", 220),
            ("perfil", "Perfil", 130),
            ("detalhe", "Setor / especialidade / cargo", 210),
            ("situacao", "Situação", 100),
        ])
        self.tabela.bind("<<TreeviewSelect>>", lambda evento: self.atualizar_botoes())
        self.tabela.bind("<Double-1>", lambda evento: self.editar())
        self.atualizar()

    def atualizar(self, *args):
        selecao = self.tabela.selection()
        self.tabela.delete(*self.tabela.get_children())
        self.usuarios = {}
        busca = self.busca.get().strip().lower()
        perfil = self.filtro_perfil.get()
        situacao = self.filtro_situacao.get()
        todos = self.app.sistema.usuarios
        for usuario in todos:
            texto = f"{usuario.nome} {usuario.email} {detalhe_do_perfil(usuario)}".lower()
            if busca and busca not in texto:
                continue
            if perfil != "Todos os perfis" and usuario.obter_perfil() != perfil:
                continue
            if situacao == "Ativos" and not usuario.esta_ativo():
                continue
            if situacao == "Bloqueados" and usuario.esta_ativo():
                continue
            chave = str(usuario.id)
            self.usuarios[chave] = usuario
            self.tabela.insert("", "end", iid=chave, tags=() if usuario.esta_ativo() else ("bloqueado",), values=(
                usuario.id, usuario.nome, usuario.email, usuario.obter_perfil(), detalhe_do_perfil(usuario),
                "Ativo" if usuario.esta_ativo() else "Bloqueado",
            ))
        if selecao and selecao[0] in self.usuarios:
            self.tabela.selection_set(selecao[0])
        self.total.configure(text=f"{len(self.usuarios)} de {len(todos)} usuários")
        self.atualizar_botoes()

    def selecionado(self):
        selecao = self.tabela.selection()
        if not selecao:
            return None
        return self.usuarios.get(selecao[0])

    def atualizar_botoes(self):
        usuario = self.selecionado()
        tecnico = isinstance(usuario, Tecnico)
        admin_ativo = isinstance(usuario, Administrador) and usuario.esta_ativo()
        self.botao_editar.configure(state="normal" if tecnico else "disabled")
        self.botao_excluir.configure(state="normal" if tecnico else "disabled")
        self.botao_desativar.configure(state="normal" if admin_ativo else "disabled")
        self.botao_bloquear.configure(state="normal" if usuario else "disabled")
        if usuario and not usuario.esta_ativo():
            self.botao_bloquear.configure(text="Desbloquear")
        else:
            self.botao_bloquear.configure(text="Bloquear")

    def executar(self, acao):
        try:
            acao()
        except (HelpDeskError, ValueError) as erro:
            mostrar_erro(self, erro)
            return
        if not self.app.usuario.esta_ativo():
            messagebox.showinfo("Acesso encerrado", "Seu acesso foi desativado. Entre com outra conta.",
                                parent=self.app)
            self.app.mostrar_login()
            return
        self.atualizar()

    def cadastrar(self):
        CadastroUsuario(self.app, self.atualizar)

    def editar(self):
        usuario = self.selecionado()
        if isinstance(usuario, Tecnico):
            EditarTecnico(self.app, usuario, self.atualizar)

    def bloquear(self):
        usuario = self.selecionado()
        if usuario is None:
            return
        acao = "bloquear" if usuario.esta_ativo() else "desbloquear"
        if messagebox.askyesno("Confirmar", f"Deseja {acao} o acesso de {usuario.nome}?", parent=self):
            self.executar(lambda: self.app.sistema.alterar_bloqueio(self.app.usuario, usuario, usuario.esta_ativo()))

    def excluir(self):
        usuario = self.selecionado()
        if not isinstance(usuario, Tecnico):
            return
        mensagem = (f"Deseja excluir o técnico {usuario.nome}?\n\n"
                    "Técnicos com chamados em atendimento não podem ser excluídos.")
        if messagebox.askyesno("Excluir técnico", mensagem, parent=self):
            self.executar(lambda: self.app.sistema.excluir_tecnico(self.app.usuario, usuario))

    def desativar(self):
        usuario = self.selecionado()
        if not isinstance(usuario, Administrador):
            return
        if messagebox.askyesno("Desativar administrador", f"Deseja desativar o acesso de {usuario.nome}?",
                               parent=self):
            self.executar(lambda: self.app.sistema.desativar_administrador(self.app.usuario, usuario))
