from __future__ import annotations

import numpy as np
import OpenGL.GL as gl
import glfw
from PIL import Image

from mmdtools.viewer.common.typeanno import Vector3D


class Window:
    def __init__(self,
        height: int, width: int, background_color: Vector3D=(1.0, 1.0, 1.0), fps: int=60
    ) -> None:
        self.height = height
        self.width = width
        self.fps = fps

        if not glfw.init():
            raise Exception()

        glfw.window_hint(glfw.VISIBLE, False)
        glfw.window_hint(glfw.SAMPLES, 4)

        window = glfw.create_window(width, height, '', None, None)
        if not window:
            glfw.terminate()
            raise Exception('Failed to create window.')

        self.window = window

        glfw.make_context_current(window)
        gl.glClearColor(*background_color, 1.0)

        self._is_polygon_mode_fill = True


    def before_render(self):
        gl.glViewport(0, 0, self.width, self.height)


    def after_render(self):
        gl.glFlush()
        glfw.swap_buffers(self.window)
        glfw.poll_events()
        glfw.wait_events_timeout(1. / self.fps)


    def close(self):
        glfw.destroy_window(self.window)
        glfw.terminate()


    def read_pixels(self, frame_buffer: int=0):
        # gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, frame_buffer)
        image_buffer = gl.glReadPixels(0, 0, self.width, self.height, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        image = np.frombuffer(image_buffer, dtype=np.uint8).reshape(self.height, self.width, -1)
        image = image[::-1, ::-1]
        image = Image.fromarray(image)
        return image
