from functools import partial

import pytest

from text_normalizer.stemming import (
    stems_gen,
    pipe_word2num,
    pipe_ord_unfold,
    pipe_makedate,
    pipe_kilo_postfix,
    pipe_merge_ccn,
    Pipeline,
    pipeline
)

from text_normalizer.normalization import compose_pipeline


@pytest.mark.benchmark(group='ivr_stemming')
def test_benchmark_stems_gen(benchmark, sentences_analysis):
    benchmark(lambda: list(stems_gen(sentences_analysis)))


@pytest.mark.benchmark(group='ivr_stemming')
def test_benchmark_pipe_word2num(benchmark, stems):
    benchmark(lambda: list(pipe_word2num(stems)))


@pytest.mark.benchmark(group='ivr_stemming')
def test_benchmark_pipe_ord_unfold(benchmark, stems):
    benchmark(lambda: list(pipe_ord_unfold(stems)))


@pytest.mark.benchmark(group='ivr_stemming')
def test_benchmark_pipe_makedate(benchmark, stems):
    nums_replaced = list(pipe_word2num(stems))
    benchmark(lambda: list(pipe_makedate(nums_replaced)))


@pytest.mark.benchmark(group='ivr_stemming')
def test_benchmark_pipe_kilo_postf(benchmark, stems):
    benchmark(lambda: list(pipe_kilo_postfix(stems)))


@pytest.mark.benchmark(group='ivr_stemming')
def test_benchmark_pipe_merge_credit_card_number(benchmark, stems):
    nums_replaced = list(pipe_word2num(stems))
    benchmark(lambda: list(pipe_merge_ccn(nums_replaced)))


@pytest.mark.benchmark(group='ivr_stemming')
def test_benchmark_full_pipeline(benchmark, sentences_analysis):
    pl = partial(pipeline, pipe=compose_pipeline(*Pipeline))
    benchmark(lambda: list(pl(sentences_analysis)))
