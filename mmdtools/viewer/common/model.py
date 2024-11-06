from __future__ import annotations

from collections import defaultdict

import numpy as np

from mmdtools.core import mmd
from mmdtools.viewer.common.bone import Bone


class Model:
    """Model

    Args:
        model_data (mmd.Model): model data.

    """
    def __init__(self, model_data: mmd.Model) -> None:
        self.vertex_data: list[mmd.Vertex] = model_data.vertex
        self.material_data: list[mmd.Material] = model_data.material
        self.bone_data: list[mmd.Bone] = model_data.bone

        self.vertex_position: np.ndarray = np.array([v.vertex for v in self.vertex_data], dtype=np.float32).reshape(-1)
        self.vertex_uv: np.ndarray = np.array([v.uv for v in self.vertex_data], dtype=np.float32).reshape(-1)
        self.vertex_normal: np.ndarray = np.array([v.normal for v in self.vertex_data], dtype=np.float32).reshape(-1)
        self.vertex_edge_scale: np.ndarray = np.array([v.edge_scale for v in self.vertex_data], dtype=np.float32).reshape(-1)
        self.vertex_bone_ids: np.ndarray = np.array([v.bone_ids for v in self.vertex_data], dtype=np.float32).reshape(-1)
        self.vertex_bone_weights: np.ndarray = np.array([v.bone_weights for v in self.vertex_data], dtype=np.float32).reshape(-1)

        self.face: np.ndarray = np.array(model_data.face, dtype=np.uint16).reshape(-1)

        self.motion_bones: list[Bone] = []
        # for fast searching of bones. O(1).
        self.name2mbone_index: dict[str, int] = {}
        self.level2mbone_indices: dict[int, list[int]] = defaultdict(list)
        self._is_bone_initialized: bool = False

        self._create_motion_bones()

        self._raw_data = model_data


    def _create_motion_bones(self, force: bool=False) -> None:
        """create bones for motion.

        Args:
            force (bool): force create bones, even if already initialized.

        """

        if self._is_bone_initialized and not force:
            return
        self._is_bone_initialized = True

        # we first create bone objects because we need reference to these objects to properly initialize
        # attributes in these objects.
        for i, bone_data in enumerate(self.bone_data):
            bone = Bone(i, bone_data)
            self.motion_bones.append(bone)
            self.name2mbone_index[bone.name] = i
            self.level2mbone_indices[bone.level].append(i)


        # set attributes that needs reference to instantiated bone objects.
        for i, bone_data in enumerate(self.bone_data):
            motion_bone = self.motion_bones[i]

            # set parent bone
            parent = None if bone_data.parent_index < 0 else self.motion_bones[bone_data.parent_index]
            motion_bone.set_parent_bone(parent)

            # set ik
            if bone_data.is_ik:
                ik_effect_bone = self.motion_bones[bone_data.ik_target_bone]
                ik_links = [self.motion_bones[i] for i in bone_data.ik_link_bones]
            else:
                ik_effect_bone, ik_links = None, None
            motion_bone.set_ik_bones(ik_effect_bone, ik_links)

            # set parent follow
            if bone_data.has_additional_location or bone_data.has_additional_rotation:
                is_translate = bone_data.has_additional_location
                grant_parent_bone = self.motion_bones[bone_data.addtional_transform[0]]
                grant_parent_rate = bone_data.addtional_transform[1]
            else:
                is_translate, grant_parent_bone, grant_parent_rate = None, None, None
            motion_bone.set_grant_transform_parent_bone(grant_parent_bone, grant_parent_rate, is_translate)

        # check all bone is initialized.
        assert all(bone.is_initialized for bone in self.motion_bones)


    def get_bone_by_name(self, bone_name: str) -> Bone:
        """get bone by it's name. Only supports Japanese names.

        Args:
            bone_name (str): Japanese bone name.

        Returns:
            Bone: motion bone object.

        """
        return self.motion_bones[self.name2mbone_index[bone_name]]


    def update_bones(self) -> None:
        """update the motion bones. This function only adjusts the bone positions according to the
        motion set to the bones via `motion.Motion` class. See `mmdtools.viewer.common.motion.Motion`.
        """

        # Only adjust bones. See `motion.Motion` class for how bones are actually moved.
        for level in sorted(self.level2mbone_indices.keys()):
            for bone_index in self.level2mbone_indices[level]:
                bone = self.motion_bones[bone_index]
                # IK
                if bone.is_ik:
                    ik_bone = bone.ik_effect_bone
                    target_vector = bone.get_global_matrix()[3, :3]
                    ik_bone.ik_move(target_vector, chain=bone.ik_links, loop_size=bone.ik_iterations)
                # follow parent
                bone.grant()

        # reset update flags
        for bone in self.motion_bones:
            bone.is_updated = False
        # apply delta to global_matrix and local_matrix attributes.
        # Then, reset delta matrix for next motion.
        for bone in self.motion_bones:
            bone.apply()
            bone.reset_delta()


    def create_vertex_transform_matrix(self) -> np.ndarray:
        """create transformation matrices for all the vertices. currently does not support SDEF weighting.
        SDEF can be used as BDEF2, so we fallback to BDEF2. This function should be called after calling
        `update_bones` function.

        Returns:
            np.ndarray: trasformation matrices for all vertices. [N,4,4], N is number of vertices.

        """
        transforms = []
        bone_transforms = [bone.local_matrix for bone in self.motion_bones]
        for vertex in self.vertex_data:
            bone_ids = vertex.bone_ids
            weights = vertex.bone_weights
            if weights.sum() == 0.0:
                transform = np.identity(4)
            else:
                transform = weights[0] * bone_transforms[bone_ids[0]]
                transform += weights[1] * bone_transforms[bone_ids[1]]
                transform += weights[2] * bone_transforms[bone_ids[2]]
                transform += weights[3] * bone_transforms[bone_ids[3]]
            transforms.append(transform)
        return np.array(transforms, dtype=np.float32)

    def collect_bone_transforms(self) -> np.ndarray:
        """Collect transformation matrices from all bones.

        The matrices are stacked on the first dimension, forming a tensor of shape [Nx4x4] where N is the number of
        bones.

        Returns:
            np.ndarray: trasformation matrices for all bones. [N,4,4]

        """
        bone_transforms = np.array([bone.local_matrix for bone in self.motion_bones], dtype=np.float32)
        return bone_transforms

    def reset_motion(self) -> None:
        """reset all motion bones to initial position."""
        for bone in self.motion_bones:
            bone.reset()
