import argparse
from mmdtools.io import load_model
from mmdtools.io.vmd import load as load_motion
from mmdtools.viewer import Model
from mmdtools.viewer import Motion
from mmdtools.viewer.opengl import Viewer
from mmdtools.viewer.opengl import Window


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('model', type=str, help='Path to PMX file.')
    parser.add_argument('--vmd', type=str, help='Path to VMD file.')
    parser.add_argument('--frames', type=int, help='Number of frames to render.')
    return parser.parse_args()


def main():
    args = get_args()

    model_data = load_model(args.model, raw=False)
    model = Model(model_data)

    if args.vmd is not None:
        motion_data = load_motion(args.vmd)
        motion = Motion(model, motion_data)
    else:
        motion = None
        args.frames = 1

    window = Window(512, 512)
    viewer = Viewer(model, motion)

    viewer.env.set_camera(position=[0.0, 11.0, -30.0], target=[0.0, 11.0, 0.0])

    images = []
    while not motion.finished() and len(images) < args.frames:
        viewer.step()

        window.before_render()
        viewer.draw()
        window.after_render()

        images.append(window.read_pixels())
        print(len(images))

    if len(images) > 1:
        images[1].save('./mmdviewer.gif', save_all=True, append_images=images[2:],
            optimize=False, duration=10, loop=0
        )
    else:
        images[0].save('mmdviewer.png')

    window.close()


if __name__ == '__main__':
    main()
