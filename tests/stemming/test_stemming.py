import json
import os
from functools import partial
from random import shuffle

import pytest

from text_normalizer import stemming
from text_normalizer.stemming import _mystem as ms
from text_normalizer.tokenization import KILO_POSTFIX, TokenType
from ..settings import TESTS_PATH

with open(os.path.join(TESTS_PATH, 'stemming/data/word2num.json'), encoding='utf=8') as f:
    word2num_ds = json.load(f)


@pytest.mark.parametrize('inp, outp', word2num_ds.items(), ids=word2num_ds.values())
def test_convert_folded_and_full_numerics_to_numbers(inp, outp, analize):
    """Конвертация полных и сокращенных числительных в числа"""

    analysis_result = analize(inp)
    pl = stemming.pipeline(analysis_result, pipe=[stemming.pipe_ord_unfold, stemming.pipe_word2num])

    assert ' '.join(str(s[0][0]) for s in pl) == outp


@pytest.mark.parametrize('inp, outp', [
    ('22 августа 2020', '22.08.2020'),
    ('22 января 2021', '22.01.2021'),
    ('22 января', '22 января'),
    ('22', '22'),
    ('10 часов 18 января 2020 года', '10 часов 18.01.2020 года'),
    ('22 сент 2021', "22.09.2021"),
    ('22.08.2020', '22.08.2020'),
    ('22.08', '22.08'),
    ('6 100 7', '6 100 7'),
])
def test_make_date(inp, outp, analize):
    """Создание токена с датой"""

    analysis_result = analize(inp)
    pipe = stemming.pipe_makedate(stemming.stems_gen(analysis_result))
    assert ' '.join(s[0][0] for s in pipe).strip() == outp


@pytest.mark.parametrize('inp, outp', [
    ('назначь встречу на десятое октября', "назначь встречу на 10 октября"),
    ('дата 22.08.2020', 'дата 22.08.2020'),
    ('22.08.2020 дата', '22.08.2020 дата'),
    ('двадцать второе августа две тысячи двадцать второго года', '22.08.2022 года'),
    ('назначь встречу на 10 часов', "назначь встречу на 10 часов"),
    ('десять часов до первого января нового года', "10 часов до 1 января нового года"),
    ('назначь встречу на десятое октября две тысячи двадцать первого и отмени предыдущую',
     "назначь встречу на 10.10.2021 и отмени предыдущую"),
    ('22/08/2020', '22/08/2020'),
    ('22 января 2020', '22.01.2020'),
    ('привет январь', 'привет январь'),
])
def test_convert_numerics_and_make_date(inp, outp, analize):
    """Создание даты с предварительной конвертацией числительных"""

    analysis_result = analize(inp)
    pl = stemming.pipeline(analysis_result, pipe=[stemming.pipe_word2num, stemming.pipe_makedate])

    assert ' '.join(s[0][0] for s in pl) == outp


@pytest.mark.parametrize('inp, outp', [
    ('кто этот гражданин', "гражданин"),
    ("Что ж такого? Это все потому, что понедельник!", "? Это , понедельник !"),
    ("Когда уже вы придете?", "придете ?")
])
def test_remove_stopwords(jstem, inp, outp, analize):
    """Фильтрация токенов со стоп-словами"""

    analysis_result = analize(inp)
    pipe = stemming.pipe_stopwords(stemming.stems_gen(analysis_result))

    assert ' '.join(s[0][0] for s in pipe) == outp


@pytest.mark.parametrize('inp, outp', [
    ("доширак", ('доширак', 'доширак', ms.POS.S, False)),
    ("-", ('-', '', None, True)),
    ("друзей", ("друзей", "друг", ms.POS.S, True)),
    ("1", ('1', '', None, True)),
    ("тысяча", ('тысяча', 'тысяча', ms.POS.NUM, True)),
    ("единица", ('единица', 'единица', ms.POS.NUM, True)),
    ("dsdsfdfd", ('dsdsfdfd', '', None, True)),
    ("20.10.2020", ('20.10.2020', '', None, True)),
    ("79991239809", ('79991239809', '', None, True)),
    ("второй", ('второй', 'второй', ms.POS.ANUM, True)),
])
def test_create_stems_from_mystem_analysis(inp, outp, jstem):
    """Процессинг результатов морфологического анализа и создание структуры данных для пайплайна"""
    analysis_result = jstem.analyze([inp])
    stems = stemming.stems_gen(analysis_result)
    stem = next(stems)
    token = stem[0]
    lemma = stem[1]
    grammem = stem[2]
    qual = stem[3]

    assert token[0] == outp[0]
    assert lemma == outp[1]
    assert qual == outp[3]

    if grammem:
        assert grammem[ms.POS] == outp[2]


@pytest.mark.parametrize('inp, outp', [
    ('', ()),
    ('S,сокр=(пр,мн|пр,ед|вин,мн|вин,ед|дат,мн|дат,ед|род,мн|род,ед|твор,мн|твор,ед|им,мн|им,ед)',
     (ms.POS.S,
      ms.OtherGrammem.ABBR,
      "(пр,мн|пр,ед|вин,мн|вин,ед|дат,мн|дат,ед|род,мн|род,ед|твор,мн|твор,ед|им,мн|им,ед)"
      )
     ),
    ('S,жен,неод=(вин,мн|род,ед|им,мн)',
     (ms.POS.S, ms.Gender.F, ms.Animacy.INANIM, "(вин,мн|род,ед|им,мн)")),
    ('S,мн,неод=пр',
     (ms.POS.S, ms.Number.PL, ms.Animacy.INANIM, ms.Case.ABL)
     ),
    ('V,несов,нп=непрош,ед,изъяв,3-л',
     (ms.POS.V,
      ms.VerbAspect.IPF,
      ms.VerbTransit.INTR,
      ms.VerbTence.INPRAES,
      ms.Number.SG,
      ms.VerbMood.INDIC,
      ms.VerbPerson.P_3)
     ),
    ('S,муж,неод=(вин,ед|им,ед)',
     (ms.POS.S, ms.Gender.M, ms.Animacy.INANIM, "(вин,ед|им,ед)")),
    ('V,несов,пе=непрош,мн,изъяв,3-л',
     (ms.POS.V,
      ms.VerbAspect.IPF,
      ms.VerbTransit.TRAN,
      ms.VerbTence.INPRAES,
      ms.Number.PL,
      ms.VerbMood.INDIC,
      ms.VerbPerson.P_3)
     ),
])
def test_mystem_grammem_parsing(inp, outp):
    """Разбор граммемной информации после морфологического анализа"""

    assert tuple(map(lambda t: t[1], ms._parse_mystem_grammem(inp)))[:-1] == outp


@pytest.mark.parametrize('inp, outp', [
    (f'{KILO_POSTFIX}5{KILO_POSTFIX}', '5000'),
    (f'{KILO_POSTFIX}1{KILO_POSTFIX}', '1000'),
    ('1', '1'),
])
def test_pipe_kilo_pref(inp, outp, jstem):
    """Конвертация токенов, помеченных как множитель '1000', в целое число"""

    analysis_result = jstem.analyze([inp])
    pipe = stemming.pipe_kilo_postfix(stemming.stems_gen(analysis_result))

    assert ' '.join(s[0][0] for s in pipe).strip() == outp


@pytest.mark.parametrize('inp, outp', [
    ('номер карты 1 1 2 4 0000 128 1 15 10', ('номер', "карты", "1124000012811510")),
    ("телефон 7 995 116 4 4 8 8 переведи на карту 5 6 34 8888 0 1 25 74 15 100 рублей",
     ("телефон", "7", "995", "116", "4", "4", "8", "8",
      "переведи", "на", "карту", "5634888801257415", "100", "рублей")),
    ("карта 5 6 34 8888 0 1 25 74 15, абвгд", ('карта', "5634888801257415", ",", "абвгд")),
    ("переведи на карту 5 6 34 8888 0 1 25 74 15 100 рублей",
     ("переведи", "на", "карту", "5634888801257415", "100", "рублей")),

])
def test_pipe_merge_card_number(inp, outp, analize):
    analysis_result = analize(inp)
    pipe = stemming.pipe_merge_ccn(stemming.stems_gen(analysis_result))
    result = list(pipe)

    assert tuple(s[0][0] for s in result) == outp
    assert list(filter(lambda s: s[0][1] == TokenType.CARDNUM, result))


def test_empty_pipeline(analize):
    s = 'мама мыла раму'
    analysis_result = analize(s)
    pl = stemming.pipeline(analysis_result)

    assert ' '.join(s[0][0] for s in pl) == s


def test_stemmer_fix_list_not_found():
    from text_normalizer.stemming import JsonStemmer

    with pytest.raises(FileNotFoundError):
        JsonStemmer(fixlist_file='helloeverybody')


def test_stem_to_dict(analize):
    s = 'мама мыла раму'
    analysis_result = analize(s)
    stems = stemming.stems_gen(analysis_result)
    stem_dicts = list(map(stemming.to_dict, stems))
    assert len(stem_dicts) == 3
    assert all(len(d) == 4 for d in stem_dicts)


def test_stem_context_manager(tokenize, benchmark_text):
    """Использование морфологического анализатора в контекстном менеджере"""

    with stemming.jstem_ctx() as stem:
        jstem = stem
        tokens = tokenize(benchmark_text)
        result = stem.analyze([t[0] for t in tokens])

        assert type(result) is list
        assert 'analysis' in result[0]
        assert jstem._proc

    assert not jstem._proc

def test_pipe_integration(benchmark_text, analize):
    """
    Специальный тест для прохода полной цепочки обработки результатов морфологического анализа.

    Здесь проверяется НЕ конечный результат работы, а сам процесс взаимодействия пайплайнов между собой
    и различные их конфигурации.

    NB! Результат работы каждого пайплайна необходимо тестировать в отдельном тесте
    """

    analize_result = analize('сто')
    _pipe = [
            stemming.pipe_word2num,
            stemming.pipe_ord_unfold,
            stemming.pipe_makedate,
            stemming.pipe_kilo_postfix,
            stemming.pipe_merge_ccn
        ]

    shuffle(_pipe)  # каждый запуск теста будет использовать новую конфигурацию пайплайна

    pl = partial(
        stemming.pipeline,
        pipe=_pipe)

    assert list(pl(analize_result))
