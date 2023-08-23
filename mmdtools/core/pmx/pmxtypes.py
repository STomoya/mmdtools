from __future__ import annotations

from enum import IntEnum
from typing import TypeAlias

from mmdtools.core.base import MMDComponent

__all__ = [
    'PMX_SIGNATURE',
    'PMX_VERSION',
    'PMXComponent',
    'BoneWeightType',
    'Header',
    'Vertex',
    'BoneWeight', 'SDEFBoneWeight',
    'Texture',
    'Material',
    'Bone',
    'IK',
    'IKLink',
    'Morph',
    'GroupMorphOffset',
    'VertexMorphOffset',
    'BoneMorphOffset',
    'UVMorphOffset',
    'MaterialMorphOffset',
    'DisplayFrame',
    'Rigid',
    'Joint',
    'Model'
]


PMX_SIGNATURE = b'PMX '
PMX_VERSION = 2.0


Vector3D: TypeAlias = "tuple[float, float, float]"
Vector4D: TypeAlias = "tuple[float, float, float, float]"


class PMXComponent(MMDComponent): pass


class BoneWeightType(IntEnum):
    BDEF1 = 0
    BDEF2 = 1
    BDEF4 = 2
    SDEF  = 3


class Header(PMXComponent):
    def __init__(self):
        self.signature: bytes = None
        self.version: float = None
        self.encoding: str = 'utf-16-le'
        self.additional_uvs: int = 0
        self.vertex_index_size: int = None
        self.texture_index_size: int = None
        self.material_index_size: int = None
        self.bone_index_size: int = None
        self.morph_index_size: int = None
        self.rigid_index_size: int = None


class Vertex(PMXComponent):
    def __init__(self) -> None:
        self.vertex: Vector3D = None
        self.normal: Vector3D = None
        self.uv: tuple[float, float] = None
        self.additional_uvs: list[Vector4D] = []
        self.weight: BoneWeight = None
        self.edge_scale: float = None


class BoneWeight(PMXComponent):
    def __init__(self) -> None:
        self.type: BoneWeightType = None
        self.bones: list[int] = []
        self.weights: float | tuple[float] | SDEFBoneWeight = None


class SDEFBoneWeight(PMXComponent):
    def __init__(self) -> None:
        self.weight: float = None
        self.c: Vector3D = None
        self.r0: Vector3D = None
        self.r1: Vector3D = None


class Texture(PMXComponent):
    def __init__(self) -> None:
        self.path: str = None


class Material(PMXComponent):
    def __init__(self) -> None:

        self.name: str = None
        self.name_en: str = ''

        self.diffuse: Vector4D = None
        self.specular_color: Vector3D = None
        self.specular_scale: float = None
        self.ambient_color: Vector3D = None

        self.is_double_sided: bool = None
        self.enabled_drop_shadow: bool = None
        self.enabled_self_shadow_map: bool = None
        self.enabled_self_shadow: bool = None
        self.enabled_toon_edge: bool = None

        self.edge_color: Vector4D = None
        self.edge_size: float = None

        self.texture_index: int = None
        self.sphere_texture_index: int = None
        self.sphere_texture_mode: int = None

        self.is_shared_toon_texture: bool = None
        self.texture_name: None | str = None
        self.toon_texture_number: int = None
        self.comment: str = None
        self.face_vertex_count: int = None


class Bone(PMXComponent):
    def __init__(self) -> None:
        self.name: str = None
        self.name_en: str = ''

        self.location: Vector3D = None
        self.parent_index: int = None
        self.transform_order: int = None

        self.display_connection: int | Vector3D = None

        self.is_rotation: bool = None
        self.is_movable: bool = None
        self.is_visible: bool = None
        self.is_controllable: bool = None
        self.is_ik: bool = None

        self.has_additional_rotation: bool = None
        self.has_additional_location: bool = None
        self.additional_transform: None | tuple[int, float] = None

        self.axis_vector: None | Vector3D = None

        self.has_local_axis: bool = None
        self.local_x_axis: None | Vector3D = None
        self.local_z_axis: None | Vector3D = None

        self.transform_after_physics: bool = None

        self.outside_parent_update: bool = None
        self.outside_parent_key: None | int = None

        self.ik: None | IK = None


class IK(PMXComponent):
    def __init__(self) -> None:
        self.target_bone: int = None
        self.iterations: int = None
        self.radius_range: float = None
        self.ik_links: list[IKLink] = []


class IKLink(PMXComponent):
    def __init__(self) -> None:
        self.target_bone: int = None
        self.has_rotation_limit: bool = None
        self.minimum_angle: None | Vector3D = None
        self.maximum_angle: None | Vector3D = None


class Morph(PMXComponent):
    def __init__(self) -> None:
        self.name: str = None
        self.name_en: str = ''
        self.panel: int = None
        self.type_index: int = None
        self.offsets: list[MorphOffset] = []

    @property
    def uv_index(self) -> int | None:
        if self.panel in (3, 4, 5, 6, 7):
            return self.type_index - 3
        else:
            return None

class MorphOffset(PMXComponent): pass


class GroupMorphOffset(MorphOffset):
    def __init__(self) -> None:
        self.morph_index: int = None
        self.factor: float = None


class VertexMorphOffset(MorphOffset):
    def __init__(self) -> None:
        self.vertex_index: int = None
        self.offset: Vector3D = None


class BoneMorphOffset(MorphOffset):
    def __init__(self) -> None:
        self.bone_index: int = None
        self.location_offset: Vector3D = None
        self.rotation_offset: Vector4D = None


class UVMorphOffset(MorphOffset):
    def __init__(self) -> None:
        self.vertex_index: int = None
        self.offset: Vector4D = None


class MaterialMorphOffset(MorphOffset):
    def __init__(self) -> None:
        self.material_index: int = None
        self.offset_type: int = None
        self.diffuse_offset: Vector4D = None
        self.specular_offset: Vector3D = None
        self.specular_alpha: float = None
        self.ambient_offset: Vector3D = None
        self.edge_color_offset: Vector4D = None
        self.edge_size_offset: float = None
        self.texture_alpha: Vector4D = None
        self.sphere_alpha: Vector4D = None
        self.toon_texture_alpha: Vector4D = None


class DisplayFrame(PMXComponent):
    def __init__(self) -> None:
        self.name: str = None
        self.name_en: str = ''
        self.is_special: bool = None
        self.indices: list[tuple[int, int]] = []


class Rigid(PMXComponent):
    def __init__(self) -> None:
        self.name: str = None
        self.name_en: str = ''

        self.bone_index: None | int = None
        self.collision_group_number: int = None
        self.collision_group_mask: int = None

        self.type: int = None
        self.size: Vector3D = None

        self.location: Vector3D = None
        self.rotation: Vector3D = None

        self.mass: float = None
        self.velocity_attenuation: float = None
        self.rotation_attenuation: float = None
        self.bounce: float = None
        self.friction: float = None

        self.mode: int = None


class Joint(PMXComponent):
    def __init__(self) -> None:
        self.name: str = None
        self.name_en: str = ''

        self.mode: int = None

        self.source_rigid_index: int = None
        self.destination_rigid_index: int = None

        self.location: Vector3D = None
        self.rotation: Vector3D = None

        self.minimum_location: Vector3D = None
        self.maximum_location: Vector3D = None

        self.minimum_rotation: Vector3D = None
        self.maximum_rotation: Vector3D = None

        self.spring_location_constant: Vector3D = None
        self.spring_rotation_constant: Vector3D = None



class Model:
    def __init__(self) -> None:
        self.filename: str
        self.header: Header

        self.name: str
        self.name_en: str
        self.comment: str
        self.comment_en: str

        self.vertex: list[Vertex] = []
        self.face: list[tuple[int, int, int]] = []
        self.texture: list[Texture] = []
        self.material: list[Material] = []
        self.bone: list[Bone] = []
        self.morph: list[Morph] = []

        root_display = DisplayFrame()
        root_display.is_special = True
        root_display.name = 'Root'
        root_display.name_en = 'Root'
        face_display = DisplayFrame()
        face_display.is_special = True
        face_display.name = '表情'
        face_display.name_en = 'Facial'

        self.display: list[DisplayFrame] = [
            root_display, face_display
        ]
        self.rigid: list[Rigid] = []
        self.joint: list[Joint] = []


    def __repr__(self) -> str:
        num_ik = sum(1 for bone in self.bone if bone.is_ik)
        return (
            '-' * 64 + '\n'
            f'Filename  : {self.filename}\n'
            f'Model name: {self.name}\n'
            f'Comment   :\n{self.comment}\n'
            + '-' * 64 + '\n'
            'Statistics\n'
            f'    Num. Vertex  : {len(self.vertex)}\n'
            f'    Num. Face    : {len(self.face)}\n'
            f'    Num. Texture : {len(self.texture)}\n'
            f'    Num. Material: {len(self.material)}\n'
            f'    Num. Bone    : {len(self.bone)}\n'
            f'        Num. IK  : {num_ik}\n'
            f'    Num. Morph   : {len(self.morph)}\n'
            f'    Num. Display : {len(self.display)}\n'
            f'    Num. Rigid   : {len(self.rigid)}\n'
            f'    Num. Joint   : {len(self.joint)}\n'
            + '-' * 64
        )
