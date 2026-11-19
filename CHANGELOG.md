# Changelog

## 0.2.0 - 2026-11-18

- Modern FreeCAD addon layout (`freecad/FeatureNamer/`, `package.xml`), so it can be installed with the Addon Manager.
- Settings moved to **Edit > Preferences > FeatureNamer**. **Tools > FeatureNamer settings...** opens that page.
- Uses FreeCAD's `PySide` shim instead of importing PySide6 directly.
- Naming rules split into a pure module with unit tests.
- Ask-after-OK also asks when the first popup was skipped.

## 0.1.0 - 2026-11-18

- Name field in the Tasks panel, name popup, auto-naming from the base feature, type postfixes.
