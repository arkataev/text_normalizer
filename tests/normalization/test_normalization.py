import pytest

from text_normalizer import normalization, stemming


@pytest.mark.parametrize('pipe_names, pipeline', [
    (stemming.Pipeline, [
        stemming.pipe_word2num,
        stemming.pipe_ord_unfold,
        stemming.pipe_makedate,
        stemming.pipe_kilo_postfix,
        stemming.pipe_merge_ccn,
        stemming.pipe_stopwords,
    ]),
    ((stemming.Pipeline.WORD2NUM,), [stemming.pipe_word2num]),
    ((stemming.Pipeline.MAKE_DATE, stemming.Pipeline.WORD2NUM), [stemming.pipe_makedate, stemming.pipe_word2num]),
    ([], []),
], ids=['full', 'single', 'double', 'empty'])
def test_compose_pipeline(pipe_names, pipeline):
    assert normalization.compose_pipeline(*pipe_names) == pipeline


def test_analyze():
    pass