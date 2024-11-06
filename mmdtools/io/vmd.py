from __future__ import annotations

import struct
from collections import defaultdict
from typing import Callable

from mmdtools.core import vmd
from mmdtools.io.utils import FileReadStream, crop_byte_string


class VMDFileReadStream(FileReadStream):
    def read_chars_cropped(self, length: int, pattern: bytes = b'\x00', decode: None | str = 'shift_jis'):
        byte_string = self.read_chars(length)
        byte_string = crop_byte_string(byte_string, pattern)
        string = byte_string.decode(encoding=decode, errors='replace') if decode else byte_string
        return string

    def read_byte_vector(self, length: int):
        return struct.unpack(f'<{length}b', self._fp.read(length))


def _loop_load(fs: VMDFileReadStream, load_fn: Callable, **kwargs) -> None:
    """load data iteratively. The data loaded inside the `load_fn` must be saved to somewere else INSIDE the
    function.

    Args:
        fs (VMDFileReadStream):
        load_fn (Callable): function to load data.
        **kwargs: Additional keyword arguments that should be passed to `load_fn`.

    """
    num_loops = fs.read_ulong()
    for _ in range(num_loops):
        load_fn(fs, **kwargs)


def _vmd_dict_load_fn(container: defaultdict, frame_key_load_fn: Callable) -> Callable:
    """Create a function that can be passed to `_loop_load` for animation data.

    Args:
        container (defaultdict): `defaultdict` object with default set to `list`. data returned from
            `frame_key_load_fn` is saved to `container`. See `mmdtools.core.vmd.vmdtypes._VMDDict`.
        frame_key_load_fn (Callable): A Callable that loads frame key data from file stream.

    Returns:
        Callable: `load_fn` that can be passed to _loop_load

    """

    def load_fn(fs: VMDFileReadStream):
        name = fs.read_chars_cropped(15)
        frame_key = frame_key_load_fn(fs)
        container[name].append(frame_key)

    return load_fn


def _vmd_list_load_fn(container: list, frame_key_load_fn: Callable) -> Callable:
    """Create a function that can be passed to `_loop_load` for animation data.

    Args:
        container (list): `list` object with default set to `list`. data returned from `frame_key_load_fn`
            is saved to `container`. See `mmdtools.core.vmd.vmdtypes._VMDList`.
        frame_key_load_fn (Callable): A Callable that loads frame key data from file stream.

    Returns:
        Callable: `load_fn` that can be passed to _loop_load

    """

    def load_fn(fs: VMDFileReadStream):
        frame_key = frame_key_load_fn(fs)
        container.append(frame_key)

    return load_fn


def _load_header(fs: VMDFileReadStream) -> vmd.Header:
    """load header."""
    header = vmd.Header()
    header.signature = fs.read_chars_cropped(30, decode=None)
    if header.signature != vmd.VMD_SIGNATURE:
        raise Exception('invalid file')
    header.model_name = fs.read_chars_cropped(20)
    return header


def _load_bone_animation(fs: VMDFileReadStream) -> vmd.BoneAnimation:
    """load bone animation."""
    bone_animation = vmd.BoneAnimation()
    load_fn = _vmd_dict_load_fn(bone_animation, _load_bone_frame_key)
    _loop_load(fs, load_fn)
    return bone_animation


def _load_bone_frame_key(fs: VMDFileReadStream) -> vmd.BoneFrameKey:
    """load bone frame key."""
    frame_key = vmd.BoneFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.location = fs.read_vector_3d()
    frame_key.rotation = fs.read_vector_4d()
    if not any(frame_key.rotation):
        frame_key.rotation = (0.0, 0.0, 0.0, 1.0)
    frame_key.interpolation = fs.read_byte_vector(64)
    return frame_key


def _load_shape_key_animation(fs: VMDFileReadStream) -> vmd.ShapeKeyAnimation:
    """load shape key animation."""
    shape_key_animation = vmd.ShapeKeyAnimation()
    load_fn = _vmd_dict_load_fn(shape_key_animation, _load_shape_key_frame_key)
    _loop_load(fs, load_fn)
    return shape_key_animation


def _load_shape_key_frame_key(fs: VMDFileReadStream) -> vmd.ShapeKeyFrameKey:
    """load shape key frame key."""
    frame_key = vmd.ShapeKeyFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.weight = fs.read_float()
    return frame_key


def _load_camera_animation(fs: VMDFileReadStream) -> vmd.CameraAnimation:
    """load camera animation"""
    camera_animation = vmd.CameraAnimation()
    load_fn = _vmd_list_load_fn(camera_animation, _load_carema_key_frame_key)
    _loop_load(fs, load_fn)
    return camera_animation


def _load_carema_key_frame_key(fs: VMDFileReadStream) -> vmd.CameraKeyFrameKey:
    """load camera key frame key."""
    frame_key = vmd.CameraKeyFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.distance = fs.read_float()
    frame_key.location = fs.read_vector_3d()
    frame_key.rotation = fs.read_vector_3d()
    frame_key.interpolation = fs.read_vector(6)
    frame_key.angle = fs.read_ulong()
    frame_key.perspective = fs.read_byte() == 0
    return frame_key


def _load_lamp_animation(fs: VMDFileReadStream) -> vmd.LampAnimation:
    """load lamp animation."""
    lamp_animation = vmd.LampAnimation()
    load_fn = _vmd_list_load_fn(lamp_animation, _load_lamp_key_frame_key)
    _loop_load(fs, load_fn)
    return lamp_animation


def _load_lamp_key_frame_key(fs: VMDFileReadStream) -> vmd.LampKeyFrameKey:
    """load lamp key frame key."""
    frame_key = vmd.LampKeyFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.color = fs.read_vector_3d()
    frame_key.direction = fs.read_vector_3d()
    return frame_key


def _load_self_shadow_animation(fs: VMDFileReadStream) -> vmd.SelfShadowAnimation:
    """load self shadow animation."""
    self_shadow_animation = vmd.SelfShadowAnimation()
    load_fn = _vmd_list_load_fn(self_shadow_animation, _load_self_shadow_frame_key)
    _loop_load(fs, load_fn)
    return self_shadow_animation


def _load_self_shadow_frame_key(fs: VMDFileReadStream) -> vmd.SelfShadowFrameKey:
    """load self shadow frame key."""
    frame_key = vmd.SelfShadowFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.mode = fs.read_byte()
    frame_key.distance = 10000 - fs.read_float() * 10000
    return frame_key


def _load_property_animation(fs: VMDFileReadStream) -> vmd.PropertyAnimation:
    """load property animation."""
    property_animation = vmd.PropertyAnimation()
    load_fn = _vmd_list_load_fn(property_animation, _load_property_frame_key)
    _loop_load(fs, load_fn)
    return property_animation


def _load_property_frame_key(fs: VMDFileReadStream) -> vmd.PropertyFrameKey:
    """load property frame key."""
    frame_key = vmd.PropertyFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.is_visible = fs.read_byte()
    load_fn = _vmd_list_load_fn(frame_key.ik_states, _load_ik_state)
    _loop_load(fs, load_fn)
    return frame_key


def _load_ik_state(fs: VMDFileReadStream) -> tuple[str, int]:
    """load ik state"""
    ik_name = fs.read_chars_cropped(20)
    state = fs.read_byte()
    return (ik_name, state)


def _load_file(fs: VMDFileReadStream) -> vmd.VMDFile:
    """load file using the given file stream."""
    vmd_file = vmd.VMDFile()
    vmd_file.filename = fs.path

    vmd_file.header = _load_header(fs)

    # these entries always have a loop count. (0 if no data.)
    vmd_file.bone_animation = _load_bone_animation(fs)
    vmd_file.shape_key_animation = _load_shape_key_animation(fs)
    vmd_file.camera_animation = _load_camera_animation(fs)
    vmd_file.lamp_animation = _load_lamp_animation(fs)

    # these do not contain loop count if not exits.
    # When so, `struct` will raise an error reporting that the buffer
    # is too small for that given format.
    # We re-raise any other errors.
    try:
        vmd_file.self_shadow_animation = _load_self_shadow_animation(fs)
        vmd_file.property_animation = _load_property_animation(fs)
    except struct.error as e:
        if 'unpack requires a buffer of' in str(e):
            pass
        else:
            raise
    except:
        raise

    return vmd_file


def load(path: str) -> vmd.VMDFile:
    """Load motion data from .vmd format file.

    Args:
        path (str): path to the .vmd file

    Returns:
        vmd.VMDFile: loaded .vmd file.

    """
    with VMDFileReadStream(path) as fs:
        vmd_file = _load_file(fs)
    return vmd_file
