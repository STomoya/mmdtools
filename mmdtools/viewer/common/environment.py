from __future__ import annotations

import numpy as np
from pyrr import matrix44

from mmdtools.viewer.common.typeanno import Vector3D


class Environment:
    """environment variables. matrices are implemented as properties. model_matrix can be set externally."""
    def __init__(self) -> None:

        self.light: Light = Light()
        self.camera: Camera = Camera()
        self.projection: Projection = Projection()

        self._model_matrix: np.ndarray = matrix44.create_identity()


    @property
    def model_matrix(self) -> np.ndarray:
        """model matrix"""
        return self._model_matrix

    @model_matrix.setter
    def model_matrix(self, model_matrix: np.ndarray) -> None:
        self._model_matrix = model_matrix


    @property
    def view_matrix(self) -> np.ndarray:
        """camera matrix"""
        return matrix44.create_look_at(
            self.camera.position, self.camera.target, self.camera.up, dtype=np.float32
        )


    @property
    def projection_matrix(self) -> np.ndarray:
        """perspective projection matrix"""
        return matrix44.create_perspective_projection(
            self.projection.fovy, self.projection.aspect, self.projection.near, self.projection.far,
            dtype=np.float32
        )


    @property
    def model_view_matrix(self) -> np.ndarray:
        """GLSL: view_matrix * model_matrix"""
        return matrix44.multiply(self.view_matrix, self.model_matrix)


    @property
    def it_model_view_matrix(self) -> np.ndarray:
        """inverse of transpose of `model_view_matrix`"""
        return matrix44.inverse(self.model_view_matrix).T


    @property
    def mvp(self) -> np.ndarray:
        """Model View Projection matrix"""
        return matrix44.multiply(self.projection_matrix, self.model_view_matrix)


    def set_light(self, *,
        position: Vector3D|None=None, color: Vector3D|None=None,
        ambient: Vector3D|None=None, diffuse: Vector3D|None=None, specular: Vector3D|None=None
    ) -> None:
        """set attributes for light.

        Args:
            position (Vector3D | None, optional): position. Default: None.
            color (Vector3D | None, optional): color. currently not used. use `diffuse`. Default: None.
            ambient (Vector3D | None, optional): ambient. Default: None.
            diffuse (Vector3D | None, optional): diffuse. Default: None.
            specular (Vector3D | None, optional): specular. Default: None.
        """
        if position is not None:
            self.light.position = position
        if color is not None:
            self.light.color = color
        if ambient is not None:
            self.light.ambient = ambient
        if diffuse is not None:
            self.light.diffuse = diffuse
        if specular is not None:
            self.light.specular = specular


    def set_projection(self, *,
        fovy: float|None=None, aspect: float|None=None, near: float|None=None, far: float|None=None
    ) -> None:
        """set attributes for projection.

        Args:
            fovy (float | None, optional): fovy. Default: None.
            aspect (float | None, optional): aspect ratio. Default: None.
            near (float | None, optional): z near. Default: None.
            far (float | None, optional): z far. Default: None.
        """
        if fovy is not None:
            self.projection.fovy = fovy
        if aspect is not None:
            self.projection.aspect = aspect
        if near is not None:
            self.projection.near = near
        if far is not None:
            self.projection.far = far


    def set_camera(self, *,
        position: Vector3D|None=None, target: Vector3D|None=None, up: Vector3D|None=None
    ) -> None:
        """set attribute for camera

        Args:
            position (Vector3D | None, optional): position. Default: None.
            target (Vector3D | None, optional): target. Default: None.
            up (Vector3D | None, optional): up. Default: None.
        """
        if position is not None:
            self.camera.position = position
        if target is not None:
            self.camera.target = target
        if up is not None:
            self.camera.up = up



class Light:
    def __init__(self,
        position: Vector3D=(0.0, 0.0, 0.0), color: Vector3D=(1.0, 1.0, 1.0),
        ambient: Vector3D=(1.0, 1.0, 1.0), diffuse: Vector3D=(0.0, 0.0, 0.0), specular: Vector3D=(0.0, 0.0, 0.0)
    ) -> None:

        self.position: Vector3D = position
        self.ambient: Vector3D = ambient
        self.diffuse: Vector3D = diffuse
        self.specular: Vector3D = specular
        self.color: Vector3D = color


class Camera:
    def __init__(self,
        position: Vector3D=(0.0, 10.0, -30.0), target: Vector3D=(0.0, 10.0, 0.0), up: Vector3D=(0.0, 1.0, 0.0)
    ) -> None:

        self.position: Vector3D = position
        self.target: Vector3D = target
        self.up: Vector3D = up


class Projection:
    def __init__(self,
        fovy: float=45.0, aspect: float=1.0, near: float=0.1, far: float=50.0
    ) -> None:

        self.fovy: float = fovy
        self.aspect: float = aspect
        self.near: float = near
        self.far: float = far
