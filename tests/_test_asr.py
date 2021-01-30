import csv
import os
from functools import partial, lru_cache

import pytest

from text_normalizer import stemming
from text_normalizer.normalization import normalize


@pytest.fixture
def numbers():
    with open(os.path.join(DATA_PATH, 'numbers.csv')) as f:
        yield csv.reader(f, delimiter='|')


def test_asr(numbers, jstem):
    pl = partial(
        stemming.pipeline,
        pipe=[
            stemming.pipe_word2num,
            stemming.pipe_makedate,
        ])

    next(numbers)

    with open(os.path.join(DATA_PATH, 'failed.csv'), 'w') as f:
        failed = csv.writer(f)
        failed.writerow(('uid', 'raw', 'asr', 'exception'))
        with open(os.path.join(DATA_PATH, 'invalid.csv'), 'w') as f:
            invalid = csv.writer(f)
            invalid.writerow(('uid', 'raw', 'asr', 'normalized'))
            for uid, raw, result in numbers:
                try:
                    normalized = ' '.join([t[0] for t in normalize(raw, jstem, pl)])
                except Exception as e:
                    failed.writerow((uid, raw, result, e))
                else:
                    if not normalized == result.lower().strip('?!.'):
                        invalid.writerow((uid, raw, result, normalized))
