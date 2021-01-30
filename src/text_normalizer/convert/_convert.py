"""Коллекция инструментов для конвертации данных"""

from functools import lru_cache

from ..config import RegexConfigType, PipelineConfigType, load_conf, load_regex_conf

__all__ = [
    'MONTHS_SET',
    'DIGITS',
    'text2int',
    'is_ordfold',
    'ord_unfold',
    'month2num',
    'MONTHS',
]

ORDINAL_ENDINGS_SET = {
    "ый", "ого", "му", "ым", "ом", "х", "их", "ми", "м", "и", "ум", "ю", "у", "ти", "й", "ой", "я", "ая", "ое", "е"}
MONTHS = (
    "январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь")
MONTHS_SHORT = ('янв', "фев", "мар", "апр", "май", "июнь", "июль", "авг", "сент", "окт", "ноя", "дек")
MONTHS_SET = {*MONTHS, *MONTHS_SHORT}
DIGITS = {"ноль", "единица", "двойка", "тройка", "четверка", "пятерка", "шестерка", "семерка", "восьмерка", "девятка"}

_numerics = {**load_conf(PipelineConfigType.NUMERICS), **load_conf(PipelineConfigType.ORDINALS)}
_ordfold_regx = load_regex_conf(RegexConfigType.ORDFOLD)


def text2int(*tokens: str) -> int:
    """
    Конвертирует простые, комплексные и составные русские числительные в целое число

    :param tokens: числительные в соответствующем порядке
    :raises ValueError: Если переданы не верные аргументы или аргументы переданы в неверном для числительного порядке
    :raises TypeError: Если передан не верный тип параметра


    >>> from text_normalizer.convert import text2int
    >>> text2int("Сто двадцать три тысячи пятьсот двадцать два")
    123522
    >>> text2int("один")
    1
    >>> text2int("первый")
    1
    >>> text2int("ноль")
    0
    >>> text2int("триста сорок один")
    341
    >>> text2int("сто миллионов двести сорок две тысячи пятьсот восемьдесят два")
    100242582
    """

    _mapping = _numerics

    if not tokens:
        return 0

    if len(tokens) == 1:
        token = tokens[0]

        if token not in _mapping:
            raise ValueError(f"Unknown token '{token}'")

        return _mapping[token][0]

    top_level = total = level = value = 0

    for token in tokens:

        if token not in _mapping:
            raise ValueError(f"Unknown token '{token}'")

        number, _level, is_mult = _mapping[token]

        if is_mult and not value and _level == 1:
            is_mult = False

        if is_mult:
            if top_level and top_level <= _level:
                raise ValueError("Invalid token order")

            top_level = _level
            total += number * value if value else number
            level = value = 0
        else:
            if level and level <= _level:
                raise ValueError("Invalid token order")

            level = _level
            value += number

    return total + value


def is_ordfold(text: str) -> bool:
    return _ordfold_regx.match(text) is not None


def ord_unfold(text: str) -> str:
    """
    Преобразует сокращенное порядковое числительное в целое число

    :param text:    порядковое числительное в виде {int}-{ending}, где ending in ORDINAL_ENDINGS_SET.
                    Аргумента в формате {int}{ending} будет обрабатываться дольше
    :raises ValueError: если передан неверный параметр

    >>> from text_normalizer.convert import ord_unfold
    >>> ord_unfold("1-ая")
    '1'
    >>> ord_unfold("8-ой")
    '8'
    >>> ord_unfold("8-й")
    '8'
    >>> ord_unfold("9-ый")
    '9'
    >>> ord_unfold("10-ого")
    '10'
    >>> ord_unfold("10-ом")
    '10'
    >>> ord_unfold("10-му")
    '10'
    >>> ord_unfold("123му")
    '123'
    """

    tokens = text.split('-')
    base, end = tokens if len(tokens) > 1 else (tokens[0], None)

    if end and end in ORDINAL_ENDINGS_SET:
        return base

    match = _ordfold_regx.match(text)

    if match:
        base, _ = match.groups()
        return base

    raise ValueError(f'Invalid argument {text}')


@lru_cache(maxsize=len(MONTHS))
def month2num(month_name: str) -> int:
    """
    Конвертация полного или сокращенного названия месяца в его порядковый номер в году.
    Название должно быть в нижнем регистре.

    Поддерживаемые сокращения названия месяца:
    {'янв', "фев", "мар", "апр", "май", "июнь", "июль", "авг", "сент", "окт", "ноя", "дек"}

    :param month_name: название месяца на русском языке
    :return: 0 if no month name found

    >>> from text_normalizer.convert import month2num
    >>> month2num('январь')
    '01'
    >>> month2num('декабрь')
    '12'
    >>> month2num('грустябрь')
    'грустябрь'
    0
    """
    months = zip(MONTHS_SHORT, MONTHS)
    d = {name: idx + 1 for idx, names in enumerate(months) for name in names}

    return d.get(month_name, 0)
