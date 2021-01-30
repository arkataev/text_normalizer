from threading import Thread
from time import sleep

import mock
import pytest

from text_normalizer import stemming
from text_normalizer.api import ipc


def _mapped_pipeline(analysis):
    yield from map(stemming.to_tuple, stemming.pipeline(analysis))


@pytest.fixture(scope='module')
def server():
    t = Thread(target=ipc.run, args=(_mapped_pipeline,), daemon=True)
    t.start()
    yield
    t.join(timeout=0.5)


@pytest.fixture
def client():
    client = ipc.TextNormalizerProxy('', 3000, timeout=None)
    sleep(.5)
    yield client
    client.close()


@pytest.fixture
def mock_conn():
    yield mock.MagicMock()


def test_ipc(server, client):
    s = 'мама мыла раму'
    client.connect()
    result = client.normalize(s)
    assert ' '.join(t[0] for t in result) == s


def test_ipc_multiclient(server, client):
    pass



def test_server_recieve(mock_conn):
    s = 'мама мыла раму'
    mapped_pipeline = lambda analysis: map(stemming.to_tuple, stemming.pipeline(analysis))
    mock_conn.poll.side_effect = [True, False]
    mock_conn.recv.side_effect = [s]

    ipc.receive(mock_conn, mapped_pipeline)

    mock_conn.send.assert_called_once()
    mock_conn.close.assert_called_once()

    result = mock_conn.send.call_args[0][0]
    assert ' '.join(t[0] for t in result) == s


def test_rtn_client_empty_sentence(client):
    assert not client.normalize('')


def test_rtn_client_recieve_if_normalization_failed_once(mock_conn):
    normalize = mock.MagicMock()
    mock_conn.poll.side_effect = [True, True, False]
    normalize.side_effect = [ValueError('Test Error'), ['test']]

    ipc.receive(mock_conn, normalize)
    mock_conn.send.assert_called_with(['test'])


def test_rtn_client_normalize_in_multiple_threads(client, server):
    from concurrent.futures import ThreadPoolExecutor

    s = {'мама мыла раму', 'папа красил забор', "бабушка пекла хлеб"}
    client.connect()

    with ThreadPoolExecutor() as executor:
        result = executor.map(client.normalize, s)

    for r in result:
        assert ' '.join(t[0] for t in r) in s


def test_rtn_client_normalization_error(client):
    client._conn = mock.MagicMock()
    client._conn.closed = False
    client._conn.send.side_effect = [BrokenPipeError, EOFError, Exception, ConnectionError]

    for _ in range(4):
        with pytest.raises(RuntimeError):
            client.normalize('aaa')

    assert client._conn.close.call_count == 4


def test_rtn_client_connect_on_first_normalize_call(client):
    client._conn = mock.MagicMock()
    client.connect = mock.MagicMock()
    client._conn.closed = True

    client.normalize('aaa')

    client.connect.assert_called_once()


def test_rtn_client_empty_result_for_sentence(client):
    client._conn = mock.MagicMock()
    client._conn.closed = False
    client._conn.poll.side_effect = [True]
    client._conn.recv.side_effect = [[]]

    with pytest.raises(RuntimeError):
        client.normalize('мама мыла раму')


def test_rtn_client_poll_timeout(client):
    client._conn = mock.MagicMock()
    client._conn.closed = False
    client._conn.poll.side_effect = [False]

    with pytest.raises(RuntimeError):
        client.normalize('aaa')

    client._conn.close.assert_called_once()


def test_rtn_client_connection_error(client):
    with mock.patch('text_normalizer.api.ipc.client.Client', mock.MagicMock()) as connection:
        connection.side_effect = Exception

        with pytest.raises(ConnectionError):
            client.connect()


def test_rtn_ctx_error_before_context_init():
    with mock.patch('text_normalizer.api.ipc.client.get_rtn', mock.MagicMock()) as get_rtn:
        get_rtn.side_effect = Exception
        count = 0

        with ipc.rtn_ctx():
            count += 1

        assert count


def test_rtn_ctx_error_while_context_run():
    with mock.patch('text_normalizer.api.ipc.client.get_rtn', mock.MagicMock()) as get_rtn:
        normalizer = mock.MagicMock()
        get_rtn.side_effect = normalizer

        with pytest.raises(Exception):
            with ipc.rtn_ctx() as normalizer_ctx:
                normalizer = normalizer_ctx
                raise Exception

        normalizer.connect.assert_called_once()
        normalizer.close.assert_called_once()
