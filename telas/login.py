import tkinter as tk
from tkinter import messagebox, ttk

from helpdesk.enums import Permissao
from telas.componentes import campo
from telas.usuarios import CadastroUsuario


class TelaLogin(ttk.Frame):
    def __init__(self, app):
        super().__init__(app)
        self.app = app

        marca = ttk.Frame(self, style="Verde.TFrame", padding=48)
        marca.pack(side="left", fill="both", expand=True)
        ttk.Label(marca, text="IFC • Campus Concórdia", style="VerdeDiscreto.TLabel").pack(anchor="w", pady=(80, 0))
        ttk.Label(marca, text="Help Desk", style="VerdeGrande.TLabel").pack(anchor="w", pady=(8, 4))
        ttk.Label(marca, text="Sistema de chamados de TI e controle de estoque",
                  style="VerdeDiscreto.TLabel").pack(anchor="w")
        ttk.Label(marca, text="Programação Orientada a Objetos I", style="VerdeDiscreto.TLabel").pack(side="bottom",
                                                                                                    anchor="w")

        formulario = ttk.Frame(self, padding=(40, 48))
        formulario.pack(side="right", fill="y")
        ttk.Label(formulario, text="Entrar no sistema", style="Titulo.TLabel").pack(anchor="w", pady=(0, 12))
        self.area = tk.StringVar(value="principal")
        ttk.Radiobutton(formulario, text="Aplicativo Principal (usuários e técnicos)", value="principal",
                        variable=self.area, command=self.trocar_area).pack(anchor="w", pady=2)
        ttk.Radiobutton(formulario, text="Painel Administrativo (administradores)", value="painel",
                        variable=self.area, command=self.trocar_area).pack(anchor="w", pady=2)
        self.email = campo(formulario, "E-mail")
        self.senha = campo(formulario, "Senha", senha=True)
        self.mostrar = tk.BooleanVar()
        ttk.Checkbutton(formulario, text="Mostrar senha", variable=self.mostrar,
                        command=self.mostrar_senha).pack(anchor="w", pady=8)
        ttk.Button(formulario, text="Entrar", style="Principal.TButton", command=self.entrar).pack(fill="x", pady=(4, 8))
        self.botao_conta = ttk.Button(formulario, text="Criar minha conta", command=self.criar_conta)
        self.botao_conta.pack(fill="x")
        ttk.Label(formulario, text="Os dados ficam em memória enquanto o programa estiver aberto.",
                  style="Discreto.TLabel").pack(side="bottom", anchor="w")

        self.email.bind("<Return>", lambda evento: self.senha.focus_set())
        self.senha.bind("<Return>", lambda evento: self.entrar())
        self.email.focus_set()

    def trocar_area(self):
        self.botao_conta.configure(state="normal" if self.area.get() == "principal" else "disabled")

    def mostrar_senha(self):
        self.senha.configure(show="" if self.mostrar.get() else "*")

    def entrar(self):
        email = self.email.get().strip()
        senha = self.senha.get()
        if not email or not senha:
            messagebox.showwarning("Campos obrigatórios", "Informe o e-mail e a senha.", parent=self)
            return
        if self.area.get() == "principal":
            acesso = Permissao.ACESSAR_APLICATIVO
        else:
            acesso = Permissao.ACESSAR_PAINEL_ADMIN
        usuario = self.app.sistema.autenticar(email, senha, acesso)
        if usuario is None:
            messagebox.showerror("Acesso negado", "E-mail ou senha incorretos, usuário bloqueado "
                                 "ou sem permissão para esta área.", parent=self)
            self.senha.delete(0, "end")
            return
        self.app.mostrar_painel(usuario)

    def criar_conta(self):
        CadastroUsuario(self.app, self.preencher_email, autocadastro=True)

    def preencher_email(self, usuario):
        self.email.delete(0, "end")
        self.email.insert(0, usuario.email)
        self.senha.delete(0, "end")
        self.senha.focus_set()
