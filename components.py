# components.py
import math
import tkinter as tk
from theme import THEME, FONTS
from closet_core import ALL_CATEGORIES, ITEM_CLASSES

try:
    from PIL import Image, ImageTk, ImageOps
    PIL_OK = True
except ImportError:
    PIL_OK = False

def load_photo(path, box):
    try:
        if PIL_OK:
            img = Image.open(path).convert("RGBA")
            img = ImageOps.contain(img, box, Image.Resampling.LANCZOS)

            # flatten transparency, then fill the frame with the photo's own background color
            base = Image.new("RGBA", img.size, "white")
            base.alpha_composite(img)
            canvas = Image.new("RGBA", box, base.getpixel((0, 0)))
            canvas.paste(base, ((box[0] - base.width) // 2, (box[1] - base.height) // 2))
            return ImageTk.PhotoImage(canvas)
        photo = tk.PhotoImage(file=str(path))
        step_x = max(1, math.ceil(photo.width() / box[0]))
        step_y = max(1, math.ceil(photo.height() / box[1]))
        return photo.subsample(step_x, step_y)
    except Exception:
        return None

class RoundedCard(tk.Frame):
    def __init__(self, master, bg=None, **kwargs):
        super().__init__(master, bg=bg or THEME["surface"], highlightbackground=THEME["border"], highlightthickness=2, **kwargs)

class PrimaryButton(tk.Button):
    def __init__(self, master, text, command, width=None, **kwargs):
        super().__init__(
            master, text=text, command=command, font=FONTS["body_bold"], bg=THEME["primary"],
            fg=THEME["on_dark"], activebackground=THEME["primary_hover"], activeforeground=THEME["on_dark"],
            relief="ridge", bd=3, cursor="hand2", width=width, **kwargs
        )

class SecondaryButton(tk.Button):
    def __init__(self, master, text, command, width=None, **kwargs):
        super().__init__(
            master, text=text, command=command, font=FONTS["body"], bg=THEME["surface_subtle"],
            fg=THEME["text"], activebackground="#CFCFCF", activeforeground=THEME["text"], relief="groove", bd=2,
            cursor="hand2", width=width, **kwargs
        )

class StyledEntry(tk.Entry):
    def __init__(self, master, **kwargs):
        super().__init__(
            master, font=FONTS["body"], bg=THEME["surface_subtle"], fg=THEME["text"],
            relief="sunken", bd=2, insertbackground=THEME["primary"], **kwargs
        )

class ImagePanel(tk.Frame):
    def __init__(self, master, box=(130, 130), placeholder="Empty Hanger"):
        # +4 so the 2px border doesn't crop the image
        super().__init__(master, bg=THEME["surface_subtle"], highlightbackground=THEME["border"],
                         highlightthickness=2, width=box[0] + 4, height=box[1] + 4)
        self.pack_propagate(False)
        self._box = box
        self._placeholder = placeholder
        self._item = None
        self.label = tk.Label(self, text=placeholder, bg=THEME["surface_subtle"], fg=THEME["text_muted"], font=FONTS["caption"])
        self.label.place(relx=0.5, rely=0.5, anchor="center")

    def resize(self, box):
        self._box = box
        self.config(width=box[0] + 4, height=box[1] + 4)
        if self._item:
            self.show(self._item)

    def show(self, item):
        if not item: return self.clear()
        self._item = item
        photo = load_photo(item.image_path, self._box)
        if photo:
            self.label.config(image=photo, text="")
            self.label.image = photo
        else:
            self.label.config(image="", text=item.name)

    def clear(self):
        self._item = None
        self.label.config(image="", text=self._placeholder)
        self.label.image = None

class OutfitBoard(tk.Frame):
    MIN_BOX_W = 48    # smallest image width
    RATIO = 1.3       # image height = width * RATIO
    PAD_X = 30        # card padding + borders + grid gap, per card
    PAD_Y = 52        # label + card padding + borders + grid gap, per row

    def __init__(self, master):
        super().__init__(master, bg=THEME["bg"])
        self.pack_propagate(False)  # size comes from the parent, not from the cards
        self.inner = tk.Frame(self, bg=THEME["bg"])
        self.inner.pack(anchor="n")
        self.panels = {}
        self._cards = []
        for cat in ALL_CATEGORIES:
            card = RoundedCard(self.inner, padx=6, pady=6)
            tk.Label(card, text=f"{ITEM_CLASSES[cat].EMOJI} {cat}", font=FONTS["caption"],
                     bg=THEME["surface"], fg=THEME["text_muted"]).pack(pady=(0, 2))
            panel = ImagePanel(card, box=(110, 120))
            panel.pack()
            self.panels[cat] = panel
            self._cards.append(card)
        self._layout = None
        self._job = None
        self.bind("<Configure>", self._on_configure)
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        if event.widget is self and self._job:
            self.after_cancel(self._job)
            self._job = None

    def _on_configure(self, event):
        # wait until resizing pauses so the images aren't reloaded on every pixel
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(60, self._apply_layout)

    def _apply_layout(self):
        self._job = None
        width, height = self.winfo_width(), self.winfo_height()
        if width < 50 or height < 50:
            return
        count = len(self._cards)

        # try every column count and keep the one that gives the biggest images
        best = None
        for c in range(count, 0, -1):
            rows = math.ceil(count / c)
            size = min(width // c - self.PAD_X, (height // rows - self.PAD_Y) / self.RATIO)
            if best is None or size > best[0]:
                best = (size, c)
        size, cols = best

        box_w = max(self.MIN_BOX_W, int(size))
        box_h = max(60, int(box_w * self.RATIO))

        layout = (cols, box_w, box_h)
        if layout == self._layout:
            return
        self._layout = layout
        for i, card in enumerate(self._cards):
            card.grid(row=i // cols, column=i % cols, padx=5, pady=5)
        for panel in self.panels.values():
            panel.resize((box_w, box_h))

    def show_outfit(self, outfit):
        for category, panel in self.panels.items():
            panel.show(outfit.item_for(category) if outfit else None)

    def clear(self):
        self.show_outfit(None)