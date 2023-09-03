from mmdtools.viewer.opengl.window import Window
from mmdtools.viewer.opengl.viewer import Viewer

try:
    import OpenGL
    IS_OPENGL_AVAILABLE = True
except ImportError as e:
    print(e)
    IS_OPENGL_AVAILABLE = False


def is_opengl_available(): return IS_OPENGL_AVAILABLE
