import tkinter as tk
from tkinter import messagebox

from helpdesk.helpdesk import HelpDesk
from helpdesk.usuarios import Administrador
from telas.componentes import configurar_estilo
from telas.login import TelaLogin
from telas.painel import TelaPainel


def criar_sistema():
    admin = Administrador("Ana Paula", "admin@empresa.com", "admin123", "Coordenadora de TI")
    sistema = HelpDesk("Empresa Exemplo", admin)
    sistema.cadastrar_tecnico(admin, "Carlos Lima", "carlos@empresa.com", "tec123", "Redes")
    sistema.cadastrar_usuario_comum("João Silva", "joao@empresa.com", "1234", "Financeiro")
    return sistema


class Aplicacao(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Help Desk - Chamados de TI")
        self.geometry("1000x640")
        self.minsize(880, 580)
        configurar_estilo(self)
        self.sistema = criar_sistema()
        self.usuario = None
        self.tela = None
        self.mostrar_login()

    def trocar_tela(self, tela):
        if self.tela is not None:
            self.tela.destroy()
        self.tela = tela
        self.tela.pack(fill="both", expand=True)

    def mostrar_login(self):
        self.usuario = None
        self.trocar_tela(TelaLogin(self))

    def mostrar_painel(self, usuario):
        self.usuario = usuario
        self.trocar_tela(TelaPainel(self))

    def sair(self):
        if messagebox.askyesno("Sair", "Deseja sair da sua conta?", parent=self):
            self.mostrar_login()


if __name__ == "__main__":
    Aplicacao().mainloop()
