"""Модуль диспетчеризации загрузки конфигураций"""

import json
from functools import singledispatch

from ._types import JsonConfig, FileConfig, ReversedJson

__all__ = ['dispatcher']


@singledispatch
def dispatcher(_):
    """
    Диспетчер функций-загрузчиков конфигураций. В зависимости от типа переданного параметра, передает вызов
    в одну из зарегистрированных функций.
    """
    raise ValueError('Config not found')


@dispatcher.register(JsonConfig)
def load_json_config(data: JsonConfig) -> dict:
    """Загружает конфигурацию из файла json"""
    with open(data.path, encoding='utf=8') as f:
        _data = json.load(f)

    return _data


@dispatcher.register(ReversedJson)
def load_rev_json_config(data: ReversedJson) -> dict:
    """
    Загружает конфигурацию из файла-json и предварительно меняет
    местами ключи и значения в полученном словаре
    """
    _data = load_json_config(data)
    return {v: k for k, values in _data.items() for v in values}


@dispatcher.register(FileConfig)
def load_file_config(data: FileConfig) -> list:
    with open(data.path, encoding='utf=8') as f:
        return f.read().split()
