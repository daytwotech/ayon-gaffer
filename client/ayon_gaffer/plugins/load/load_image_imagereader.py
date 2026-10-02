import ayon_gaffer.api.lib
import ayon_gaffer.api.utils
import ayon_gaffer.api.plugin
from ayon_gaffer.api import gaffercomp

import GafferImage


class GafferLoadImageReader(ayon_gaffer.api.plugin.GafferImageLoaderBase):
    """Load ImageReader"""

    product_types = ["image", "imagesequence", "review", "render", "plate", "paint", "roto"]
    product_base_types = ["image"]
    representations = ["*"]

    label = "Load sequence (ImageReader)"
    order = -10
    icon = "code-fork"
    color = "orange"
    node_class = GafferImage.ImageReader

    def load(self, context, name, namespace, options):
        node = self.node_class()

        path = self.prepare_image_path(context, options)
        node["fileName"].setValue(path)

        self.set_up_node(name, namespace, node, context)
        self.set_node_colorspace(
            node["colorSpace"],
            context,
            path)

        if gaffercomp.is_available():
            gaffercomp.configure_reader(node)

    def update(self, container, context):
        representation = context["representation"]
        node = container["_node"]
        path = self.prepare_image_path(context, node=node)

        node["fileName"].setValue(path)

        # Update the imprinted representation
        node["user"]["representation"].setValue(str(representation["id"]))

        self.set_node_colorspace(
            node["colorSpace"],
            context,
            path)

        if gaffercomp.is_available():
            gaffercomp.configure_reader(node)
