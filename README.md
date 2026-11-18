# FeatureNamer

A FreeCAD addon that lets you name Sketcher and PartDesign features in the dialog where you create or edit them, instead of renaming them in the model tree afterwards.

**Manual:** https://avongil.github.io/FreeCAD-FeatureNamer/

## What it does

- Adds a **Name** field at the top of the Tasks panel while a Sketch or PartDesign feature is being edited. Typing renames the feature live, and Cancel / Ctrl+Z undo it together with the feature.
- When a feature still has its default name (`Sketch003`, `Pad001`, ...), it pops up a small dialog asking for a name. The field starts empty (the default name shows greyed out), so you just type and press Enter.
- Features built from an already named feature are named automatically, without a popup: a Pad from `OutsideMoat_SKT` becomes `OutsideMoat_PAD`, and a Fillet on that becomes `OutsideMoat_FIL`. The name comes from `Profile`, `Base` (dress-up features) or `Originals` (patterns).
- A type postfix is added to names you type: `OutsideMoat` for a sketch becomes `OutsideMoat_SKT`. Defaults include `_SKT` Sketch, `_PAD` Pad, `_PKT` Pocket, `_REV` Revolution, `_GRV` Groove, `_HOLE` Hole, `_SWP` Sweep (additive pipe), `_LOFT` Loft, `_FIL` Fillet, `_CHF` Chamfer, `_MIR` Mirrored, `_LPAT` / `_PPAT` patterns. Edit them in **Tools > FeatureNamer settings...**
- All options are in one dialog: **Tools > FeatureNamer settings...** (green tag icon, below *Edit Parameters*). Settings live in `BaseApp/Preferences/Mod/FeatureNamer`.

| Parameter | Default | Effect |
|---|---|---|
| `ShowNameField` | on | Name field at the top of the Tasks panel |
| `PromptIfUnnamed` | on | Popup when editing starts on a default-named feature |
| `NameFromBase` | on | Name a feature after the feature it is built from, without asking |
| `AutoPostfix` | on | Add the type postfix to names |
| `Postfixes` | see above | One `TypeId=postfix` per line |
| `FocusNameField` | off | Put the cursor in the Name field instead of a popup |
| `AskOnClose` | off | Ask again after OK if the name is still the default, even if you skipped the first popup |
| `ExcludeTypes` | `PartDesign::Body` | Comma-separated TypeIds to ignore |

## Install

1. Click **Code > Download ZIP** on this page and unzip it.
2. Copy the **`FeatureNamer`** folder from the ZIP (the one with `InitGui.py`) into the `Mod` folder of your FreeCAD user folder, so it ends up like this:

   ```
   <your FreeCAD user folder>/
   └── Mod/
       └── FeatureNamer/            <- the folder you copied
           ├── InitGui.py
           ├── FeatureNamerCore.py
           └── Resources/
               └── FeatureNamer.svg
   ```

3. Restart FreeCAD.

**Where is my FreeCAD user folder?** In FreeCAD, open *View > Panels > Python console* and type `App.getUserAppDataDir()`. It prints the path. Usually it is:

- Windows: `%APPDATA%\FreeCAD\vXX-Y` (for example `C:\Users\<you>\AppData\Roaming\FreeCAD\v1-1`)
- Linux: `~/.local/share/FreeCAD/vXX-Y`
- macOS: `~/Library/Application Support/FreeCAD/vXX-Y`

`vXX-Y` is your FreeCAD version. If there is no `Mod` folder yet, create it.

Built against FreeCAD 27.1.0dev (weekly 2026.11.04), Python 3.13, PySide6 6.11.

## Status

Working prototype, offered as a reference for adding a feature-name field to FreeCAD's task dialogs in core. See the manual's "Proposal for core" section.

## License

LGPL-2.1-or-later, the same license as FreeCAD.
