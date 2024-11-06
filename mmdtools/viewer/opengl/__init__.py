try:
    import glfw
    import OpenGL

    IS_OPENGL_AVAILABLE = True
except ImportError as e:
    print(e)
    IS_OPENGL_AVAILABLE = False


def is_opengl_available():
    return IS_OPENGL_AVAILABLE


if IS_OPENGL_AVAILABLE:
    from mmdtools.viewer.opengl.viewer import Viewer
    from mmdtools.viewer.opengl.window import Window
