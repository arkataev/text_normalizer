import pytest

from text_normalizer.tokenization import replace_bigrams


@pytest.mark.benchmark(group='ivr_convert')
def test_benchmark_replace_synonyms(benchmark, tokenize, benchmark_text):
    tokens = list(tokenize(benchmark_text))
    benchmark(lambda: list(replace_bigrams(tokens)))
