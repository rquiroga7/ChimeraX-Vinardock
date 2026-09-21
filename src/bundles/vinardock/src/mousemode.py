# vim: set expandtab shiftwidth=4 softtabstop=4:

# This file is part of the ChimeraX-Vinardock bundle, an original
# ChimeraX plugin.  See the bundle's LICENSE file for terms.

import numpy

from chimerax.mouse_modes import MouseMode

from .box import find_box

MOVE_MODE = "dock box"
RESIZE_MODE = "dock box resize"


def register_mousemode(session):
    if not session.ui.is_gui:
        return
    mm = session.ui.mouse_modes
    if mm.named_mode(MOVE_MODE) is None:
        mm.add_mode(DockBoxMouseMode(session, resize=False))
    if mm.named_mode(RESIZE_MODE) is None:
        mm.add_mode(DockBoxMouseMode(session, resize=True))


def _notify_tool(session):
    from .tool import current_tool
    tool = current_tool()
    if tool is not None:
        tool.sync_controls()


class DockBoxMouseMode(MouseMode):
    """Mouse mode for the docking box.

    Left-drag moves the whole box.  Right-drag moves the clicked face: the
    opposite face stays put, so the box changes size.  Shift-left-drag is an
    alternative way to resize.
    """

    name = MOVE_MODE

    def __init__(self, session, resize=False):
        super().__init__(session)
        self._resize_only = resize
        if resize:
            self.name = RESIZE_MODE
        self._box = None
        self._action = None
        self._resize = None
        self._last = None
        self._pixel_size = 1.0

    def mouse_down(self, event):
        super().mouse_down(event)
        self._last = event.position()
        self._box = find_box(self.session)
        self._action = None
        self._resize = None
        if self._box is None:
            return
        view = self.session.main_view
        line = view.clip_plane_points(*self._last)
        if line[0] is None or line[1] is None:
            return
        self._pixel_size = view.pixel_size(self._box.center)
        if self._resize_only or event.shift_down():
            self._resize = self._pick_face(line)
            self._action = 'resize' if self._resize is not None else None
        else:
            self._action = 'move'

    def mouse_drag(self, event):
        if self._box is None or self._last is None or self._action is None:
            return
        x0, y0 = self._last
        x, y = event.position()
        dx, dy = x - x0, y - y0
        if dx == 0 and dy == 0:
            return
        self._last = (x, y)
        if self._action == 'resize':
            self._resize_box(dx, dy)
        else:
            self._move_box(dx, dy)
        _notify_tool(self.session)

    def mouse_up(self, event):
        self._box = None
        self._action = None
        self._resize = None
        self._last = None
        super().mouse_up(event)

    def _move_box(self, dx, dy):
        view = self.session.main_view
        step = view.camera.position.transform_vector(
            (dx * self._pixel_size, -dy * self._pixel_size, 0.0))
        self._box.set_box(numpy.asarray(self._box.center) + step, self._box.size)

    def _resize_box(self, dx, dy):
        axis, side = self._resize
        normal = numpy.zeros(3)
        normal[axis] = 1.0 if side else -1.0
        view = self.session.main_view
        camera_normal = view.camera.position.inverse().transform_vector(normal)
        growth = (camera_normal[0] * dx - camera_normal[1] * dy) * self._pixel_size

        size = numpy.array(self._box.size, dtype=numpy.float64)
        center = numpy.array(self._box.center, dtype=numpy.float64)
        new_size = max(0.5, size[axis] + growth)
        actual = new_size - size[axis]
        size[axis] = new_size
        # Move the dragged face; keep the opposite face fixed.
        if side:
            center[axis] += 0.5 * actual
        else:
            center[axis] -= 0.5 * actual
        self._box.set_box(center, size)

    def _pick_face(self, line):
        p0 = numpy.asarray(line[0], dtype=numpy.float64)
        direction = numpy.asarray(line[1], dtype=numpy.float64) - p0
        lo = numpy.asarray(self._box.bounds_min, dtype=numpy.float64)
        hi = numpy.asarray(self._box.bounds_max, dtype=numpy.float64)
        best = None
        best_t = None
        for axis in range(3):
            for side, value in ((1, hi[axis]), (0, lo[axis])):
                if abs(direction[axis]) < 1e-9:
                    continue
                t = (value - p0[axis]) / direction[axis]
                if t <= 0.0:
                    continue
                point = p0 + t * direction
                inside = True
                for other in range(3):
                    if other == axis:
                        continue
                    if point[other] < lo[other] - 1e-6 or point[other] > hi[other] + 1e-6:
                        inside = False
                        break
                if inside and (best_t is None or t < best_t):
                    best_t = t
                    best = (axis, side)
        return best
