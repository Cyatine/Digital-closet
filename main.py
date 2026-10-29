# main.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from theme import THEME, FONTS
from components import RoundedCard, PrimaryButton, SecondaryButton, StyledEntry, ImagePanel, OutfitBoard
from views_base import BaseView
from closet_core import DataStore, UserManager, UserSpace, ALL_CATEGORIES, ClosetError, OutfitGenerator

from view_auth import LoginView, SignUpView
from view_home import HomeView

class UploadView(BaseView):
    def __init__(self, master, app):
        super().__init__(master, app)
        self._path = None
        self._fit_job = None
        container = tk.Frame(self, bg=THEME["bg"])
        container.pack(fill="both", expand=True, padx=36, pady=24)

        tk.Label(container, text="Add to Trunk", font=FONTS["title"], bg=THEME["bg"], fg=THEME["text"]).pack(anchor="w")
        card = RoundedCard(container, padx=28, pady=24)
        card.pack(fill="both", expand=True, pady=10)

        # two equal halves that stretch with the window
        card.columnconfigure(0, weight=1, uniform="half")
        card.columnconfigure(1, weight=1, uniform="half")
        card.rowconfigure(0, weight=1)

        # ---- left: photo preview fills its whole half ----
        left = tk.Frame(card, bg=THEME["surface"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        SecondaryButton(left, "Browse Files", self._browse).pack(side="bottom", fill="x", pady=(10, 0), ipady=4)
        self.holder = tk.Frame(left, bg=THEME["surface"])
        self.holder.pack(fill="both", expand=True)
        self.preview = ImagePanel(self.holder, box=(220, 220), placeholder="Select Photo")
        self.preview.place(relx=0.5, rely=0.5, anchor="center")
        self.holder.bind("<Configure>", self._fit_preview)
        self.bind("<Destroy>", self._on_destroy)

        # ---- right: form fills its whole half ----
        right = tk.Frame(card, bg=THEME["surface"])
        right.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        form = tk.Frame(right, bg=THEME["surface"])
        form.pack(fill="x", expand=True)

        tk.Label(form, text="Category", font=FONTS["heading"], bg=THEME["surface"]).pack(anchor="w")
        self.category = ttk.Combobox(form, values=list(ALL_CATEGORIES), state="readonly")
        self.category.current(0)
        self.category.pack(fill="x", pady=(4, 18), ipady=4)

        tk.Label(form, text="Item Name / Tag", font=FONTS["heading"], bg=THEME["surface"]).pack(anchor="w")
        self.name = StyledEntry(form)
        self.name.pack(fill="x", pady=(4, 24), ipady=6)

        PrimaryButton(form, "Add to Wardrobe", self._add).pack(fill="x", ipady=6)

    def _on_destroy(self, event):
        if event.widget is self and self._fit_job:
            self.after_cancel(self._fit_job)
            self._fit_job = None

    def _fit_preview(self, event):
        # wait until resizing pauses so the photo isn't reloaded on every pixel
        if self._fit_job:
            self.after_cancel(self._fit_job)
        self._fit_job = self.after(60, lambda: self._apply_fit(event.width, event.height))

    def _apply_fit(self, width, height):
        self._fit_job = None
        self.preview.resize((max(120, width - 8), max(120, height - 8)))

    def _browse(self):
        path = filedialog.askopenfilename(title="Select Item", filetypes=[("Images", "*.png *.gif *.jpg *.jpeg")])
        if path:
            self._path = path
            self.preview.show(type("Dummy", (), {"image_path": path, "name": "Selected"})())

    def _add(self):
        if not self._path: return messagebox.showwarning("Notice", "Select an image.")
        try:
            self.app.space.add_item(self.category.get(), self._path, self.name.get().strip() or None)
            messagebox.showinfo("Success", "Garment added to your thrift trunk!")
            self._path = None
            self.preview.clear()
            self.name.delete(0, "end")
        except ClosetError as err:
            messagebox.showerror("Error", str(err))

class WardrobeView(BaseView):
    """Browse, rename, re-categorize and delete garments."""

    def __init__(self, master, app):
        super().__init__(master, app)
        self._items = []
        self._current = None

        tk.Label(self, text="My Closet", font=FONTS["title"], bg=THEME["bg"]).pack(pady=(24, 8))
        body = tk.Frame(self, bg=THEME["bg"])
        body.pack(fill="both", expand=True, padx=36, pady=8)

        left = RoundedCard(body, padx=14, pady=14)
        left.pack(side="left", fill="y", padx=(0, 16))
        self.filter = ttk.Combobox(left, values=["All"] + list(ALL_CATEGORIES), state="readonly", width=20)
        self.filter.current(0)
        self.filter.pack(fill="x", pady=(0, 8))
        self.filter.bind("<<ComboboxSelected>>", lambda e: self._refresh())
        self.listbox = tk.Listbox(left, width=22, height=5, font=FONTS["body"],
                                  bg=THEME["surface_subtle"], fg=THEME["text"], exportselection=False)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._select())

        right = RoundedCard(body, padx=20, pady=16)
        right.pack(side="left", fill="both", expand=True)

        # form sits at the bottom; the photo takes all the space above it
        form = tk.Frame(right, bg=THEME["surface"])
        form.pack(side="bottom", fill="x", pady=(12, 0))
        tk.Label(form, text="Name", font=FONTS["heading"], bg=THEME["surface"]).pack(anchor="w")
        self.name = StyledEntry(form)
        self.name.pack(fill="x", pady=(2, 8), ipady=6)
        tk.Label(form, text="Category", font=FONTS["heading"], bg=THEME["surface"]).pack(anchor="w")
        self.category = ttk.Combobox(form, values=list(ALL_CATEGORIES), state="readonly")
        self.category.pack(fill="x", pady=(2, 10), ipady=4)
        buttons = tk.Frame(form, bg=THEME["surface"])
        buttons.pack(fill="x")
        PrimaryButton(buttons, "Save Changes", self._save).pack(side="left", expand=True, fill="x", padx=(0, 4), ipady=5)
        SecondaryButton(buttons, "Delete", self._delete).pack(side="left", expand=True, fill="x", padx=(4, 0), ipady=5)

        self.holder = tk.Frame(right, bg=THEME["surface"])
        self.holder.pack(fill="both", expand=True)
        self.preview = ImagePanel(self.holder, box=(180, 220), placeholder="Select a garment")
        self.preview.place(relx=0.5, rely=0.5, anchor="center")
        self._fit_job = None
        self.holder.bind("<Configure>", self._fit_preview)
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        if event.widget is self and self._fit_job:
            self.after_cancel(self._fit_job)
            self._fit_job = None

    def _fit_preview(self, event):
        # wait until resizing pauses so the photo isn't reloaded on every pixel
        if self._fit_job:
            self.after_cancel(self._fit_job)
        self._fit_job = self.after(60, lambda: self._apply_fit(event.width, event.height))

    def _apply_fit(self, width, height):
        self._fit_job = None
        self.preview.resize((max(120, width - 8), max(120, height - 8)))

    def on_show(self):
        self._refresh()

    def _refresh(self):
        wanted = self.filter.get()
        cats = ALL_CATEGORIES if wanted in ("", "All") else (wanted,)
        self._items = [i for c in cats for i in self.app.space.closet.items_in(c)]
        self.listbox.delete(0, "end")
        for item in self._items:
            self.listbox.insert("end", f"{item.category}: {item.name}")
        self._current = None
        self.preview.clear()
        self.name.delete(0, "end")
        self.category.set("")

    def _select(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._current = self._items[sel[0]]
        self.preview.show(self._current)
        self.name.delete(0, "end")
        self.name.insert(0, self._current.name)
        self.category.set(self._current.category)

    def _save(self):
        if not self._current:
            return messagebox.showinfo("Notice", "Select a garment first.")
        try:
            self.app.space.update_item(self._current.id, self.name.get(), self.category.get())
            messagebox.showinfo("Saved", "Garment updated.")
            self._refresh()
        except ClosetError as err:
            messagebox.showerror("Error", str(err))

    def _delete(self):
        if not self._current:
            return messagebox.showinfo("Notice", "Select a garment first.")
        if messagebox.askyesno("Confirm", f"Delete '{self._current.name}' from your closet?"):
            self.app.space.remove_item(self._current.id)
            self._refresh()

class GeneratorView(BaseView):
    def __init__(self, master, app):
        super().__init__(master, app)
        self._generator = OutfitGenerator()
        self._outfit = None

        tk.Label(self, text="Thrift Roulette", font=FONTS["title"], bg=THEME["bg"]).pack(pady=(24, 4))
        self.board = OutfitBoard(self)
        self.board.pack(fill="both", expand=True, padx=20, pady=8)

        actions = tk.Frame(self, bg=THEME["bg"])
        actions.pack(pady=12)
        PrimaryButton(actions, "Roll Dice", self._generate).pack(side="left", padx=6)
        SecondaryButton(actions, "Save to Lookbook", self._save).pack(side="left", padx=6)

    def on_show(self):
        self.board.clear()
        self._outfit = None

    def _generate(self):
        try:
            self._outfit = self._generator.generate(self.app.space.closet)
            self.board.show_outfit(self._outfit)
        except ClosetError as err:
            messagebox.showwarning("Unavailable", str(err))

    def _save(self):
        if not self._outfit: return messagebox.showinfo("Notice", "Generate a look first.")
        try:
            self.app.space.save_outfit(self._outfit)
            messagebox.showinfo("Saved", "Look added!")
        except ClosetError as err:
            messagebox.showwarning("Attention", str(err))

class SavedView(BaseView):
    def __init__(self, master, app):
        super().__init__(master, app)
        tk.Label(self, text="Lookbook", font=FONTS["title"], bg=THEME["bg"]).pack(pady=(24, 12))

        body = tk.Frame(self, bg=THEME["bg"])
        body.pack(fill="both", expand=True, padx=36, pady=8)

        left = RoundedCard(body, padx=14, pady=14)
        left.pack(side="left", fill="y", padx=(0, 16))

        self.listbox = tk.Listbox(left, width=20, height=12, font=FONTS["body"], bg=THEME["surface_subtle"], fg=THEME["text"])
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._show_selected())
        SecondaryButton(left, "Discard Look", self._delete, width=16).pack(pady=(12, 0))

        right = tk.Frame(body, bg=THEME["bg"])
        right.pack(side="left", fill="both", expand=True)
        self.board = OutfitBoard(right)
        self.board.pack(fill="both", expand=True)

    def on_show(self):
        self.listbox.delete(0, "end")
        outfits = self.app.space.outfits.all()
        for outfit in outfits:
            self.listbox.insert("end", outfit.name)
        self.board.clear()
        if outfits:
            self.listbox.selection_set(0)
            self._show_selected()

    def _show_selected(self):
        sel = self.listbox.curselection()
        if sel:
            self.board.show_outfit(self.app.space.outfits.all()[sel[0]])

    def _delete(self):
        sel = self.listbox.curselection()
        if sel and messagebox.askyesno("Confirm", "Discard this outfit?"):
            self.app.space.delete_outfit(sel[0])
            self.on_show()

class MainView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg"])
        self.app = app

        self.sidebar = tk.Frame(self, bg=THEME["sidebar"], width=175, relief="ridge", bd=4)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Label(self.sidebar, text="DIGITAL\nCLOSET", font=FONTS["brand_small"], bg=THEME["sidebar"], fg=THEME["on_dark"], pady=20)
        brand.pack(fill="x")

        self.content = tk.Frame(self, bg=THEME["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        self.views = {
            "Dashboard": HomeView(self.content, app),
            "Add Garment": UploadView(self.content, app),
            "My Closet": WardrobeView(self.content, app),
            "Roulette": GeneratorView(self.content, app),
            "Lookbook": SavedView(self.content, app),
        }

        self._nav_buttons = {}
        for label in self.views.keys():
            btn = tk.Button(
                self.sidebar, text=f"• {label}", font=FONTS["body"], fg=THEME["on_dark_muted"], bg=THEME["sidebar"],
                activebackground=THEME["sidebar_active"], activeforeground=THEME["on_dark"], relief="flat",
                bd=0, anchor="w", padx=20, pady=10, cursor="hand2", command=lambda l=label: self.show(l)
            )
            btn.pack(fill="x")
            self._nav_buttons[label] = btn

        tk.Button(
            self.sidebar, text="• Log Out", font=FONTS["body"], fg=THEME["on_dark_muted"], bg=THEME["sidebar"],
            activebackground=THEME["sidebar_active"], relief="flat", anchor="w", padx=20, pady=10, command=app.logout
        ).pack(side="bottom", fill="x", pady=10)

        self._current_label = None

    def show(self, label):
        if self._current_label:
            self.views[self._current_label].pack_forget()
            self._nav_buttons[self._current_label].config(fg=THEME["on_dark_muted"], font=FONTS["body"])

        self._current_label = label
        self._nav_buttons[label].config(fg=THEME["on_dark"], font=FONTS["body_bold"])

        self.views[label].pack(fill="both", expand=True)
        self.views[label].on_show()

class DigitalClosetApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Digital Closet")
        self.geometry("1040x630")
        self.minsize(860, 560)
        self.configure(bg=THEME["bg"])

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=THEME["surface_subtle"], background=THEME["surface"], foreground=THEME["text"])

        self.store = DataStore("closet_data")
        self.users = UserManager(self.store)
        self.space = None
        self._screen = None
        self.show_login()

    def _swap(self, screen):
        if self._screen: self._screen.destroy()
        self._screen = screen
        screen.pack(fill="both", expand=True)
        if hasattr(screen, "on_show"): screen.on_show()

    def show_login(self): self._swap(LoginView(self, self))
    def show_signup(self): self._swap(SignUpView(self, self))

    def start_session(self, user):
        self.space = UserSpace(user, self.store)
        main = MainView(self, self)
        self._swap(main)
        main.show("Dashboard")

    def logout(self):
        self.space = None
        self.show_login()

if __name__ == "__main__":
    DigitalClosetApp().mainloop()