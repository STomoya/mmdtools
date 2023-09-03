from __future__ import annotations

import numpy as np
import OpenGL.GL as gl

from mmdtools.core.mmd.mmdtypes import Material
from mmdtools.viewer.opengl.shader import Shader
from mmdtools.viewer.opengl.texture import Texture, TextureUnit



class Mesh:
    def __init__(self, index: int, material: Material, face: np.ndarray, shader: Shader, edge_shader: Shader|None=None) -> None:
        self.index = index
        self.shader = shader
        self.edge_shader = edge_shader

        # front polygons
        self.shader.set_index(self.index, face)

        # textures
        self.texture = Texture.create(material.texture_name)
        self.sphere_texture = Texture.create(material.sphere_texture_name, is_sphere=True)
        self.sphere_texture_mode = material.sphere_texture_mode
        self.toon_texture = Texture.create(material.toon_texture_name, is_toon=True)
        self.use_toon_texture = 0.0 if self.toon_texture.gl_texture is None else 1.0

        # color
        self.ambient = material.mirror_color
        self.specular = material.specular_color
        self.diffuse = material.diffuse[:3]
        self.alpha = material.diffuse[3]
        self.shininess = material.specular_scale

        # edge
        # enable edge drawing only if need.
        self.enable_edge = material.enabled_edge and isinstance(edge_shader, Shader)
        if self.enable_edge: self.edge_shader.set_index(self.index, face)

        self.edge_color = material.edge_color
        self.edge_size = material.edge_size

        # for opengl
        self.face_vertex_size = material.face_vertex_size
        self.disable_cull_facing = material.is_double_sided

        self._material_data = material


    def draw(self, draw_edge=False):

        # edge drawing path.

        if draw_edge and not self.enable_edge:
            return

        elif draw_edge:

            with self.edge_shader.drawing():

                # # bind edge specific variables

                # edge
                self.edge_shader.set_vec4('uEdgeColor', self.edge_color)
                self.edge_shader.set_float('uEdgeSize', self.edge_size)
                self.edge_shader.set_float('uAlpha', self.alpha)

                # triangle
                self.edge_shader.bind_vbo()
                self.edge_shader.bind_index(self.index)

                # # draw mesh

                gl.glDrawElements(gl.GL_TRIANGLES, self.face_vertex_size, gl.GL_UNSIGNED_SHORT, None)

            return

        # normal polygon drawing path.

        # switch cull facing mode.
        if self.disable_cull_facing:
            gl.glDisable(gl.GL_CULL_FACE)
        else:
            gl.glEnable(gl.GL_CULL_FACE)

        with self.shader.drawing():

            # # bind material specific variables

            # textures
            # base texture
            self.texture.use()
            self.shader.set_int('uTexture', TextureUnit.BASE)
            # sphere texture
            self.sphere_texture.use()
            self.shader.set_int('uSphereTexture', TextureUnit.SPHERE)
            self.shader.set_float('uSphereTextureMode', self.sphere_texture_mode)
            # toon texture
            self.toon_texture.use()
            self.shader.set_int('uToonTexture', TextureUnit.TOON)
            self.shader.set_float('uIsToonTexture', self.use_toon_texture)

            # material color
            self.shader.set_vec3('uAmbientColor', self.ambient)
            self.shader.set_vec3('uSpecularColor', self.specular)
            self.shader.set_vec3('uDiffuseColor', self.diffuse)
            self.shader.set_float('uAlpha', self.alpha)
            self.shader.set_float('uShininess', self.shininess)

            # bind triangles
            self.shader.bind_vbo()
            self.shader.bind_index(self.index)

            # # draw mesh

            gl.glDrawElements(gl.GL_TRIANGLES, self.face_vertex_size, gl.GL_UNSIGNED_SHORT, None)
