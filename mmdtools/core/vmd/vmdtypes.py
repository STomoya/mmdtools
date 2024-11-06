from __future__ import annotations

from collections import defaultdict
from typing import TypeAlias

from mmdtools.core.base import MMDComponent

__all__ = [
    'VMD_SIGNATURE',
    'VMDComponent',
    'Header',
    'BoneFrameKey',
    'ShapeKeyFrameKey',
    'CameraKeyFrameKey',
    'LampKeyFrameKey',
    'SelfShadowFrameKey',
    'PropertyFrameKey',
    'BoneAnimation',
    'ShapeKeyAnimation',
    'CameraAnimation',
    'LampAnimation',
    'SelfShadowAnimation',
    'PropertyAnimation',
    'VMDFile',
]


VMD_SIGNATURE = b'Vocaloid Motion Data 0002'

Vector3D: TypeAlias = 'tuple[float, float, float]'
Vector4D: TypeAlias = 'tuple[float, float, float, float]'


class VMDComponent(MMDComponent):
    pass


class Header(VMDComponent):
    def __init__(self) -> None:
        self.signature: bytes = None
        self.model_name: str = ''


class BoneFrameKey(VMDComponent):
    def ___init__(self):
        self.frame_number: int = 0
        self.location: Vector3D = None
        self.rotation: Vector4D = None
        self.interpolation: tuple[float, ...] = None


class ShapeKeyFrameKey(VMDComponent):
    def __init__(self) -> None:
        self.frame_number: int = 0
        self.weight: float = None


class CameraKeyFrameKey(VMDComponent):
    def __init__(self) -> None:
        self.frame_number: int = 0
        self.distance: float = 0.0
        self.location: Vector3D = None
        self.rotation: Vector3D = None
        self.interpolation: tuple[float, ...] = None
        self.angle: float = 0.0
        self.perspective: bool = None


class LampKeyFrameKey(VMDComponent):
    def __init__(self) -> None:
        self.frame_number: int = 0
        self.color: Vector3D = None
        self.direction: Vector3D = None


class SelfShadowFrameKey(VMDComponent):
    def __init__(self) -> None:
        self.frame_number: int = None
        self.mode: int = 0
        self.distance: float = 0.0


class PropertyFrameKey(VMDComponent):
    def __init__(self) -> None:
        self.frame_number: int = 0
        self.is_visible: bool = None
        self.ik_states: list[tuple[str, int]] = []


class _VMDDict(defaultdict, VMDComponent):
    def __init__(self):
        super().__init__(list)


class _VMDList(list, VMDComponent):
    pass


class BoneAnimation(_VMDDict):
    pass


class ShapeKeyAnimation(_VMDDict):
    pass


class CameraAnimation(_VMDList):
    pass


class LampAnimation(_VMDList):
    pass


class SelfShadowAnimation(_VMDList):
    pass


class PropertyAnimation(_VMDList):
    pass


class VMDFile:
    def __init__(self) -> None:
        self.filename: str = ''
        self.header: Header = None
        self.bone_animation: BoneAnimation = {}
        self.shape_key_animation: ShapeKeyAnimation = {}
        self.camera_animation: CameraAnimation = []
        self.lamp_animation: LampAnimation = []
        self.self_shadow_animation: SelfShadowAnimation = []
        self.property_animation: PropertyAnimation = []

    def __repr__(self):
        return (
            '-' * 64 + '\n'
            f'Filename: {self.filename}\n' + '-' * 64 + '\n'
            'Statistics\n'
            f'    Num. bones: {len(self.bone_animation)}\n'
            f'    Num. shapes: {len(self.shape_key_animation)}\n'
            f'    Num. camera frames: {len(self.camera_animation)}\n'
            f'    Num. lamp frames: {len(self.lamp_animation)}\n'
            f'    Num. self shadow frames: {len(self.self_shadow_animation)}\n'
            f'    Num. property frames: {len(self.property_animation)}\n' + '-' * 64
        )
