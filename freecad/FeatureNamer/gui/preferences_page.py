"""Edit > Preferences > FeatureNamer page."""

from __future__ import annotations

import FreeCAD as App

from .. import preferences as prefs
from ..core.naming import DEFAULT_POSTFIXES
from . import widgets as w
from .qt import QtCore, QtWidgets

translate = App.Qt.translate


class SettingsForm(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FeatureNamer")
        lay = QtWidgets.QVBoxLayout(self)
        self.checks = {}

        def add(layout, key, text, tip):
            box = QtWidgets.QCheckBox(text)
            box.setToolTip(tip)
            layout.addWidget(box)
            self.checks[key] = box
            return box

        g1 = QtWidgets.QGroupBox(translate("FeatureNamer", "Naming features"))
        l1 = QtWidgets.QVBoxLayout(g1)
        add(l1, "ShowNameField",
            translate("FeatureNamer", "Show a Name field at the top of the Tasks panel"),
            translate("FeatureNamer", "While a Sketch or PartDesign feature is being edited."))
        self.ask = add(l1, "PromptIfUnnamed",
                       translate("FeatureNamer", "Ask for a name when editing an unnamed feature"),
                       translate("FeatureNamer", "Pops up when the feature still has its default name (Sketch001, Pad002...)."))
        self.focus = add(l1, "FocusNameField",
                         translate("FeatureNamer", "Instead, put the cursor in the Name field"),
                         translate("FeatureNamer", "Quieter alternative to the popup. Only used when the popup is off."))
        self.focus.setStyleSheet("margin-left:20px")
        add(l1, "AskOnClose",
            translate("FeatureNamer", "Ask again after OK if the feature is still unnamed"),
            translate("FeatureNamer", "Also asks if you skipped the first popup."))
        self.ask.toggled.connect(lambda on: self.focus.setEnabled(not on))
        lay.addWidget(g1)

        g2 = QtWidgets.QGroupBox(translate("FeatureNamer", "Automatic names"))
        l2 = QtWidgets.QVBoxLayout(g2)
        add(l2, "NameFromBase",
            translate("FeatureNamer", "Name features after the feature they are built from"),
            translate("FeatureNamer", "A Pad from OutsideMoat_SKT becomes OutsideMoat_PAD without asking."))
        add(l2, "AutoPostfix",
            translate("FeatureNamer", "Add the type postfix to names (_SKT, _PAD, ...)"),
            translate("FeatureNamer", "Typing OutsideMoat for a sketch gives OutsideMoat_SKT."))
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(
            [translate("FeatureNamer", "Feature type (TypeId)"), translate("FeatureNamer", "Postfix")]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(260)
        l2.addWidget(self.table, 1)
        row = QtWidgets.QHBoxLayout()
        for text, fn in (
            (translate("FeatureNamer", "Add row"), lambda: self._add_row()),
            (translate("FeatureNamer", "Remove row"), self._remove_rows),
            (translate("FeatureNamer", "Reset to defaults"), lambda: self._fill(DEFAULT_POSTFIXES)),
        ):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(fn)
            row.addWidget(button)
        row.addStretch(1)
        l2.addLayout(row)
        tip = QtWidgets.QLabel(translate(
            "FeatureNamer",
            "To find a TypeId, select the feature and run "
            "<code>Gui.Selection.getSelection()[0].TypeId</code> in the Python console.",
        ))
        tip.setWordWrap(True)
        tip.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        l2.addWidget(tip)
        lay.addWidget(g2, 1)

        g3 = QtWidgets.QGroupBox(translate("FeatureNamer", "Ignore these feature types (comma separated TypeIds)"))
        l3 = QtWidgets.QVBoxLayout(g3)
        self.exclude = QtWidgets.QLineEdit()
        l3.addWidget(self.exclude)
        lay.addWidget(g3)

    def _fill(self, pairs):
        self.table.setRowCount(0)
        for type_id, pf in pairs:
            self._add_row(type_id, pf)

    def _add_row(self, type_id="", pf=""):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(type_id))
        self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(pf))
        if not type_id:
            self.table.scrollToBottom()
            self.table.editItem(self.table.item(r, 0))

    def _remove_rows(self):
        for r in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(r)

    def load(self):
        for key, box in self.checks.items():
            box.setChecked(prefs.get_bool(key))
        self.focus.setEnabled(not self.ask.isChecked())
        self._fill(prefs.postfixes())
        self.exclude.setText(prefs.exclude_text())

    def save(self):
        pairs = []
        for r in range(self.table.rowCount()):
            t_item, p_item = self.table.item(r, 0), self.table.item(r, 1)
            type_id = t_item.text().strip() if t_item else ""
            pf = p_item.text().strip() if p_item else ""
            if type_id:
                pairs.append((type_id, pf))
        prefs.set_postfixes(pairs)
        for key, box in self.checks.items():
            prefs.set_bool(key, box.isChecked())
        prefs.set_exclude_text(self.exclude.text())
        if not prefs.get_bool("ShowNameField"):
            w.remove_boxes()


class PreferencesPage:
    """Programmatic preference page (Gui.addPreferencePage)."""

    def __init__(self, _parent=None):
        self.form = SettingsForm()

    def loadSettings(self):
        self.form.load()

    def saveSettings(self):
        self.form.save()
