import os
from functools import partial

import pytest

from text_normalizer import stemming, tokenization, config, normalization
from text_normalizer.config import PipelineConfigType, load_conf
from text_normalizer.settings import DATA_PATH


@pytest.fixture(scope='session', autouse=True)
def cache():
    stemming.init_cache()
    tokenization.init_cache()
    config.init_cache()
    normalization.init_cache()
    print('cache init')
    yield
    stemming.cache_clear()
    tokenization.cache_clear()
    config.cache_clear()
    normalization.cache_clear()
    print('cache clear')


@pytest.fixture(scope='session')
def jstem():
    stem_conf = load_conf(PipelineConfigType.MYSTEM)
    stem = stemming.JsonStemmer(
        fixlist_file=os.path.join(DATA_PATH, stem_conf['fixlist_file']),
        weight=False
    )
    stem.start()
    yield stem
    stem.close()


@pytest.fixture(scope='package')
def benchmark_text():
    return """
    Пятьсот двадцать три пин-кода выданы для ста банковских карт, 
    третьего сентября две тысячи двадцатого года в 18:00 
    5к клиентам в 3х отделениях. Переведи на карту пять шесть тридцать четыре 
    четыре восьмерки ноль один двадцать пять семь четыре пятнадцать сто рублей
    """


@pytest.fixture(scope='session')
def tokenizer() -> tokenization.TokTok:
    return tokenization.TokTok()


@pytest.fixture(scope='session')
def tokenize(tokenizer):
    return partial(tokenization.sent_tokenize, tokenizer=tokenizer)


@pytest.fixture(scope='session')
def analize(jstem, tokenize):
    def _analyze(inp):
        tokens = tokenize(inp)
        return jstem.analyze([t[0] for t in tokens])

    yield _analyze


@pytest.fixture(scope='module')
def sentences_analysis(analize, benchmark_text):
    sentences_analysis = list(analize(benchmark_text))

    return sentences_analysis


@pytest.fixture(scope='module')
def stems(sentences_analysis):
    return list(stemming.stems_gen(sentences_analysis))
