import os

import GafferDispatch

from ayon_core.pipeline import publish
from ayon_gaffer.api import gaffercomp
from ayon_gaffer.api.plugin import GafferExtractorPlugin


class Extract2DRender(GafferExtractorPlugin, publish.OptionalPyblishPluginMixin):
    label = "Extract 2D Render"
    hosts = ["gaffer"]
    families = ["render.local"]
    representations = ["exr"]

    def process(self, instance):
        render_node = instance.data.get("transientData", {}).get("node", None)
        if not render_node:
            raise RuntimeError("Unable to find the 2d render node")
        self.log.debug(f"Using node: {render_node.getName()}")

        file_path = render_node["fileName"].getValue()
        dirname = os.path.dirname(file_path)
        frames = gaffercomp.render_frames(render_node)
        if not frames:
            raise RuntimeError(
                f"Render node {render_node.getName()} has an empty frame range"
            )

        files = [
            os.path.basename(gaffercomp.expand_frame_path(file_path, frame))
            for frame in frames
        ]

        if gaffercomp.is_write(render_node):
            self.log.debug(
                "Rendering GafferComp Write frames: "
                + ",".join(str(frame) for frame in frames)
            )
            with render_node.scriptNode().context():
                render_node.render(frames)
        else:
            dispatcher = GafferDispatch.LocalDispatcher()
            dispatcher["framesMode"].setValue(2)  # custom range
            frange = f"{min(frames)}-{max(frames)}"
            self.log.debug(f"Using frame range: {frange}")
            dispatcher["frameRange"].setValue(frange)

            with render_node.scriptNode().context():
                dispatcher.dispatch([render_node])

        if "representations" not in instance.data:
            instance.data["representations"] = []

        instance.data["representations"].append({
            "name": self.representations[0],
            "ext": self.representations[0],
            "files": files,
            "stagingDir": dirname,
        })

        families = instance.data["families"]
        if "render.local" in families:
            families.remove("render.local")
            families.insert(0, "render")
