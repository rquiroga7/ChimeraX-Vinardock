# vim: set expandtab shiftwidth=4 softtabstop=4:

# This file is part of the ChimeraX-Vinardock bundle, an original
# ChimeraX plugin.  See the bundle's LICENSE file for terms.

from chimerax.core.tools import ToolInstance
from chimerax.ui import MainToolWindow

from .box import DockBoxModel, find_box

_tool_instance = None


def current_tool():
    return _tool_instance


class DockBoxTool(ToolInstance):
    """Tool window for editing the docking search box."""

    help = None
    SESSION_ENDURING = False
    SESSION_SAVE = False

    def __init__(self, session, tool_name):
        super().__init__(session, tool_name)
        self.display_name = "Docking Box"
        self.tool_window = MainToolWindow(self)
        self._syncing = False
        self._prev_mouse_modes = None
        self._handlers = []
        self.box = find_box(session)
        if self.box is None:
            self.box = DockBoxModel(session, (0.0, 0.0, 0.0), (20.0, 20.0, 20.0))
            session.models.add([self.box])
        from .mousemode import register_mousemode
        register_mousemode(session)
        self._build_ui()
        self._sync_from_box()
        self.tool_window.manage("side")
        global _tool_instance
        _tool_instance = self

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        from Qt.QtWidgets import (QVBoxLayout, QGridLayout, QLabel, QDoubleSpinBox,
            QGroupBox, QCheckBox, QPushButton, QComboBox)
        layout = QVBoxLayout()

        grid = QGridLayout()
        for col, axis in enumerate("XYZ"):
            grid.addWidget(QLabel(axis), 0, col + 1)
        grid.addWidget(QLabel("Center"), 1, 0)
        self._center_spins = []
        self._size_spins = []
        for col in range(3):
            spin = self._make_spin(-100000.0)
            self._center_spins.append(spin)
            grid.addWidget(spin, 1, col + 1)
        grid.addWidget(QLabel("Size"), 2, 0)
        for col in range(3):
            spin = self._make_spin(0.1)
            self._size_spins.append(spin)
            grid.addWidget(spin, 2, col + 1)
        layout.addLayout(grid)

        self._show_cb = QCheckBox("Show box")
        self._show_cb.toggled.connect(self._show_toggled)
        layout.addWidget(self._show_cb)

        group = QGroupBox("Autobox around ligand")
        gl = QGridLayout()
        self._ligand_combo = QComboBox()
        gl.addWidget(QLabel("Ligand"), 0, 0)
        gl.addWidget(self._ligand_combo, 0, 1)
        self._autobox_size_spin = QDoubleSpinBox()
        self._autobox_size_spin.setRange(0.0, 10000.0)
        self._autobox_size_spin.setDecimals(1)
        self._autobox_size_spin.setSingleStep(1.0)
        self._autobox_size_spin.setValue(10.0)
        gl.addWidget(QLabel("Autobox_size"), 1, 0)
        gl.addWidget(self._autobox_size_spin, 1, 1)
        self._autobox_btn = QPushButton("Autobox")
        self._autobox_btn.clicked.connect(self._autobox_clicked)
        gl.addWidget(self._autobox_btn, 2, 0, 1, 2)
        group.setLayout(gl)
        layout.addWidget(group)

        self._mouse_cb = QCheckBox("Move/resize box with mouse")
        self._mouse_cb.setToolTip("Left-drag moves the box; right-drag a side to move that side "
                                  "(the opposite side stays fixed), changing the box size.")
        self._mouse_cb.toggled.connect(self._mouse_toggled)
        layout.addWidget(self._mouse_cb)

        self._delete_btn = QPushButton("Delete box")
        self._delete_btn.clicked.connect(self._delete_clicked)
        layout.addWidget(self._delete_btn)

        layout.addStretch(1)
        self.tool_window.ui_area.setLayout(layout)

        self._populate_ligands()
        from chimerax.core.models import ADD_MODELS, REMOVE_MODELS
        t = self.session.triggers
        self._handlers = [
            t.add_handler(ADD_MODELS, self._models_changed),
            t.add_handler(REMOVE_MODELS, self._models_changed),
        ]

    def _make_spin(self, minimum):
        from Qt.QtWidgets import QDoubleSpinBox
        spin = QDoubleSpinBox()
        spin.setRange(minimum, 100000.0)
        spin.setDecimals(3)
        spin.setSingleStep(1.0)
        spin.valueChanged.connect(self._controls_changed)
        return spin

    # ------------------------------------------------------------------
    # control <-> box synchronization
    # ------------------------------------------------------------------
    def sync_controls(self):
        self._sync_from_box()

    def _sync_from_box(self):
        if self.box is None:
            return
        self._syncing = True
        try:
            for spin, value in zip(self._center_spins, self.box.center):
                spin.setValue(float(value))
            for spin, value in zip(self._size_spins, self.box.size):
                spin.setValue(float(value))
            self._show_cb.setChecked(self.box.display)
        finally:
            self._syncing = False

    def _controls_changed(self, *args):
        if self._syncing or self.box is None:
            return
        center = [spin.value() for spin in self._center_spins]
        size = [spin.value() for spin in self._size_spins]
        self.box.set_box(center, size)

    def _show_toggled(self, checked):
        if self.box is not None:
            self.box.display = checked

    # ------------------------------------------------------------------
    # actions
    # ------------------------------------------------------------------
    def _populate_ligands(self):
        from chimerax.atomic import AtomicStructure
        current = self._ligand_combo.currentData()
        self._ligand_combo.clear()
        first_pose = None
        for m in self.session.models.list():
            if isinstance(m, AtomicStructure):
                self._ligand_combo.addItem(m.name, m)
                if first_pose is None and hasattr(m, 'viewdock_data'):
                    first_pose = m
        if current is not None:
            index = self._ligand_combo.findData(current)
        elif first_pose is not None:
            # Default to the first ligand pose of a docking output file.
            index = self._ligand_combo.findData(first_pose)
        else:
            index = 0
        if index >= 0:
            self._ligand_combo.setCurrentIndex(index)

    def _models_changed(self, *args):
        self._populate_ligands()

    def _autobox_clicked(self, *args):
        model = self._ligand_combo.currentData()
        if model is None:
            from chimerax.core.errors import UserError
            raise UserError("No ligand model chosen for autobox")
        from .cmd import autobox_bounds
        center, size = autobox_bounds(model.atoms, self._autobox_size_spin.value())
        self.box.set_box(center, size)
        self._sync_from_box()

    def _mouse_toggled(self, checked):
        mm = self.session.ui.mouse_modes
        if checked:
            from .mousemode import register_mousemode, MOVE_MODE, RESIZE_MODE
            register_mousemode(self.session)
            self._prev_mouse_modes = (mm.mode('left', []), mm.mode('right', []))
            mm.bind_mouse_mode(mouse_button='left', mode=mm.named_mode(MOVE_MODE))
            mm.bind_mouse_mode(mouse_button='right', mode=mm.named_mode(RESIZE_MODE))
        else:
            prev = getattr(self, '_prev_mouse_modes', (None, None)) or (None, None)
            mm.bind_mouse_mode(mouse_button='left', mode=prev[0])
            mm.bind_mouse_mode(mouse_button='right', mode=prev[1])
            self._prev_mouse_modes = None

    def _delete_clicked(self, *args):
        if self.box is not None:
            self.box.delete()
            self.box = None
        self.delete()

    def delete(self):
        global _tool_instance
        if self._mouse_cb.isChecked():
            self._mouse_cb.setChecked(False)
        for handler in self._handlers:
            self.session.triggers.remove_handler(handler)
        self._handlers = []
        if _tool_instance is self:
            _tool_instance = None
        super().delete()
