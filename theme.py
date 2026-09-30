"""theme.py — Dark Indigo Vault theme, matching myvault-prototype.jsx"""
from datetime import date, datetime


# Google Font used for big display numbers in the JSX ('Space Grotesk').
# Registered on page.fonts in main.py; pass this as font_family=DISPLAY_FONT
# on any Text control that mirrors a JSX element using that font.
DISPLAY_FONT = "Space Grotesk"


class T:
    bg = "#0B0718"
    surface = "#15102B"
    surface2 = "#1C1640"
    surface_border = "#2A2358"
    accent = "#6366F1"
    accent_soft = "#818CF8"
    brass = "#C9A66B"
    brass_soft = "#E4CFA0"
    success = "#34D399"
    warning = "#F5A623"
    danger = "#F5637A"
    text = "#F1EEFB"
    muted = "#948FBD"
    muted_faint = "#5D577E"


# icon field holds a compat.icon()-resolvable NAME string, resolved lazily
# in components/screens so this module has no hard Flet dependency.
CATEGORIES = {
    "Gadget": {"icon": "SMARTPHONE_ROUNDED", "color": T.accent},
    "Liburan": {"icon": "FLIGHT_ROUNDED", "color": T.success},
    "Darurat": {"icon": "SHIELD_ROUNDED", "color": T.danger},
    "Pendidikan": {"icon": "SCHOOL_ROUNDED", "color": T.warning},
    "Lainnya": {"icon": "INVENTORY_2_ROUNDED", "color": T.accent_soft},
}

MONTHS_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def fmt(n, currency="IDR"):
    n = n or 0
    if currency == "USD":
        usd = n / 15800
        return "$" + f"{usd:,.2f}"
    return "Rp" + f"{round(n):,}".replace(",", ".")


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def days_between(a: str, b: str) -> int:
    return (parse_date(b) - parse_date(a)).days


def today_str() -> str:
    return date.today().isoformat()
