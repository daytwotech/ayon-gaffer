import os

from ayon_core.addon import (
    AYONAddon, IHostAddon, IPluginPaths
)


from .version import __version__


GAFFER_HOST_DIR = os.path.dirname(os.path.abspath(__file__))
_URL_NOT_SET = object()


class GafferAddon(
    AYONAddon,
    IHostAddon,
    IPluginPaths,
):
    name = "gaffer"
    version = __version__
    host_name = "gaffer"
    enabled = True

    def initialize(self, module_settings):
        self.enabled = True

    def get_publish_plugin_paths(self, host_name):
        return [os.path.join(GAFFER_HOST_DIR, "plugins", "farm")]

    def add_implementation_envs(self, env, _app):
        # Add AYON requirements to GAFFER_EXTENSION_PATHS. If an AYON
        # application variant supplies GAFFERCOMP_ROOT, prepend GafferComp as
        # an extension as well. os.pathsep keeps this correct on Windows (;)
        # and Linux (:).
        extension_paths = []

        gaffercomp_root = env.get("GAFFERCOMP_ROOT")
        if gaffercomp_root:
            extension_paths.append(gaffercomp_root)

        startup_path = os.path.join(GAFFER_HOST_DIR, "deploy")
        gaffer_deadline_path = os.path.join(startup_path, "GafferDeadline")
        extension_paths.extend((startup_path, gaffer_deadline_path))

        existing_paths = env.get("GAFFER_EXTENSION_PATHS")
        if existing_paths:
            extension_paths.append(existing_paths)

        env["GAFFER_EXTENSION_PATHS"] = os.pathsep.join(extension_paths)

        gaffer_deadline_dep_path = os.path.join(
            gaffer_deadline_path, "gaffer_batch_dependency.py")

        env["DEADLINE_DEPENDENCY_SCRIPT_PATH"] = gaffer_deadline_dep_path

    def get_launch_hook_paths(self, app):
        if app.host_name != self.host_name:
            return []
        return [
            os.path.join(GAFFER_HOST_DIR, "hooks")
        ]

    def get_workfile_extensions(self):
        return [".gfr"]

    def tray_init(self):
        # doing nothing in here for now
        pass

    def tray_start(self):
        pass

    def tray_exit(self):
        pass

    def tray_menu(self, tray_menu):
        pass
