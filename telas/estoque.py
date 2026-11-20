from tkinter import ttk


class TelaEstoque(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai, padding=16)
        self.app = app
