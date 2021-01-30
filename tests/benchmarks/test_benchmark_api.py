import pytest

from text_normalizer.api.ipc.client import rtn_ctx

# TODO:: add skip if ipc clien is not connected
@pytest.mark.benchmark(group='ivr_text_normal_api')
def test_benchmark_api(benchmark, benchmark_text):
    with rtn_ctx() as normalizer:
        benchmark(normalizer.normalize, benchmark_text)
