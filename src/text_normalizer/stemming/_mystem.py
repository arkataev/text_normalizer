"""Модуль для лемматизации и морфологического анализа токенов с помощью MyStem"""

import errno
import json
import logging
import os
from contextlib import contextmanager
from enum import Enum
from functools import lru_cache
from itertools import chain
from typing import Iterator, Tuple, Mapping, List, Dict, Any

from pymystem3 import Mystem

from ..config import PipelineConfigType, load_conf
from ..settings import DATA_PATH
from ..tokenization import TokenType, token_type, iTokenTuple

__all__ = [
    'stems_gen',
    'jstem_inst',
    'jstem_ctx',
    'to_dict',
    'to_tuple',
    'iStemTuple',
    'POS',
    'JsonStemmer',
]

logger = logging.getLogger('rtn')

_numerics = load_conf(PipelineConfigType.NUMERICS)
_stem_conf = load_conf(PipelineConfigType.MYSTEM)

"""
Граммемная информация
см. https://yandex.ru/dev/mystem/doc/grammemes-values.html
"""


class POS(Enum):
    """Part of Speech"""
    A = 'A'
    ADV = 'ADV'
    ADVPRO = 'ADVPRO'
    ANUM = "ANUM"
    APRO = 'APRO'
    COM = 'COM'
    CONJ = 'CONJ'
    INTJ = 'INTJ'
    NUM = 'NUM'
    PART = 'PART'
    PR = 'PR'
    S = 'S'
    SPRO = 'SPRO'
    V = 'V'


class VerbTence(Enum):

    PRAES = "наст"
    INPRAES = "непрош"
    PRAET = "прош"


class Gender(Enum):
    M = "муж"
    F = "жен"
    N = "сред"


class Animacy(Enum):
    ANIM = "од"
    INANIM = "неод"


class Case(Enum):
    NOM = "им"
    GEN = "род"
    DAT = "дат"
    ACC = "вин"
    INS = "твор"
    ABL = "пр"
    PART = "парт"
    LOC = "местн"
    VOC = "зват"


class Number(Enum):
    SG = "ед"
    PL = "мн"


class VerbMood(Enum):
    GER = "деепр"
    INF = "инф"
    PARTCP = "прич"
    INDIC = "изъяв"
    IMPER = "пов"


class VerbPerson(Enum):
    P_1 = "1-л"
    P_2 = "2-л"
    P_3 = "3-л"


class VerbAspect(Enum):
    IPF = "несов"
    PF = "сов"


class VerbVoice(Enum):
    ACT = "действ"
    PASS = "страд"


class VerbTransit(Enum):
    TRAN = "пе"
    INTR = "нп"


class AdjForm(Enum):
    BREV = "кр"
    PLEN = "полн"
    POSS = "притяж"


class CompDegree(Enum):
    SUPR = "прев"
    COMP = "срав"


class OtherGrammem(Enum):
    PARENTH = "вводн"
    GEO = "гео"
    AWKW = "затр"
    PERSN = "имя"
    DIST = "искаж"
    MF = "мж"
    OBSC = "обсц"
    PATRN = "отч"
    PRAED = "прдк"
    INFORM = "разг"
    RARE = "редк"
    ABBR = "сокр"
    OBSOL = "устар"
    FAMN = "фам"


class Ambiguous(Enum):
    AMBIGOUS = ""


class iStemTuple(Tuple):
    """
    Интерфейс для построения пайплайна обработки результата морфологического анализа

    NB! Данный класс НЕ следует использовать в качестве конструктора, т.к это значительно замедлит
    создание объектов. Оптимальнее - возвращать из функций, реализующих данный интерфейс, простые
    картежи с элементами нужного типа в нужном порядке.
    """

    _token:      iTokenTuple
    _lemma:      str
    _grammem:    Mapping
    _qual:       bool


class Stemmer(Mystem):
    """Интерфейс для работы с морфологическим анализатором Mystem"""

    def __init__(self, fixlist_file: str = None, **kwargs):
        """
        Используйте команду /usr/local/bin/mystem --help чтобы получить полезную информацию
        о параметрах настройки поддерживаемых утилитой mystem

        :param fixlist_file: путь к файлу с пользовательскими граммемами
        """

        super().__init__(**kwargs)

        if fixlist_file:
            if os.path.exists(fixlist_file):
                self._mystemargs.append('--fixlist')
                self._mystemargs.append(fixlist_file)
            else:
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), fixlist_file)

    def stop(self):
        logger.debug('Stopping MyStem...')
        super().close()
        assert self._proc is None, 'MyStem did not close'
        logger.debug('MyStem stopped')


class JsonStemmer(Stemmer):
    """Реализация морфологического анализатора для работы со списком токенов"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mystemargs.append("--input-format")
        self._mystemargs.append("json")

    def analyze(self, tokens: Iterator[str]) -> List[dict]:
        """Получить результат морфологического разбора списка токенов"""

        tokens_json = json.dumps([{"analysis": [], "text": t} for t in tokens]).encode("utf-8")

        return self._analyze_impl(tokens_json)


def jstem_inst() -> JsonStemmer:
    """Получить экземпляр json-стеммера"""
    return JsonStemmer(
        fixlist_file=os.path.join(DATA_PATH, _stem_conf['fixlist_file']),
        weight=False
    )


@contextmanager
def jstem_ctx() -> JsonStemmer:
    """
    Контекстный менеджер для работы с JsonStemmer.

    В начале работы стеммер запускает отдельный процесс c утилитой `mystem`.
    Контекстный менеджер поможет освободить выделенные при этом ресурсы::

        with jstem_ctx() as stem:
            result = stem.analize(tokens)
            # do smth with result

    """
    stem = jstem_inst()
    logger.debug('Starting Mystem...')
    stem.start()
    logger.debug('MyStem Ready')
    try:
        yield stem
    finally:
        stem.stop()


def stems_gen(analysis_result: Iterator[dict]) -> Iterator[iStemTuple]:
    """
    Преобразует результ морфологического разбора MyStem в итератор картежей.

    Создание картежей происходит быстрее (иногда на порядок), чем других часто используемых структур данных
    вроде списков или словарей. Рекомендуется использовать картежи при построении
    пайплайна обработки результатов анализа и конвертировать в другие структуры данных как можно позднее.

    :param analysis_result: результ морфологического разбора MyStem

    """

    for d in analysis_result:
        if 'analysis' in d and 'text' in d:
            analysis, text = d['analysis'], d['text']

            if not analysis:
                # Анализ не будет проведен если семантика токена неопределена
                t = (text, token_type(text))

                yield t, '', None, True
            else:
                t = (text, TokenType.TXT)
                lemma = analysis[0]['lex']
                grammem = dict(_parse_mystem_grammem(analysis[0]['gr']))

                # уточнение части речи для некоторых числительных (e.g. единица, сотня, тысяча)
                if grammem[POS] != POS.NUM and lemma in _numerics:
                    grammem[POS] = POS.NUM

                qual = False if 'qual' in analysis[0] else True

                yield t, lemma, grammem, qual


def to_dict(stem_tuple: iStemTuple) -> Dict[str, Any]:
    """
    Конвертирует картеж с данными морф.анализа в словарь.

    Служит реализацией интерфейса для более удобной сериализации.
    Все функции реализующие этапы пайплайна используют картежи так как эту структуру
    можно значительно быстрее создавать и получать доступ к ее данным.

    """
    grammem_data = stem_tuple[2] or {}
    grammem_keys_types = (
        ('pos', POS),
        ('gender', Gender),
        ('animacy', Animacy),
        ('case', Case),
        ('number', Number),
        ('verb_tence', VerbTence),
        ('verb_mood', VerbMood),
        ('verb_person', VerbPerson),
        ('verb_aspect', VerbAspect),
        ('verb_voice', VerbVoice),
        ('verb_transit', VerbTransit),
        ('comp_degree', CompDegree),
        ('adj_form', AdjForm),
        ('other_grammem', OtherGrammem),
        ('ambiguous', Ambiguous)
    )

    return {
        'token': f'{stem_tuple[0][0]}',
        'lemma': f'{stem_tuple[1]}',
        'grammem': {k: getattr(grammem_data[v], 'value', grammem_data[v])
                    for k, v in grammem_keys_types if v in grammem_data},
        'qual': stem_tuple[3]
    }


def to_tuple(stem_tuple: iStemTuple) -> tuple:
    """
    Служит реализацией интерфейса для более удобной сериализации.
    Все функции реализующие этапы пайплайна используют картежи так как эту структуру
    можно значительно быстрее создавать и получать доступ к ее данным.

    """
    grammem_data = stem_tuple[2] or {}
    grammem_keys_types = (
        ('pos', POS),
        ('gender', Gender),
        ('animacy', Animacy),
        ('case', Case),
        ('number', Number),
        ('verb_tence', VerbTence),
        ('verb_mood', VerbMood),
        ('verb_person', VerbPerson),
        ('verb_aspect', VerbAspect),
        ('verb_voice', VerbVoice),
        ('verb_transit', VerbTransit),
        ('comp_degree', CompDegree),
        ('adj_form', AdjForm),
        ('other_grammem', OtherGrammem),
        ('ambiguous', Ambiguous)
    )

    return (
        f'{stem_tuple[0][0]}',
        f'{stem_tuple[1]}',
        tuple((k, getattr(grammem_data[v], 'value', grammem_data[v]))
              for k, v in grammem_keys_types if v in grammem_data),
        stem_tuple[3]
    )


_grammems = (
    Case, POS, VerbTence, Gender, Animacy, Number, VerbMood, VerbPerson, VerbAspect, VerbVoice, VerbTransit, AdjForm,
    CompDegree, OtherGrammem)
gramm_rev_dict = dict(chain(*map(lambda e: ((attr.value, attr) for attr in e), _grammems)))


def init_cache():
    list(map(_decode_grammem_part, gramm_rev_dict))
    logger.debug('Cache initiated')


def cache_clear():
    _decode_grammem_part.cache_clear()
    logger.debug('Cache cleared')


def _parse_mystem_grammem(mystem_grammem_str: str) -> Iterator[tuple]:
    if not mystem_grammem_str:
        return

    main, extra = mystem_grammem_str.split('=')

    if ',' not in main:
        yield POS, getattr(POS, main, None)
    else:
        yield from map(_decode_grammem_part, main.split(','))

    if extra:
        if extra[0] == '(':
            yield Ambiguous, extra
        else:
            yield from map(_decode_grammem_part, extra.split(','))

    yield 'raw', mystem_grammem_str


@lru_cache(maxsize=len(gramm_rev_dict))
def _decode_grammem_part(grammem_part: str):
    grammem = gramm_rev_dict.get(grammem_part, None)
    return type(grammem), grammem
