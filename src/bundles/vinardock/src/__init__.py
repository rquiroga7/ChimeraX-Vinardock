# vim: set expandtab shiftwidth=4 softtabstop=4:

# This file is part of the ChimeraX-Vinardock bundle, an original ChimeraX
# plugin distributed under the GNU Lesser General Public License v2.1.
# See the bundled LICENSE file.

from chimerax.core.toolshed import BundleAPI


class _VinardockAPI(BundleAPI):

    api_version = 1

    @staticmethod
    def initialize(session, bundle_info):
        from .mousemode import register_mousemode
        register_mousemode(session)

    @staticmethod
    def start_tool(session, bi, ti):
        if ti.name == "Docking Box":
            from chimerax.core import tools
            from .tool import DockBoxTool
            return tools.get_singleton(session, DockBoxTool, ti.name, create=True)

    @staticmethod
    def get_class(class_name):
        if class_name == "DockBoxModel":
            from .box import DockBoxModel
            return DockBoxModel
        return None

    @staticmethod
    def register_command(bi, ci, logger):
        from . import cmd
        cmd.register_command(ci.name, logger)

    @staticmethod
    def run_provider(session, name, mgr, **kw):
        """Open-command provider for PDBT/PDBQT files."""
        from chimerax.open_command import OpenerInfo

        class VinardockOpenerInfo(OpenerInfo):
            def open(self, session, data, file_name, **kw):
                from .pdbt import open_pdbt
                models, status = open_pdbt(session, data, file_name, True, True)
                _maybe_show_viewdock(session, models)
                return models, status

        return VinardockOpenerInfo()


def _maybe_show_viewdock(session, models):
    """Open the ViewDock tool for multi-pose results that carry dock data."""
    if not session.ui.is_gui:
        return
    all_models = sum([m.all_models() for m in models], start=[])
    if len(all_models) < 2:
        return
    if not any(hasattr(m, 'viewdock_data') for m in all_models):
        return
    from chimerax.viewdock import open_viewdock_tool
    from Qt.QtCore import QTimer
    QTimer.singleShot(0, lambda s=session, m=models: open_viewdock_tool(s, m))


bundle_api = _VinardockAPI()
