import pytest


@pytest.mark.benchmark(group='ivr_tokenization')
def test_benchmark_tokenize(benchmark, tokenize, benchmark_text):
    benchmark(lambda: list(tokenize(benchmark_text)))
