# Digital Closet

A Python OOP desktop app (Tkinter) for cataloguing your wardrobe and generating outfits in five styles, with a local Lookbook and secure login.

Course project for IT102 Object-Oriented Programming, Mapúa Malayan Colleges Mindanao.

## Features

- **Accounts:** sign up and log in with password rules and a lockout after 5 failed attempts. Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes.
- **Closet:** upload clothing photos under five categories (Top, Bottom, Shoes, Outer Top, Accessory). Rename, re-categorize, or delete items in My Closet.
- **Outfit generator:** five styles (Minimal, Layered, Accessorized, Full Fit, Surprise Me) plus a random Roulette screen.
- **Lookbook:** save, review, and discard outfits.
- **Local storage:** each user's data is kept as JSON files and image copies in `closet_data/`.

## Requirements

- Python 3, with Tkinter (included in the standard Windows and macOS installers)
- [Pillow](https://pypi.org/project/pillow/) (optional, for better photo loading and scaling)

```
pip install pillow
```

## How to run

```
git clone https://github.com/Cyatine/Digital-closet.git
cd Digital-closet
python main.py
```

Create an account on the sign-up screen, then add garments from the **Add Garment** screen. The `Sample Images` folder has photos you can use for testing. An outfit needs at least a Top, a Bottom, and Shoes in your closet.

## OOP design

| Principle | Where it appears |
|---|---|
| Encapsulation | Private attributes with read-only properties in `ClothingItem`, `Closet`, and `User` |
| Inheritance | `Top`, `Bottom`, `Shoes`, `Accessory`, `OuterTop` extend `ClothingItem`; five style classes extend `OutfitStyle` |
| Polymorphism | Each item overrides `style_tip()`; each style overrides `extra_categories()` |
| Abstraction | `ClothingItem` and `OutfitStyle` are abstract base classes (`abc`) |

## Project structure

| File | Purpose |
|---|---|
| `closet_core.py` | Model classes: items, closet, outfits, users, data storage |
| `outfit_styles.py` | The five outfit style classes |
| `main.py` | App window and main screens |
| `view_auth.py`, `view_home.py`, `views_base.py` | Login, sign-up, dashboard, and base view |
| `components.py`, `theme.py` | Reusable widgets and styling |
| `closet_data/` | Saved closets and outfits |

## Notes

- Everything runs offline, and no data leaves your computer.
- JSON files and photos are not encrypted.
