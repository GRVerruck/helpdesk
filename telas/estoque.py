import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from helpdesk.excecoes import HelpDeskError
from telas.chamados import EM_ANDAMENTO, caixa_texto
from telas.componentes import Formulario, campo, criar_tabela, escolha, mostrar_erro


SITUACOES = ["Em estoque", "Abaixo do mínimo", "Baixado"]


def situacao_equipamento(equipamento):
    if not equipamento.ativo:
        return "Baixado"
    if equipamento.abaixo_do_minimo():
        return "Abaixo do mínimo"
    return "Em estoque"


class CadastroEquipamento(Formulario):
    def __init__(self, app, ao_salvar):
        super().__init__(app, "Adicionar equipamento")
        self.ao_salvar = ao_salvar
        ttk.Label(self.corpo, text="Cadastre um item novo no estoque de TI.", style="Discreto.TLabel").pack(anchor="w")
        self.codigo = campo(self.corpo, "Código")
        self.descricao = campo(self.corpo, "Descrição")
        self.tipo = campo(self.corpo, "Tipo")
        self.quantidade = campo(self.corpo, "Quantidade inicial")
        self.quantidade.insert(0, "0")
        self.quantidade_minima = campo(self.corpo, "Quantidade mínima")
        self.quantidade_minima.insert(0, "0")
        self.adicionar_botoes(self.salvar, "Cadastrar")
        self.codigo.focus_set()

    def salvar(self):
        codigo = self.codigo.get().strip()
        descricao = self.descricao.get().strip()
        tipo = self.tipo.get().strip()
        if not codigo or not descricao or not tipo:
            messagebox.showwarning("Campos obrigatórios", "Preencha código, descrição e tipo.", parent=self)
            return
        try:
            quantidade = int(self.quantidade.get())
            quantidade_minima = int(self.quantidade_minima.get())
        except ValueError:
            messagebox.showwarning("Quantidade inválida", "Informe as quantidades como números inteiros.",
                                   parent=self)
            return
        try:
            equipamento = self.app.sistema.cadastrar_equipamento(
                self.app.usuario, codigo, descricao, tipo, quantidade, quantidade_minima)
        except (HelpDeskError, ValueError) as erro:
            mostrar_erro(self, erro)
            return
        self.destroy()
        messagebox.showinfo("Cadastro concluído", f"{equipamento.descricao} foi adicionado ao estoque.",
                            parent=self.app)
        self.ao_salvar()


def descrever_movimentacao(movimentacao):
    linha = f"{movimentacao.quantidade} un.  |  {movimentacao.motivo}\nResponsável: {movimentacao.responsavel.nome}"
    if movimentacao.chamado is not None:
        linha += f"  |  Chamado #{movimentacao.chamado.id}"
    return linha


class DetalheEquipamento(Formulario):
    def __init__(self, app, equipamento, ao_salvar):
        super().__init__(app, f"Equipamento {equipamento.codigo}")
        self.equipamento = equipamento
        self.ao_salvar = ao_salvar
        ativo = equipamento.ativo

        resumo = (f"{equipamento.descricao}\n\n"
                  f"{situacao_equipamento(equipamento)}  |  Tipo: {equipamento.tipo}\n"
                  f"Quantidade: {equipamento.quantidade}  |  Mínimo: {equipamento.quantidade_minima}")
        ttk.Label(self.corpo, text=resumo, justify="left").pack(anchor="w", pady=(0, 12))

        botoes = ttk.Frame(self.corpo)
        botoes.pack(side="bottom", fill="x", pady=(14, 0))
        ttk.Button(botoes, text="Fechar", command=self.destroy).pack(side="right")
        if ativo:
            ttk.Button(botoes, text="Dar baixa", command=self.dar_baixa).pack(side="left")

        abas = ttk.Notebook(self.corpo)
        abas.pack(fill="both", expand=True)

        historico = ttk.Frame(abas, padding=14)
        abas.add(historico, text="Movimentações")
        ttk.Label(historico, text="Histórico do equipamento", style="Subtitulo.TLabel").pack(anchor="w", pady=(0, 6))
        registros = [descrever_movimentacao(m) for m in reversed(equipamento.listar_movimentacoes())]
        caixa_texto(historico, 10, "\n\n".join(registros) or "Ainda não há movimentações neste equipamento.")

        if ativo:
            reposicao = ttk.Frame(abas, padding=14)
            abas.add(reposicao, text="Repor estoque")
            self.qtd_entrada = campo(reposicao, "Quantidade que entrou")
            self.motivo_entrada = campo(reposicao, "Motivo")
            ttk.Button(reposicao, text="Repor estoque", style="Principal.TButton",
                       command=self.repor).pack(anchor="e", pady=(12, 0))

            saida = ttk.Frame(abas, padding=14)
            abas.add(saida, text="Registrar saída")
            self.chamados = {
                f"#{c.id} - {c.titulo}": c for c in app.sistema.listar_chamados(app.usuario)
                if c.responsavel is app.usuario and c.status in EM_ANDAMENTO
            }
            if self.chamados:
                self.qtd_saida = campo(saida, "Quantidade que saiu")
                self.chamado = escolha(saida, "Chamado", list(self.chamados))
                ttk.Button(saida, text="Registrar saída", style="Principal.TButton",
                           command=self.registrar_saida).pack(anchor="e", pady=(12, 0))
            else:
                ttk.Label(saida, text="A saída precisa estar vinculada a um chamado seu em andamento, "
                                      "e você não tem nenhum no momento.", style="Discreto.TLabel",
                          wraplength=420, justify="left").pack(anchor="w")

            edicao = ttk.Frame(abas, padding=14)
            abas.add(edicao, text="Editar dados")
            self.nova_descricao = campo(edicao, "Descrição")
            self.nova_descricao.insert(0, equipamento.descricao)
            self.novo_minimo = campo(edicao, "Quantidade mínima")
            self.novo_minimo.insert(0, str(equipamento.quantidade_minima))
            ttk.Button(edicao, text="Salvar alterações", style="Principal.TButton",
                       command=self.atualizar_dados).pack(anchor="e", pady=(12, 0))
        self.grab_set()

    def inteiro(self, texto):
        try:
            return int(texto)
        except ValueError:
            messagebox.showwarning("Quantidade inválida", "Informe um número inteiro.", parent=self)
            return None

    def executar(self, acao):
        try:
            acao()
        except (HelpDeskError, ValueError) as erro:
            mostrar_erro(self, erro)
            return
        self.destroy()
        self.ao_salvar()
        DetalheEquipamento(self.app, self.equipamento, self.ao_salvar)

    def repor(self):
        quantidade = self.inteiro(self.qtd_entrada.get())
        motivo = self.motivo_entrada.get().strip()
        if quantidade is None:
            return
        if not motivo:
            messagebox.showwarning("Campo obrigatório", "Informe o motivo da reposição.", parent=self)
            return
        self.executar(lambda: self.app.sistema.repor_equipamento(
            self.app.usuario, self.equipamento.codigo, quantidade, motivo))

    def registrar_saida(self):
        quantidade = self.inteiro(self.qtd_saida.get())
        if quantidade is None:
            return
        chamado = self.chamados[self.chamado.get()]
        self.executar(lambda: self.app.sistema.registrar_saida_equipamento(
            self.app.usuario, self.equipamento.codigo, quantidade, chamado))

    def atualizar_dados(self):
        minimo = self.inteiro(self.novo_minimo.get())
        if minimo is None:
            return
        self.executar(lambda: self.app.sistema.atualizar_equipamento(
            self.app.usuario, self.equipamento.codigo, self.nova_descricao.get().strip(), minimo))

    def dar_baixa(self):
        motivo = simpledialog.askstring("Dar baixa", "Motivo da baixa (o equipamento não poderá mais "
                                        "ser movimentado):", parent=self)
        if motivo is None:
            return
        if not motivo.strip():
            messagebox.showwarning("Campo obrigatório", "Informe o motivo da baixa.", parent=self)
            return
        self.executar(lambda: self.app.sistema.dar_baixa_equipamento(
            self.app.usuario, self.equipamento.codigo, motivo.strip()))


class TelaEstoque(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai, padding=16)
        self.app = app
        self.equipamentos = {}

        ttk.Label(self, text="Estoque", style="Subtitulo.TLabel").pack(anchor="w")
        ttk.Label(self, text="Controle os equipamentos de TI, as reposições, as saídas para chamados e as baixas.",
                  style="Discreto.TLabel").pack(anchor="w", pady=(4, 12))

        filtros = ttk.Frame(self)
        filtros.pack(fill="x", pady=(0, 8))
        ttk.Label(filtros, text="Buscar:").pack(side="left")
        self.busca = tk.StringVar()
        self.busca.trace_add("write", self.atualizar)
        ttk.Entry(filtros, textvariable=self.busca).pack(side="left", fill="x", expand=True, padx=(6, 12))
        self.filtro_situacao = ttk.Combobox(filtros, state="readonly", width=18,
                                            values=["Todas as situações"] + SITUACOES)
        self.filtro_situacao.current(0)
        self.filtro_situacao.pack(side="left")
        self.filtro_situacao.bind("<<ComboboxSelected>>", self.atualizar)

        rodape = ttk.Frame(self)
        rodape.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Button(rodape, text="Ver equipamento", command=self.ver_equipamento).pack(side="right")
        ttk.Button(rodape, text="+ Adicionar equipamento", style="Principal.TButton",
                   command=self.adicionar_equipamento).pack(side="right", padx=(0, 8))

        self.tabela = criar_tabela(self, [
            ("codigo", "Código", 90),
            ("descricao", "Descrição", 280),
            ("tipo", "Tipo", 130),
            ("quantidade", "Quantidade", 100),
            ("minimo", "Mínimo", 90),
            ("situacao", "Situação", 140),
        ])
        self.tabela.bind("<Double-1>", lambda evento: self.ver_equipamento())
        self.atualizar()

    def atualizar(self, *args):
        self.tabela.delete(*self.tabela.get_children())
        self.equipamentos = {}
        busca = self.busca.get().strip().lower()
        situacao = self.filtro_situacao.get()
        for equipamento in self.app.sistema.listar_equipamentos(self.app.usuario, apenas_ativos=False):
            texto = f"{equipamento.codigo} {equipamento.descricao} {equipamento.tipo}".lower()
            if busca and busca not in texto:
                continue
            situacao_atual = situacao_equipamento(equipamento)
            if situacao != "Todas as situações" and situacao_atual != situacao:
                continue
            chave = str(equipamento.codigo)
            self.equipamentos[chave] = equipamento
            self.tabela.insert("", "end", iid=chave, tags=() if equipamento.ativo else ("bloqueado",), values=(
                equipamento.codigo, equipamento.descricao, equipamento.tipo, equipamento.quantidade,
                equipamento.quantidade_minima, situacao_atual,
            ))

    def adicionar_equipamento(self):
        CadastroEquipamento(self.app, self.atualizar)

    def ver_equipamento(self):
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showinfo("Selecione um equipamento", "Selecione uma linha para ver os detalhes.",
                                parent=self)
            return
        DetalheEquipamento(self.app, self.equipamentos[selecao[0]], self.atualizar)
