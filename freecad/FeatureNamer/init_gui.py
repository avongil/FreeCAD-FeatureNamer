"""GUI entry point. FeatureNamer adds no workbench; it hooks into edit mode
for Sketcher and PartDesign features and adds one Tools menu entry."""

from pathlib import Path

import FreeCADGui as Gui
from PySide import QtCore

_ICONS = Path(__file__).parent / "resources" / "icons"
Gui.addIconPath(str(_ICONS))


class _Manipulator:
    def modifyMenuBar(self):
        return [{"insert": "FeatureNamer_Settings", "menuItem": "Std_DlgParameter", "after": ""}]


_state = {}


def _install():
    """Deferred until the main window exists: no work at import time."""
    if _state:
        return
    try:
        from . import commands  # noqa: F401  (registers FeatureNamer_Settings)
        from .gui.controller import Controller
        from .gui.preferences_page import PreferencesPage

        _state["controller"] = Controller()
        Gui.addDocumentObserver(_state["controller"])
        Gui.addPreferencePage(PreferencesPage, "FeatureNamer")
        _state["manipulator"] = _Manipulator()
        Gui.addWorkbenchManipulator(_state["manipulator"])
    except Exception:
        import traceback

        import FreeCAD as App

        App.Console.PrintError(f"FeatureNamer failed to start: {traceback.format_exc()}\n")


QtCore.QTimer.singleShot(0, _install)
