# FeatureNamer

A FreeCAD addon that lets you name Sketcher and PartDesign features in the dialog where you create or edit them, instead of renaming them in the model tree afterwards.

**Manual:** https://avongil.github.io/FreeCAD-FeatureNamer/

## What it does

- Adds a **Name** field at the top of the Tasks panel while a Sketch or PartDesign feature is being edited. Typing renames the feature live, and Cancel / Ctrl+Z undo it together with the feature.
- When a feature still has its default name (`Sketch003`, `Pad001`, ...), it pops up a small dialog asking for a name. The field starts empty (the default name shows greyed out), so you just type and press Enter.
- Features built from an already named feature are named automatically, without a popup: a Pad from `OutsideMoat_SKT` becomes `OutsideMoat_PAD`, and a Fillet on that becomes `OutsideMoat_FIL`. The name comes from `Profile`, `Base` (dress-up features) or `Originals` (patterns).
- A type postfix is added to names you type: `OutsideMoat` for a sketch becomes `OutsideMoat_SKT`. Defaults include `_SKT` Sketch, `_PAD` Pad, `_PKT` Pocket, `_REV` Revolution, `_GRV` Groove, `_HOLE` Hole, `_SWP` Sweep (additive pipe), `_LOFT` Loft, `_FIL` Fillet, `_CHF` Chamfer, `_MIR` Mirrored, `_LPAT` / `_PPAT` patterns. Edit them in **Edit > Preferences > FeatureNamer**.
- All options are on one page: **Edit > Preferences > FeatureNamer**. **Tools > FeatureNamer settings...** (green tag icon, below *Edit Parameters*) opens it. Settings live in `BaseApp/Preferences/Mod/FeatureNamer`.

![FeatureNamer preference page, with a model tree named HEX_SKT, HEX_PAD, HEX_Bottom_CHF and HEX_Top_SHL](docs/images/preferences.png)

*The FeatureNamer page in Edit > Preferences. On the left, the tree it produces: the Pad built from `HEX_SKT` was named `HEX_PAD` automatically.*

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

### With the Addon Manager (recommended)

FeatureNamer is not in the official addon list yet, so add it as a custom repository once:

1. **Edit > Preferences > Addon Manager > Custom repositories**: add
   `https://github.com/avongil/FreeCAD-FeatureNamer` with branch `main`.
2. Open **Tools > Addon Manager**, find **FeatureNamer**, click **Install**.
3. Restart FreeCAD.

The Addon Manager also tells you when there is an update.

### By hand

1. Click **Code > Download ZIP** on this page and unzip it.
2. Rename the unzipped folder from `FreeCAD-FeatureNamer-main` to **`FeatureNamer`**.
3. Move it into the `Mod` folder of your FreeCAD user folder, so it ends up like this:

   ```
   <your FreeCAD user folder>/
   └── Mod/
       └── FeatureNamer/            <- the unzipped folder, renamed
           ├── package.xml
           └── freecad/
               └── FeatureNamer/
                   ├── init_gui.py
                   └── ...
   ```

4. Restart FreeCAD.

**Where is my FreeCAD user folder?** In FreeCAD, open *View > Panels > Python console* and type `App.getUserAppDataDir()`. It prints the path. Usually it is:

- Windows: `%APPDATA%\FreeCAD\vXX-Y` (for example `C:\Users\<you>\AppData\Roaming\FreeCAD\v1-1`)
- Linux: `~/.local/share/FreeCAD/vXX-Y`
- macOS: `~/Library/Application Support/FreeCAD/vXX-Y`

`vXX-Y` is your FreeCAD version. If there is no `Mod` folder yet, create it.

Requires FreeCAD 1.1 or newer. Developed on FreeCAD 27.1.0dev (weekly 2026.11.04).

## Development

Modern FreeCAD addon layout: code in `freecad/FeatureNamer/`, metadata in `package.xml`. The naming rules live in `core/naming.py` with no FreeCAD imports, and are tested with:

```
python -m unittest tests/test_naming.py
```

## Status

Working prototype, offered as a reference for adding a feature-name field to FreeCAD's task dialogs in core. See the manual's "Proposal for core" section.

## License

LGPL-2.1-or-later, the same license as FreeCAD.
