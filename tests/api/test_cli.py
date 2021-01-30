import pytest
import mock
from text_normalizer.api.cli.args import parse_normalization_args, NormalizationArgs
from text_normalizer.stemming import Pipeline

_pl_values = [True] * len(Pipeline)


@pytest.mark.parametrize('args, norm_arg', [
    (['abc', '--word2num'], NormalizationArgs('abc', 'tuple', *[True, *map(lambda v: not v, _pl_values[1:])])),
    (['', '--word2num', '--ord_unfold', '--makedate', '--kilo', '--merge_ccn', '--stopwords'],
     NormalizationArgs('', 'tuple', *_pl_values)
     ),
    (['abc'], NormalizationArgs('abc', 'tuple', *map(lambda v: not v, _pl_values))),
    (['abc', '--all'], NormalizationArgs('abc', 'tuple', *_pl_values)),
    (['abc', '--all', '--word2num'], NormalizationArgs('abc', 'tuple', *[True, *map(lambda v: not v, _pl_values[1:])])),
])
def test_parse_normalization_args(args, norm_arg):
    assert parse_normalization_args(args) == norm_arg


def test_inconsistent_cli_args():
    with mock.patch('text_normalizer.api.cli.args.PIPELINE_ARGS', [1] * (len(Pipeline) - 1)):
        with pytest.raises(AssertionError):
            parse_normalization_args()
