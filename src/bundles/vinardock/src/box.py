# vim: set expandtab shiftwidth=4 softtabstop=4:

# This file is part of the ChimeraX-Vinardock bundle, an original ChimeraX
# plugin distributed under the GNU Lesser General Public License v2.1.
# See the bundled LICENSE file.

import numpy

from chimerax.core.models import Model


def box_corners(llb, urf):
    x0, y0, z0 = llb
    x1, y1, z1 = urf
    return numpy.array([
        (x0, y0, z0), (x1, y0, z0), (x0, y1, z0), (x1, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x0, y1, z1), (x1, y1, z1),
    ], dtype=numpy.float32)


# Triangles for the 12 faces of a box, same layout as the volume outline box.
_BOX_TRIANGLES = numpy.array([
    (0, 4, 5), (5, 1, 0), (0, 2, 6), (6, 4, 0),
    (0, 1, 3), (3, 2, 0), (7, 3, 1), (1, 5, 7),
    (7, 6, 2), (2, 3, 7), (7, 5, 4), (4, 6, 7),
], dtype=numpy.int32)

# Edge mask showing the triangle edges but hiding each face's diagonal, so the
# Mesh drawing looks like the 12 edges of a box.
_BOX_EDGE_MASK = numpy.array([8 | 2 | 1] * len(_BOX_TRIANGLES), dtype=numpy.uint8)


class DockBoxModel(Model):
    """An axis-aligned box used to define a docking search space.

    The box is defined by a center and a (x, y, z) size, both in the scene
    coordinate system.  Moving or resizing the box just regenerates a wireframe
    drawing, so it always stays axis aligned.
    """

    def __init__(self, session, center, size, color=(0, 255, 0, 255), name="docking box"):
        super().__init__(name, session)
        self.center = numpy.asarray(center, dtype=numpy.float64)
        self.size = numpy.asarray(size, dtype=numpy.float64)
        self._drawing = d = self.new_drawing("box")
        d.display_style = d.Mesh
        d.use_lighting = False
        d.casts_shadows = False
        d.pickable = False
        d.color = color
        self._update_geometry()

    @property
    def bounds_min(self):
        return self.center - 0.5 * self.size

    @property
    def bounds_max(self):
        return self.center + 0.5 * self.size

    def set_box(self, center, size):
        self.center = numpy.asarray(center, dtype=numpy.float64)
        self.size = numpy.asarray(size, dtype=numpy.float64)
        self._update_geometry()

    def set_color(self, color):
        self._drawing.color = color

    def _update_geometry(self):
        d = self._drawing
        d.set_geometry(box_corners(self.bounds_min, self.bounds_max), None, _BOX_TRIANGLES)
        d.edge_mask = _BOX_EDGE_MASK
        self.redraw_needed()

    def take_snapshot(self, session, flags):
        return {
            'version': 1,
            'base data': super().take_snapshot(session, flags),
            'center': tuple(self.center),
            'size': tuple(self.size),
            'color': tuple(self._drawing.color),
        }

    @classmethod
    def restore_snapshot(cls, session, data):
        box = cls(session, data['center'], data['size'], color=data.get('color', (0, 255, 0, 255)))
        Model.set_state_from_snapshot(box, session, data['base data'])
        return box


def find_box(session):
    """Return the first docking box in the session, or None."""
    for m in session.models.list():
        if isinstance(m, DockBoxModel):
            return m
    return None
