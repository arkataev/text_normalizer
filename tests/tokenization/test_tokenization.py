import json
import os

import pytest

from text_normalizer.config import PipelineConfigType, load_conf
from text_normalizer.tokenization import token_type, to_token, TokenType, replace_bigrams
from ..settings import TESTS_PATH

with open(os.path.join(TESTS_PATH, 'tokenization/data/sentences.json'), encoding='utf=8') as f:
    sentences = json.load(f)


@pytest.mark.parametrize('inp, outp', [
    ('мама', TokenType.TXT),
    (' ', TokenType.SPACE),
    ('', TokenType.NONE),
    ('1', TokenType.NUM),
    ('1-ый', TokenType.TXT),
    ('2ой', TokenType.TXT),
    (',', TokenType.PUNKT),
    ('{', TokenType.PUNKT_ISO),
    ('"', TokenType.PUNKT_ISO),
    ('[', TokenType.PUNKT_ISO),
    (']', TokenType.PUNKT_ISO),
    ('20.10.2020', TokenType.DATE),
    ('20/10/2020', TokenType.DATE),
    ('20.100.2020', TokenType.TXT),
    ('18:00', TokenType.TIME),
    ('18:30:30', TokenType.TIME),
    ('18:30:300', TokenType.TXT),
    ('https://pypi.org/project/pytest-csv/', TokenType.URL),
    ('my_mail@google.com', TokenType.EMAIL),
    ('yoklmn5678@google.com', TokenType.EMAIL),
])
def test_token_type(inp, outp):
    assert token_type(inp) == outp


@pytest.mark.parametrize('inp', ['мама', "мыла", "раму"])
def test_token2type(inp):
    assert type(to_token(inp)) is tuple


@pytest.mark.parametrize('sentence, types', sentences.items())
def test_toktok_tokenizer(sentence, types, tokenize):
    assert [t[1] for t in tokenize(sentence)] == types


@pytest.mark.parametrize('inp, outp', load_conf(PipelineConfigType.SYNONIMS).items())
def test_synonym_dict(inp, outp, tokenize):
    tokens = tokenize(inp)

    assert next(replace_bigrams(tokens))[0] == outp


@pytest.mark.parametrize('inp, outp', [
    ('снова cash back закинь 050 рублей на 0050', [
        ('снова', TokenType.TXT),
        ('cashback', TokenType.TXT),
        ('закинь', TokenType.TXT),
        ('050', TokenType.NUM),
        ('rur', TokenType.TXT),
        ('на', TokenType.TXT),
        ('0050', TokenType.NUM),
    ]),
    ('cash back 100 рублей бабушке', [
        ('cashback', TokenType.TXT), ('100', TokenType.NUM), ('rur', TokenType.TXT), ('бабушке', TokenType.TXT)]),
    ('cash back', [('cashback', TokenType.TXT)]),
    ('cash back рублей 100', [
        ('cashback', TokenType.TXT),
        ('rur', TokenType.TXT),
        ('100', TokenType.NUM),
    ]),
    ('cash', [('наличные средства', TokenType.TXT)]),
    ('abcd', [('abcd', TokenType.TXT)]),
    ('50 лет бабушке', [('50', TokenType.NUM), ('лет', TokenType.TXT), ('бабушке', TokenType.TXT)]),
    ('5000 бабушке', [('5000', TokenType.NUM), ('бабушке', TokenType.TXT)]),
    ('5000 рублей', [('5000', TokenType.NUM), ('rur', TokenType.TXT)]),
])
def test_replace_synonyms(inp, outp, tokenize):
    tokens = tokenize(inp)

    assert list(replace_bigrams(tokens)) == outp
