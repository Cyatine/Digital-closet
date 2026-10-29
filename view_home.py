# view_home.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from theme import THEME, FONTS
from components import RoundedCard, PrimaryButton, SecondaryButton, OutfitBoard
from views_base import BaseView
from closet_core import ALL_CATEGORIES, ITEM_CLASSES, ClosetError
from outfit_styles import STYLES

class HomeView(BaseView):
    def __init__(self, master, app):
        super().__init__(master, app)
        self._style = None
        self._outfit = None

        header = tk.Frame(self, bg=THEME["bg"])
        header.pack(fill="x", padx=36, pady=(14, 4))

        tk.Label(header, text="Your Vintage Collection", font=FONTS["title"], bg=THEME["bg"], fg=THEME["text"]).pack(anchor="w")

        self.clock = tk.Label(header, font=FONTS["caption"], bg=THEME["bg"], fg=THEME["text_muted"])
        self.clock.pack(anchor="w", pady=(2, 0))

        self.stats_container = tk.Frame(self, bg=THEME["bg"])
        self.stats_container.pack(fill="x", padx=36, pady=(4, 2))

        self.stat_cards = {}
        for category in ALL_CATEGORIES:
            card = RoundedCard(self.stats_container, padx=10, pady=4)
            card.pack(side="left", fill="both", expand=True, padx=4)
            emoji = ITEM_CLASSES[category].EMOJI
            tk.Label(card, text=emoji, font=("Segoe UI", 12), bg=THEME["surface"]).pack()
            val_lbl = tk.Label(card, text="0", font=FONTS["subtitle"], bg=THEME["surface"], fg=THEME["text"])
            val_lbl.pack()
            tk.Label(card, text=category, font=FONTS["caption"], bg=THEME["surface"], fg=THEME["text_muted"]).pack()
            self.stat_cards[category] = val_lbl

        # ---- Outfit styles ----
        tk.Label(self, text="Outfit Styles", font=FONTS["subtitle"], bg=THEME["bg"], fg=THEME["text"]).pack(anchor="w", padx=36, pady=(8, 2))

        styles_row = tk.Frame(self, bg=THEME["bg"])
        styles_row.pack(fill="x", padx=36)

        self.style_cards = {}
        for style in STYLES:
            card = RoundedCard(styles_row, padx=6, pady=6)
            card.pack(side="left", fill="both", expand=True, padx=2)
            tk.Label(card, text=style.name, font=(FONTS["heading"][0], 11, FONTS["heading"][2]), bg=THEME["surface"], fg=THEME["text"]).pack()
            tk.Label(card, text=style.tagline, font=FONTS["caption"], bg=THEME["surface"], fg=THEME["text_muted"],
                     wraplength=104, justify="center").pack(pady=(2, 0))
            for widget in (card, *card.winfo_children()):
                widget.bind("<Button-1>", lambda e, s=style: self._select(s))
                widget.config(cursor="hand2")
            self.style_cards[style] = card

        actions = tk.Frame(self, bg=THEME["bg"])
        actions.pack(side="bottom", pady=6)
        PrimaryButton(actions, "Shuffle", self._roll).pack(side="left", padx=6)
        SecondaryButton(actions, "Save to Lookbook", self._save).pack(side="left", padx=6)

        self.board = OutfitBoard(self)
        self.board.pack(fill="both", expand=True, padx=36, pady=(6, 0))

        self._tick_job = None
        self.bind("<Destroy>", self._stop_tick)
        self._tick()

    def _tick(self):
        self.clock.config(text=datetime.now().strftime("%A, %B %d, %Y  •  %I:%M %p"))
        self._tick_job = self.after(1000, self._tick)

    def _stop_tick(self, event):
        if event.widget is self and self._tick_job:
            self.after_cancel(self._tick_job)
            self._tick_job = None

    def on_show(self):
        space = self.app.space
        for cat in ALL_CATEGORIES:
            self.stat_cards[cat].config(text=str(space.closet.count(cat)))
        self._style = None
        self._outfit = None
        self._highlight(None)
        self.board.clear()

    def _highlight(self, selected):
        for style, card in self.style_cards.items():
            card.config(highlightbackground=THEME["primary"] if style is selected else THEME["border"])

    def _select(self, style):
        self._style = style
        self._highlight(style)
        self._roll()

    def _roll(self):
        if not self._style:
            return messagebox.showinfo("Notice", "Pick a style first.")
        try:
            self._outfit = self._style.build(self.app.space.closet)
            self.board.show_outfit(self._outfit)
        except ClosetError as err:
            messagebox.showwarning("Unavailable", str(err))

    def _save(self):
        if not self._outfit:
            return messagebox.showinfo("Notice", "Pick a style first.")
        try:
            self.app.space.save_outfit(self._outfit)
            messagebox.showinfo("Saved", "Look added!")
        except ClosetError as err:
            messagebox.showwarning("Attention", str(err))