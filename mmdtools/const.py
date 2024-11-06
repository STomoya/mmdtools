import os

MODULE_ROOT_DIR = os.path.dirname(__file__)
TOON_ROOT_DIR = os.path.join(MODULE_ROOT_DIR, 'toon')

_GLSL_SHADER_DIR = os.path.join(MODULE_ROOT_DIR, 'viewer', 'glsl')

GLSL_VERTEX_SHADER_SOURCE = os.path.join(_GLSL_SHADER_DIR, 'vertex_shader.glsl')
GLSL_FRAGMENT_SHADER_SOURCE = os.path.join(_GLSL_SHADER_DIR, 'fragment_shader.glsl')

GLSL_EDGE_VERTEX_SHADER_SOURCE = os.path.join(_GLSL_SHADER_DIR, 'edge_vertex_shader.glsl')
GLSL_EDGE_FRAGMENT_SHADER_SOURCE = os.path.join(_GLSL_SHADER_DIR, 'edge_fragment_shader.glsl')

GLSL_DEPTH_VERTEX_SHADER_SOURCE = os.path.join(_GLSL_SHADER_DIR, 'depth_vertex_shader.glsl')
GLSL_DEPTH_FRAGMENT_SHADER_SOURCE = os.path.join(_GLSL_SHADER_DIR, 'depth_fragment_shader.glsl')

GLSL_DEFAULT_NUM_BONES = 200
