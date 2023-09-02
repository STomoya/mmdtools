from __future__ import annotations

from functools import lru_cache
import numpy as np
from pyrr import quaternion
from mmdtools.core import vmd

from mmdtools.viewer.common.bone import Bone


@lru_cache(maxsize=512)
def solve_bezier(x: tuple[float, float], y: tuple[float, float], linear_rate: float) -> float:
    """Calculate approximation of y value from given x of a cubic Bezier curve using bisection method.
    This function assumes that starting and ending Ps are (0.0, 0.0) and (1.0, 1.0) respectively.

    code from: https://edvakf.hatenadiary.org/entry/20111016/1318716097
    converted to Python by STomoya.

    Args:
        x (tuple[float, float]): x value of two controlling points.
        y (tuple[float, float]): y value of two controlling points.
        linear_rate (float): normalized position between two key frames.

    Returns:
        float: approximated value.
    """
    t = s = 0.5
    for i in range(15):
        ft = (3 * s ** 2 * t * x[0]) + (3 * s * t ** 2 * x[1]) + (t**3) - linear_rate
        if np.abs(ft) < 1e-5: break
        sign = -1 if ft > 0 else 1
        t += sign * 1 / (4 << i)
        s = 1 - t
    return (3 * s ** 2 * t * y[0]) + (3 * s * t ** 2 * y[1]) + (t**3)


class BoneMotionKeyFrame:
    """Bone motion key frames.
    """
    def __init__(self, bone, key_frame: vmd.BoneFrameKey) -> None:
        self.bone: Bone = bone

        self.frame_number: int = key_frame.frame_number
        self.rotation: np.ndarray = key_frame.rotation
        self.translation: np.ndarray = key_frame.location

        bezier_points = np.array(key_frame.interpolation)[:16].reshape(2, 8).T / 127.0
        self.bezier_points: dict[str, dict[str, tuple[int, int]]] = {
            'x': {'x': tuple(bezier_points[0]), 'y': tuple(bezier_points[4])},
            'y': {'x': tuple(bezier_points[1]), 'y': tuple(bezier_points[5])},
            'z': {'x': tuple(bezier_points[2]), 'y': tuple(bezier_points[6])},
            'r': {'x': tuple(bezier_points[3]), 'y': tuple(bezier_points[7])}
        }

        self.next_frame: BoneMotionKeyFrame = None

        self._is_next_frame_initialized = False


    @property
    def is_initialized(self) -> bool:
        return self._is_next_frame_initialized


    def set_next_frame(self, next_frame: BoneMotionKeyFrame) -> None:
        """set next frame. input must be an instatiated `BoneMotionKeyFrame` object.

        Args:
            next_frame (BoneMotionKeyFrame): reference to next key frame object.
        """
        self._is_next_frame_initialized = True
        self.next_frame = next_frame


    def get_linear_rate(self, frame: int) -> float:
        """get linear interpolation between key frames

        Args:
            frame (int): current frame.

        Returns:
            float: normalized frame.
        """
        if self.next_frame is not None:
            if self.next_frame.frame_number == self.frame_number:
                rate = 0.0
            else:
                rate = (frame - self.frame_number) / (self.next_frame.frame_number - self.frame_number)

        return rate


    def update(self, frame: int) -> BoneMotionKeyFrame|None:
        """update

        Args:
            frame (int): current frame.

        Returns:
            BoneMotionKeyFrame|None: current frame object or the next frame object, according to the
                input `frame`.
        """

        #  we stay in the current position.
        if self.next_frame is None:
            self.bone.translate(self.translation)
            self.bone.rotate(self.rotation)
            return self

        linear_rate = self.get_linear_rate(frame)
        # This is for when the very first frame's frame_number attr is not 0.
        if linear_rate < 1:
            return self
        # If multiple frames were skipped, exceeding the current key frame.
        if linear_rate > 1:
            return self.next_frame

        # interpolate translation between key frames using bezier curve.
        translation = self.interp_translation(linear_rate)
        self.bone.translate(translation)
        # interpolate rotation between key frames using bezier curve.
        rotation = self.interp_rotation(linear_rate)
        self.bone.rotate(rotation)

        # next key frame?
        if self.next_frame and self.next_frame.frame_number <= frame:
            return self.next_frame

        return self


    def interp_translation(self, linear_rate: float) -> np.ndarray:
        """bezier interpolation of translation for each x, y, z coordinate.

        Args:
            linear_rate (float): normalized frame position between key frames.

        Returns:
            np.ndarray: interpolated translation.
        """
        bezier_x_rate = solve_bezier(**self.bezier_points['x'], linear_rate)
        bezier_y_rate = solve_bezier(**self.bezier_points['y'], linear_rate)
        bezier_z_rate = solve_bezier(**self.bezier_points['z'], linear_rate)
        rate = np.array([bezier_x_rate, bezier_y_rate, bezier_z_rate])
        return self.next_frame.translation * rate + self.translation * (1 - rate)


    def interp_rotation(self, linear_rate: float) -> np.ndarray:
        """bezier interpolation of rotation. uses slerp.

        Args:
            linear_rate (float): normalized frame position between key frames.

        Returns:
            np.ndarray: interpolated rotation.
        """
        bezier_r_rate = solve_bezier(**self.bezier_points['r'], linear_rate)
        return quaternion.slerp(self.rotation, self.next_frame.rotation, bezier_r_rate)
