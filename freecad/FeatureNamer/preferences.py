"""Settings stored in the FreeCAD parameter store (console-safe)."""

from __future__ import annotations

import FreeCAD as App

from .core.naming import DEFAULT_POSTFIXES, format_postfixes, parse_postfixes

PARAM_PATH = "User parameter:BaseApp/Preferences/Mod/FeatureNamer"

DEFAULT_BOOLS = {
    "ShowNameField": True,  # Name field at the top of the Tasks panel
    "PromptIfUnnamed": True,  # popup when editing starts on a default-named feature
    "FocusNameField": False,  # cursor in the Name field instead of the popup
    "AskOnClose": False,  # ask again after OK if still default-named
    "AutoPostfix": True,  # append the type postfix to names
    "NameFromBase": True,  # Pad from "Moat_SKT" becomes "Moat_PAD" without asking
}
DEFAULT_EXCLUDE = "PartDesign::Body"


def params():
    return App.ParamGet(PARAM_PATH)


def get_bool(key: str) -> bool:
    return params().GetBool(key, DEFAULT_BOOLS[key])


def set_bool(key: str, value: bool) -> None:
    params().SetBool(key, bool(value))


def postfixes() -> list[tuple[str, str]]:
    raw = params().GetString("Postfixes", "")
    return parse_postfixes(raw) if raw.strip() else list(DEFAULT_POSTFIXES)


def set_postfixes(pairs) -> None:
    params().SetString("Postfixes", format_postfixes(pairs))


def postfix_for(type_id: str) -> str:
    """Postfix for a TypeId, or '' when auto postfix is off or none is set."""
    if not get_bool("AutoPostfix"):
        return ""
    return dict(postfixes()).get(type_id, "")


def all_postfixes() -> list[str]:
    return [pf for _, pf in postfixes() if pf]


def excluded_types() -> set[str]:
    raw = params().GetString("ExcludeTypes", DEFAULT_EXCLUDE)
    return {s.strip() for s in raw.split(",") if s.strip()}


def exclude_text() -> str:
    return params().GetString("ExcludeTypes", DEFAULT_EXCLUDE)


def set_exclude_text(text: str) -> None:
    params().SetString("ExcludeTypes", text.strip())
