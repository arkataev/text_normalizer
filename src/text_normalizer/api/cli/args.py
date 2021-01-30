from argparse import ArgumentParser
from collections import namedtuple

from text_normalizer.stemming import Pipeline

__all__ = ['parse_normalization_args']


NormalizationArgs = namedtuple('NormalizationArgs', ['sentence', 'fmt', *[p.value for p in Pipeline]])

PIPELINE_ARGS = {
    Pipeline.WORD2NUM: 'Конвертация имен числительных в числа и цифры',
    Pipeline.ORD_UNFOLD: 'Конвертация сокращенных порядковых числительных в число (e.g. "N[-][е,му,го ...] -> N")',
    Pipeline.MAKE_DATE: 'Преобразование текстовых дат',
    Pipeline.KILO: 'Конвертация цифр и чисел с тысячным постфиксом (e.g 5к - 5000)',
    Pipeline.CCN: 'Выделение номеров кредитных карт',
    Pipeline.STOPWORDS: 'Фильтрация стоп-слов'
}


def parse_normalization_args(args=None) -> NormalizationArgs:
    """Парсинг аргументов из командной строки"""
    parser = ArgumentParser()

    assert len(PIPELINE_ARGS) == len(Pipeline), 'Inconsistent cli arguments description'

    for p in PIPELINE_ARGS:
        parser.add_argument(f'--{p.value}', action="store_true", help=PIPELINE_ARGS[p])

    parser.add_argument('--all', action='store_true', help='Применить все опции пайплайна')
    parser.add_argument('--fmt', type=str, default='tuple', choices=['dict', 'tuple'], help='Форматирование результата')
    parser.add_argument('sentence', type=str, default='', nargs='?', help='Строка для нормализации')

    ns = parser.parse_args(args)

    pipeline_args = [getattr(ns, el.value) for el in Pipeline]
    # если передан какой-либо из аргументов пайплайна, то используем только его
    # иначе весь пайплайн считается активным
    all_pipeline = False if any(pipeline_args) else ns.all
    pipeline_args = [True] * len(Pipeline) if all_pipeline else pipeline_args

    return NormalizationArgs(ns.sentence, ns.fmt, *pipeline_args)
