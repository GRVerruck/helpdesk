from tkinter import ttk

from helpdesk.enums import Permissao
from telas.chamados import TelaChamados
from telas.estoque import TelaEstoque
from telas.usuarios import MinhaConta, TelaUsuarios


class TelaPainel(ttk.Frame):
    def __init__(self, app):
        super().__init__(app)
        usuario = app.usuario
        if usuario.possui_permissao(Permissao.ACESSAR_PAINEL_ADMIN):
            area = "Painel Administrativo"
        else:
            area = "Aplicativo Principal"

        cabecalho = ttk.Frame(self, style="Verde.TFrame", padding=(20, 12))
        cabecalho.pack(fill="x")
        ttk.Label(cabecalho, text=f"Help Desk  |  {area}", style="Verde.TLabel").pack(side="left")
        ttk.Button(cabecalho, text="Sair", command=app.sair).pack(side="right")
        ttk.Label(cabecalho, text=f"{usuario.nome} ({usuario.obter_perfil()})",
                  style="VerdeDiscreto.TLabel").pack(side="right", padx=12)

        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True, padx=16, pady=16)
        self.abas.add(TelaChamados(self.abas, app), text="Chamados")
        if usuario.possui_permissao(Permissao.GERENCIAR_USUARIOS):
            self.abas.add(TelaUsuarios(self.abas, app), text="Usuários")
        if usuario.possui_permissao(Permissao.GERENCIAR_ESTOQUE):
            self.abas.add(TelaEstoque(self.abas, app), text="Estoque")
        self.abas.add(MinhaConta(self.abas, app), text="Minha conta")
