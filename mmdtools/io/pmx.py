from __future__ import annotations

import os
import struct
from typing import Any, Callable
import warnings

from mmdtools.core import pmx
from mmdtools.io.utils import FileReadStream, parse_flags


class PMXFileReadStream(FileReadStream):
    def __init__(self, path) -> None:
        super().__init__(path)
        self._header: pmx.Header = None
        self._index_size_formats: dict[int, str] = {1: '<b', 2: '<h', 4: '<i'}

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, __incoming: pmx.Header):
        assert isinstance(__incoming, pmx.Header)
        self._header = __incoming

    def _read_index(self, size: int, unsigned: bool=False) -> int:
        """read index value with the specific size.

        Args:
            size (int): the size of the index.
            unsigned (bool, optional): is the index unsigned. Defaults to False.

        Returns:
            int: index
        """
        unpack_format = self._index_size_formats[size]
        unpack_format = unpack_format.upper() if unsigned else unpack_format
        return struct.unpack(unpack_format, self._fp.read(size))[0]

    def read_vertex_index(self) -> int:
        return self._read_index(self.header.vertex_index_size, unsigned=True)

    def read_bone_index(self) -> int:
        return self._read_index(self.header.bone_index_size)

    def read_texture_index(self) -> int:
        return self._read_index(self.header.texture_index_size)

    def read_morph_index(self) -> int:
        return self._read_index(self.header.morph_index_size)

    def read_rigid_index(self) -> int:
        return self._read_index(self.header.rigid_index_size)

    def read_material_index(self) -> int:
        return self._read_index(self.header.material_index_size)

    def read_str(self):
        """read string"""
        length = self.read_int()
        buffer = struct.unpack(f'<{length}s', self._fp.read(length))[0]
        return str(buffer, self.header.encoding, errors='replace')


"""loading functions"""


def _loop_load(fs: PMXFileReadStream, load_fn: Callable, output: list=None, step: int=1, **kwargs: dict[str, Any]) -> list:
    """load data iteratively using the given `load_fn`. If `output` is given, all return values will be appended to this list.
    If not new list will be made.

    Args:
        fs (PMXFileReadStream):
        load_fn (Callable): function to load data from fs.
        output (list, optional): list to append outputs to. Default: None.
        step (int, optional): step for loop count. Defaults to 1.

    Returns:
        list: list of output elements.
    """
    if output is None:
        output = []

    num_loops = fs.read_int() // step
    for _ in range(num_loops):
        loaded = load_fn(fs, **kwargs)
        output.append(loaded)

    return output


def _load_header(fs: PMXFileReadStream) -> pmx.Header:
    """load header"""
    header = pmx.Header()
    header.signature = fs.read_bytes(4)
    if header.signature[:3] != pmx.PMX_SIGNATURE[:3]:
        raise Exception(f'invalid file')
    header.version = fs.read_float()
    if header.version != pmx.PMX_VERSION:
        raise Exception(f'unsupported version')
    header_byte = fs.read_ubyte()
    if header_byte != 8 or header.signature[3] != pmx.PMX_SIGNATURE[3]:
        warnings.warn('This file might be corrupted.')
    encoding_index = fs.read_byte()
    header.encoding = 'utf-16-le' if encoding_index == 0 else 'utf-8'
    header.additional_uvs = fs.read_ubyte()
    header.vertex_index_size = fs.read_ubyte()
    header.texture_index_size = fs.read_ubyte()
    header.material_index_size = fs.read_ubyte()
    header.bone_index_size = fs.read_ubyte()
    header.morph_index_size = fs.read_ubyte()
    header.rigid_index_size = fs.read_ubyte()
    return header


def _load_vertex(fs: PMXFileReadStream) -> pmx.Vertex:
    """load vertex"""
    vertex = pmx.Vertex()

    vertex.vertex = fs.read_vector_3d()
    vertex.normal = fs.read_vector_3d()
    vertex.uv = fs.read_vector(2)
    for _ in range(fs.header.additional_uvs):
        vertex.additional_uvs.append(fs.read_vector_4d())
    vertex.weight = _load_bone_weight(fs)
    vertex.edge_scale = fs.read_float()
    return vertex


def _load_bone_weight(fs: PMXFileReadStream) -> pmx.BoneWeight:
    """load bone weight"""
    bone_weight = pmx.BoneWeight()
    bone_weight.type = fs.read_ubyte()

    if bone_weight.type == pmx.BoneWeightType.BDEF1:
        bone_weight.bones.append(fs.read_bone_index())
        bone_weight.weights = 1.0
    elif bone_weight.type == pmx.BoneWeightType.BDEF2:
        bone_weight.bones.append(fs.read_bone_index())
        bone_weight.bones.append(fs.read_bone_index())
        bone_weight.weights = fs.read_float()
    elif bone_weight.type == pmx.BoneWeightType.BDEF4:
        bone_weight.bones.append(fs.read_bone_index())
        bone_weight.bones.append(fs.read_bone_index())
        bone_weight.bones.append(fs.read_bone_index())
        bone_weight.bones.append(fs.read_bone_index())
        bone_weight.weights = fs.read_vector_4d()
    elif bone_weight.type == pmx.BoneWeightType.SDEF:
        bone_weight.bones.append(fs.read_bone_index())
        bone_weight.bones.append(fs.read_bone_index())
        bone_weight.weights = _load_sdef_bone_weight(fs)

    return bone_weight


def _load_sdef_bone_weight(fs: PMXFileReadStream) -> pmx.SDEFBoneWeight:
    """load SDEF bone weight"""
    weight = pmx.SDEFBoneWeight()
    weight.weight = fs.read_float()
    weight.c = fs.read_vector_3d()
    weight.r0 = fs.read_vector_3d()
    weight.r1 = fs.read_vector_3d()
    return weight


def _load_face(fs: PMXFileReadStream) -> tuple[int, int, int]:
    """load face"""
    return (
        fs.read_vertex_index(),
        fs.read_vertex_index(),
        fs.read_vertex_index()
    )


def _load_texture(fs: PMXFileReadStream) -> pmx.Texture:
    """load texture"""
    texture = pmx.Texture()
    texture.path = fs.read_str()
    texture.path = texture.path.replace('\\', os.path.sep)
    if not os.path.isabs(texture.path):
        texture.path = os.path.normpath(os.path.join(os.path.dirname(fs.path), texture.path))
    return texture


def _load_material(fs: PMXFileReadStream, num_textures: int) -> pmx.Material:
    """load material"""
    material = pmx.Material()

    material.name = fs.read_str()
    material.name_en = fs.read_str()

    material.diffuse = fs.read_vector_4d()
    material.specular_color = fs.read_vector_3d()
    material.specular_scale = fs.read_float()
    material.ambient_color = fs.read_vector_3d()

    flags = fs.read_ubyte()
    parsed_flags = parse_flags(flags, 5)
    material.is_double_sided = parsed_flags[0]
    material.enabled_drop_shadow = parsed_flags[1]
    material.enabled_self_shadow_map = parsed_flags[2]
    material.enabled_self_shadow = parsed_flags[3]
    material.enabled_toon_edge = parsed_flags[4]

    material.edge_color = fs.read_vector_4d()
    material.edge_size = fs.read_float()

    material.texture_index = fs.read_texture_index()
    material.sphere_texture_index = fs.read_texture_index()
    material.sphere_texture_mode = fs.read_ubyte()

    material.is_shared_toon_texture = fs.read_byte() == 1
    if material.is_shared_toon_texture:
        material.toon_texture_number = fs.read_byte()
    else:
        material.toon_texture_number = fs.read_texture_index()

    material.comment = fs.read_str()
    material.face_vertex_count = fs.read_int()

    return material


def _load_bone(fs: PMXFileReadStream) -> pmx.Bone:
    """load bone"""
    bone = pmx.Bone()
    bone.name = fs.read_str()
    bone.name_en = fs.read_str()

    bone.location = fs.read_vector_3d()
    bone.parent_index = fs.read_bone_index()
    bone.transform_order = fs.read_int()

    flags = fs.read_short()
    parsed_flags = parse_flags(flags, 14)

    if parsed_flags[0]:
        bone.display_connection = fs.read_bone_index()
    else:
        bone.display_connection = fs.read_vector_3d()

    bone.is_rotation = parsed_flags[1]
    bone.is_movable = parsed_flags[2]
    bone.is_visible = parsed_flags[3]
    bone.is_controllable = parsed_flags[4]

    bone.is_ik = parsed_flags[5]

    bone.has_additional_location = parsed_flags[8]
    bone.has_additional_rotation = parsed_flags[9]
    bone.additional_transform = None
    if bone.has_additional_location or bone.has_additional_rotation:
        t = fs.read_bone_index()
        v = fs.read_float()
        bone.additional_transform = (t, v)

    bone.axis_vector = None
    if parsed_flags[10]:
        bone.axis_vector = fs.read_vector_3d()

    bone.has_local_axis = parsed_flags[11]
    bone.local_x_axis = None
    bone.local_z_axis = None
    if bone.has_local_axis:
        bone.local_x_axis = fs.read_vector_3d()
        bone.local_z_axis = fs.read_vector_3d()

    bone.transform_after_physics = parsed_flags[12]

    bone.outside_parent_update = parsed_flags[12]
    bone.outside_parent_key = None
    if bone.outside_parent_update:
        bone.outside_parent_key = fs.read_int()

    bone.ik = None
    if bone.is_ik:
        bone.ik = _load_ik(fs)

    return bone


def _load_ik(fs: PMXFileReadStream) -> pmx.IK:
    """load IK"""
    ik = pmx.IK()
    ik.target_bone = fs.read_bone_index()
    ik.iterations = fs.read_int()
    ik.radius_range = fs.read_float()
    _loop_load(fs, _load_ik_link, ik.ik_links)
    return ik


def _load_ik_link(fs: PMXFileReadStream) -> pmx.IKLink:
    """load IK Link"""
    ik_link = pmx.IKLink()
    ik_link.target_bone = fs.read_bone_index()
    ik_link.has_rotation_limit = fs.read_byte()

    ik_link.minimum_angle = None
    ik_link.maximum_angle = None
    if ik_link.has_rotation_limit == 1:
        ik_link.minimum_angle = fs.read_vector_3d()
        ik_link.maximum_angle = fs.read_vector_3d()

    return ik_link


def _load_morph(fs: PMXFileReadStream) -> pmx.Morph:
    """load morph"""
    morph = pmx.Morph()
    morph.name = fs.read_str()
    morph.name_en = fs.read_str()
    morph.panel = fs.read_byte()
    morph.type_index = fs.read_byte()

    offset_load_fn = {
        0: _load_group_morph_offset,
        1: _load_vertex_morph_offset,
        2: _load_bone_morph_offset,
        3: _load_uv_morph_offset,
        4: _load_uv_morph_offset,
        5: _load_uv_morph_offset,
        6: _load_uv_morph_offset,
        7: _load_uv_morph_offset,
        8: _load_material_morph_offset
    }[morph.type_index]

    _loop_load(fs, offset_load_fn, morph.offsets)

    return morph


def _load_group_morph_offset(fs: PMXFileReadStream) -> pmx.GroupMorphOffset:
    """load group morph offset"""
    offset = pmx.GroupMorphOffset()
    offset.morph_index = fs.read_morph_index()
    offset.factor = fs.read_float()
    return offset


def _load_vertex_morph_offset(fs: PMXFileReadStream) -> pmx.VertexMorphOffset:
    """load vertex morph offset"""
    offset = pmx.VertexMorphOffset()
    offset.vertex_index = fs.read_vertex_index()
    offset.offset = fs.read_vector_3d()
    return offset


def _load_bone_morph_offset(fs: PMXFileReadStream) -> pmx.BoneMorphOffset:
    """load bone morph offset"""
    offset = pmx.BoneMorphOffset()
    offset.bone_index = fs.read_bone_index()
    offset.location_offset = fs.read_vector_3d()
    offset.rotation_offset = fs.read_vector_4d()
    if not any(offset.rotation_offset):
        offset.rotation_offset = (0.0, 0.0, 0.0, 1.0)
    return offset


def _load_uv_morph_offset(fs: PMXFileReadStream) -> pmx.UVMorphOffset:
    """load UV morph offset"""
    offset = pmx.UVMorphOffset()
    offset.vertex_index = fs.read_vertex_index()
    offset.offset = fs.read_vector_4d()
    return offset


def _load_material_morph_offset(fs: PMXFileReadStream) -> pmx.MaterialMorphOffset:
    """load material morph offset"""
    offset = pmx.MaterialMorphOffset()
    offset.material_index = fs.read_material_index()
    offset.offset_type = fs.read_byte()
    offset.diffuse_offset = fs.read_vector_4d()
    offset.specular_offset = fs.read_vector_3d()
    offset.specular_alpha = fs.read_float()
    offset.ambient_offset = fs.read_vector_3d()
    offset.edge_color_offset = fs.read_vector_4d()
    offset.edge_size_offset = fs.read_float()
    offset.texture_alpha = fs.read_vector_4d()
    offset.sphere_alpha = fs.read_vector_4d()
    offset.toon_texture_alpha = fs.read_vector_4d()
    return offset


def _load_display_frame(fs: PMXFileReadStream) -> pmx.DisplayFrame:
    """load display"""
    display = pmx.DisplayFrame()
    display.name = fs.read_str()
    display.name_en = fs.read_str()
    display.is_special = fs.read_ubyte() == 1
    num_data = fs.read_int()
    for _ in range(num_data):
        display_type = fs.read_ubyte()
        if display_type == 0:
            index = fs.read_bone_index()
        elif display_type == 1:
            index = fs.read_morph_index()
        else:
            raise Exception(f'invalid value')
        display.indices.append((display_type, index))
    return display


def _load_rigid(fs: PMXFileReadStream) -> pmx.Rigid:
    """load rigid"""
    rigid = pmx.Rigid()
    rigid.name = fs.read_str()
    rigid.name_en = fs.read_str()

    rigid.bone_index = None
    bone_index = fs.read_bone_index()
    if bone_index != -1:
        rigid.bone_index = bone_index

    rigid.collision_group_number = fs.read_byte()
    rigid.collision_group_mask = fs.read_ushort()

    rigid.type = fs.read_byte()
    rigid.size = fs.read_vector_3d()

    rigid.location = fs.read_vector_3d()
    rigid.rotation = fs.read_vector_3d()

    rigid.mass = fs.read_float()
    rigid.velocity_attenuation = fs.read_float()
    rigid.rotation_attenuation = fs.read_float()
    rigid.bounce = fs.read_float()
    rigid.friction = fs.read_float()

    rigid.mode = fs.read_byte()

    return rigid


def _load_joint(fs: PMXFileReadStream) -> pmx.Joint:
    """load joint"""
    joint = pmx.Joint()
    try:
        joint.name = fs.read_str()
        joint.name_en = fs.read_str()

        joint.mode = fs.read_byte()

        joint.source_rigid_index = fs.read_rigid_index()
        joint.destination_rigid_index = fs.read_rigid_index()
        if joint.source_rigid_index == -1:
            joint.source_rigid_index = None
        if joint.destination_rigid_index == -1:
            joint.destination_rigid_index = None

        joint.location = fs.read_vector_3d()
        joint.rotation = fs.read_vector_3d()

        joint.minimum_location = fs.read_vector_3d()
        joint.maximum_location = fs.read_vector_3d()
        joint.minimum_rotation = fs.read_vector_3d()
        joint.maximum_rotation = fs.read_vector_3d()

        joint.spring_location_constant = fs.read_vector_3d()
        joint.spring_rotation_constant = fs.read_vector_3d()
    except struct.error:
        if joint.source_rigid_index is None or joint.destination_rigid_index is None:
            raise
        joint.location = joint.location or (0, 0, 0)
        joint.rotation = joint.rotation or (0, 0, 0)
        joint.maximum_location = joint.maximum_location or (0, 0, 0)
        joint.minimum_location = joint.minimum_location or (0, 0, 0)
        joint.maximum_rotation = joint.maximum_rotation or (0, 0, 0)
        joint.minimum_rotation = joint.minimum_rotation or (0, 0, 0)
        joint.spring_location_constant = joint.spring_location_constant or (0, 0, 0)
        joint.spring_rotation_constant = joint.spring_rotation_constant or (0, 0, 0)

    return joint


def _load_model(fs: PMXFileReadStream) -> pmx.Model:
    """load model"""
    model = pmx.Model()

    model.filename=fs.path
    model.header=fs.header
    model.name=fs.read_str()
    model.name_en=fs.read_str()
    model.comment=fs.read_str()
    model.comment_en=fs.read_str()

    _loop_load(fs, _load_vertex, model.vertex)
    _loop_load(fs, _load_face, model.face, step=3)
    _loop_load(fs, _load_texture, model.texture)
    _loop_load(fs, _load_material, model.material, num_textures=len(model.texture))
    _loop_load(fs, _load_bone, model.bone)
    _loop_load(fs, _load_morph, model.morph)
    _loop_load(fs, _load_display_frame, model.display)
    _loop_load(fs, _load_rigid, model.rigid)
    _loop_load(fs, _load_joint, model.joint)

    if fs.read_rest() != b'':
        raise Exception('There are remaining bytes that were not loaded. Aborting.')

    return model


def load(path: str) -> pmx.Model:
    """load model from pmx format file.

    Args:
        path (str): path to .pmx format.

    Returns:
        pmx.Model: model data.
    """
    with PMXFileReadStream(path) as fs:
        header = _load_header(fs)
        fs.header = header
        model = _load_model(fs)
    return model
