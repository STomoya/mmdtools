
from collections import defaultdict
from mmdtools.core import vmd
from mmdtools.viewer.common.key_frame import BoneMotionKeyFrame
from mmdtools.viewer.common.model import Model



class Motion:
    """Motion"""
    def __init__(self, model: Model, motion_data: vmd.VMDFile) -> None:
        self.motions_key_frames: dict[str, list[BoneMotionKeyFrame]] = defaultdict(list)

        for name, key_frames in motion_data.bone_animation.items():
            for key_frame in key_frames:
                motion_frame = BoneMotionKeyFrame(model.get_bone_by_name(name), key_frame)
                self.motions_key_frames[name].append(motion_frame)
            self.motions_key_frames[name].sort(key=lambda x: x.frame_number)
            self.motions_key_frames[name].append(None)
            for current, next in zip(self.motions_key_frames[name], self.motions_key_frames[name][1:]):
                current.set_next_frame(next)

        self.current_key_frames = {name: key_frames[0] for name, key_frames in self.motions_key_frames.items()}
        self.current_frame = 0


    def finished(self) -> bool:
        """is motion data finished?"""
        for key_frame in self.current_key_frames.values():
            if key_frame.next_frame is not None:
                return False
        return True


    def step(self) -> None:
        """step frame.
        """
        for name in self.current_key_frames.keys():
            key_frame = self.current_key_frames[name]
            if key_frame is not None:
                self.current_key_frames[name] = key_frame.update(self.current_frame)
        self.current_frame += 1
