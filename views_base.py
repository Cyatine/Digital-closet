# views_base.py
import tkinter as tk
from theme import THEME

class BaseView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg"])
        self.app = app

    def on_show(self):
        pass