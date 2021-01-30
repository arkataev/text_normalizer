"""Пакет для проведения и обработки результатов морфологического анализа токенов"""
import os
from ..settings import DATA_PATH


if not os.environ.get("MYSTEM_BIN", None):
    MYSTEM_DIR = os.path.join(DATA_PATH, 'mystem_files')
    MYSTEM_PATH = os.path.join(MYSTEM_DIR, 'mystem')
    os.environ["MYSTEM3_PATH"] = os.environ.setdefault("MYSTEM3_PATH", MYSTEM_PATH)


    if not os.path.isfile(MYSTEM_PATH) or not os.access(MYSTEM_PATH, os.X_OK):
        if not os.path.isfile(MYSTEM_PATH) or not os.access(MYSTEM_PATH, os.X_OK):
            from ._utils import install
            install(MYSTEM_DIR)


from ._mystem import *
from ._processing import *


def init_cache():
    from ._mystem import init_cache
    init_cache()


def cache_clear():
    from ._mystem import cache_clear
    cache_clear()
