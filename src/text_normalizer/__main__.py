import json
import sys
from functools import partial
from itertools import chain

from . import stemming
from . import tokenization
from . import config
from .api.cli.args import parse_normalization_args
from .normalization import analyze, compose_pipeline

if __name__ == "__main__":
    args = parse_normalization_args()

    tokenization.init_cache()
    stemming.init_cache()
    config.init_cache()

    pl_args = [el for el in stemming.Pipeline if getattr(args, el.value)]
    pipeline = partial(stemming.pipeline, pipe=compose_pipeline(*pl_args))
    converter = stemming.to_tuple if args.fmt == 'tuple' else stemming.to_dict

    with stemming.jstem_ctx() as stemmer:
        mapped_pipeline = lambda analysis_result: map(converter, pipeline(analysis_result))
        analysis = partial(analyze, stemmer=stemmer)

        if sys.stdin.isatty():
            sys.stdout.write(json.dumps(list(mapped_pipeline(analysis(args.sentence))), ensure_ascii=False))
            sys.stdout.write("\n")
        else:
            for result in chain(*map(lambda s: mapped_pipeline(analysis(s)), sys.stdin)):
                sys.stdout.write(json.dumps(result, ensure_ascii=False))
                sys.stdout.write('\n')

    tokenization.cache_clear()
    stemming.cache_clear()
    config.cache_clear()
