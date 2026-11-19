"""Commands (registered on import)."""

from __future__ import annotations

from pathlib import Path

import FreeCADGui as Gui
from PySide.QtCore import QT_TRANSLATE_NOOP

ICON = str(Path(__file__).parent / "resources" / "icons" / "FeatureNamer.svg")
SETTINGS_CMD = "FeatureNamer_Settings"


class OpenSettings:
    def GetResources(self):
        return {
            "Pixmap": ICON,
            "MenuText": QT_TRANSLATE_NOOP(SETTINGS_CMD, "FeatureNamer settings..."),
            "ToolTip": QT_TRANSLATE_NOOP(
                SETTINGS_CMD, "Name field, name popups, automatic names and postfixes"
            ),
            # Usable while a task dialog is open (e.g. while sketching).
            "CmdType": "ForEdit",
        }

    def IsActive(self):
        return True

    def Activated(self):
        Gui.showPreferences("FeatureNamer", 0)


Gui.addCommand(SETTINGS_CMD, OpenSettings())
