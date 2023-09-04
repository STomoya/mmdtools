from __future__ import annotations

import numpy as np
import OpenGL.GL as gl
import glfw
from PIL import Image

from mmdtools.viewer.common.typeanno import Vector3D


class Window:
    """glfw window.

    Args:
        height (int): height of window.
        width (int): width of window.
        background_color (Vector3D): background color. Default: (1.0, 1.0, 1.0).
        target_fps (int): target FPS. Default: 60.
    """
    def __init__(self,
        height: int, width: int, background_color: Vector3D=(1.0, 1.0, 1.0), target_fps: int=60
    ) -> None:
        self.height = height
        self.width = width
        self.target_fps = target_fps

        # initialize context
        if not glfw.init():
            raise Exception()

        # set window options
        glfw.window_hint(glfw.VISIBLE, False)
        glfw.window_hint(glfw.SAMPLES, 4)

        # create window
        window = glfw.create_window(width, height, '', None, None)
        if not window:
            glfw.terminate()
            raise Exception('Failed to create window.')

        self.window = window

        glfw.make_context_current(window)
        gl.glClearColor(*background_color, 1.0)


    def before_render(self) -> None:
        """functions to run before rendering
        """
        self.width, self.height = glfw.get_framebuffer_size(self.window)
        gl.glViewport(0, 0, self.width, self.height)


    def after_render(self) -> None:
        """functions to run after rendering.
        """
        gl.glFlush()
        glfw.swap_buffers(self.window)
        glfw.poll_events()
        glfw.wait_events_timeout(1. / self.target_fps)


    def close(self) -> None:
        """close window.
        """
        if self.window is not None:
            glfw.destroy_window(self.window)
        glfw.terminate()


    def read_pixels(self, frame_buffer: int=0) -> Image.Image:
        """read pixels from specific frame buffer.

        Args:
            frame_buffer (int): frame buffer identifier. defaults to default frame buffer. Deafult: 0.

        Returns:
            Image.Image: PIL image object.
        """
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, frame_buffer)
        image_buffer = gl.glReadPixels(0, 0, self.width, self.height, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        image = np.frombuffer(image_buffer, dtype=np.uint8).reshape(self.height, self.width, -1)
        image = image[::-1, ::-1]
        image = Image.fromarray(image)
        return image
