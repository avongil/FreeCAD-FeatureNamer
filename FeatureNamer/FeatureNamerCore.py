# FeatureNamer - name Sketcher / PartDesign features as you create/edit them.
#
#  * Adds a "Name:" field at the top of the Tasks panel while a Sketch or
#    PartDesign feature is in edit mode. Typing renames the feature live
#    (inside the edit transaction, so Cancel / Undo revert it).
#  * Pops up a dialog asking for a name when you enter edit on a feature that
#    still has its default name (Sketch001, Pad002, ...).
#  * Features built from an already named feature are named automatically:
#    OutsideMoat_SKT -> Pad -> OutsideMoat_PAD (no popup).
#  * Auto postfix per feature type (_SKT, _PAD, _SWP, ...), editable.
#
# Settings: Tools menu -> "FeatureNamer settings...", or
#   Tools > Edit parameters > BaseApp/Preferences/Mod/FeatureNamer

import os
import re
import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtGui, QtWidgets

try:
    import shiboken6

    def _alive(w):
        return w is not None and shiboken6.isValid(w)
except Exception:  # pragma: no cover
    def _alive(w):
        return w is not None

PARAM_PATH = "User parameter:BaseApp/Preferences/Mod/FeatureNamer"
BOX_NAME = "FeatureNamerBox"

DEFAULTS_BOOL = {
    "ShowNameField": True,      # name field at top of task panel
    "PromptIfUnnamed": True,    # popup when entering edit on a default-named feature
    "FocusNameField": False,    # put cursor in the name field when still default-named
    "AskOnClose": False,        # popup after OK if it is still default-named
    "AutoPostfix": True,        # append the type postfix (_SKT, _PAD, ...) to names
    "NameFromBase": True,       # Pad from "Moat_SKT" becomes "Moat_PAD" without asking
}
DEFAULTS_STR = {
    "ExcludeTypes": "PartDesign::Body",   # comma separated TypeIds to ignore
}

# TypeId -> postfix. Editable in Tools > FeatureNamer settings....
DEFAULT_POSTFIXES = [
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
DRESSUP_TYPES = {"PartDesign::Fillet", "PartDesign::Chamfer",
                 "PartDesign::Draft", "PartDesign::Thickness"}


def params():
    return App.ParamGet(PARAM_PATH)


def _ensure_defaults():
    p = params()
    try:
        existing = {c[1] for c in (p.GetContents() or [])}
    except Exception:
        existing = set()
    for k, v in DEFAULTS_BOOL.items():
        if k not in existing:
            p.SetBool(k, v)
    for k, v in DEFAULTS_STR.items():
        if k not in existing:
            p.SetString(k, v)
    if "Postfixes" not in existing:
        save_postfixes(DEFAULT_POSTFIXES)


def pref(key):
    return params().GetBool(key, DEFAULTS_BOOL[key])


def load_postfixes():
    """List of (TypeId, postfix) in user order."""
    raw = params().GetString("Postfixes", "")
    out = []
    for line in raw.splitlines():
        if "=" in line:
            t, pf = line.split("=", 1)
            if t.strip():
                out.append((t.strip(), pf.strip()))
    return out


def save_postfixes(pairs):
    params().SetString("Postfixes", "\n".join("%s=%s" % (t, pf) for t, pf in pairs))


def postfix_for(obj):
    if not pref("AutoPostfix"):
        return ""
    return dict(load_postfixes()).get(obj.TypeId, "")


def _log_error(where):
    import traceback
    App.Console.PrintError("FeatureNamer (%s): %s\n" % (where, traceback.format_exc()))


# --------------------------------------------------------------------------
# helpers

def _is_target(obj):
    try:
        t = obj.TypeId
    except Exception:
        return False
    excl = {s.strip() for s in params().GetString("ExcludeTypes", "").split(",") if s.strip()}
    if t in excl:
        return False
    return t.startswith("Sketcher::") or t.startswith("PartDesign::")


def _kind(obj):
    return re.sub(r"\d+$", "", obj.Name) or obj.TypeId.split("::")[-1]


def _is_default_label(obj):
    label, name = obj.Label, obj.Name
    if label == name:
        return True
    base = re.sub(r"\d+$", "", name)
    return re.fullmatch(re.escape(base) + r"\d*", label) is not None


def _obj_alive(obj):
    """True if obj still exists in its document (not deleted by Cancel)."""
    try:
        return obj.Document.getObject(obj.Name) is obj
    except Exception:
        return False


def _key(obj):
    return (obj.Document.Name, obj.Name)


def _focus_3d_view():
    mw = Gui.getMainWindow()
    mdi = mw.findChild(QtWidgets.QMdiArea)
    if mdi and mdi.activeSubWindow() and mdi.activeSubWindow().widget():
        mdi.activeSubWindow().widget().setFocus()


def with_postfix(obj, text):
    """Append obj's type postfix to text unless it already ends with it."""
    text = text.strip()
    pf = postfix_for(obj)
    if text and pf and not text.lower().endswith(pf.lower()):
        text += pf
    return text


def strip_postfix(label):
    """'OutsideMoat_SKT' -> 'OutsideMoat' (longest known postfix wins)."""
    for pf in sorted({p for _, p in load_postfixes() if p}, key=len, reverse=True):
        if label.lower().endswith(pf.lower()) and len(label) > len(pf):
            return label[: -len(pf)]
    return label


# --- "relies on an already named feature"

def _first_obj(value):
    """Pull the first DocumentObject out of a link / link-sub / list value."""
    if value is None:
        return None
    if isinstance(value, App.DocumentObject):
        return value
    if isinstance(value, (list, tuple)):
        for v in value:
            o = _first_obj(v)
            if o is not None:
                return o
    return None


def is_dependent(obj):
    """Feature types that are built from another feature."""
    if obj.TypeId.startswith("Sketcher::"):
        return False
    return (hasattr(obj, "Profile") or hasattr(obj, "Originals")
            or obj.TypeId in DRESSUP_TYPES)


def base_feature(obj):
    props = ["Profile", "Originals"]
    if obj.TypeId in DRESSUP_TYPES:
        props.append("Base")
    for prop in props:
        if hasattr(obj, prop):
            try:
                o = _first_obj(getattr(obj, prop))
            except Exception:
                o = None
            if o is not None and o is not obj:
                return o
    return None


def derived_name(obj):
    """Name from the feature it is built on, or None if it can't be derived."""
    base = base_feature(obj)
    if base is None or _is_default_label(base):
        return None
    stem = strip_postfix(base.Label)
    pf = dict(load_postfixes()).get(obj.TypeId, "") if pref("AutoPostfix") else ""
    if not pf:
        return None   # no postfix for this type -> would just copy the base name
    return stem + pf


# --------------------------------------------------------------------------
# popup dialog

class NameDialog(QtWidgets.QDialog):
    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Name feature")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        lay = QtWidgets.QVBoxLayout(self)
        pf = postfix_for(obj)
        hint = " &nbsp;<span style='color:gray'>(%s added automatically)</span>" % pf if pf else ""
        lay.addWidget(QtWidgets.QLabel("Name for this <b>%s</b>:%s" % (_kind(obj), hint)))
        start = "" if _is_default_label(obj) else strip_postfix(obj.Label)
        self.edit = QtWidgets.QLineEdit(start)
        self.edit.setPlaceholderText(obj.Label)
        f = self.edit.font()
        f.setPointSizeF(f.pointSizeF() * 1.3)
        self.edit.setFont(f)
        self.edit.setMinimumWidth(340)
        self.edit.selectAll()
        lay.addWidget(self.edit)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.button(QtWidgets.QDialogButtonBox.Cancel).setText("Skip")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def text(self):
        return self.edit.text().strip()


def set_label(obj, text, own_transaction=False):
    if not text or text == obj.Label:
        return False
    doc = obj.Document
    if own_transaction:
        doc.openTransaction("Rename %s" % obj.Label)
    obj.Label = text
    if own_transaction:
        doc.commitTransaction()
    return True


def prompt_for_name(obj, own_transaction=False):
    dlg = NameDialog(obj, Gui.getMainWindow())
    if dlg.exec() != QtWidgets.QDialog.Accepted:
        return False
    return set_label(obj, with_postfix(obj, dlg.text()), own_transaction)


# --------------------------------------------------------------------------
# settings dialog (Tools > FeatureNamer settings...)

ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources", "FeatureNamer.svg")


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FeatureNamer settings")
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(520, 680)
        lay = QtWidgets.QVBoxLayout(self)

        # --- asking for names
        g1 = QtWidgets.QGroupBox("Naming features")
        l1 = QtWidgets.QVBoxLayout(g1)
        self.cb = {}

        def add(layout, key, text, tip):
            c = QtWidgets.QCheckBox(text)
            c.setToolTip(tip)
            c.setChecked(pref(key))
            layout.addWidget(c)
            self.cb[key] = c
            return c

        add(l1, "ShowNameField", "Show a Name field at the top of the Tasks panel",
            "While a Sketch or PartDesign feature is being edited.")
        ask = add(l1, "PromptIfUnnamed", "Ask for a name when editing an unnamed feature",
                  "Pops up when the feature still has its default name (Sketch001, Pad002...).")
        focus = add(l1, "FocusNameField", "Instead, put the cursor in the Name field",
                    "Quieter alternative to the popup. Only used when the popup is off.")
        focus.setStyleSheet("margin-left:20px")
        add(l1, "AskOnClose", "Ask again after OK if the feature is still unnamed",
            "Also asks if you skipped the first popup.")
        focus.setEnabled(not ask.isChecked())
        ask.toggled.connect(lambda on: focus.setEnabled(not on))
        lay.addWidget(g1)

        # --- automatic names
        g2 = QtWidgets.QGroupBox("Automatic names")
        l2 = QtWidgets.QVBoxLayout(g2)
        add(l2, "NameFromBase", "Name features after the feature they are built from",
            "A Pad from OutsideMoat_SKT becomes OutsideMoat_PAD without asking.")
        add(l2, "AutoPostfix", "Add the type postfix to names (_SKT, _PAD, ...)",
            "Typing OutsideMoat for a sketch gives OutsideMoat_SKT.")
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Feature type (TypeId)", "Postfix"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        l2.addWidget(self.table, 1)
        self._fill(load_postfixes())
        row = QtWidgets.QHBoxLayout()
        for text, fn in (("Add row", lambda: self._add()), ("Remove row", self._remove),
                         ("Reset to defaults", lambda: self._fill(DEFAULT_POSTFIXES))):
            b = QtWidgets.QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        row.addStretch(1)
        l2.addLayout(row)
        tip = QtWidgets.QLabel("To find a TypeId, select the feature and run "
                               "<code>Gui.Selection.getSelection()[0].TypeId</code> in the Python console.")
        tip.setWordWrap(True)
        tip.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        l2.addWidget(tip)
        lay.addWidget(g2, 1)

        # --- exclusions
        g3 = QtWidgets.QGroupBox("Ignore these feature types (comma separated TypeIds)")
        l3 = QtWidgets.QVBoxLayout(g3)
        self.exclude = QtWidgets.QLineEdit(params().GetString("ExcludeTypes", ""))
        l3.addWidget(self.exclude)
        lay.addWidget(g3)

        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _fill(self, pairs):
        self.table.setRowCount(0)
        for t, pf in pairs:
            self._add(t, pf)

    def _add(self, t="", pf=""):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(t))
        self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(pf))
        if not t:
            self.table.scrollToBottom()
            self.table.editItem(self.table.item(r, 0))

    def _remove(self):
        for r in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(r)

    def _save(self):
        pairs = []
        for r in range(self.table.rowCount()):
            t = (self.table.item(r, 0).text() if self.table.item(r, 0) else "").strip()
            pf = (self.table.item(r, 1).text() if self.table.item(r, 1) else "").strip()
            if t:
                pairs.append((t, pf))
        save_postfixes(pairs)
        for key, c in self.cb.items():
            params().SetBool(key, c.isChecked())
        params().SetString("ExcludeTypes", self.exclude.text().strip())
        if not pref("ShowNameField"):
            _remove_boxes()
        self.accept()


# --------------------------------------------------------------------------
# inline field in the task panel

class NameBox(QtWidgets.QFrame):
    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.setObjectName(BOX_NAME)
        self.obj = obj
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lbl = QtWidgets.QLabel("Name:")
        bf = lbl.font()
        bf.setBold(True)
        lbl.setFont(bf)
        lay.addWidget(lbl)
        self.edit = QtWidgets.QLineEdit(obj.Label)
        f = self.edit.font()
        f.setPointSizeF(f.pointSizeF() * 1.25)
        self.edit.setFont(f)
        pf = postfix_for(obj)
        self.edit.setToolTip("%s  (internal name: %s)\nEnter = done%s"
                             % (_kind(obj), obj.Name, ("\n%s is added when you finish" % pf) if pf else ""))
        lay.addWidget(self.edit, 1)
        self.edit.textEdited.connect(self._live)
        self.edit.editingFinished.connect(self._finish)
        self.edit.returnPressed.connect(self._done)

    def _live(self, text):
        text = text.strip()
        if text and _obj_alive(self.obj) and text != self.obj.Label:
            try:
                self.obj.Label = text
            except Exception:
                _log_error("rename")

    def _finish(self):
        """Editing finished: add the postfix, then show the real label."""
        if _obj_alive(self.obj) and self.edit.isModified():
            self.edit.setModified(False)
            text = self.edit.text().strip()
            if text:
                try:
                    set_label(self.obj, with_postfix(self.obj, text))
                except Exception:
                    _log_error("postfix")
        self.sync()

    def sync(self):
        if _obj_alive(self.obj) and self.edit.text() != self.obj.Label:
            self.edit.setText(self.obj.Label)

    def _done(self):
        self._finish()
        self.edit.clearFocus()
        _focus_3d_view()


def _task_panels():
    """Visible Gui::TaskView::TaskPanel widgets (the area holding task boxes)."""
    mw = Gui.getMainWindow()
    out = []
    for w in mw.findChildren(QtWidgets.QWidget):
        try:
            if w.metaObject().className() == "Gui::TaskView::TaskPanel" and w.isVisible():
                out.append(w)
        except Exception:
            pass
    return out


def _sync_boxes():
    for b in Gui.getMainWindow().findChildren(QtWidgets.QFrame, BOX_NAME):
        b.sync()


def _remove_boxes():
    mw = Gui.getMainWindow()
    for b in mw.findChildren(QtWidgets.QFrame, BOX_NAME):
        b.hide()
        b.setParent(None)
        b.deleteLater()


# --------------------------------------------------------------------------
# controller

class Controller(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.current = None
        self.asked = set()        # popup shown when entering edit
        self.asked_close = set()  # popup shown after OK
        self.focused_once = False
        self.waiting_for_base = False
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self._tick)

    # --- Gui document observer slots
    def slotInEdit(self, vp):
        try:
            obj = vp.Object
            if not _is_target(obj):
                return
            self.current = obj
            self.focused_once = False
            self.waiting_for_base = False
            QtCore.QTimer.singleShot(0, self._on_enter)
        except Exception:
            _log_error("slotInEdit")

    def slotResetEdit(self, vp):
        try:
            self._edit_ended(getattr(vp, "Object", None))
        except Exception:
            _log_error("slotResetEdit")

    def _edit_ended(self, obj=None):
        """Called by slotResetEdit or by the watchdog, whichever sees it first."""
        cur = self.current
        if cur is None or (obj is not None and obj is not cur):
            return
        waiting = self.waiting_for_base
        self.timer.stop()
        _remove_boxes()
        self.current = None
        self.waiting_for_base = False
        if waiting or pref("AskOnClose"):
            QtCore.QTimer.singleShot(0, lambda o=cur, w=waiting: self._after_close(o, w))

    # --- logic
    def _try_derive(self, obj, own_transaction=False):
        """Auto-name from the base feature. True if it named the object."""
        if not pref("NameFromBase"):
            return False
        name = derived_name(obj)
        if name:
            set_label(obj, name, own_transaction)
            self.asked.add(_key(obj))
            self.asked_close.add(_key(obj))
            return True
        return False

    def _on_enter(self):
        obj = self.current
        if obj is None or not _obj_alive(obj):
            return
        try:
            unnamed = _is_default_label(obj) and _key(obj) not in self.asked
            if unnamed and self._try_derive(obj):
                unnamed = False
            elif (unnamed and pref("NameFromBase") and is_dependent(obj)
                  and base_feature(obj) is None):
                # e.g. a pattern opened with nothing selected: wait until the
                # user picks the feature, then name it from that.
                self.waiting_for_base = True
                unnamed = False
            self._inject()
            self.timer.start()
            if unnamed and pref("PromptIfUnnamed"):
                self.asked.add(_key(obj))
                prompt_for_name(obj)
                _sync_boxes()
        except Exception:
            _log_error("enter")

    def _after_close(self, obj, waiting):
        try:
            # Skipping the first popup does not stop this one: asking again
            # after OK is the whole point of AskOnClose.
            if not _obj_alive(obj) or not _is_default_label(obj) or _key(obj) in self.asked_close:
                return
            if self._try_derive(obj, own_transaction=True):
                return
            if (waiting and pref("PromptIfUnnamed")) or pref("AskOnClose"):
                self.asked.add(_key(obj))
                self.asked_close.add(_key(obj))
                prompt_for_name(obj, own_transaction=True)
        except Exception:
            _log_error("after close")

    def _tick(self):
        obj = self.current
        try:
            gdoc = Gui.getDocument(obj.Document.Name) if obj is not None and _obj_alive(obj) else None
            vp = gdoc.getInEdit() if gdoc else None
            if vp is None or getattr(vp, "Object", None) is not obj:
                self._edit_ended(obj)
                return
            if self.waiting_for_base and _is_default_label(obj) and self._try_derive(obj):
                self.waiting_for_base = False
                _sync_boxes()
            self._inject()
        except Exception:
            self.timer.stop()
            _log_error("tick")

    def _inject(self):
        obj = self.current
        if obj is None or not pref("ShowNameField"):
            return
        for panel in _task_panels():
            box = panel.findChild(QtWidgets.QFrame, BOX_NAME)
            if _alive(box) and box.obj is obj:
                continue
            if _alive(box):
                box.setParent(None)
                box.deleteLater()
            lay = panel.layout()
            if not isinstance(lay, QtWidgets.QBoxLayout):
                continue
            box = NameBox(obj, panel)
            lay.insertWidget(0, box)
            box.show()
            if (pref("FocusNameField") and not self.focused_once
                    and _is_default_label(obj) and not pref("PromptIfUnnamed")):
                self.focused_once = True
                box.edit.setFocus()
                box.edit.selectAll()


# --------------------------------------------------------------------------
# Tools menu entry

_SETTINGS_CMD = "FeatureNamer_Settings"


class _SettingsCmd:
    def GetResources(self):
        return {"Pixmap": ICON_PATH,
                "MenuText": "FeatureNamer settings...",
                "ToolTip": "Feature naming: name field, name popups, automatic names and postfixes"}

    def Activated(self):
        SettingsDialog(Gui.getMainWindow()).exec()

    def IsActive(self):
        return True


class _Manipulator:
    def modifyMenuBar(self):
        return [{"append": _SETTINGS_CMD, "menuItem": "Std_DlgParameter"}]


# --------------------------------------------------------------------------

_controller = None


def install():
    global _controller
    if _controller is not None:
        return
    try:
        _ensure_defaults()
        _controller = Controller()
        Gui.addDocumentObserver(_controller)
        Gui.addCommand(_SETTINGS_CMD, _SettingsCmd())
        try:
            Gui.addWorkbenchManipulator(_Manipulator())
        except Exception:
            _log_error("menu")
        App.Console.PrintLog("FeatureNamer loaded\n")
    except Exception:
        _log_error("install")
