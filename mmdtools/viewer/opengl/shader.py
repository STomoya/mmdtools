from __future__ import annotations

import os
from contextlib import contextmanager

import numpy as np
import OpenGL.GL as gl

from mmdtools import const
from mmdtools.viewer.common.typeanno import Vector2D, Vector3D, Vector4D


class Shader:
    """Shader"""

    def __init__(
        self, vertex_shader_source: str, fragment_shader_source: str, source_keyvals: dict | None = None
    ) -> None:
        self.program: int = gl.glCreateProgram()
        self._source: dict[int, str] = {gl.GL_VERTEX_SHADER: '', gl.GL_FRAGMENT_SHADER: ''}
        self.variable_locations: dict[str, int] = {}

        if source_keyvals is None:
            source_keyvals = {
                gl.GL_VERTEX_SHADER: {'num_bones': const.GLSL_DEFAULT_NUM_BONES},
                gl.GL_FRAGMENT_SHADER: {'num_bones': const.GLSL_DEFAULT_NUM_BONES},
            }

        if not self.create_shader(gl.GL_VERTEX_SHADER, vertex_shader_source, source_keyvals[gl.GL_VERTEX_SHADER]):
            raise Exception('Vertex shader compile failed.')
        if not self.create_shader(gl.GL_FRAGMENT_SHADER, fragment_shader_source, source_keyvals[gl.GL_FRAGMENT_SHADER]):
            raise Exception('Fragment shader compile failed.')

        gl.glLinkProgram(self.program)
        if gl.glGetProgramiv(self.program, gl.GL_LINK_STATUS) == 0:
            print(gl.glGetProgramInfoLog(self.program))
            raise Exception('Program link failed.')

        # automatically find attributes and uniforms and find locations in program.
        def get_name(line):
            name = []
            for letter in line[-2::-1]:
                if letter == ' ':
                    break
                else:
                    name.append(letter)
            name = ''.join(name[::-1])
            # We skip the array declaration syntax ([N]) and only extract the variable name.
            if '[' in name:
                index = name.index('[')
                name = name[:index]
            return name

        attributes = set()
        uniforms = set()
        for line in self._source[gl.GL_VERTEX_SHADER].strip().splitlines():
            line = line.strip()
            # attribute definition starts with 'layout (location = n) in ...'
            if line.startswith(('layout ')):
                attributes.add(get_name(line))
            # uniform definition starts with 'uniform'
            elif line.startswith('uniform '):
                uniforms.add(get_name(line))
        for line in self._source[gl.GL_FRAGMENT_SHADER].strip().splitlines():
            line = line.strip()
            # fragment shader only uses uniform variables.
            if line.startswith('uniform '):
                uniforms.add(get_name(line))

        self.vbos: dict[str, dict[str, int]] = {}
        self.vbo_indices: dict[int, int] = {}
        self.vao: int = gl.glGenVertexArrays(1)

        with self.use_program(), self.bind_vao():
            for attribute in attributes:
                self.variable_locations[attribute] = gl.glGetAttribLocation(self.program, attribute)
                gl.glEnableVertexAttribArray(self.variable_locations[attribute])
            for uniform in uniforms:
                self.variable_locations[uniform] = gl.glGetUniformLocation(self.program, uniform)

    def create_shader(self, shader_type: int, shader_source: str, keyvals: dict) -> bool:
        """create shader and attach to program. `shader_type` should be either of `GL_VERTEX_SHADER` or
        `GL_FRAGMENT_SHADER`. `shader_source` can be a path to a shader program file or a str object
        containing the shader program content.

        Args:
            shader_type (int): either of `GL_VERTEX_SHADER` or `GL_FRAGMENT_SHADER`
            shader_source (str): a path to a shader program file or str object of a shader program.

        Returns:
            bool: successful compilation?

        """
        if os.path.exists(shader_source):
            # Read and format source code.
            with open(shader_source, 'r') as fp:
                source = fp.read()
            lines = source.splitlines()
            formatted_lines = []
            # Format string for declaration of arrays with adaptive length.
            # NOTE: currently supports uniform variables only.
            for index, line in enumerate(lines):
                if line.startswith('uniform'):
                    line = line.format(**keyvals)
                # skip to the end when we find the main function.
                # TODO: How can we find user defined functions? This will be much efficient.
                if 'void' in line and 'main' in line:
                    rest = '\n'.join(lines[index:])
                    break
                formatted_lines.append(line)
            # Recontruct source code.
            shader_source = '\n'.join(formatted_lines) + '\n' + rest
        self._source[shader_type] = shader_source

        shader = gl.glCreateShader(shader_type)
        gl.glShaderSource(shader, shader_source)
        gl.glCompileShader(shader)
        if gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS) == 0:
            print(gl.glGetShaderInfoLog(shader).decode())
            return False
        gl.glAttachShader(self.program, shader)
        gl.glDeleteShader(shader)
        return True

    @classmethod
    def create(cls, type: str = 'polygon') -> Shader:
        if type == 'edge':
            return cls(
                vertex_shader_source=const.GLSL_EDGE_VERTEX_SHADER_SOURCE,
                fragment_shader_source=const.GLSL_EDGE_FRAGMENT_SHADER_SOURCE,
            )
        elif type == 'polygon':
            return cls(
                vertex_shader_source=const.GLSL_VERTEX_SHADER_SOURCE,
                fragment_shader_source=const.GLSL_FRAGMENT_SHADER_SOURCE,
            )
        elif type == 'depth':
            return cls(
                vertex_shader_source=const.GLSL_DEPTH_VERTEX_SHADER_SOURCE,
                fragment_shader_source=const.GLSL_DEPTH_FRAGMENT_SHADER_SOURCE,
            )
        else:
            raise Exception(
                ('Unknown shader type. either create object using ' 'constructor or pass "polygon" or "edge" as type.')
            )

    @contextmanager
    def use_program(self):
        """bind program"""
        gl.glUseProgram(self.program)
        yield
        gl.glUseProgram(0)

    @contextmanager
    def bind_vao(self):
        """bind vao"""
        gl.glBindVertexArray(self.vao)
        yield
        gl.glBindVertexArray(0)

    @contextmanager
    def drawing(self):
        """bind program and vao. useful when drawing"""
        with self.use_program(), self.bind_vao():
            yield

    def set_int(self, name: str, value: int) -> None:
        """set int value to program.

        Args:
            name (str): name of variable inside program
            value (int): value to set

        """
        gl.glUniform1i(self.variable_locations[name], value)

    def set_float(self, name: str, value: float) -> None:
        """set float value to program.

        Args:
            name (str): name of variable inside program
            value (float): value to set

        """
        gl.glUniform1f(self.variable_locations[name], value)

    def set_vec2(self, name: str, value: Vector2D) -> None:
        """set vector of size 2 to program.

        Args:
            name (str): name of variable inside program
            value (Vector2D): value to set

        """
        gl.glUniform2fv(self.variable_locations[name], 1, value)

    def set_vec3(self, name: str, value: Vector3D) -> None:
        """set vector of size 3 to program.

        Args:
            name (str): name of variable inside program
            value (Vector3D): value to set

        """
        gl.glUniform3fv(self.variable_locations[name], 1, value)

    def set_vec4(self, name: str, value: Vector4D) -> None:
        """set vector of size 4 to program.

        Args:
            name (str): name of variable inside program
            value (Vector4D): value to set

        """
        gl.glUniform4fv(self.variable_locations[name], 1, value)

    def set_mat4(self, name: str, value: np.ndarray, elements: int = 1) -> None:
        """set 4x4 matrix to program

        Args:
            name (str): name of variable inside program
            value (np.ndarray): value to set

        """
        gl.glUniformMatrix4fv(self.variable_locations[name], elements, gl.GL_FALSE, value)

    def set_vbo(self, name: str, size: int, data: np.ndarray) -> None:
        """set array as vertex buffer object to project

        Args:
            name (str): name of variable inside program
            size (int): size of each element in list.
            data (np.ndarray): value to set

        """
        vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data.nbytes, data, gl.GL_STATIC_DRAW)
        self.vbos[name] = {'size': size, 'buffer': vbo}

    def set_index(self, name: str, face: np.ndarray) -> None:
        """set list of index for vertex buffer object.

        Args:
            name (str): id.
            face (np.ndarray): list of indices, representing the face.

        """
        vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, face.nbytes, face, gl.GL_STATIC_DRAW)
        self.vbo_indices[name] = vbo

    def bind_vbo(self) -> None:
        """bind vbo"""
        for name, vbo in self.vbos.items():
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo['buffer'])
            gl.glVertexAttribPointer(self.variable_locations[name], vbo['size'], gl.GL_FLOAT, gl.GL_FALSE, 0, None)

    def bind_index(self, name: str) -> None:
        """bind index to use.

        Args:
            name (str): id.

        """
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.vbo_indices[name])
