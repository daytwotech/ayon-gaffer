"""Compatibility helpers for the optional GafferComp extension.

The AYON Gaffer addon must remain usable in stock Gaffer.  Keep all imports of
GafferComp behind this module so creators/loaders/publishers can opt in when
the extension is present without making it a hard dependency.
"""

import re

import GafferDispatch
import GafferImage
import IECore


def write_class():
    """Return GafferComp.Write when the extension is available."""
    try:
        import GafferComp
    except ImportError:
        return None
    return getattr(GafferComp, "Write", None)


def is_available():
    return write_class() is not None


def create_write(name="Write"):
    cls = write_class()
    if cls is None:
        raise RuntimeError("GafferComp is not available in this Gaffer session")
    return cls(name)


def is_write(node):
    if node is None:
        return False
    try:
        if node.typeName() == "GafferComp::Write":
            return True
    except Exception:
        pass
    cls = write_class()
    return cls is not None and isinstance(node, cls)


def configure_reader(reader):
    """Apply GafferComp/Nuke-style hold behaviour to an ImageReader.

    Real image sequences clamp to their first and last frame outside the
    sequence range. Single files keep Gaffer's default behaviour.
    """
    file_name = reader["fileName"].getValue()
    frames = None
    if "#" in file_name:
        try:
            sequence = IECore.ls(file_name)
        except Exception:
            sequence = None
        if isinstance(sequence, IECore.FileSequence):
            disk_frames = sequence.frameList.asList()
            if disk_frames:
                frames = (min(disk_frames), max(disk_frames))

    mode = GafferImage.ImageReader.FrameMaskMode
    for plug_name, frame in zip(("start", "end"), frames or (0, 0)):
        plug = reader[plug_name]
        if not plug["mode"].settable() or not plug["frame"].settable():
            continue
        if frames is None:
            plug["mode"].setToDefault()
            plug["frame"].setToDefault()
        else:
            plug["mode"].setValue(mode.ClampToFrame)
            plug["frame"].setValue(frame)


def render_frames(node):
    """Return the concrete frames represented by either render node type."""
    if is_write(node):
        return list(node.frames())

    start = node["startFrame"].getValue()
    end = node["endFrame"].getValue()
    return list(range(start, end + 1))


def expand_frame_path(path, frame):
    """Expand a run of # characters using its actual padding width."""
    match = re.search(r"#+", path)
    if not match:
        return path
    padding = len(match.group(0))
    return path[:match.start()] + f"{frame:0{padding}d}" + path[match.end():]


def task_nodes(root_node):
    """Yield dispatchable task nodes, including a direct GafferComp Write."""
    nodes = []
    if isinstance(root_node, GafferDispatch.TaskNode):
        nodes.append(root_node)
    nodes.extend(root_node.children(GafferDispatch.TaskNode))
    return nodes
