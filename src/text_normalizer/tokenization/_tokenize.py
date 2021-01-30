"""Модуль для создания и работы с токенами"""
import logging
import re
import string
from enum import IntEnum
from functools import lru_cache
from typing import Tuple, Iterator

from nltk.corpus import stopwords
from nltk.tokenize import ToktokTokenizer
from nltk.tokenize.api import TokenizerI

from ..config import RegexConfigType, PipelineConfigType, load_regex_conf, load_conf

__all__ = [
    'sent_tokenize',
    'TokTok',
    'token_type',
    'to_token',
    'TokenType',
    'iTokenTuple',
    'russian_stopwords',
    'replace_bigrams',
    'KILO_POSTFIX',
    'init_cache',
    'cache_clear',
    'get_tokenizer'
]

logger = logging.getLogger('rtn')

# Символ, которым токенизатор будет выделять токены с "тысячным" префиксом (e.g. 5к, 5 к )
KILO_POSTFIX = '%'

russian_stopwords = stopwords.words("russian")
_spaces = string.whitespace
_punct = set(f'{string.punctuation}{"«»…=#-——–``"}{string.whitespace}')
_isolating_punct = {'"', "'", '{', '}', '[', ']', '(', ')', '«', '»'}
_synonyms = load_conf(PipelineConfigType.SYNONIMS)
_regex_time = load_regex_conf(RegexConfigType.TIME)


class TokenType(IntEnum):
    """
    Типы токенов.

    NB! IntEnum позволяет быстро проверять соответствие типа токена

    >>> TokenType.NUM == TokenType.NUM
    True
    >>> [TokenType.TXT, TokenType.PUNKT] == [TokenType.TXT, TokenType.PUNKT]
    True

    """
    NONE = 0
    TXT = 1
    PUNKT = 2
    DATE = 3
    NUM = 4
    TIME = 5
    PHONE = 6
    EMOJI = 7
    URL = 8
    EMAIL = 9
    PUNKT_ISO = 10  # изолирующая пунктуация (e.g. "", (), [] etc.)
    SPACE = 11
    CARDNUM = 12


class iTokenTuple(Tuple):
    """
    Интерфейс для создания и работы с токенами.

    NB! Данный класс НЕ следует использовать в качестве конструктора, т.к это значительно замедлит
    создание объектов. Оптимальнее - возвращать из функций, реализующих данный интерфейс, простые
    картежи с элементами нужного типа в нужном порядке.
    """
    _value: str
    _type: TokenType


class RegexTokenType:
    """
    Определитель типа токена на основе регулярных выражений.

    Проверяет совпадения токена против фиксированного списка регулярных выражений.
    Если совпадение найдено, возвращается соответствующий тип токена, иначе - специальный тип TokeType.NONE

    >>> tok_rextype = RegexTokenType()
    >>> tok_rextype('20.10.2020')
    TokenType.DATE
    >>> tok_rextype('test@gmail.com')
    TokenType.EMAIL
    >>> tok_rextype('https://pypi.org/')
    TokenType.URL

    """

    def __init__(self):
        self.regex = {
            TokenType.DATE: load_regex_conf(RegexConfigType.DATE),
            TokenType.EMAIL: load_regex_conf(RegexConfigType.EMAIL),
            TokenType.URL: load_regex_conf(RegexConfigType.URL),
            TokenType.TIME: load_regex_conf(RegexConfigType.TIME),
        }

    def __call__(self, token: str) -> TokenType:
        r = self.regex

        for key in r:
            if r[key].match(token):
                return key

        return TokenType.NONE


class TokTok(TokenizerI):
    """
    В качестве основы используется набор регулярных выражений и упрощенный алгоритм обработки строки
    из токенизатора `TokTok <https://www.nltk.org/api/nltk.tokenize.html#module-nltk.tokenize.toktok>`_.

    """
    def __init__(self):
        self._regexes = ToktokTokenizer.TOKTOK_REGEXES[:]

        self._regexes[2] = (_regex_time, r"(\1)")
        self._regexes.insert(3, (re.compile(r"(?<![а-яА-Я])([а-яА-Я]{1})(\/)([а-яА-Я]{1})"), r"\1\3 "))
        self._regexes.insert(4, (re.compile(r"(\d)(-)([а-яА-Я]+)"), r"\1\3 "))
        self._regexes.append((re.compile(r"(-«»)"), r" \1 "))
        self._regexes.append((re.compile(r"\s+(-)(\w+)"), r" \1 \2 "))
        self._regexes.append((re.compile(r"(\w+)(-)\s"), r" \1 \2 "))
        self._regexes.append((re.compile(r"(?<=[а-яА-я])([/\\])"), r" \1 "))
        self._regexes.append((re.compile(r"([=…№\-——'\s]+)(\d+)([=…№\-——'\s]+)"), r" \1 \2 \3"))
        # Выделение токенов с "тысячным" префиксом (e.g. 5к, 5 к )
        self._regexes.append((re.compile(r"(\d)\s?[кk]"), rf"{KILO_POSTFIX}\1{KILO_POSTFIX}"))
        self._regexes.append(ToktokTokenizer.FUNKY_PUNCT_2)

    def tokenize(self, text: str) -> [str]:
        for regexp, subsitution in self._regexes:
            text = regexp.sub(subsitution, text)

        text = text.strip()

        return text.split()


@lru_cache(maxsize=1)
def get_tokenizer() -> TokenizerI:
    return TokTok()


@lru_cache(maxsize=1)
def get_regex_type() -> RegexTokenType:
    return RegexTokenType()


def sent_tokenize(sentence: str, tokenizer: TokenizerI) -> Iterator[iTokenTuple]:
    """
    Создает итератор картежей с токеном и типом токена из предложения

    :param sentence: предложение
    :param tokenizer: токенизатор поддерживающий интерфейс NLTK-TokenizerI
    """

    return map(to_token, tokenizer.tokenize(sentence))


def token_type(token_string: str) -> TokenType:
    """Определить тип токена"""

    if not token_string:
        return TokenType.NONE

    if token_string in _spaces:    # "in" works faster then calling a method ' '.isspace()
        return TokenType.SPACE
    elif token_string in _isolating_punct:
        return TokenType.PUNKT_ISO
    elif token_string in _punct:
        return TokenType.PUNKT
    elif token_string.isnumeric():
        return TokenType.NUM

    rextype = get_regex_type()
    type_ = rextype(token_string)

    if type_ is not TokenType.NONE:
        return type_

    return TokenType.TXT


def to_token(token_string: str) -> iTokenTuple:
    """
    Создать токен из строки

    >>> to_token('.')
    ('.', TokenType.PUNKT)
    >>> to_token('1ый')
    ('1', TokenType.NUM)
    >>> to_token('hello@gmail.com')
    ('hello@gmail.com', TokenType.EMAIL)

    :param token_string: строка без пробелов
    """

    return token_string, token_type(token_string)


def replace_bigrams(tokens: Iterator[iTokenTuple]) -> Iterator[iTokenTuple]:
    """
    Заменить биграммы на токены из словаря.
    Служит для быстрой замены токенов вроде "когда то" на "когда-то", а также прочих биграмм.

    >>> from text_normalizer.tokenization import replace_bigrams
    >>> replace_bigrams(iter(['окко', TokenType.TXT), ('тв', TokenType.TXT)]))
    ('окко-тв', TokenType.TXT)
    """

    crnt = None
    buffer = []

    for token, _type in tokens:
        crnt, prev = token, crnt

        synonym = _synonyms.get(f'{crnt}', crnt)

        if prev:
            bigram = _synonyms.get(f'{prev} {crnt}')

            if bigram:
                buffer[-1] = (bigram, _type)
                continue

        buffer.append((synonym, _type))

    yield from buffer


def init_cache():
    get_regex_type()
    get_tokenizer()
    logger.debug('Cache initiated')


def cache_clear():
    get_regex_type.cache_clear()
    get_tokenizer.cache_clear()
    logger.debug('Cache cleared')
