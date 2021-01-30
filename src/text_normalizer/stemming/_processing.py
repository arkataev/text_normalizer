"""
Модуль для обработки результатов лемматизации и морфологического анализа

## ВАЖНО!
При добавлении новых функций пайплайна в модуль важно придерживать следующего паттерна именования функций:
    PIPE_PREFIX[имя_функции]
"""
from enum import Enum
from functools import reduce
from typing import Iterator, Callable, Sequence

from ._mystem import iStemTuple, stems_gen, POS
from ..config import PipelineConfigType, load_conf
from ..convert import text2int, MONTHS_SET, month2num, is_ordfold, ord_unfold, DIGITS
from ..tokenization import TokenType, russian_stopwords, KILO_POSTFIX

__all__ = [
    'pipe_makedate',
    'pipe_word2num',
    'pipe_kilo_postfix',
    'pipe_ord_unfold',
    'pipeline',
    'pipe_stopwords',
    'pipe_merge_ccn',
    'Pipeline',
    'PIPE_PREFIX'
]

PIPE_PREFIX = 'pipe_'

# функция возвращает изменяемый объект, который могут использовать другие части приложения
# поэтому используется копия объекта, а не ссылка
_numerics = load_conf(PipelineConfigType.NUMERICS).copy()
_numerics.update(load_conf(PipelineConfigType.ORDINALS))


class Pipeline(Enum):
    """
    Перечень наименований функций пайплайна обработки результатов морфологического анализа.
    Объект используется для динамического построения пайплайнов на основе функций данного модуля.

    NB! При добавлени новой функции-пайплайна в модуль необходимо также добавить ее наименование в этот объект
    иначе она не будет учавствовать в процедурах построения пайплайна.

    Значение атрибутов должно соответствовать части имени фунции после 'pipe_'::
        'pipe_word2num' -> 'word2num'

    """
    WORD2NUM = 'word2num'
    ORD_UNFOLD = 'ord_unfold'
    MAKE_DATE = 'makedate'
    KILO = 'kilo_postfix'
    CCN = 'merge_ccn'
    STOPWORDS = 'stopwords'


def pipeline(
        analysis_result: Iterator[dict],
        pipe: Sequence[Callable[[Iterator[iStemTuple]], Iterator[iStemTuple]]] = ()
) -> Iterator[iStemTuple]:
    """
    Создание пайплайна для обработки результатов морфологического анализа Mystem.
    Используйте параметр `pipe` для добавления последовательных этапов обработки::

        pipe = [foo, bar, baz]
        pl = pipeline([
            {'analysis': [{'lex': 'мама', 'gr': 'S,жен,од=им,ед'}], 'text': 'мама'}
        ], pipe)

        # или

        from functools import partial

        pipeline = partial(pipeline, pipe=[foo, bar, baz])
        pl = pipeline([{'analysis': [{'lex': 'мама', 'gr': 'S,жен,од=им,ед'}], 'text': 'мама'}])

        for result in pl:
            # do smth with result

    Каждая функция в списке параметра `pipe` будет вызвана в порядке добавления в список. При этом
    результат работы первой функции станет аргументом для работы остальных функций в списке.

    :param analysis_result: результ морфологического разбора MyStem
    :param pipe: список callable-объектов с указанным интерфейсом
    """
    yield from _pipeline(stems_gen(analysis_result), *pipe)


def pipe_word2num(
        stems: Iterator[iStemTuple],
        convert: Callable[[Sequence[str]], int] = text2int
) -> Iterator[iStemTuple]:
    """
    Заменяет в токенах простые и комплексные числительные на целое число (int)
    или строковую последовательность чисел (str).

    :param stems: итератор результатов морфологического разбора
    :param convert: функция для конверации строки в число
    """

    num_pos = {POS.NUM, POS.ANUM}  # numerical part of speech
    # данные числа находятся на одном уровне с цифрами и требуют исключительного определения
    ambigous_level_nums = {11, 12, 13, 14, 15, 16, 17, 18, 19}
    last_level = 1
    _num_buffer = []
    append = _num_buffer.append  # небольшая оптимизация, для ускорения вызова метода в цикле

    def num_buffer():
        _num = convert(*(_s[1] for _s in _num_buffer))
        yield (f'{_num}', TokenType.NUM), _num, grammem, qual

    for s in stems:
        token, lemma, grammem, qual = s
        pos = grammem[POS] if grammem else None  # part of speech

        if pos in num_pos and lemma in _numerics:
            num_value, current_level, is_mult = _numerics[lemma]

            if _num_buffer:

                if token[0] in DIGITS:
                    yield from num_buffer()
                    _num_buffer.clear()

                elif lemma in DIGITS:
                    # Если лемма - это цифра
                    # нужно выдать строку - последовательность лемм
                    # длиной равную последнему добавленному в буфер числу
                    last_added = _num_buffer.pop()

                    if _num_buffer:
                        yield from num_buffer()
                        _num_buffer.clear()

                    length = convert(last_added[1])
                    num = f'{convert(s[1])}' * length  # "3" * 3 -> "333"

                    yield (num, TokenType.NUM), num, grammem, qual
                    continue

                elif (current_level >= last_level
                      or (last_level == 2 and num_value in ambigous_level_nums)) and not is_mult:
                    yield from num_buffer()
                    _num_buffer.clear()

            append(s)
            last_level = current_level
            continue
        else:
            if _num_buffer:
                yield from num_buffer()
                _num_buffer.clear()
        yield s

    if _num_buffer:
        yield from num_buffer()


def pipe_makedate(stems: Iterator[iStemTuple]) -> Iterator[iStemTuple]:
    """
    Собирает из подходящих токенов, токен с датой в формате %d.%m.%Y (e.g. 22 июня 2020 -> 22.06.2020)

    NB! Для конвертации числительных в число можно использовать `pipe_word2num`
    (e.g. первое января две тысячи двадцатого года -> 1.01.2020 года)

    Функция работает только с числовыми токенами и не производит конвертаций, поэтому ее следует
    использовать ПОСЛЕ функций конвертации строк в числа

    :param stems: итератор результатов морфологического разбора

    """

    _date_buffer = []
    date_token_type, numtoken_type = TokenType.DATE, TokenType.NUM

    def date_buffer():
        if len(_date_buffer) != 3:
            yield from _date_buffer
        else:
            day, month, year = [_s[1] or _s[0][0] for _s in _date_buffer]
            _month = month2num(month)

            if not _month:
                yield from _date_buffer
            else:
                month = f'{_month}'.zfill(2)
                _date_str = f'{day}.{month}.{year}'

                yield (_date_str, date_token_type), '', grammem, qual

    for s in stems:
        token, lemma, grammem, qual = s

        if token[1] is date_token_type:
            yield (token[0], date_token_type), '', None, qual
            continue

        if token[1] is numtoken_type or lemma in MONTHS_SET:
            _date_buffer.append(s)
            continue

        if _date_buffer:
            yield from date_buffer()
            _date_buffer = []

        yield s

    if _date_buffer:
        yield from date_buffer()


def pipe_ord_unfold(stems: Iterator[iStemTuple]) -> Iterator[iStemTuple]:
    """
    Преобразует токены с краткой записью порядкового числительного в токены с целым числом. (e.g. 1ый/1-ый -> 1)

    :param stems: итератор результатов морфологического разбора

    """

    for s in stems:
        token, lemma, grammem, qual = s
        token_val, t_type = token
        pos = grammem[POS] if grammem else None

        if not pos and t_type == TokenType.TXT and not lemma:
            if is_ordfold(token_val):
                token_val = ord_unfold(token_val)

        yield (token_val, t_type), lemma, grammem, qual


def pipe_kilo_postfix(stems: Iterator[iStemTuple]) -> Iterator[iStemTuple]:
    """Замена токенов с "тысячным" постфиксом на целое число (e.g. 5к -> 5000)"""

    for s in stems:
        token, type_ = s[0]

        if type_ == TokenType.TXT and token[0] == token[-1] == KILO_POSTFIX:
            yield (token.strip(KILO_POSTFIX).ljust(4, '0'), TokenType.NUM), s[1], s[2], s[3]
        else:
            yield s


def pipe_stopwords(stems: Iterator[iStemTuple]) -> Iterator[iStemTuple]:
    """Фильтрация токенов со стоп-словами"""
    yield from filter(lambda stem: stem[1] not in russian_stopwords, stems)


def pipe_merge_ccn(stems: Iterator[iStemTuple]) -> Iterator[iStemTuple]:
    """
    Создание токена с типом Кредитная Карта.
    Любая последовательность из 16 цифр объединяется в один токен.

    NB! Валидация номера карты не происходит. В токене может быть любая последовательность цифр.
    Гарантируется только их количество - 16.

    Функция работает только с числовыми токенами и не производит конвертаций, поэтому ее следует
    использовать ПОСЛЕ функций конвертации строк в числа

    """

    _buffer = []
    buffer_len = 0
    append = _buffer.append

    def buffer():
        if buffer_len == 16:
            yield (''.join(_s[0][0] for _s in _buffer), TokenType.CARDNUM), '', None, True
            _buffer.clear()
        else:
            yield from _buffer
            _buffer.clear()

    for s in stems:
        token = s[0]

        if buffer_len < 16 and token[1] == TokenType.NUM:
            append(s)
            buffer_len += len(token[0])
        else:
            if _buffer:
                yield from buffer()
                buffer_len = 0
            yield s

    if _buffer:
        yield from buffer()


def _pipeline(
        stems: Iterator[iStemTuple],
        *pipe: Callable[[Iterator[iStemTuple]], Iterator[iStemTuple]]
) -> Iterator[iStemTuple]:
    if not pipe:
        yield from stems
    else:
        yield from reduce(lambda result, func: func(result), pipe[1:], pipe[0](stems))
