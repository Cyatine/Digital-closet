"""
Digital Closet - core OOP model
-------------------------------
Python version of the Digital Closet WinForms project.
This file has no GUI code. It holds the classes that do the real work:

    ClothingItem (abstract)  ->  Top, Bottom, Shoes, Accessory, OuterTop
    Closet                   ->  stores items by category (encapsulation)
    Outfit                   ->  a combination of items (composition)
    OutfitGenerator          ->  random mix & match
    OutfitBook               ->  saved outfits
    User / UserManager       ->  sign up, log in (salted PBKDF2, lockout after failed attempts)
    UserSpace                ->  one user's closet + outfits + file storage (add, edit, delete items)
    DataStore                ->  JSON read/write
"""

import hashlib
import hmac
import json
import random
import secrets
import shutil
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path


# ----------------------------------------------------------------------
# Custom exceptions
# ----------------------------------------------------------------------
class ClosetError(Exception):
    """Base class for all errors raised by this app."""


class AuthError(ClosetError):
    """Raised when sign up or log in fails."""


class LockedOutError(AuthError):
    """Raised when too many wrong passwords were entered."""


class IncompleteClosetError(ClosetError):
    """Raised when there are not enough items to build an outfit."""


# ----------------------------------------------------------------------
# Clothing items: abstraction + inheritance + polymorphism
# ----------------------------------------------------------------------
class ClothingItem(ABC):
    """Abstract parent of every clothing type."""

    CATEGORY = ""
    EMOJI = ""

    def __init__(self, image_path, name=None, item_id=None):
        self._id = item_id or uuid.uuid4().hex[:8]
        self._image_path = str(image_path)
        self._name = name or Path(image_path).stem

    # Encapsulation: read-only access through properties
    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def image_path(self):
        return self._image_path

    @property
    def category(self):
        return self.CATEGORY

    @abstractmethod
    def style_tip(self):
        """Each subclass gives its own styling advice (polymorphism)."""

    def label(self):
        return f"{self.EMOJI} {self.CATEGORY}: {self._name}"

    def to_dict(self):
        return {
            "id": self._id,
            "name": self._name,
            "image_path": self._image_path,
            "category": self.CATEGORY,
        }

    def __str__(self):
        return self.label()

    def __repr__(self):
        return f"{type(self).__name__}(id={self._id!r}, name={self._name!r})"


class Top(ClothingItem):
    CATEGORY = "Top"
    EMOJI = "\U0001F455"

    def style_tip(self):
        return "Keep the top simple if your bottoms are loud."


class Bottom(ClothingItem):
    CATEGORY = "Bottom"
    EMOJI = "\U0001F456"

    def style_tip(self):
        return "Match the bottom's tone with your shoes."


class Shoes(ClothingItem):
    CATEGORY = "Shoes"
    EMOJI = "\U0001F45E"

    def style_tip(self):
        return "Shoes finish the look, so pick them before accessories."


class Accessory(ClothingItem):
    CATEGORY = "Accessory"
    EMOJI = "\U0001F3A7"

    def style_tip(self):
        return "One standout accessory is usually enough."


class OuterTop(ClothingItem):
    CATEGORY = "Outer Top"
    EMOJI = "\U0001F9E5"

    def style_tip(self):
        return "An outer layer works best over a plain top."


# Registry + factory so the rest of the code never hard-codes class names
ITEM_CLASSES = {cls.CATEGORY: cls for cls in (Top, Bottom, Shoes, Accessory, OuterTop)}
REQUIRED_CATEGORIES = ("Top", "Bottom", "Shoes")
OPTIONAL_CATEGORIES = ("Outer Top", "Accessory")
ALL_CATEGORIES = REQUIRED_CATEGORIES + OPTIONAL_CATEGORIES


def create_item(category, image_path, name=None, item_id=None):
    try:
        cls = ITEM_CLASSES[category]
    except KeyError:
        raise ClosetError(f"Unknown category: {category}")
    return cls(image_path, name=name, item_id=item_id)


def item_from_dict(data):
    return create_item(
        data["category"], data["image_path"], data.get("name"), data.get("id")
    )


# ----------------------------------------------------------------------
# Closet
# ----------------------------------------------------------------------
class Closet:
    """Holds every uploaded item, grouped by category."""

    def __init__(self):
        self._items = {category: [] for category in ALL_CATEGORIES}

    def add(self, item):
        self._items[item.category].append(item)

    def remove(self, item_id):
        for items in self._items.values():
            for item in items:
                if item.id == item_id:
                    items.remove(item)
                    return True
        return False

    def items_in(self, category):
        return list(self._items[category])  # copy, so callers can't mess with it

    def find(self, item_id):
        for items in self._items.values():
            for item in items:
                if item.id == item_id:
                    return item
        return None

    def count(self, category):
        return len(self._items[category])

    def total(self):
        return sum(len(items) for items in self._items.values())

    def missing_required(self):
        return [c for c in REQUIRED_CATEGORIES if not self._items[c]]

    def is_ready(self):
        return not self.missing_required()

    def to_dict(self):
        return {c: [i.to_dict() for i in items] for c, items in self._items.items()}

    @classmethod
    def from_dict(cls, data):
        closet = cls()
        for items in data.values():
            for item_data in items:
                closet.add(item_from_dict(item_data))
        return closet


# ----------------------------------------------------------------------
# Outfit (composition: an outfit is made of clothing items)
# ----------------------------------------------------------------------
class Outfit:
    def __init__(self, items, name=None, created=None):
        self._items = dict(items)  # category -> ClothingItem
        self._created = created or datetime.now().strftime("%Y-%m-%d %H:%M")
        self._name = name or f"Outfit {self._created}"

    @property
    def name(self):
        return self._name

    @property
    def created(self):
        return self._created

    def item_for(self, category):
        return self._items.get(category)

    def items(self):
        return [self._items[c] for c in ALL_CATEGORIES if c in self._items]

    def is_complete(self):
        return all(c in self._items for c in REQUIRED_CATEGORIES)

    def summary(self):
        return "\n".join(item.label() for item in self.items())

    def to_dict(self):
        return {
            "name": self._name,
            "created": self._created,
            "items": [i.to_dict() for i in self.items()],
        }

    @classmethod
    def from_dict(cls, data):
        items = {}
        for item_data in data["items"]:
            item = item_from_dict(item_data)
            items[item.category] = item
        return cls(items, name=data["name"], created=data["created"])

    def __str__(self):
        return f"{self._name} ({len(self._items)} pieces)"


# ----------------------------------------------------------------------
# Generator
# ----------------------------------------------------------------------
class OutfitGenerator:
    """Builds a random outfit. The random source is injectable for testing."""

    def __init__(self, rng=None):
        self._rng = rng or random.Random()

    def generate(self, closet, include_optional=True):
        missing = closet.missing_required()
        if missing:
            raise IncompleteClosetError(
                "Upload at least one item for: " + ", ".join(missing)
            )
        picks = {c: self._rng.choice(closet.items_in(c)) for c in REQUIRED_CATEGORIES}
        if include_optional:
            for c in OPTIONAL_CATEGORIES:
                options = closet.items_in(c)
                if options and self._rng.random() < 0.6:
                    picks[c] = self._rng.choice(options)
        return Outfit(picks)


class OutfitBook:
    """Saved outfits."""

    def __init__(self):
        self._outfits = []

    def add(self, outfit):
        self._outfits.append(outfit)

    def delete(self, index):
        del self._outfits[index]

    def all(self):
        return list(self._outfits)

    def uses_image(self, image_path):
        """True if any saved outfit still shows this image."""
        return any(i.image_path == str(image_path) for o in self._outfits for i in o.items())

    def __len__(self):
        return len(self._outfits)

    def to_dict(self):
        return [o.to_dict() for o in self._outfits]

    @classmethod
    def from_dict(cls, data):
        book = cls()
        for entry in data:
            book.add(Outfit.from_dict(entry))
        return book


# ----------------------------------------------------------------------
# Users and authentication
# ----------------------------------------------------------------------
class User:
    """Stores a salted PBKDF2 hash, never the plain password."""

    ITERATIONS = 600_000          # OWASP recommendation for PBKDF2-HMAC-SHA256
    LEGACY_ITERATIONS = 100_000   # accounts made by the first version

    def __init__(self, username, password_hash, salt, iterations=None):
        self._username = username
        self._hash = password_hash
        self._salt = salt
        self._iterations = iterations or self.LEGACY_ITERATIONS

    @property
    def username(self):
        return self._username

    @property
    def needs_rehash(self):
        return self._iterations < self.ITERATIONS

    @classmethod
    def create(cls, username, password):
        salt = secrets.token_hex(16)
        return cls(username, cls._hash_password(password, salt, cls.ITERATIONS), salt, cls.ITERATIONS)

    @staticmethod
    def _hash_password(password, salt, iterations):
        raw = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), iterations
        )
        return raw.hex()

    def check_password(self, password):
        attempt = self._hash_password(password, self._salt, self._iterations)
        return hmac.compare_digest(attempt, self._hash)

    def upgrade_hash(self, password):
        """Re-hash with the current iteration count (call only after a correct login)."""
        self._salt = secrets.token_hex(16)
        self._iterations = self.ITERATIONS
        self._hash = self._hash_password(password, self._salt, self._iterations)

    def to_dict(self):
        return {"username": self._username, "hash": self._hash,
                "salt": self._salt, "iterations": self._iterations}

    @classmethod
    def from_dict(cls, data):
        return cls(data["username"], data["hash"], data["salt"], data.get("iterations"))


class DataStore:
    """All file access lives here (JSON files + image copies)."""

    def __init__(self, root="closet_data"):
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def read(self, path, default):
        path = Path(path)
        if not path.exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write(self, path, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @property
    def users_file(self):
        return self._root / "users.json"

    def user_dir(self, username):
        folder = self._root / username
        (folder / "images").mkdir(parents=True, exist_ok=True)
        return folder


class UserManager:
    MIN_USERNAME = 3
    MIN_PASSWORD = 8
    MAX_ATTEMPTS = 5      # wrong passwords allowed in a row
    LOCKOUT_SECONDS = 30

    def __init__(self, store, clock=time.monotonic):
        self._store = store
        self._clock = clock
        self._failures = {}   # username -> (count, locked_until)
        self._users = {
            u["username"].lower(): User.from_dict(u)
            for u in store.read(store.users_file, [])
        }

    def register(self, username, password, confirm):
        username = username.strip()
        if len(username) < self.MIN_USERNAME:
            raise AuthError(f"Username must be at least {self.MIN_USERNAME} characters.")
        if not username.replace("_", "").isalnum() or not username.isascii():
            raise AuthError("Username can only use letters, numbers and underscores.")
        if len(password) < self.MIN_PASSWORD:
            raise AuthError(f"Password must be at least {self.MIN_PASSWORD} characters.")
        if password.isalpha() or password.isdigit():
            raise AuthError("Password must mix letters with numbers or symbols.")
        if password.lower() == username.lower():
            raise AuthError("Password must be different from the username.")
        if password != confirm:
            raise AuthError("Passwords do not match.")
        if username.lower() in self._users:
            raise AuthError("That username is already taken.")
        user = User.create(username, password)
        self._users[username.lower()] = user
        self._save()
        return user

    def login(self, username, password):
        key = username.strip().lower()
        self._check_lock(key)
        user = self._users.get(key)
        if user is None or not user.check_password(password):
            self._record_failure(key)
            raise AuthError("Wrong username or password.")
        self._failures.pop(key, None)
        if user.needs_rehash:               # quietly upgrade old accounts
            user.upgrade_hash(password)
            self._save()
        return user

    def _check_lock(self, key):
        count, until = self._failures.get(key, (0, 0))
        remaining = until - self._clock()
        if remaining > 0:
            raise LockedOutError(f"Too many attempts. Try again in {int(remaining) + 1} seconds.")

    def _record_failure(self, key):
        count, _ = self._failures.get(key, (0, 0))
        count += 1
        until = self._clock() + self.LOCKOUT_SECONDS if count >= self.MAX_ATTEMPTS else 0
        self._failures[key] = (0 if until else count, until)

    def _save(self):
        self._store.write(
            self._store.users_file, [u.to_dict() for u in self._users.values()]
        )


# ----------------------------------------------------------------------
# One logged-in user's data
# ----------------------------------------------------------------------
class UserSpace:
    """Ties a user to their closet, saved outfits and image folder."""

    def __init__(self, user, store):
        self._user = user
        self._store = store
        self._folder = store.user_dir(user.username)
        self.closet = Closet.from_dict(store.read(self._folder / "closet.json", {}))
        self.outfits = OutfitBook.from_dict(store.read(self._folder / "outfits.json", []))

    @property
    def username(self):
        return self._user.username

    def add_item(self, category, source_image, name=None):
        """Copy the image into the user's folder so it survives if the original moves."""
        source = Path(source_image)
        if not source.is_file():
            raise ClosetError("That image file could not be found.")
        target = self._folder / "images" / f"{uuid.uuid4().hex[:8]}_{source.name}"
        shutil.copy2(source, target)
        item = create_item(category, target, name or source.stem)
        self.closet.add(item)
        self.save()
        return item

    def remove_item(self, item_id):
        """Remove a garment. Its image is deleted too unless a saved outfit still uses it."""
        item = self.closet.find(item_id)
        if item is None:
            return False
        self.closet.remove(item_id)
        if not self.outfits.uses_image(item.image_path):
            try:
                Path(item.image_path).unlink()
            except OSError:
                pass
        self.save()
        return True

    def update_item(self, item_id, name=None, category=None):
        """Rename a garment and/or move it to another category (keeps id and image)."""
        old = self.closet.find(item_id)
        if old is None:
            raise ClosetError("That garment no longer exists.")
        new_name = (name or old.name).strip() or old.name
        new_category = category or old.category
        self.closet.remove(item_id)
        self.closet.add(create_item(new_category, old.image_path, new_name, old.id))
        self.save()
        return self.closet.find(item_id)

    def save_outfit(self, outfit):
        if not outfit.is_complete():
            raise IncompleteClosetError("An outfit needs a top, bottom and shoes.")
        self.outfits.add(outfit)
        self.save()

    def delete_outfit(self, index):
        self.outfits.delete(index)
        self.save()

    def save(self):
        self._store.write(self._folder / "closet.json", self.closet.to_dict())
        self._store.write(self._folder / "outfits.json", self.outfits.to_dict())