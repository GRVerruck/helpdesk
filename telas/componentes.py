import tkinter as tk
from tkinter import font, messagebox, ttk

VERDE = "#2f9e41"
VERDE_ESCURO = "#1d6b2c"
FUNDO = "#f3f6f3"
TEXTO = "#1f2a20"
CINZA = "#5d6b5f"

PERFIS = ["Usuário Comum", "Técnico de TI", "Administrador"]


def configurar_estilo(janela):
    familia = font.nametofont("TkDefaultFont").actual("family")
    janela.configure(background=FUNDO)
    estilo = ttk.Style(janela)
    estilo.theme_use("clam")
    estilo.configure(".", font=(familia, 11), background=FUNDO, foreground=TEXTO)
    estilo.configure("Titulo.TLabel", font=(familia, 18, "bold"))
    estilo.configure("Subtitulo.TLabel", font=(familia, 14, "bold"))
    estilo.configure("Discreto.TLabel", foreground=CINZA, font=(familia, 10))
    estilo.configure("Verde.TFrame", background=VERDE_ESCURO)
    estilo.configure("Verde.TLabel", background=VERDE_ESCURO, foreground="white", font=(familia, 14, "bold"))
    estilo.configure("VerdeGrande.TLabel", background=VERDE_ESCURO, foreground="white", font=(familia, 30, "bold"))
    estilo.configure("VerdeDiscreto.TLabel", background=VERDE_ESCURO, foreground="#cfe8d3", font=(familia, 11))
    estilo.configure("TButton", padding=(12, 6))
    estilo.configure("Principal.TButton", background=VERDE, foreground="white")
    estilo.map("Principal.TButton", background=[("disabled", "#a8d1ae"), ("active", VERDE_ESCURO)])
    estilo.configure("TEntry", fieldbackground="white", padding=5)
    estilo.configure("TCombobox", padding=5)
    estilo.map("TCombobox", fieldbackground=[("readonly", "white")])
    estilo.configure("TRadiobutton", background=FUNDO)
    estilo.configure("TCheckbutton", background=FUNDO)
    estilo.configure("Treeview", rowheight=30, background="white", fieldbackground="white")
    estilo.configure("Treeview.Heading", font=(familia, 11, "bold"), padding=(6, 6))
    estilo.map("Treeview", background=[("selected", "#cfe8d3")], foreground=[("selected", TEXTO)])
    estilo.configure("TNotebook.Tab", padding=(16, 6))
    estilo.map("TNotebook.Tab", foreground=[("selected", VERDE_ESCURO)],padding=[("selected", (16, 6))])

def campo(pai, rotulo, senha=False):
    ttk.Label(pai, text=rotulo).pack(anchor="w", pady=(10, 4))
    entrada = ttk.Entry(pai, width=40, show="*" if senha else "")
    entrada.pack(fill="x")
    return entrada


def escolha(pai, rotulo, valores):
    ttk.Label(pai, text=rotulo).pack(anchor="w", pady=(10, 4))
    caixa = ttk.Combobox(pai, values=valores, state="readonly")
    caixa.current(0)
    caixa.pack(fill="x")
    return caixa


def criar_tabela(pai, colunas):
    quadro = ttk.Frame(pai)
    quadro.pack(fill="both", expand=True)
    tabela = ttk.Treeview(quadro, columns=[coluna[0] for coluna in colunas], show="headings", selectmode="browse")
    for chave, titulo, largura in colunas:
        tabela.heading(chave, text=titulo)
        tabela.column(chave, width=largura, anchor="w")
    barra = ttk.Scrollbar(quadro, command=tabela.yview)
    tabela.configure(yscrollcommand=barra.set)
    barra.pack(side="right", fill="y")
    tabela.pack(side="left", fill="both", expand=True)
    tabela.tag_configure("bloqueado", foreground="#9a9a9a")
    return tabela


def mostrar_erro(pai, erro):
    messagebox.showerror("Não foi possível concluir", str(erro), parent=pai)


class Formulario(tk.Toplevel):
    def __init__(self, app, titulo):
        super().__init__(app)
        self.app = app
        self.title(titulo)
        self.configure(background=FUNDO)
        self.resizable(False, False)
        self.transient(app)
        self.geometry(f"+{app.winfo_rootx() + 120}+{app.winfo_rooty() + 60}")
        self.corpo = ttk.Frame(self, padding=24)
        self.corpo.pack(fill="both", expand=True)
        ttk.Label(self.corpo, text=titulo, style="Titulo.TLabel").pack(anchor="w", pady=(0, 6))
        self.bind("<Escape>", lambda evento: self.destroy())

    def adicionar_botoes(self, comando, texto="Salvar"):
        linha = ttk.Frame(self.corpo)
        linha.pack(fill="x", pady=(20, 0))
        ttk.Button(linha, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(linha, text=texto, style="Principal.TButton", command=comando).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda evento: comando())
        self.grab_set()
