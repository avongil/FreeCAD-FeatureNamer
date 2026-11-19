"""Questions about FreeCAD document objects (console-safe, no GUI)."""

from __future__ import annotations

import FreeCAD as App

from . import preferences as prefs
from .core import naming


def is_target(obj) -> bool:
    """Sketches and PartDesign features that are not excluded."""
    try:
        type_id = obj.TypeId
    except Exception:
        return False
    if type_id in prefs.excluded_types():
        return False
    return type_id.startswith(("Sketcher::", "PartDesign::"))


def is_alive(obj) -> bool:
    """True if obj still exists in its document (Cancel deletes new features)."""
    try:
        return obj.Document.getObject(obj.Name) is obj
    except Exception:
        return False


def key(obj) -> tuple[str, str]:
    return (obj.Document.Name, obj.Name)


def kind(obj) -> str:
    return naming.kind_from_name(obj.Name) or obj.TypeId.split("::")[-1]


def is_default_label(obj) -> bool:
    return naming.is_default_label(obj.Label, obj.Name)


def postfix_for(obj) -> str:
    return prefs.postfix_for(obj.TypeId)


def with_postfix(obj, text: str) -> str:
    return naming.add_postfix(text, postfix_for(obj))


def _first_obj(value):
    """First DocumentObject in a link, link-sub tuple, or list value."""
    if value is None:
        return None
    if isinstance(value, App.DocumentObject):
        return value
    if isinstance(value, (list, tuple)):
        for item in value:
            found = _first_obj(item)
            if found is not None:
                return found
    return None


def is_dependent(obj) -> bool:
    """Feature types built from another feature (profile, base, or originals)."""
    if obj.TypeId.startswith("Sketcher::"):
        return False
    return (
        hasattr(obj, "Profile")
        or hasattr(obj, "Originals")
        or obj.TypeId in naming.DRESSUP_TYPES
    )


def base_feature(obj):
    props = ["Profile", "Originals"]
    if obj.TypeId in naming.DRESSUP_TYPES:
        props.append("Base")
    for prop in props:
        if not hasattr(obj, prop):
            continue
        try:
            found = _first_obj(getattr(obj, prop))
        except Exception:
            found = None
        if found is not None and found is not obj:
            return found
    return None


def derived_name(obj) -> str | None:
    """Name from the feature obj is built on, or None if it can't be derived."""
    base = base_feature(obj)
    if base is None or is_default_label(base):
        return None
    return naming.derive_label(base.Label, prefs.all_postfixes(), postfix_for(obj))
