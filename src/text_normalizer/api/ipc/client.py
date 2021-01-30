"""Модуль для работы с сервером нормализации"""

import logging
from contextlib import contextmanager
from functools import lru_cache
from multiprocessing.connection import Client
from os import environ
from threading import RLock
from typing import Sequence

from .server import RTN_SERVER_LOGGER_NAME

__all__ = ['TextNormalizerProxy', 'rtn_ctx', 'get_rtn']

_RTN_PORT = int(environ.get('RTN_PORT', 3000))
_RTN_HOST = environ.get('RTN_HOST', 'rtn')
_RTN_SECRET = environ.get('RTN_SECRET')
_RTN_TIMEOUT = int(environ.get('RTN_TIMEOUT', 1))

logger = logging.getLogger('rtn')


class TextNormalizerProxy:
    def __init__(
            self,
            host: str = _RTN_HOST,
            port: int = _RTN_PORT,
            authkey: bytes = _RTN_SECRET,
            timeout: int = _RTN_TIMEOUT
    ):
        self._host = host
        self._port = port
        self._authkey = authkey
        self._timeout = timeout
        self._conn = None
        self._lock = RLock()

    def normalize(self, sentence: str) -> Sequence:
        """
        Нормализация строки.

        :param sentence: строка для нормализации
        :raise RuntimeError: Если нормализация строки не удалась
        :return:    - Результаты нормализации и анализа переданной строки
                    - Пустой список если строка пустая
        """
        if not sentence:
            return []

        try:
            if not self._conn or self._conn.closed:
                self.connect()

            with self._lock:
                self._conn.send(sentence)
                # ждем данные от нормализатора с таймаутом или отпускаем блок
                if self._conn.poll(timeout=self._timeout):
                    result = self._conn.recv()
                    if result:
                        return result

                    # Если мы отправили непустую строку, но получили пустой ответ,
                    # то нормализация считается неудавшейся.
                    logger.warning(
                        f'Got no result from RTN for {sentence}. See {RTN_SERVER_LOGGER_NAME} logs for details')
                else:
                    logger.warning(f'RTN timeout: {sentence}')

        except (BrokenPipeError, EOFError):
            logger.error(f'RTN сonnection broken')
        except Exception as e:
            logger.exception(f'RTN failed with error: {e}')

        # необходимо закрыть соединение в случае ошибки, иначе предыдущий результат
        # может прийти при повторной отправке данных на нормализацию
        self.close()
        raise RuntimeError('RTN failed')

    def connect(self):
        self.close()

        with self._lock:
            try:
                self._conn = Client((self._host, self._port), family='AF_INET', authkey=self._authkey)
            except Exception as e:
                logger.error(f'Could not connect to RTN at {self._host}:{self._port}. Error {e}')
            else:
                logger.info(f'RTN connected at {self._host}:{self._port}')
                return
            raise ConnectionError('RTN connection failed')

    def close(self):
        with self._lock:
            if self._conn:
                self._conn.close()
                logger.debug('RTN connection closed')

    def __del__(self):
        self.close()


def get_rtn(*args, **kwargs):
    return TextNormalizerProxy(*args, **kwargs)


@contextmanager
def rtn_ctx(*args, **kwargs):
    """Контекстный менеджер для подключения к удаленному нормализатору"""

    normalizer = None

    try:
        normalizer = get_rtn(*args, **kwargs)
        normalizer.connect()
    except Exception as e:
        logger.error(f'Could not connect to RTN. Error: {e}')
    finally:
        try:
            yield normalizer
        finally:
            if normalizer:
                normalizer.close()
