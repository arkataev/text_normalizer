"""Модуль для загрузки различных типов конфигураций"""

import logging
from enum import Enum
from functools import lru_cache
from os import path
from re import compile
from typing import Tuple, Callable, Any

from ._load import dispatcher
from ._types import *
from ..settings import DATA_PATH

__all__ = ['CONFIGS_DATA', 'load_regex_conf', 'load_conf', 'cache_clear', 'dispatcher', 'init_cache']

logger = logging.getLogger('rtn')


CONFIGS_DATA = (
    JsonConfig(path.join(DATA_PATH, "regex.json"), PipelineConfigType.REGEX),
    JsonConfig(path.join(DATA_PATH, "numerics.json"), PipelineConfigType.NUMERICS),
    JsonConfig(path.join(DATA_PATH, "ordinals.json"), PipelineConfigType.ORDINALS),
    ReversedJson(path.join(DATA_PATH, "dict_synonyms.json"), PipelineConfigType.SYNONIMS),
    JsonConfig(path.join(DATA_PATH, "mystem_parameters.json"), PipelineConfigType.MYSTEM),
    FileConfig(path.join(DATA_PATH, "stopwords.txt"), PipelineConfigType.STOPWORDS),
)


@lru_cache()
def load_regex_conf(conf_type: RegexConfigType):
    """
    Кэшируемый загрузчик прекомпилированных объектов регулярных выражений

    :param conf_type: Тип конфигурации, которую требуется загрузить
    """
    regex_data = load_conf(PipelineConfigType.REGEX)
    compiled = {getattr(RegexConfigType, key): compile(val) for key, val in regex_data.items()}

    return compiled[conf_type]


@lru_cache()
def load_conf(
        conf_type: Enum,
        conf_data: Tuple[str, FileConfig] = CONFIGS_DATA,
        load_func: Callable[[FileConfig], Any] = dispatcher
):
    """
    Универсальный кэшируемый загрузчик конфигураций::

        from config import PipelineConfigType
        numerics_config = load_conf(PipelineConfigType.NUMERICS)

    :param conf_type:  Тип конфигурации, которую требуется загрузить
    :param conf_data:  Данные конфигураций
    :param load_func:  функция-загрузчик конфигураций
    """
    confd = {d.type: d for d in conf_data}
    config = confd[conf_type]
    data = load_func(config)

    return data


def init_cache():
    list(map(load_conf, PipelineConfigType))
    list(map(load_regex_conf, RegexConfigType))
    logger.debug('Cache initiated')


def cache_clear():
    load_conf.cache_clear()
    load_regex_conf.cache_clear()
    logger.debug('Cache cleared')
