"""Модуль с описанием типов конфигураций дял использования в приложении"""
from enum import Enum
from typing import NamedTuple

__all__ = ['PipelineConfigType', 'RegexConfigType', 'FileConfig', 'JsonConfig', 'ReversedJson']


class PipelineConfigType(Enum):
    """Тип конфигурации для загрузки объектов пайплайна нормализации"""

    SYNONIMS = 'synonims'
    MYSTEM = 'mystem'
    REGEX = 'regex'
    NUMERICS = 'numerics'
    ORDINALS = 'ordinals'
    STOPWORDS = 'stopwords'


class RegexConfigType(Enum):
    """Тип конфигурации для загрузки регулярных выражений"""

    DATE = 'date_reg'
    TIME = 'time_reg'
    URL = 'url_reg'
    EMAIL = 'email_reg'
    ORDFOLD = 'ordfold_reg'


class FileConfig(NamedTuple):
    """Данные для загрузки конфигурации из файла"""

    path: str       #  путь к файлу
    type: Enum      #  тип конфигурации


class JsonConfig(NamedTuple):
    path: str
    type: Enum


class ReversedJson(NamedTuple):
    path: str
    type: Enum
