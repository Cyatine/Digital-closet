# outfit_styles.py
import random
from abc import ABC, abstractmethod
from datetime import datetime
from closet_core import REQUIRED_CATEGORIES, OPTIONAL_CATEGORIES, Outfit, IncompleteClosetError


class OutfitStyle(ABC):
    """Abstract parent of every outfit style. Each style decides which extra pieces to add."""

    NAME = ""
    TAGLINE = ""

    def __init__(self, rng=None):
        self._rng = rng or random.Random()

    @property
    def name(self):
        return self.NAME

    @property
    def tagline(self):
        return self.TAGLINE

    @abstractmethod
    def extra_categories(self, closet):
        """Optional categories this style adds on top of top, bottom and shoes (polymorphism)."""

    def build(self, closet):
        missing = closet.missing_required()
        if missing:
            raise IncompleteClosetError("Upload at least one item for: " + ", ".join(missing))

        extras = tuple(self.extra_categories(closet))
        lacking = [c for c in extras if closet.count(c) == 0]
        if lacking:
            raise IncompleteClosetError(
                f"{self.NAME} needs at least one item for: " + ", ".join(lacking)
            )

        picks = {c: self._rng.choice(closet.items_in(c)) for c in REQUIRED_CATEGORIES + extras}
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return Outfit(picks, name=f"{self.NAME} {stamp}", created=stamp)


class MinimalStyle(OutfitStyle):
    NAME = "Minimal"
    TAGLINE = "Top, bottom and shoes. Nothing extra."

    def extra_categories(self, closet):
        return ()


class LayeredStyle(OutfitStyle):
    NAME = "Layered"
    TAGLINE = "The base look with an outer top over it."

    def extra_categories(self, closet):
        return ("Outer Top",)


class AccessorizedStyle(OutfitStyle):
    NAME = "Accessorized"
    TAGLINE = "The base look plus one accessory."

    def extra_categories(self, closet):
        return ("Accessory",)


class FullFitStyle(OutfitStyle):
    NAME = "Full Fit"
    TAGLINE = "Every piece: outer top and accessory too."

    def extra_categories(self, closet):
        return OPTIONAL_CATEGORIES


class SurpriseStyle(OutfitStyle):
    NAME = "Surprise Me"
    TAGLINE = "Random extras, a different mix each time."

    def extra_categories(self, closet):
        return [c for c in OPTIONAL_CATEGORIES
                if closet.count(c) and self._rng.random() < 0.5]


STYLES = [MinimalStyle(), LayeredStyle(), AccessorizedStyle(), FullFitStyle(), SurpriseStyle()]