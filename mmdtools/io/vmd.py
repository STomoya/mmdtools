from __future__ import annotations
from collections import defaultdict

import os
import struct
from typing import Any, Callable
import warnings

from mmdtools.core import vmd
from mmdtools.io.utils import FileReadStream, crop_byte_string


class VMDFileReadStream(FileReadStream):
    def read_chars_cropped(self, length: int, pattern: bytes=b'\x00', decode: None|str='shift_jis'):
        byte_string = self.read_chars(length)
        byte_string = crop_byte_string(byte_string, pattern)
        string = byte_string.decode(encoding=decode, errors='replace') if decode else byte_string
        return string


def _loop_load(fs: VMDFileReadStream, load_fn: Callable, **kwargs):
    num_loops = fs.read_ulong()
    for _ in range(num_loops):
        load_fn(fs, **kwargs)


def _vmd_dict_load_fn(container: defaultdict, frame_key_load_fn: Callable):
    def load_fn(fs: VMDFileReadStream):
        name = fs.read_chars_cropped(15)
        frame_key = frame_key_load_fn(fs)
        container[name].append(frame_key)
    return load_fn


def _vmd_list_load_fn(container: list, frame_key_load_fn: Callable):
    def load_fn(fs: VMDFileReadStream):
        frame_key = frame_key_load_fn(fs)
        container.append(frame_key)
    return load_fn


def _load_header(fs: VMDFileReadStream):
    header = vmd.Header()
    header.signature = fs.read_chars_cropped(30, decode=None)
    if header.signature != vmd.VMD_SIGNATURE:
        raise Exception(f'invalid file')
    header.model_name = fs.read_chars_cropped(20)
    return header


def _load_bone_animation(fs: VMDFileReadStream):
    bone_animation = vmd.BoneAnimation()
    load_fn = _vmd_dict_load_fn(bone_animation, _load_bone_frame_key)
    _loop_load(fs, load_fn)
    return bone_animation


def _load_bone_frame_key(fs: VMDFileReadStream):
    frame_key = vmd.BoneFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.location = fs.read_vector_3d()
    frame_key.rotation = fs.read_vector_4d()
    if not any(frame_key.rotation):
        frame_key.rotation = (0.0, 0.0, 0.0, 1.0)
    frame_key.interpolation = fs.read_vector(16)
    return frame_key


def _load_shape_key_animation(fs: VMDFileReadStream):
    shape_key_animation = vmd.ShapeKeyAnimation()
    load_fn = _vmd_dict_load_fn(shape_key_animation, _load_shape_key_frame_key)
    _loop_load(fs, load_fn)
    return shape_key_animation


def _load_shape_key_frame_key(fs: VMDFileReadStream):
    frame_key = vmd.ShapeKeyFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.weight = fs.read_float()
    return frame_key


def _load_camera_animation(fs: VMDFileReadStream):
    camera_animation = vmd.CameraAnimation()
    load_fn = _vmd_list_load_fn(camera_animation, _load_carema_key_frame_key)
    _loop_load(fs, load_fn)
    return camera_animation


def _load_carema_key_frame_key(fs: VMDFileReadStream):
    frame_key = vmd.CameraKeyFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.distance = fs.read_float()
    frame_key.location = fs.read_vector_3d()
    frame_key.rotation = fs.read_vector_3d()
    frame_key.interpolation = fs.read_vector(6)
    frame_key.angle = fs.read_ulong()
    frame_key.perspective = (fs.read_byte() == 0)
    return frame_key


def _load_lamp_animation(fs: VMDFileReadStream):
    lamp_animation = vmd.LampAnimation()
    load_fn = _vmd_list_load_fn(lamp_animation, _load_lamp_key_frame_key)
    _loop_load(fs, load_fn)
    return lamp_animation


def _load_lamp_key_frame_key(fs: VMDFileReadStream):
    frame_key = vmd.LampKeyFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.color = fs.read_vector_3d()
    frame_key.direction = fs.read_vector_3d()
    return frame_key


def _load_self_shadow_animation(fs: VMDFileReadStream):
    self_shadow_animation = vmd.SelfShadowAnimation()
    load_fn = _vmd_list_load_fn(self_shadow_animation, _load_self_shadow_frame_key)
    _loop_load(fs, load_fn)
    return self_shadow_animation


def _load_self_shadow_frame_key(fs: VMDFileReadStream):
    frame_key = vmd.SelfShadowFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.mode = fs.read_byte()
    frame_key.distance = 10000 - fs.read_float() * 10000
    return frame_key


def _load_property_animation(fs: VMDFileReadStream):
    property_animation = vmd.PropertyAnimation()
    load_fn = _vmd_list_load_fn(property_animation, _load_property_frame_key)
    _loop_load(fs, load_fn)
    return property_animation


def _load_property_frame_key(fs: VMDFileReadStream):
    frame_key = vmd.PropertyFrameKey()
    frame_key.frame_number = fs.read_ulong()
    frame_key.is_visible = fs.read_byte()
    load_fn = _vmd_list_load_fn(frame_key.ik_states, _load_property_state)
    _loop_load(fs, load_fn)
    return frame_key


def _load_property_state(fs: VMDFileReadStream):
    ik_name = fs.read_chars_cropped(20)
    state = fs.read_byte()
    return (ik_name, state)


def _load_file(fs: VMDFileReadStream):
    vmd_file = vmd.VMDFile()
    vmd_file.filename = fs.path

    vmd_file.header = _load_header(fs)

    # these entries always have a loop count. (0 if no data.)
    vmd_file.bone_animation = _load_bone_animation(fs)
    vmd_file.shape_key_animation = _load_shape_key_animation(fs)
    vmd_file.camera_animation = _load_camera_animation(fs)
    vmd_file.lamp_animation = _load_lamp_animation(fs)

    try:
        vmd_file.self_shadow_animation = _load_self_shadow_animation(fs)
        vmd_file.property_animation = _load_property_animation(fs)
    except struct.error:
        pass

    return vmd_file


def load(path: str):
    with VMDFileReadStream(path) as fs:
        vmd_file = _load_file(fs)
    return vmd_file
