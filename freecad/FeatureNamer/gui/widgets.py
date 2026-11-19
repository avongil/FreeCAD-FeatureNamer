"""Name popup, task-panel Name field, and helpers to place them."""

from __future__ import annotations

import FreeCAD as App
import FreeCADGui as Gui

from .. import features as feat
from .. import preferences as prefs
from ..core import naming
from .qt import QtCore, QtWidgets, alive

translate = App.Qt.translate

BOX_NAME = "FeatureNamerBox"


def log_error(where: str) -> None:
    import traceback

    App.Console.PrintError(f"FeatureNamer ({where}): {traceback.format_exc()}\n")


def set_label(obj, text: str, own_transaction: bool = False) -> bool:
    """Rename obj. own_transaction=True when no edit transaction is open."""
    if not text or text == obj.Label:
        return False
    if not own_transaction:
        obj.Label = text
        return True
    doc = obj.Document
    doc.openTransaction(translate("FeatureNamer", "Rename {}").format(obj.Label))
    try:
        obj.Label = text
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise
    return True


def focus_3d_view() -> None:
    mdi = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)
    sub = mdi.activeSubWindow() if mdi else None
    if sub and sub.widget():
        sub.widget().setFocus()


# --------------------------------------------------------------------------
# popup


class NameDialog(QtWidgets.QDialog):
    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate("FeatureNamer", "Name feature"))
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        lay = QtWidgets.QVBoxLayout(self)
        pf = feat.postfix_for(obj)
        hint = ""
        if pf:
            hint = " &nbsp;<span style='color:gray'>{}</span>".format(
                translate("FeatureNamer", "({} added automatically)").format(pf)
            )
        lay.addWidget(
            QtWidgets.QLabel(
                translate("FeatureNamer", "Name for this <b>{}</b>:").format(feat.kind(obj)) + hint
            )
        )
        start = "" if feat.is_default_label(obj) else naming.strip_postfix(obj.Label, prefs.all_postfixes())
        self.edit = QtWidgets.QLineEdit(start)
        self.edit.setPlaceholderText(obj.Label)
        font = self.edit.font()
        font.setPointSizeF(font.pointSizeF() * 1.3)
        self.edit.setFont(font)
        self.edit.setMinimumWidth(340)
        self.edit.selectAll()
        lay.addWidget(self.edit)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.button(QtWidgets.QDialogButtonBox.Cancel).setText(translate("FeatureNamer", "Skip"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def text(self) -> str:
        return self.edit.text().strip()


def prompt_for_name(obj, own_transaction: bool = False) -> bool:
    dlg = NameDialog(obj, Gui.getMainWindow())
    if dlg.exec() != QtWidgets.QDialog.Accepted:
        return False
    return set_label(obj, feat.with_postfix(obj, dlg.text()), own_transaction)


# --------------------------------------------------------------------------
# Name field at the top of the Tasks panel


class NameBox(QtWidgets.QFrame):
    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.setObjectName(BOX_NAME)
        self.obj = obj
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        label = QtWidgets.QLabel(translate("FeatureNamer", "Name:"))
        bold = label.font()
        bold.setBold(True)
        label.setFont(bold)
        lay.addWidget(label)
        self.edit = QtWidgets.QLineEdit(obj.Label)
        font = self.edit.font()
        font.setPointSizeF(font.pointSizeF() * 1.25)
        self.edit.setFont(font)
        tip = translate("FeatureNamer", "{} (internal name: {})\nEnter = done").format(feat.kind(obj), obj.Name)
        pf = feat.postfix_for(obj)
        if pf:
            tip += "\n" + translate("FeatureNamer", "{} is added when you finish").format(pf)
        self.edit.setToolTip(tip)
        lay.addWidget(self.edit, 1)
        self.edit.textEdited.connect(self._live)
        self.edit.editingFinished.connect(self._finish)
        self.edit.returnPressed.connect(self._done)

    def _live(self, text: str) -> None:
        # Writes inside the open edit transaction, so Cancel / Undo revert it.
        text = text.strip()
        if text and feat.is_alive(self.obj) and text != self.obj.Label:
            try:
                self.obj.Label = text
            except Exception:
                log_error("rename")

    def _finish(self) -> None:
        if feat.is_alive(self.obj) and self.edit.isModified():
            self.edit.setModified(False)
            text = self.edit.text().strip()
            if text:
                try:
                    set_label(self.obj, feat.with_postfix(self.obj, text))
                except Exception:
                    log_error("postfix")
        self.sync()

    def sync(self) -> None:
        if feat.is_alive(self.obj) and self.edit.text() != self.obj.Label:
            self.edit.setText(self.obj.Label)

    def _done(self) -> None:
        self._finish()
        self.edit.clearFocus()
        focus_3d_view()


def task_panels() -> list:
    """Visible Gui::TaskView::TaskPanel widgets (the area that holds task boxes).

    FreeCAD has no public hook for adding a widget to another command's task
    dialog, so this looks the panel up by its Qt class name.
    """
    out = []
    for w in Gui.getMainWindow().findChildren(QtWidgets.QWidget):
        try:
            if w.metaObject().className() == "Gui::TaskView::TaskPanel" and w.isVisible():
                out.append(w)
        except Exception:
            pass
    return out


def name_boxes() -> list:
    return [b for b in Gui.getMainWindow().findChildren(QtWidgets.QFrame, BOX_NAME) if alive(b)]


def sync_boxes() -> None:
    for box in name_boxes():
        box.sync()


def remove_boxes() -> None:
    for box in name_boxes():
        box.hide()
        box.setParent(None)
        box.deleteLater()
