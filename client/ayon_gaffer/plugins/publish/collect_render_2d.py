import os

import pyblish.api

from ayon_core.lib import get_formatted_current_time
from ayon_gaffer.api import gaffercomp
from ayon_gaffer.api.colorspace import ARenderProduct
from ayon_gaffer.api.lib import get_color_management_preferences


class CollectRender2D(pyblish.api.InstancePlugin):
    """Collect current Gaffer script"""

    order = pyblish.api.CollectorOrder
    label = "Collect render 2d"
    hosts = ["gaffer"]
    families = ["render"]

    def process(self, instance):
        context = instance.context
        render_node = instance.data.get("transientData", {}).get("node", None)
        if not render_node:
            raise RuntimeError("Unable to find the 2d render node")

        is_gaffercomp_write = gaffercomp.is_write(render_node)
        if (
            render_node.typeName() != "AyonGaffer::Render2D"
            and not is_gaffercomp_write
        ):
            self.log.debug(
                "Skip collecting node, not a Render2D/GafferComp Write node, "
                f"type is {render_node.typeName()}"
            )
            return
        self.log.debug(f"Using node: {render_node.getName()}")

        scene_path = context.data["currentFile"].replace("\\", "/")

        img_seq_filepath = render_node["fileName"].getValue()
        dirname = os.path.dirname(img_seq_filepath)
        frames = gaffercomp.render_frames(render_node)
        if not frames:
            raise RuntimeError(
                f"Render node {render_node.getName()} has an empty frame range"
            )
        start_frame = min(frames)
        end_frame = max(frames)

        file_paths = [
            gaffercomp.expand_frame_path(img_seq_filepath, frame)
            for frame in frames
        ]
        file_names = [os.path.basename(path) for path in file_paths]

        colorspace_data = get_color_management_preferences(render_node.scriptNode())
        data = {

            "attachTo": [],

            "multipartExr": True,

            # the handles are already included in the frame range
            "handleStart": 0,
            "handleEnd": 0,
            "frameStart": start_frame,
            "frameEnd": end_frame,
            "frameStartHandle": 0,
            "frameEndHandle": 0,
            "frameList": frames,
            "byFrameStep": 1,
            "expectedFiles": file_paths,

            "colorspaceConfig": colorspace_data["config"],
            "colorspaceDisplay": colorspace_data["display"],
            "colorspaceView": colorspace_data["view"],
            "colorspace": colorspace_data["colorspace"],

            "time": get_formatted_current_time(),
            "author": context.data["user"],

            "outputDir": dirname,
            "stagingDir": dirname,
            "source": scene_path,
            "renderProducts": ARenderProduct(render_node.scriptNode(), ["beauty"]),

            # this utilizes an RVX modification to the publishing process
            # where we can enable/disable hardlinking when instances
            # request it
            "do_hardlink": True
        }

        render_target = instance.data["creator_attributes"]["render_target"]

        if render_target == "frames":
            self.log.debug("Using existing frames for local publish")
            if "representations" not in data:
                data["representations"] = []
            data["representations"].append({
                "name": "exr",
                "ext": "exr",
                "files": file_names,
                "stagingDir": dirname,
            })

        elif render_target == "frames_farm":
            self.log.debug("Using existing frames for farm publish")

            if "representations" not in data:
                data["representations"] = []

            data["representations"].append({
                "name": "exr",
                "ext": "exr",
                "files": file_names,
                "stagingDir": dirname,
            })

            data["transfer"] = False
            data["farm"] = True
            instance.data["families"].append("render.frames_farm")

        elif render_target == "farm":
            self.log.debug("Using farm for render and publish")
            data["farm"] = True
            instance.data["families"].append("render.farm")

        elif render_target == "local":
            self.log.debug("Using local for render and publish")
            instance.data["families"] = ["render.local"]

        label = "{0} ({1})".format("render", instance.data["folderPath"])
        label += "  [{0}-{1}]".format(start_frame, end_frame)

        data["label"] = label
        instance.data.update(data)
        if "publish_attributes" not in instance.data.keys():
            instance.data["publish_attributes"] = {}
        if "CollectJobInfo" not in instance.data["publish_attributes"].keys():
            instance.data["publish_attributes"]["CollectJobInfo"] = {}
        instance.data["publish_attributes"]["CollectJobInfo"]["frames"] = ",".join(
            [str(frame) for frame in frames]
        )
