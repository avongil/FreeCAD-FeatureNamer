"""Gui document observer that drives the Name field, popups, and auto-naming."""

from __future__ import annotations

import FreeCADGui as Gui

from .. import features as feat
from .. import preferences as prefs
from . import widgets as w
from .qt import QtCore, QtWidgets, alive


class Controller(QtCore.QObject):
    """One instance per session, registered with Gui.addDocumentObserver."""

    def __init__(self):
        super().__init__()
        self.current = None
        self.asked = set()  # popup shown when entering edit
        self.asked_close = set()  # popup shown after OK
        self.focused_once = False
        self.waiting_for_base = False
        # Only runs while a target is in edit. There is no signal when a task
        # dialog rebuilds its panel, or when a base feature gets picked.
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self._tick)

    # --- Gui document observer slots

    def slotInEdit(self, vp):
        try:
            obj = vp.Object
            if not feat.is_target(obj):
                return
            self.current = obj
            self.focused_once = False
            self.waiting_for_base = False
            # Let setEdit() finish building its task dialog first.
            QtCore.QTimer.singleShot(0, self._on_enter)
        except Exception:
            w.log_error("slotInEdit")

    def slotResetEdit(self, vp):
        try:
            self._edit_ended(getattr(vp, "Object", None))
        except Exception:
            w.log_error("slotResetEdit")

    # --- logic

    def _edit_ended(self, obj=None):
        """Called by slotResetEdit or the watchdog, whichever sees it first."""
        cur = self.current
        if cur is None or (obj is not None and obj is not cur):
            return
        waiting = self.waiting_for_base
        self.timer.stop()
        w.remove_boxes()
        self.current = None
        self.waiting_for_base = False
        if waiting or prefs.get_bool("AskOnClose"):
            QtCore.QTimer.singleShot(0, lambda o=cur, wt=waiting: self._after_close(o, wt))

    def _try_derive(self, obj, own_transaction=False) -> bool:
        if not prefs.get_bool("NameFromBase"):
            return False
        name = feat.derived_name(obj)
        if not name:
            return False
        w.set_label(obj, name, own_transaction)
        self.asked.add(feat.key(obj))
        self.asked_close.add(feat.key(obj))
        return True

    def _on_enter(self):
        obj = self.current
        if obj is None or not feat.is_alive(obj):
            return
        try:
            unnamed = feat.is_default_label(obj) and feat.key(obj) not in self.asked
            if unnamed and self._try_derive(obj):
                unnamed = False
            elif (
                unnamed
                and prefs.get_bool("NameFromBase")
                and feat.is_dependent(obj)
                and feat.base_feature(obj) is None
            ):
                # e.g. a pattern opened with nothing selected: name it once the
                # user picks the feature.
                self.waiting_for_base = True
                unnamed = False
            self._inject()
            self.timer.start()
            if unnamed and prefs.get_bool("PromptIfUnnamed"):
                self.asked.add(feat.key(obj))
                w.prompt_for_name(obj)
                w.sync_boxes()
        except Exception:
            w.log_error("enter")

    def _after_close(self, obj, waiting):
        try:
            # Skipping the first popup does not block this one: asking again
            # after OK is the point of AskOnClose.
            if (
                not feat.is_alive(obj)
                or not feat.is_default_label(obj)
                or feat.key(obj) in self.asked_close
            ):
                return
            if self._try_derive(obj, own_transaction=True):
                return
            if (waiting and prefs.get_bool("PromptIfUnnamed")) or prefs.get_bool("AskOnClose"):
                self.asked.add(feat.key(obj))
                self.asked_close.add(feat.key(obj))
                w.prompt_for_name(obj, own_transaction=True)
        except Exception:
            w.log_error("after close")

    def _tick(self):
        obj = self.current
        try:
            gdoc = Gui.getDocument(obj.Document.Name) if obj is not None and feat.is_alive(obj) else None
            vp = gdoc.getInEdit() if gdoc else None
            if vp is None or getattr(vp, "Object", None) is not obj:
                self._edit_ended(obj)
                return
            if self.waiting_for_base and feat.is_default_label(obj) and self._try_derive(obj):
                self.waiting_for_base = False
                w.sync_boxes()
            self._inject()
        except Exception:
            self.timer.stop()
            w.log_error("tick")

    def _inject(self):
        obj = self.current
        if obj is None or not prefs.get_bool("ShowNameField"):
            return
        for panel in w.task_panels():
            box = panel.findChild(QtWidgets.QFrame, w.BOX_NAME)
            if alive(box) and box.obj is obj:
                continue
            if alive(box):
                box.setParent(None)
                box.deleteLater()
            lay = panel.layout()
            if not isinstance(lay, QtWidgets.QBoxLayout):
                continue
            box = w.NameBox(obj, panel)
            lay.insertWidget(0, box)
            box.show()
            if (
                prefs.get_bool("FocusNameField")
                and not prefs.get_bool("PromptIfUnnamed")
                and not self.focused_once
                and feat.is_default_label(obj)
            ):
                self.focused_once = True
                box.edit.setFocus()
                box.edit.selectAll()
