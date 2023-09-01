
import numpy as np
from mmdtools.core import pmx
from mmdtools.core.mmd import mmdtypes


__all__ = [
    'from_pmx'
]


def atleast_4d(value, fill=0, dtype=int):
    out = np.full((4, ), fill_value=fill, dtype=dtype)
    value = np.atleast_1d(np.array(value))
    out[:len(value)] = value
    return out

def from_pmx(pmx_model: pmx.Model):
    """convert PMX format model to MMD."""
    model = mmdtypes.Model()

    metadata = mmdtypes.Metadata()
    metadata.name = pmx_model.name
    metadata.name_en = pmx_model.name_en
    metadata.comment = pmx_model.comment
    metadata.comment_en = pmx_model.comment_en
    model.metadata = metadata

    for pmx_vertex in pmx_model.vertex:
        vertex = mmdtypes.Vertex()

        vertex.vertex = np.array(pmx_vertex.vertex)
        vertex.normal = np.array(pmx_vertex.normal)
        vertex.uv = np.array(pmx_vertex.uv)
        vertex.bone_weight_type = pmx_vertex.weight.type
        vertex.bone_ids = atleast_4d(pmx_vertex.weight.bones)
        if vertex.bone_weight_type in [pmx.BoneWeightType.BDEF4, pmx.BoneWeightType.BDEF1]:
            weight = pmx_vertex.weight.weights
        elif vertex.bone_weight_type == pmx.BoneWeightType.BDEF2:
            weight = pmx_vertex.weight.weights
            weight = (weight, 1 - weight)
        elif vertex.bone_weight_type == pmx.BoneWeightType.SDEF:
            weight = pmx_vertex.weight.weights.weight
            weight = (weight, 1 - weight)
            vertex.sdef_options.c = pmx_vertex.weight.weights.c
            vertex.sdef_options.r0 = pmx_vertex.weight.weights.r0
            vertex.sdef_options.r1 = pmx_vertex.weight.weights.r1
        vertex.bone_weights = atleast_4d(weight, dtype=np.float32)
        vertex.edge_scale = pmx_vertex.edge_scale

        model.vertex.append(vertex)

    for face in pmx_model.face:
        model.face.append(face)

    face_vertex_count = 0
    for pmx_material in pmx_model.material:
        material = mmdtypes.Material()

        material.diffuse = np.array(pmx_material.diffuse)
        material.specular_color = np.array(pmx_material.specular_color)
        material.specular_scale = pmx_material.specular_scale
        material.mirror_color = np.array(pmx_material.ambient_color)

        material.enabled_edge = pmx_material.enabled_toon_edge
        material.edge_color = np.array(pmx_material.edge_color)
        material.edge_size = pmx_material.edge_size

        num_textures = len(pmx_model.texture)
        material.texture_name = pmx_model.texture[pmx_material.texture_index].path

        if pmx_material.sphere_texture_index in range(num_textures):
            material.sphere_texture_name = pmx_model.texture[pmx_material.sphere_texture_index].path
            material.sphere_texture_mode = pmx_material.sphere_texture_mode

        if pmx_material.is_shared_toon_texture:
            material.toon_texture_name = f'toon{pmx_material.toon_texture_number+1:02}.bmp'
        elif pmx_material.sphere_texture_index in range(num_textures):
            material.toon_texture_name = pmx_model.texture[pmx_material.toon_texture_number].path

        material.comment = pmx_material.comment

        material.face_vertex_index_start = face_vertex_count
        material.face_vertex_size = pmx_material.face_vertex_count
        face_vertex_count += pmx_material.face_vertex_count

        model.material.append(material)

    for pmx_bone in pmx_model.bone:
        bone = mmdtypes.Bone()

        bone.name = pmx_bone.name
        bone.name_en = pmx_bone.name_en

        bone.location = np.array(pmx_bone.location)
        bone.parent_index = pmx_bone.parent_index
        bone.weight = pmx_bone

        bone.is_rotation = pmx_bone.is_rotation
        bone.is_movable = pmx_bone.is_movable
        bone.is_visible = pmx_bone.is_visible
        bone.is_controllable = pmx_bone.is_controllable
        bone.has_additional_location = pmx_bone.has_additional_location
        bone.has_additional_rotation = pmx_bone.has_additional_rotation
        bone.addtional_transform = pmx_bone.additional_transform

        bone.is_ik = pmx_bone.is_ik
        if bone.is_ik:
            bone.ik_target_bone = pmx_bone.ik.target_bone
            bone.ik_iteration = pmx_bone.ik.iterations
            bone.ik_link_bones = [ik_link.target_bone for ik_link in pmx_bone.ik.ik_links]

        model.bone.append(bone)

    return model
