"""Template registry — multi-language Lean error explanations.

Architecture:
- Default locale: English (locales/en.py) — the primary market.
- Additional locales are optional plugins (e.g. locales/zh.py).

To add a language: create `locales/<code>.py` exposing a
`TEMPLATES_<CODE>` dict, then register it in `_LOCALES`.
"""

from __future__ import annotations

import importlib
from typing import Any, Optional

from .classify import ErrorCategory
from .locales.en import TEMPLATES_EN

# Language registry: code -> module name (relative to this package)
_LOCALES: dict[str, str] = {
    "en": ".locales.en",
    "zh": ".locales.zh",
}


def available_languages() -> list[str]:
    """Return the list of installed language codes."""
    return list(_LOCALES.keys())


def _load_templates(lang: str) -> dict[ErrorCategory, dict[str, Any]]:
    if lang == "en":
        return TEMPLATES_EN
    if lang not in _LOCALES:
        raise KeyError(
            f"Unsupported language {lang!r}. Available: {available_languages()}"
        )
    module = importlib.import_module(_LOCALES[lang], package=__package__)
    return getattr(module, f"TEMPLATES_{lang.upper()}")


def render(
    category: ErrorCategory,
    code: str | None = None,
    lang: str = "en",
) -> dict[str, Any]:
    """Render the explanation for a category in the given language.

    Falls back to English when a category is missing in a locale plugin.
    """
    templates = _load_templates(lang)
    t = templates.get(category)
    if t is None:
        t = TEMPLATES_EN.get(category, TEMPLATES_EN[ErrorCategory.UNKNOWN])

    text = {
        "title": t["title"],
        "what": t["what"],
        "why": t["why"],
        "fix": t["fix"],
        "example": t.get("example"),
    }
    if code and "{code}" in text["what"]:
        text["what"] = text["what"].replace("{code}", code)
    return text
