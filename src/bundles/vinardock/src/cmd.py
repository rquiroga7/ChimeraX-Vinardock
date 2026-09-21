# vim: set expandtab shiftwidth=4 softtabstop=4:

# This file is part of the ChimeraX-Vinardock bundle, an original
# ChimeraX plugin.  See the bundle's LICENSE file for terms.

import numpy

from chimerax.core.errors import UserError

from .box import DockBoxModel, find_box


def autobox_bounds(atoms, autobox_size):
    """Return (center, size) of the ligand's bounding box expanded by autobox_size."""
    coords = atoms.scene_coords
    lo = coords.min(axis=0)
    hi = coords.max(axis=0)
    center = 0.5 * (lo + hi)
    size = (hi - lo) + autobox_size
    return tuple(center), tuple(size)


def dockbox(session, *, center=None, size=None, autobox=None, autobox_size=10.0, color=None,
            name=None, id=None, show_tool=True, close=False):
    box = find_box(session)
    if close:
        if box is not None:
            box.delete()
        return None

    if autobox is not None:
        if len(autobox) == 0:
            raise UserError("No atoms specified for autobox")
        center, size = autobox_bounds(autobox, autobox_size)

    if box is None:
        if center is None:
            center = (0.0, 0.0, 0.0)
        if size is None:
            size = (20.0, 20.0, 20.0)
        box = DockBoxModel(session, center, size, name=name or "docking box")
        session.models.add([box])
        if id is not None:
            box.id = id
    else:
        box.set_box(box.center if center is None else center,
                    box.size if size is None else size)
        if name is not None:
            box.name = name

    if color is not None:
        box.set_color(color.uint8x4())

    if show_tool and session.ui.is_gui and not session.in_script:
        from chimerax.core.commands import run
        run(session, "ui tool show 'Docking Box'", log=False)
    return box


def register_command(command_name, logger):
    from chimerax.core.commands import (CmdDesc, register, BoolArg, FloatArg,
                                        Float3Arg, ColorArg, StringArg, ModelIdArg)
    from chimerax.atomic import AtomsArg
    desc = CmdDesc(
        keyword=[
            ('center', Float3Arg),
            ('size', Float3Arg),
            ('autobox', AtomsArg),
            ('autobox_size', FloatArg),
            ('color', ColorArg),
            ('name', StringArg),
            ('id', ModelIdArg),
            ('show_tool', BoolArg),
            ('close', BoolArg),
        ],
        synopsis='Define or edit a docking search box')
    register('dockbox', desc, dockbox, logger=logger)
