# FeatureNamer

A FreeCAD addon that lets you name Sketcher and PartDesign features in the dialog where you create or edit them, instead of renaming them in the model tree afterwards.

**Manual:** https://avongil.github.io/FreeCAD-FeatureNamer/

## What it does

- Adds a **Name** field at the top of the Tasks panel while a Sketch or PartDesign feature is being edited. Typing renames the feature live, and Cancel / Ctrl+Z undo it together with the feature.
- When a feature still has its default name (`Sketch003`, `Pad001`, ...), it pops up a small dialog asking for a name. The current name is preselected, so you just type and press Enter.
- Features built from an already named feature are named automatically, without a popup: a Pad from `OutsideMoat_SKT` becomes `OutsideMoat_PAD`, and a Fillet on that becomes `OutsideMoat_FIL`. The name comes from `Profile`, `Base` (dress-up features) or `Originals` (patterns).
- A type postfix is added to names you type: `OutsideMoat` for a sketch becomes `OutsideMoat_SKT`. Defaults include `_SKT` Sketch, `_PAD` Pad, `_PKT` Pocket, `_REV` Revolution, `_GRV` Groove, `_HOLE` Hole, `_SWP` Sweep (additive pipe), `_LOFT` Loft, `_FIL` Fillet, `_CHF` Chamfer, `_MIR` Mirrored, `_LPAT` / `_PPAT` patterns. Edit them in **Tools > FeatureNamer: edit postfixes...**
- Each behavior can be switched on or off from the **Tools** menu (below *Edit parameters...*). Settings live in `BaseApp/Preferences/Mod/FeatureNamer`.

| Parameter | Default | Effect |
|---|---|---|
| `ShowNameField` | on | Name field at the top of the Tasks panel |
| `PromptIfUnnamed` | on | Popup when editing starts on a default-named feature |
| `NameFromBase` | on | Name a feature after the feature it is built from, without asking |
| `AutoPostfix` | on | Add the type postfix to names |
| `Postfixes` | see above | One `TypeId=postfix` per line |
| `FocusNameField` | off | Put the cursor in the Name field instead of a popup |
| `AskOnClose` | off | Ask after OK if the name is still the default |
| `ExcludeTypes` | `PartDesign::Body` | Comma-separated TypeIds to ignore |

## Install

Copy this folder (as `FeatureNamer`) into your FreeCAD user Mod directory and restart FreeCAD:

- Windows: `%APPDATA%\FreeCAD\vXX-Y\Mod\FeatureNamer`
- Linux: `~/.local/share/FreeCAD/vXX-Y/Mod/FeatureNamer`
- macOS: `~/Library/Application Support/FreeCAD/vXX-Y/Mod/FeatureNamer`

Built against FreeCAD 27.1.0dev (weekly 2026.11.04), Python 3.13, PySide6 6.11.

## Status

Working prototype, offered as a reference for adding a feature-name field to FreeCAD's task dialogs in core. See the manual's "Proposal for core" section.

## License

LGPL-2.1-or-later, the same license as FreeCAD.
