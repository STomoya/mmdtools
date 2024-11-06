from __future__ import annotations

import numpy as np
from pyrr import matrix44
from scipy.spatial.transform import Rotation

from mmdtools.core import mmd
from mmdtools.viewer.common.typeanno import Vector3D, Vector4D


def normalize(v: np.ndarray, eps: float = 1e-32) -> np.ndarray:
    norm = np.linalg.norm(v)
    return v / (norm + eps)


class Bone:
    """Bone class for motion. The functionalities should not be needed to be called by users."""

    def __init__(self, index: int, bone: mmd.Bone) -> None:
        self.id = index
        self.name = bone.name
        self.name_en = bone.name_en
        self.level = bone.level

        # initial bone position (constant)
        self.init_matrix: np.ndarray = matrix44.create_from_translation(bone.location)

        # used for IK (constant)
        self.offset_matrix: np.ndarray = matrix44.inverse(self.init_matrix)

        # transformation from current position (reset on each frame)
        self.delta_matrix: np.ndarray = matrix44.create_identity()

        # local matrix when rendering (set on each frame)
        self.local_matrix: np.ndarray = matrix44.create_identity()

        # global_matrix = part_matrix * parent.global_matrix (constant)
        self.part_matrix: np.ndarray = matrix44.create_identity()

        # cummulative transformations
        self.global_matrix: np.ndarray = self.init_matrix.copy()

        # parent bone
        self.parent: Bone = None

        # flags (currently not used.)
        self.is_controllable = bone.is_controllable
        self.is_rotatable = bone.is_rotation
        self.is_movable = bone.is_movable

        # IK
        self.is_ik = bone.is_ik
        self.ik_bone: Bone | None = self if self.is_ik else None
        self.ik_effect_bone: Bone | None = None
        self.ik_iterations: int | None = bone.ik_iteration
        self.ik_links: list[Bone] | None = None

        # follow paranet bone
        self.grant_is_translation = False
        self.grant_parent_bone: Bone | None = None
        self.grant_parent_rate: float | None = None

        # for faster implementation.
        self.is_updated = False

        # initialized flags.
        self._is_parent_initialized = False
        self._is_ik_initialized = False
        self._is_additional_trans_initialized = False

        # raw bone data
        self._raw_data = bone

    @property
    def is_initialized(self) -> bool:
        """Returns if the object is properly initialized. Call `set_parent_bone`, `set_ik_bone`, and
        `set_grant_transform_parent_bone`, beforehand for this property to work properly.
        """
        return self._is_parent_initialized & self._is_ik_initialized & self._is_additional_trans_initialized

    def reset(self) -> None:
        """reset bone to initial position."""
        self.global_matrix = self.init_matrix.copy()
        self.delta_matrix = matrix44.create_identity()
        self.local_matrix = matrix44.create_identity()

    """Setters.
    NOTE: These functions triggers the initialization flags, therefore needs to be called even when all arguments
          are `None`. But this is not a requirement if not using `Bone.is_initialized` attr.
    """

    def set_parent_bone(self, parent: Bone | None) -> None:
        """Set the parent bone alongside with some matrix attributes according to the input.

        The input must be an instantiated `Bone` class object.

        Args:
            parent (Bone | None): The parent bone object. None if no parent bone.

        """
        self._is_parent_initialized = True

        if parent is None:
            return

        if self.id < parent.id:
            return

        self.parent = parent
        self.part_matrix = matrix44.multiply(self.init_matrix, parent.offset_matrix)

    def set_ik_bones(self, effect_bone: Bone | None, links: list[Bone] | None) -> None:
        """Set the effected and linked bone object for IK. The input must be an instantiated `Bone` class object.

        Args:
            effect_bone (Bone | None): effected bone object.
            links (list[Bone] | None): list of linked bone objects.

        """
        self._is_ik_initialized = True

        if effect_bone is None:
            return

        self.ik_effect_bone = effect_bone
        self.ik_links = links

    def set_grant_transform_parent_bone(self, bone: Bone, rate: float, is_translation: bool) -> None:
        """Set configuration for bones following its parent. `bone` argument must be an instantiated `Bone` class
        object.

        Args:
            bone (Bone): the parent bone to follow
            rate (float): the rate of followance.
            is_translation (bool): configures the method of fallowing. If `False`, uses rotation.

        """
        self._is_additional_trans_initialized = True

        self.grant_is_translation = is_translation
        self.grant_parent_bone = bone
        self.grant_parent_rate = rate

    """
    matrix getter/setters
    NOTE: Functions affecting `global_matrix` contains 'global' in function name. If not, `delta_matrix` is updated.
    """

    def reset_delta(self) -> None:
        """Reset the `delta_matrix` for next motion."""
        self.delta_matrix = np.identity(4)

    def add_matrix(self, matrix: np.ndarray) -> None:
        """Apply partial transformation matrix to the `delta_matrix`.

        Args:
            matrix (np.ndarray): the partial transformation matrix.

        """
        self.delta_matrix = matrix44.multiply(matrix, self.delta_matrix)

    def translate(self, translation: np.ndarray | Vector3D) -> None:
        """Apply translation to `delta_matrix`. should be a translation vector of size 3.

        The vector is transformed to an 4x4 matrix inside the function.

        Args:
            translation (np.ndarray | Vector3D): 1D array representing the translation.

        """
        matrix = matrix44.create_from_translation(translation)
        self.add_matrix(matrix)

    def rotate(self, rotation: np.ndarray | Vector4D) -> None:
        """Apply rotation to `delta_matrix`. should be a quaternion vector of size 4.

        The vector is transformed to a 4x4 matrix inside the function.

        Args:
            rotation (np.ndarray | Vector4D): 1D array representing the rotation (quaternion).

        """
        matrix = matrix44.create_from_inverse_of_quaternion(rotation)
        self.add_matrix(matrix)

    def get_global_matrix(self, check_updated: bool = False) -> np.ndarray:
        """Get global matrix, considering the parent bone.

        Args:
            check_updated (bool, optional): Check if the bone is already updated. Default: False.

        Returns:
            np.ndarray: the global matrix of the bone.

        """
        if check_updated and self.is_updated:
            return self.global_matrix
        global_matrix = self.global_matrix
        if self.parent:
            parent_matrix = self.parent.get_global_matrix(check_updated)
            global_matrix = matrix44.multiply(self.part_matrix, parent_matrix)
        return matrix44.multiply(self.delta_matrix, global_matrix)

    def get_global_position(self) -> np.ndarray:
        """Get the translation vector from the bone's `global_matrix`.

        Returns:
            np.ndarray: the translation vector of size 3.

        """
        return self.global_matrix[3, 0:3]

    def set_global_position(self, position: np.ndarray) -> None:
        """Get position to the `global_matrix`, given a translation vector of size 3.

        Args:
            position (np.ndarray): position. a vector of size 3.

        """
        self.global_matrix[3, 0:3] = position

    def get_rotation(self) -> np.ndarray:
        """Get global rotation from `delta_matrix` as a rotation vector.

        NOTE: This function returns the angles, not in quaternion.

        Returns:
            np.ndarray: the rotation vector. a vector of size 3.

        """
        return Rotation.from_matrix(self.delta_matrix[:3, :3]).as_rotvec()

    def set_rotation(self, rotation: np.ndarray | Vector3D) -> None:
        """Apply rotation to `delta_matrix` given a rotation vector of size 3.

        NOTE: this function expects angles, not quaternion.

        Args:
            rotation (np.ndarray | Vector3D): rotation vector. vector of size 3.

        """
        matrix = np.identity(4)
        matrix[:3, :3] = Rotation.from_rotvec(rotation).as_matrix()
        self.add_matrix(matrix)

    def rotate_axis(self, axis: np.ndarray, rotation: float, update: bool = False) -> None:
        """Apply rotation to `delta_matrix` given the axis and rotation.

        Args:
            axis (np.ndarray): axis.
            rotation (float): rotation.
            update (bool, optional): If False, returns the 4x4 rotation matrix. Default: False.

        """
        matrix = matrix44.create_from_axis_rotation(axis, rotation)
        if not update:
            return matrix
        self.add_matrix(matrix)

    """Bone mover functions."""

    @staticmethod
    def rotatable_control(bone: Bone, axis: np.ndarray, rotation: float) -> None:
        """Define the rotation control function for bones.

        Args:
            bone (Bone): bone to rotate.
            axis (np.ndarray): axis.
            rotation (float): rotation.

        """
        if bone.name == 'ひざ':
            v = bone.rotate_axis(axis, rotation, update=False)[1, 2]
            if v < 0.02:  # noqa: PLR2004
                bone.rotate_axis(axis, rotation)
        else:
            bone.rotate_axis(axis, rotation)

    def ik_move(self, target_position: np.ndarray, chain: list[Bone], loop_size: int, loop_range: int = 256) -> None:
        """IK.

        Args:
            target_position (np.ndarray):
            chain (list[Bone]): list of linked bones.
            loop_size (int): iterations.
            loop_range (int, optional): max loop size. Defaults to 256.

        """
        bias = 1e-2
        loop_size = min(loop_size, loop_range)

        effect_bone = self
        target_matrix = matrix44.create_from_translation(target_position)

        for chain_bone in chain:
            exit_flag = False
            for _ in range(loop_size):
                effector_matrix = chain_bone.get_global_matrix()
                base_matrix = np.linalg.inv(effector_matrix)

                local_target_position = np.matmul(target_matrix, base_matrix)[3, :3]
                local_target_position = normalize(local_target_position)

                local_effect_position = np.matmul(effect_bone.get_global_matrix(), base_matrix)[3, :3]
                local_effect_position = normalize(local_effect_position)

                dot = np.clip(np.inner(local_effect_position, local_target_position), -1, 1)
                rot = np.arccos(dot)
                if abs(rot) < bias:
                    exit_flag = True
                    break

                axis = np.cross(local_effect_position, local_target_position)
                if np.sum(np.abs(axis)) < bias:
                    exit_flag = True
                    break

                axis = normalize(axis)
                chain_bone.rotatable_control(chain_bone, axis, rot)

            if exit_flag:
                break

    def grant(self) -> None:
        """Apply parent follow."""
        if self.grant_parent_bone is None:
            return

        rate = self.grant_parent_rate

        if self.grant_is_translation:
            pos = self.grant_parent_bone.get_global_position()
            self.set_global_position(pos * rate)
        else:
            rotation = self.grant_parent_bone.get_rotation()
            self.set_rotation(rotation * rate)

    def apply(self):
        """Apply `delta_matrix` to `global_matrix` and `local_matrix`, considering the parent bones."""
        if self.parent and not self.parent.is_updated:
            self.parent.apply()
        self.global_matrix = self.get_global_matrix(check_updated=True)
        self.local_matrix = np.matmul(self.offset_matrix, self.global_matrix)
        self.is_updated = True
