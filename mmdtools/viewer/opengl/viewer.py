from __future__ import annotations

import OpenGL.GL as gl

from mmdtools.viewer.common.environment import Environment
from mmdtools.viewer.common.model import Model
from mmdtools.viewer.common.motion import Motion
from mmdtools.viewer.opengl.mesh import Mesh
from mmdtools.viewer.opengl.shader import Shader


class Viewer:
    """Viewer class. Responsible for visualization.

    Args:
        model (Model): model data.
        motion (Motion): motion data. Pass `None` if no motion data.

    """

    def __init__(self, model: Model, motion: Motion) -> None:
        self.model = model
        self.motion = motion

        self.mesh: list[Mesh] = []
        self.env: Environment = Environment()

        # create shaders and set constant variables.
        self.shader = Shader.create(type='polygon')
        self.shader.set_vbo('aVertex', 3, self.model.vertex_position)
        self.shader.set_vbo('aUV', 2, self.model.vertex_uv)
        self.shader.set_vbo('aNormal', 3, self.model.vertex_normal)
        self.shader.set_vbo('aBoneIndex', 4, self.model.vertex_bone_ids)
        self.shader.set_vbo('aBoneWeights', 4, self.model.vertex_bone_weights)
        self.edge_shader = Shader.create(type='edge')
        self.edge_shader.set_vbo('aVertex', 3, self.model.vertex_position)
        self.edge_shader.set_vbo('aNormal', 3, self.model.vertex_normal)
        self.edge_shader.set_vbo('aEdgeScale', 1, self.model.vertex_edge_scale)
        self.edge_shader.set_vbo('aBoneIndex', 4, self.model.vertex_bone_ids)
        self.edge_shader.set_vbo('aBoneWeights', 4, self.model.vertex_bone_weights)

        self._create_mesh()

        self._is_polygon_mode_fill = True

    def _create_mesh(self):
        """create mesh for visulization."""
        total_face = self.model.face.copy()
        for material_index, material_data in enumerate(self.model.material_data):
            mesh_face = total_face[: material_data.face_vertex_size].copy()
            total_face = total_face[material_data.face_vertex_size :]
            mesh = Mesh(material_index, material_data, mesh_face, self.shader, self.edge_shader)
            self.mesh.append(mesh)

    def switch_polygon_mode(self):
        """switch polygon mode. If wireframe mode, switch to fill and vice versa."""
        if self._is_polygon_mode_fill:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            self._is_polygon_mode_fill = False
        else:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            self._is_polygon_mode_fill = True

    def set_variables(self):
        """set variables to shader."""
        bone_transforms = self.model.collect_bone_transforms()

        with self.shader.use_program():
            self.shader.set_vec3('uLightAmbient', self.env.light.ambient)
            self.shader.set_vec3('uLightDiffuse', self.env.light.diffuse)
            self.shader.set_vec3('uLightSpecular', self.env.light.specular)
            self.shader.set_vec3('uLightPosition', self.env.light.position)
            self.shader.set_vec3('uCameraPosition', self.env.camera.position)
            self.shader.set_mat4('uProjectionM', self.env.projection_matrix)
            self.shader.set_mat4('uModelViewM', self.env.model_view_matrix)
            self.shader.set_mat4('uITModelViewM', self.env.it_model_view_matrix)
            self.shader.set_mat4('uBoneTransform', bone_transforms, bone_transforms.shape[0])

        with self.edge_shader.use_program():
            self.edge_shader.set_mat4('uProjectionM', self.env.projection_matrix)
            self.edge_shader.set_mat4('uModelViewM', self.env.model_view_matrix)
            self.edge_shader.set_mat4('uBoneTransform', bone_transforms, bone_transforms.shape[0])

    def draw(self):
        """draw model."""
        # enable depth test
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LEQUAL)
        # enable texture
        gl.glEnable(gl.GL_TEXTURE_2D)
        # enable alpha blending
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA, gl.GL_SRC_ALPHA, gl.GL_DST_ALPHA)
        # enable multisample
        gl.glEnable(gl.GL_MULTISAMPLE)
        # enable cull facing
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glFrontFace(gl.GL_CCW)  # counter clock-wise (CCW)

        # set face culling to back for drawing polygons.
        gl.glCullFace(gl.GL_BACK)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # set variables needed for drawing.
        self.set_variables()

        for mesh in self.mesh:
            mesh.draw()

        # set cull facing to front for drawing edges.
        gl.glCullFace(gl.GL_FRONT)

        for mesh in self.mesh:
            mesh.draw(draw_edge=True)

        # diable enabled settings for further rendering (if any).
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glDisable(gl.GL_MULTISAMPLE)
        gl.glDisable(gl.GL_BLEND)
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glDisable(gl.GL_DEPTH_TEST)

    def step(self):
        """step motion."""
        if self.motion is not None:
            self.motion.step()
            self.model.update_bones()
