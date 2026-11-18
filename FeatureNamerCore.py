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
# Settings: Tools menu -> "FeatureNamer: ..." entries, or
#   Tools > Edit parameters > BaseApp/Preferences/Mod/FeatureNamer

import re
import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtCore, QtWidgets

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

# TypeId -> postfix. Editable via Tools > "FeatureNamer: edit postfixes...".
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
# postfix editor

class PostfixDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FeatureNamer postfixes")
        self.resize(460, 560)
        lay = QtWidgets.QVBoxLayout(self)
        self.auto = QtWidgets.QCheckBox("Add postfix automatically when naming")
        self.auto.setChecked(pref("AutoPostfix"))
        self.derive = QtWidgets.QCheckBox("Name features after the feature they are built from")
        self.derive.setChecked(pref("NameFromBase"))
        lay.addWidget(self.auto)
        lay.addWidget(self.derive)
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Feature type (TypeId)", "Postfix"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table, 1)
        self._fill(load_postfixes())
        row = QtWidgets.QHBoxLayout()
        add = QtWidgets.QPushButton("Add row")
        rem = QtWidgets.QPushButton("Remove row")
        reset = QtWidgets.QPushButton("Reset to defaults")
        add.clicked.connect(self._add)
        rem.clicked.connect(self._remove)
        reset.clicked.connect(lambda: self._fill(DEFAULT_POSTFIXES))
        for b in (add, rem, reset):
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        tip = QtWidgets.QLabel("Tip: select a feature and run <code>Gui.Selection.getSelection()[0].TypeId</code> "
                               "in the Python console to find a type you want to add.")
        tip.setWordWrap(True)
        tip.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        lay.addWidget(tip)
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
        self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(t if isinstance(t, str) else ""))
        self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(pf if isinstance(pf, str) else ""))
        if not t:
            self.table.editItem(self.table.item(r, 0))

    def _remove(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def _save(self):
        pairs = []
        for r in range(self.table.rowCount()):
            t = (self.table.item(r, 0).text() if self.table.item(r, 0) else "").strip()
            pf = (self.table.item(r, 1).text() if self.table.item(r, 1) else "").strip()
            if t:
                pairs.append((t, pf))
        save_postfixes(pairs)
        params().SetBool("AutoPostfix", self.auto.isChecked())
        params().SetBool("NameFromBase", self.derive.isChecked())
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
        self.asked = set()
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
            obj = getattr(vp, "Object", None)
            if obj is not None and obj is not self.current:
                return
            waiting = self.waiting_for_base
            self.timer.stop()
            _remove_boxes()
            self.current = None
            self.waiting_for_base = False
            if obj is not None and (waiting or pref("AskOnClose")):
                QtCore.QTimer.singleShot(0, lambda o=obj, w=waiting: self._after_close(o, w))
        except Exception:
            _log_error("slotResetEdit")

    # --- logic
    def _try_derive(self, obj, own_transaction=False):
        """Auto-name from the base feature. True if it named the object."""
        if not pref("NameFromBase"):
            return False
        name = derived_name(obj)
        if name:
            set_label(obj, name, own_transaction)
            self.asked.add(_key(obj))
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
            if not _obj_alive(obj) or not _is_default_label(obj) or _key(obj) in self.asked:
                return
            if self._try_derive(obj, own_transaction=True):
                return
            if (waiting and pref("PromptIfUnnamed")) or pref("AskOnClose"):
                self.asked.add(_key(obj))
                prompt_for_name(obj, own_transaction=True)
        except Exception:
            _log_error("after close")

    def _tick(self):
        obj = self.current
        try:
            gdoc = Gui.getDocument(obj.Document.Name) if obj is not None and _obj_alive(obj) else None
            vp = gdoc.getInEdit() if gdoc else None
            if vp is None or getattr(vp, "Object", None) is not obj:
                self.timer.stop()
                _remove_boxes()
                self.current = None
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
# Tools menu entries

_TOGGLES = [
    ("FeatureNamer_ShowNameField", "ShowNameField", "FeatureNamer: name field in task panel"),
    ("FeatureNamer_PromptIfUnnamed", "PromptIfUnnamed", "FeatureNamer: ask for name when unnamed"),
    ("FeatureNamer_NameFromBase", "NameFromBase", "FeatureNamer: name from base feature"),
    ("FeatureNamer_AutoPostfix", "AutoPostfix", "FeatureNamer: add type postfix (_SKT, _PAD...)"),
    ("FeatureNamer_FocusNameField", "FocusNameField", "FeatureNamer: focus name field when unnamed"),
    ("FeatureNamer_AskOnClose", "AskOnClose", "FeatureNamer: ask for name after OK if unnamed"),
]
_EDIT_CMD = "FeatureNamer_EditPostfixes"


class _ToggleCmd:
    def __init__(self, key, text):
        self.key, self.text = key, text

    def GetResources(self):
        return {"MenuText": self.text, "ToolTip": self.text,
                "Checkable": pref(self.key)}

    def Activated(self, checked=None):
        if checked is None:
            checked = not pref(self.key)
        params().SetBool(self.key, bool(checked))
        if self.key == "ShowNameField" and not checked:
            _remove_boxes()

    def IsActive(self):
        return True


class _EditPostfixesCmd:
    def GetResources(self):
        return {"MenuText": "FeatureNamer: edit postfixes...",
                "ToolTip": "Edit the postfix added to each feature type"}

    def Activated(self):
        PostfixDialog(Gui.getMainWindow()).exec()

    def IsActive(self):
        return True


class _Manipulator:
    def modifyMenuBar(self):
        cmds = [c for c, _, _ in _TOGGLES] + [_EDIT_CMD]
        return [{"append": c, "menuItem": "Std_DlgParameter"} for c in reversed(cmds)]


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
        for cmd, key, text in _TOGGLES:
            Gui.addCommand(cmd, _ToggleCmd(key, text))
        Gui.addCommand(_EDIT_CMD, _EditPostfixesCmd())
        try:
            Gui.addWorkbenchManipulator(_Manipulator())
        except Exception:
            _log_error("menu")
        App.Console.PrintLog("FeatureNamer loaded\n")
    except Exception:
        _log_error("install")
