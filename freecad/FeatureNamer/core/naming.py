"""Pure naming rules. No FreeCAD imports, so this module is testable anywhere."""

from __future__ import annotations

import re
from collections.abc import Iterable

# TypeId -> postfix, in display order.
DEFAULT_POSTFIXES: list[tuple[str, str]] = [
    ("Sketcher::SketchObject", "_SKT"),
    ("PartDesign::Pad", "_PAD"),
    ("PartDesign::Pocket", "_PKT"),
    ("PartDesign::Revolution", "_REV"),
    ("PartDesign::Groove", "_GRV"),
    ("PartDesign::Hole", "_HOLE"),
    ("PartDesign::AdditivePipe", "_SWP"),
    ("PartDesign::SubtractivePipe", "_SSWP"),
    ("PartDesign::AdditiveLoft", "_LOFT"),
    ("PartDesign::SubtractiveLoft", "_SLOFT"),
    ("PartDesign::AdditiveHelix", "_HLX"),
    ("PartDesign::SubtractiveHelix", "_SHLX"),
    ("PartDesign::Fillet", "_FIL"),
    ("PartDesign::Chamfer", "_CHF"),
    ("PartDesign::Draft", "_DFT"),
    ("PartDesign::Thickness", "_SHL"),
    ("PartDesign::Mirrored", "_MIR"),
    ("PartDesign::LinearPattern", "_LPAT"),
    ("PartDesign::PolarPattern", "_PPAT"),
    ("PartDesign::MultiTransform", "_MTR"),
    ("PartDesign::Scaled", "_SCL"),
    ("PartDesign::Boolean", "_BOOL"),
    ("PartDesign::Plane", "_PLN"),
    ("PartDesign::Line", "_AXS"),
    ("PartDesign::Point", "_PNT"),
    ("PartDesign::CoordinateSystem", "_CSYS"),
    ("PartDesign::ShapeBinder", "_BND"),
    ("PartDesign::SubShapeBinder", "_BND"),
]

# Feature types whose "Base" property is the feature they modify.
DRESSUP_TYPES = frozenset(
    {"PartDesign::Fillet", "PartDesign::Chamfer", "PartDesign::Draft", "PartDesign::Thickness"}
)


def parse_postfixes(raw: str) -> list[tuple[str, str]]:
    """'TypeId=_PF' lines -> [(TypeId, '_PF')]. Blank and malformed lines are skipped."""
    out = []
    for line in raw.splitlines():
        if "=" not in line:
            continue
        type_id, postfix = (s.strip() for s in line.split("=", 1))
        if type_id:
            out.append((type_id, postfix))
    return out


def format_postfixes(pairs: Iterable[tuple[str, str]]) -> str:
    return "\n".join(f"{t}={pf}" for t, pf in pairs)


def kind_from_name(name: str) -> str:
    """Internal name without its counter: 'Pad003' -> 'Pad'."""
    return re.sub(r"\d+$", "", name)


def is_default_label(label: str, name: str) -> bool:
    """True if the label is still FreeCAD's default (Pad003, or Pad after a copy)."""
    if label == name:
        return True
    base = kind_from_name(name)
    return bool(base) and re.fullmatch(re.escape(base) + r"\d*", label) is not None


def add_postfix(text: str, postfix: str) -> str:
    """Append postfix unless text already ends with it (case-insensitive)."""
    text = text.strip()
    if text and postfix and not text.lower().endswith(postfix.lower()):
        text += postfix
    return text


def strip_postfix(label: str, postfixes: Iterable[str]) -> str:
    """'OutsideMoat_SKT' -> 'OutsideMoat'. The longest matching postfix wins."""
    for pf in sorted({p for p in postfixes if p}, key=len, reverse=True):
        if len(label) > len(pf) and label.lower().endswith(pf.lower()):
            return label[: -len(pf)]
    return label


def derive_label(base_label: str, all_postfixes: Iterable[str], new_postfix: str) -> str | None:
    """Name for a feature built on base_label: 'Moat_SKT' + '_PAD' -> 'Moat_PAD'.

    Returns None without a postfix, since that would only copy the base name.
    """
    if not new_postfix:
        return None
    stem = strip_postfix(base_label, all_postfixes)
    return stem + new_postfix if stem else None
