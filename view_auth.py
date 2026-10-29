# view_auth.py
import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont
from theme import THEME, FONTS, HEADING, BODY, HEADING_STYLE, BRAND_STYLE
from views_base import BaseView
from closet_core import AuthError

BLACK = THEME["sidebar"]
WHITE = THEME["on_dark"]
CREAM = "#F5F2EC"
GOLD = "#C9A86A"
GREY = "#8A8A8A"
ERROR = "#9B1C1C"
ART_BG = "#FFFFFF"   # artwork panel background
ART_TEXT = "#000000"  # title text
LINE = "#BBBBBB"


def make_font(spec):
    family, size, *style = spec
    style = style[0] if style else ""
    return tkfont.Font(family=family, size=size,
                       weight="bold" if "bold" in style else "normal",
                       slant="italic" if "italic" in style else "roman")


class AuthScreen(BaseView):
    """Two panels: black artwork on the left, a clean form on the right.
    Everything (text, fields, artwork) scales with the window."""

    TITLE = ""
    SUBTITLE = ""
    BUTTON = ""

    def __init__(self, master, app):
        super().__init__(master, app)
        self.config(bg=WHITE)
        self._base = {"title": 22, "body": 11, "caption": 9, "hint": 9}
        self._fonts = {
            "title": make_font((HEADING, 22, HEADING_STYLE)),
            "body": make_font((BODY, 11, "bold")),
            "caption": make_font((BODY, 9, "bold")),
            "hint": make_font((BODY, 9)),
        }
        self._padded = []      # (widget, base ipady)
        self._lines = []       # underline frames, to colour on focus
        self._scale = 1.0

        self.columnconfigure(0, weight=11, uniform="panel")
        self.columnconfigure(1, weight=9, uniform="panel")
        self.rowconfigure(0, weight=1)

        self.art = tk.Canvas(self, bg=ART_BG, highlightthickness=0, bd=0)
        self.art.grid(row=0, column=0, sticky="nsew")
        self.art.bind("<Configure>", self._draw_art)

        self.panel = tk.Frame(self, bg=WHITE)
        self.panel.grid(row=0, column=1, sticky="nsew")
        self.content = tk.Frame(self.panel, bg=WHITE)
        self.content.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.78)

        self._label(self.TITLE, "title", anchor="w")
        self._label(self.SUBTITLE, "hint", anchor="w", pady=(2, 22), fg=GREY)
        self.build_form()
        self.message = tk.Label(self.content, text="", font=self._fonts["hint"], bg=WHITE, fg=ERROR,
                                wraplength=300, justify="left", anchor="w")
        self.message.pack(fill="x", pady=(10, 0))
        self.build_footer()

        self.bind("<Configure>", self._rescale)

    # ---- hooks for the subclasses ------------------------------------
    def build_form(self):
        pass

    def build_footer(self):
        pass

    # ---- scaling -----------------------------------------------------
    def _rescale(self, event):
        scale = max(1.0, min(event.width / 1040, event.height / 630, 1.8))
        self._scale = scale
        for key, font in self._fonts.items():
            font.configure(size=int(self._base[key] * scale))
        for widget, base in self._padded:
            widget.pack_configure(ipady=int(base * scale))
        self.message.config(wraplength=int(self.panel.winfo_width() * 0.72))

    # ---- widgets -----------------------------------------------------
    def _label(self, text, font, fg=None, **pack):
        label = tk.Label(self.content, text=text, font=self._fonts[font], bg=WHITE, fg=fg or BLACK)
        label.pack(**pack)
        return label

    def _field(self, caption, secret=False):
        """A label above an entry with an underline that turns black when focused."""
        self._label(caption.upper(), "caption", anchor="w", fg=GREY, pady=(0, 2))
        row = tk.Frame(self.content, bg=WHITE)
        row.pack(fill="x")
        entry = tk.Entry(row, font=self._fonts["body"], bg=WHITE, fg=BLACK, relief="flat", bd=0,
                         highlightthickness=0, insertbackground=BLACK, show="•" if secret else "")
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        self._padded.append((entry, 6))
        if secret:
            toggle = tk.Label(row, text="SHOW", font=self._fonts["caption"], bg=WHITE, fg=GREY, cursor="hand2")
            toggle.pack(side="right", padx=(8, 2))
            toggle.bind("<Button-1>", lambda e, en=entry, t=toggle: self._toggle(en, t))
        line = tk.Frame(self.content, bg=LINE, height=2)
        line.pack(fill="x", pady=(0, 14))
        entry.bind("<FocusIn>", lambda e, l=line: l.config(bg=BLACK))
        entry.bind("<FocusOut>", lambda e, l=line: l.config(bg=LINE))
        entry.bind("<Key>", lambda e: self.show_message(""), add="+")
        return entry

    def _toggle(self, entry, toggle):
        hidden = entry.cget("show") != ""
        entry.config(show="" if hidden else "•")
        toggle.config(text="HIDE" if hidden else "SHOW")

    def _button(self, text, command):
        button = tk.Button(self.content, text=text.upper(), command=command, font=self._fonts["body"],
                           bg=BLACK, fg=WHITE, activebackground="#333333", activeforeground=WHITE,
                           relief="flat", bd=0, cursor="hand2")
        button.pack(fill="x", pady=(6, 0), ipady=8)
        self._padded.append((button, 8))
        button.bind("<Enter>", lambda e: button.config(bg="#333333"))
        button.bind("<Leave>", lambda e: button.config(bg=BLACK))
        return button

    def _link(self, lead, action_text, command):
        row = tk.Frame(self.content, bg=WHITE)
        row.pack(pady=(18, 0))
        tk.Label(row, text=lead + " ", font=self._fonts["hint"], bg=WHITE, fg=GREY).pack(side="left")
        link = tk.Label(row, text=action_text, font=self._fonts["caption"], bg=WHITE, fg=BLACK, cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: command())
        link.bind("<Enter>", lambda e: link.config(fg=GOLD))
        link.bind("<Leave>", lambda e: link.config(fg=BLACK))
        return link

    def show_message(self, text):
        self.message.config(text=text)

    # ---- artwork -----------------------------------------------------
    @staticmethod
    def _tracked(text):
        """Wide letter spacing (Tk has none built in) using thin spaces between letters."""
        return "\u2009".join(text)

    def _draw_art(self, event):
        c = self.art
        c.delete("all")
        w, h = event.width, event.height
        if w < 80 or h < 80:
            return
        top, bottom = self._tracked("DIGITAL"), self._tracked("CLOSET")
        size = max(20, int(h / 6))
        while size > 20:     # shrink until the widest line fits the panel
            font = tkfont.Font(family=HEADING, size=size, weight="bold" if "bold" in BRAND_STYLE else "normal",
                                slant="italic" if "italic" in BRAND_STYLE else "roman")
            if font.measure(top) <= w * 0.86:
                break
            size -= 2
        c.create_line(w - 1, 0, w - 1, h, fill=ART_TEXT, width=2)   # divider between the two panels
        gap = int(size * 1.45)
        c.create_text(w / 2, h / 2 - gap / 2, text=top, fill=ART_TEXT, font=(HEADING, size, BRAND_STYLE))
        c.create_text(w / 2, h / 2 + gap / 2, text=bottom, fill=ART_TEXT, font=(HEADING, size, BRAND_STYLE))
        rule_y = h / 2 + gap / 2 + size * 1.05
        c.create_line(w / 2 - size * 1.2, rule_y, w / 2 + size * 1.2, rule_y, fill=ART_TEXT, width=3)


class LoginView(AuthScreen):
    TITLE = "Welcome back"
    SUBTITLE = "Sign in to open your trunk."

    def build_form(self):
        self.username = self._field("Username")
        self.password = self._field("Password", secret=True)
        self.username.bind("<Return>", lambda e: self.password.focus_set())
        self.password.bind("<Return>", lambda e: self._login())
        self._button("Unlock Trunk", self._login)

    def build_footer(self):
        self._link("New here?", "Create an account", self.app.show_signup)

    def on_show(self):
        self.password.delete(0, "end")
        self.show_message("")
        self.username.focus_set()

    def _login(self):
        if not self.username.get().strip() or not self.password.get():
            return self.show_message("Enter your username and password.")
        try:
            user = self.app.users.login(self.username.get(), self.password.get())
        except AuthError as err:
            self.password.delete(0, "end")
            self.password.focus_set()
            return self.show_message(str(err))
        self.app.start_session(user)


class SignUpView(AuthScreen):
    TITLE = "Create account"
    SUBTITLE = "8+ characters, mixing letters with numbers or symbols."

    def build_form(self):
        self.entries = {
            "user": self._field("Username"),
            "pw": self._field("Password", secret=True),
            "confirm": self._field("Confirm password", secret=True),
        }
        self.entries["user"].bind("<Return>", lambda e: self.entries["pw"].focus_set())
        self.entries["pw"].bind("<Return>", lambda e: self.entries["confirm"].focus_set())
        self.entries["confirm"].bind("<Return>", lambda e: self._do_register())
        self._button("Register", self._do_register)

    def build_footer(self):
        self._link("Already have an account?", "Sign in", self.app.show_login)

    def on_show(self):
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.show_message("")
        self.entries["user"].focus_set()

    def _do_register(self):
        username = self.entries["user"].get().strip()
        try:
            self.app.users.register(username, self.entries["pw"].get(), self.entries["confirm"].get())
        except AuthError as err:
            return self.show_message(str(err))
        messagebox.showinfo("Welcome", "Account created successfully.")
        self.app.show_login()
        login = getattr(self.app, "_screen", None)
        if hasattr(login, "username"):          # hand the new username to the login form
            login.username.insert(0, username)
            login.password.focus_set()