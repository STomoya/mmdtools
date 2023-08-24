from __future__ import annotations

import numpy as np

from mmdtools.core.base import MMDComponent

__all__ = [
    'Metadata',
    'Vertex',
    'Material',
    'Bone',
    'Model'
]


class Metadata(MMDComponent):
    def __init__(self) -> None:
        self.name: str = None
        self.name_en: str = None
        self.comment: str = None
        self.comment_en: str = None


class Vertex(MMDComponent):
    def __init__(self) -> None:
        self.vertex: np.ndarray = None
        self.normal: np.ndarray = None
        self.uv: np.ndarray = None
        self.additional_uvs: np.ndarray = None
        self.bone_weight_type: int = 1 # default to BDEF2 for PMD.
        self.bone_ids: np.ndarray = np.zeros(4, dtype=int)
        self.bone_weights: np.ndarray = np.zeros(4, dtype=int)
        self.sdef_options: SDEFOptions = None
        self.edge_scale: float = None


class SDEFOptions(MMDComponent):
    def __init__(self) -> None:
        self.c: np.ndarray = None
        self.r0: np.ndarray = None
        self.r1: np.ndarray = None


class Material(MMDComponent):
    def __init__(self) -> None:
        self.name: str = None
        self.name_en: str = None

        self.diffuse: np.ndarray = None
        self.specular_color: np.ndarray = None
        self.specular_scale: float = 1.0
        self.mirror_color: np.ndarray = None

        self.is_double_sided: bool = None

        self.edge_color: np.ndarray = None
        self.edge_size: float = None

        self.texture_name: str = None

        self.sphere_texture_index: str = None
        self.sphere_texture_mode: int = None

        self.is_shared_toon_texture: bool = None
        self.toon_texture_name: str = None

        self.comment: str = ''

        self.face_vertex_index_start: int = None
        self.face_vertex_size: int = None


class Bone(MMDComponent):
    def __init__(self) -> None:
        self.name: str = None
        self.name_en: str = None

        self.location: np.ndarray = None
        self.weight: float = 1.0
        self.parent_index: int = None

        self.is_rotation: bool = None
        self.is_movable: bool = None
        self.is_visible: bool = None
        self.is_controllable: bool = None

        self.has_additional_rotation: bool = None
        self.has_additional_location: bool = None
        self.addtional_transform: tuple[int, float] = None

        self.is_ik: bool = None
        self.ik_target_bone: bool = None
        self.ik_iteration: int = None
        self.ik_link_bones: list[int] = None


class Model(MMDComponent):
    def __init__(self) -> None:
        self.metadata: Metadata = None

        self.vertex: list[Vertex] = []
        self.face: list[tuple[int, int, int]] = []
        self.material: list[Material] = []
        self.bone: list[Bone] = []

        self._raw = None

    def __repr__(self):
        return (
            '-' * 64 + '\n'
            f'Model name: {self.metadata.name}\n'
            f'Comment:\n{self.metadata.comment}\n'
            + '-' * 64
        )
