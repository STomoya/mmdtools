import os

from mmdtools import core
from mmdtools.io.pmx import load as load_pmx


def load_model(model_path: str, raw: bool = True) -> core.pmx.Model | core.mmd.Model:
    ext = os.path.splitext(os.path.basename(model_path))[-1].lower()

    if ext == '.pmx':
        model = load_pmx(model_path)
        if not raw:
            model = core.mmd.from_pmx(model)
    else:
        raise Exception(f'File format "{ext}" not supprted.')

    return model
