import json
import os
from contextlib import contextmanager

import pytest

from text_normalizer.convert import text2int, ord_unfold, is_ordfold, MONTHS, month2num
from text_normalizer.convert._convert import _numerics
from ..settings import TESTS_PATH

with open(os.path.join(TESTS_PATH, 'convert/data/numerics_ds.json'), encoding='utf=8') as f:
    nums_dataset = json.load(f)


@contextmanager
def does_not_raise():
    yield


@pytest.mark.parametrize('text, num', _numerics.items())
def test_text2int_single(text, num):
    nums_list = text.split()
    assert text2int(*nums_list) == num[0]


@pytest.mark.parametrize('num, text', nums_dataset.items())
def _test_text2int_dataset(text, num):
    nums_list = text.split()
    assert text2int(*nums_list) == int(num)


@pytest.mark.parametrize('text, num', [
    ("десяток", 10),
    ("два десяток", 20),
    ("пять десяток", 50),
    ("сотня", 100),
    ("две сотня", 200),
    ("", 0),
])
def test_text2int_custom(text, num):
    nums_list = text.split()
    assert text2int(*nums_list) == num


@pytest.mark.parametrize('text, num, expected', [
    ('двести', 200, does_not_raise()),
    ('пять десятков', 50, pytest.raises(ValueError)),
    ('сто один двадцать', 0, pytest.raises(ValueError)),
    ('десяток двоек', 0, pytest.raises(ValueError)),
    ('тысяча миллион', 0, pytest.raises(ValueError)),
    ('абвгд', 0, pytest.raises(ValueError)),
])
def test_text2int_raises(text, num, expected):
    nums_list = text.split()

    with expected:
        assert text2int(*nums_list) == num


@pytest.mark.parametrize('inp, outp', [
    ('10-ый', True),
    ('10-го', True),
    ('10-му', True),
    ('10-го', True),
    ('10-ым', True),
    ('10-м', True),
    ('10-ом', True),
    ('10', False),
])
def test_isordfold(inp, outp):
    assert is_ordfold(inp) == outp


@pytest.mark.parametrize('inp, outp, expected', [
    ('10-ый', '10', does_not_raise()),
    ('10-го', '10', does_not_raise()),
    ('10-му', '10', does_not_raise()),
    ('10-го', '10', does_not_raise()),
    ('10-ым', '10', does_not_raise()),
    ('10-м', '10', does_not_raise()),
    ('10-ом', '10', does_not_raise()),
    ('10ый', '10', does_not_raise()),
    ('10го', '10', does_not_raise()),
    ('10му', '10', does_not_raise()),
    ('10го', '10', does_not_raise()),
    ('10ым', '10', does_not_raise()),
    ('10м', '10', does_not_raise()),
    ('10ом', '10', does_not_raise()),
    ("", '', pytest.raises(ValueError)),
    ("asdc", '', pytest.raises(ValueError)),
])
def test_ord_unfold(inp, outp, expected):
    with expected:
        assert ord_unfold(inp) == outp


@pytest.mark.parametrize('inp, outp', zip(MONTHS, range(1, 13)), ids=MONTHS)
def test_month2num(inp, outp):
    assert month2num(inp) == outp
