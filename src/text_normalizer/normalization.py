import logging
from functools import lru_cache, partial
from typing import Iterator, Sequence, Callable

from . import stemming
from .stemming import iStemTuple, JsonStemmer, PIPE_PREFIX, Pipeline
from .tokenization import sent_tokenize, replace_bigrams, get_tokenizer

__all__ = ['analyze', 'compose_pipeline', 'cache_clear', 'init_cache', 'normalize']


logger = logging.getLogger('rtn')


@lru_cache(maxsize=len(Pipeline))
def compose_pipeline(
        *pipelines: Sequence[Pipeline]) -> Sequence[Callable[[Iterator[iStemTuple]], Iterator[iStemTuple]]]:
    """
    Построить пайплайн на основе переданных наименований::

        pipes = compose_pipeline(Pipeline.WORD2NUM) # word2num pipeline
        pipes = compose_pipeline(Pipeline.WORD2NUM, ORD_UNFOLD) # word2num and ord_unfold pipelines
        pipes = compose_pipeline(*Pipeline) # all pipelines

        processing_pipeline = partial(stemming.pipeline, pipe=pipes)
        ...

    :param pipelines: одно или несколько наименований пайплайнов
    """
    from inspect import getmembers, isfunction

    d = dict(zip(
        sorted(Pipeline, key=lambda p: p.value),  # getmembers возвращает функции сортированные по имени
        map(lambda func: func[1],
            filter(lambda func: func[0].startswith(PIPE_PREFIX, 0, len(PIPE_PREFIX) + 1),
                   getmembers(stemming, isfunction)))
        ))

    return [d[p] for p in pipelines if p in d]


def analyze(sentence: str, stemmer: JsonStemmer, bigrams=True) -> Iterator[dict]:
    """
    Морфологический анализ строки.

    :param sentence: Строка для анализа
    :param stemmer:  Предложенный анализатор
    :param bigrams:  Заменять биграммы в предложении на основе правил приложения
    :return:         Итератор словарей с данными морфологического анализа
    """

    tokens = sent_tokenize(sentence, tokenizer=get_tokenizer())

    if not bigrams:
        tokens = replace_bigrams(tokens)

    yield from stemmer.analyze(t[0] for t in tokens)


def normalize(
        sentence: str,
        stemmer: JsonStemmer,
        pipeline: Sequence = Pipeline,
        bigrams: bool = True) -> Iterator[iStemTuple]:
    """
    Анализ предложения на основе базового пайплайна::
        from text_normalizer.stemming import jstem_ctx

        with jstem_ctx() as stemmer:
            result = normalize('мама мыла раму', stemmer, [Pipeline.WORD2NUM, Pipeline.ORD_UNFOLD])
            print(list(result))

    :param sentence: строка для нормализации
    :param stemmer:  предложенный морфологический анализатор
    :param pipeline: последовательность типов пайплайнов
    :param bigrams:  замена биграм
    """
    processing_pipeline = partial(stemming.pipeline, pipe=compose_pipeline(*pipeline))
    yield from map(stemming.to_tuple, processing_pipeline(analyze(sentence, stemmer, bigrams=bigrams)))


def init_cache():
    list(map(compose_pipeline, Pipeline))
    compose_pipeline(*Pipeline)
    compose_pipeline()
    logger.debug('Cache initiated')


def cache_clear():
    compose_pipeline.cache_clear()
    logger.debug('Cache cleared')
