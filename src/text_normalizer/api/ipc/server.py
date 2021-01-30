"""Модуль для запуска сервера нормализации"""

import cProfile
import logging
import os
from functools import partial
from multiprocessing import Pool, cpu_count
from multiprocessing.connection import Connection, Listener
from time import process_time, time
from typing import Callable, Iterator

import text_normalizer as tn
from text_normalizer import stemming, tokenization, normalization, config, settings
from ..cli.args import parse_normalization_args

__all__ = ['receive', 'run', 'RTN_SERVER_LOGGER_NAME']

_PORT = int(os.environ.get('RTN_PORT', 3000))
_WORKERS = int(os.environ.get('RTN_WORKERS', cpu_count()))
_RTN_CONNECTION_LIFE_TIME = int(os.environ.get('RTN_CONNECTION_LIFE_TIME', 300))  # seconds
_PROFILER = int(os.environ.get('CP_ENABLED', 0))
RTN_SERVER_LOGGER_NAME = 'rtn_server'

logger = logging.getLogger(RTN_SERVER_LOGGER_NAME)
perflog = logging.getLogger('perflog')


def receive(conn: Connection, _pipeline: Callable[[Iterator[dict]], Iterator]):
    """
    Процедура получения строки через сетевое соединение и обратной передачи данных нормализации
    """
    sentence = ''
    stemming.init_cache()
    tokenization.init_cache()
    config.init_cache()

    try:
        with stemming.jstem_ctx() as stemmer:
            while True:
                if conn.poll(timeout=_RTN_CONNECTION_LIFE_TIME):
                    sentence = conn.recv()

                    logger.debug(f'Received: "{sentence}"')

                    if _PROFILER:
                        profiler.enable()

                    start = process_time()
                    try:
                        analisys = normalization.analyze(sentence, stemmer)
                        result = list(_pipeline(analisys))
                    except Exception as e:
                        logger.error(f'Normalization failed with error: {e} \n {sentence}')
                        result = []
                    end = process_time()

                    if _PROFILER:
                        profiler.disable()

                    conn.send(result)
                    logger.debug(f'Sent: {result}')
                    perflog.debug(f'RTN time: {round((end-start) * 1000, 2)} ms')

                    if _PROFILER:
                        profiler.dump_stats(os.path.join(settings.ROOT_PATH, f'rtn_{time()}.cprof'))
                else:
                    raise TimeoutError
    except EOFError:
        logger.info('Incoming connection closed')
    except TimeoutError:
        logger.warning('Incoming connection timeout')
    except Exception:
        logger.exception(sentence if sentence else 'Normalization Failed')
    finally:
        stemming.cache_clear()
        tokenization.cache_clear()
        config.cache_clear()
        logger.debug('Closing connection...')
        conn.close()
        logger.debug('Connection closed')


def run(_pipeline: Callable[[Iterator[dict]], Iterator]):
    with Pool(processes=_WORKERS) as pool:
        with Listener(('', _PORT), family='AF_INET', backlog=10) as listener:
            while True:
                conn = listener.accept()
                logger.info(f'New connection from: {listener.last_accepted}')
                pool.apply_async(func=receive, args=(conn, _pipeline))


if __name__ == '__main__':

    try:
        from importlib import metadata
    except ImportError:
        from pkg_resources import get_distribution
        version = get_distribution(tn.__name__).version
    else:
        try:
            version = metadata.version(tn.__name__)
        except metadata.PackageNotFoundError:
            version = 'dev'

    if _PROFILER:
        logger.warning('!!WARNING!! PROFILER ENABLED')
        profiler = cProfile.Profile(subcalls=True, builtins=True)

    logger.info(f"RTN version [{version}]")
    logger.info(f'Logging level set to {logging.getLevelName(logger.level)}')

    args = parse_normalization_args()
    # составляем список названий функций пайплайна из аргументов полученных из cli
    pl_args = [el for el in stemming.Pipeline if getattr(args, el.value)]
    # составляем пайплайн их названий списка функций
    pipeline = partial(stemming.pipeline, pipe=normalization.compose_pipeline(*pl_args))
    converter = stemming.to_tuple if args.fmt == 'tuple' else stemming.to_dict

    logger.debug(f'RTN pipeline options: {[arg.value for arg in pl_args]}')
    logger.debug(f'RTN output converter: {converter}')

    # NB! Лямбда-функцию нельзя использовать в качестве аргумента для передачи в процесс
    def _mapped_pipeline(analysis):
        yield from map(converter, pipeline(analysis))

    try:
        run(_mapped_pipeline)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception('RTN Server Error')
    finally:
        logger.info('Exiting...')
