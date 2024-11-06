from __future__ import annotations

import os
from enum import IntEnum
from typing import ClassVar

import numpy as np
import OpenGL.GL as gl
from PIL import Image

from mmdtools import const


class TextureUnit(IntEnum):
    BASE = 0
    SPHERE = 1
    TOON = 2


class Texture:
    """Texture class. reuses same object if already exists.
    NOTE: do not instantiate object via constructor but use `create` classmethod.
    """

    _cache: ClassVar = {}

    def __init__(self, filename: None | str = None, unit: int = 0) -> None:
        self.gl_texture: int = None
        self.filename: str = filename
        self.unit: TextureUnit = unit
        self._load()

    @classmethod
    def create(cls, filename: str, is_sphere: bool = False, is_toon: bool = False) -> Texture:
        """class method that returns the texture object. It reuses the same object if already exits.
        `is_sphere` and `is_toon` cannot be triggered together.

        Args:
            filename (str): path to the texture image file.
            is_sphere (bool, optional): is sphere texture? Defaults to False.
            is_toon (bool, optional): is toon texture? Defaults to False.

        Returns:
            Texture: created texture object.

        """
        assert not (is_sphere and is_toon)

        unit = TextureUnit.BASE
        if is_sphere:
            unit = TextureUnit.SPHERE
        if is_toon:
            unit = TextureUnit.TOON
            if filename is not None and not os.path.exists(filename):
                filename = os.path.join(const.TOON_ROOT_DIR, filename)
        key = (filename, unit) if filename else None

        if key in cls._cache:
            return cls._cache[key]

        texture_obj = cls(filename, unit)
        cls._cache[key] = texture_obj
        return texture_obj

    def _load(self) -> None:
        """load image and setup"""
        if self.filename is None or not os.path.exists(self.filename):
            return

        image = Image.open(self.filename).convert('RGBA')
        width, height = image.size
        image_array = np.asarray(image).reshape(height, width, -1)

        self.gl_texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.gl_texture)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, image_array)

        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)
        if self.unit == TextureUnit.TOON:
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        else:
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)

        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

    def use(self) -> None:
        """call before this texture is used."""
        if self.gl_texture is None:
            return

        gl.glActiveTexture(gl.GL_TEXTURE0 + self.unit)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.gl_texture)
