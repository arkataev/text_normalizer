from typing import Iterator

from text_normalizer.normalization import normalize as _normalize
from text_normalizer.stemming import JsonStemmer, iStemTuple, Pipeline


def normalize(sentence: str, stemmer: JsonStemmer, pipeline=Pipeline, bigrams=True) -> Iterator[iStemTuple]:
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
    yield from _normalize(sentence, stemmer, pipeline=pipeline, bigrams=bigrams)
