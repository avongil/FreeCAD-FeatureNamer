"""GUI entry point. FeatureNamer adds no workbench; it hooks into edit mode
for Sketcher and PartDesign features and adds one Tools menu entry.

Registration happens at import: the manipulator must exist before the first
workbench builds its menus, or the Tools entry only appears after a
workbench switch. Nothing here is heavy; the observer only reacts to edits.
"""

from pathlib import Path

import FreeCADGui as Gui

from . import commands  # noqa: F401  (registers FeatureNamer_Settings)
from .gui.controller import Controller
from .gui.preferences_page import FeatureNamerPreferencesPage

Gui.addIconPath(str(Path(__file__).parent / "resources" / "icons"))


class _Manipulator:
    def modifyMenuBar(self):
        return [{"insert": commands.SETTINGS_CMD, "menuItem": "Std_DlgParameter", "after": ""}]


_controller = Controller()
Gui.addDocumentObserver(_controller)
# FreeCAD keys Python preference pages by class name, so the name must be globally unique.
Gui.addPreferencePage(FeatureNamerPreferencesPage, "FeatureNamer")
_manipulator = _Manipulator()
Gui.addWorkbenchManipulator(_manipulator)
