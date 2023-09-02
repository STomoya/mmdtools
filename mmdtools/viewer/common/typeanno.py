from __future__ import annotations

from typing import TypeAlias

__all__ = [
    'Vector2D',
    'Vector3D',
    'Vector4D'
]


Vector2D: TypeAlias = 'tuple[float, float]'
Vector3D: TypeAlias = 'tuple[float, float, float]'
Vector4D: TypeAlias = 'tuple[float, float, float, float]'
