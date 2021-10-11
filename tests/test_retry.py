import logging
from io import StringIO
from uuid import uuid1

try:
    from unittest.mock import create_autospec
except ImportError:
    from mock import create_autospec

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

import time

import pytest

from retry.api import retry_call
from retry.api import retry


def test_retry(monkeypatch):
    mock_sleep_time = [0]

    def mock_sleep(seconds):
        mock_sleep_time[0] += seconds

    monkeypatch.setattr(time, 'sleep', mock_sleep)

    hit = [0]

    tries = 5
    delay = 1
    backoff = 2

    @retry(tries=tries, delay=delay, backoff=backoff)
    def f():
        hit[0] += 1
        1 / 0

    with pytest.raises(ZeroDivisionError):
        f()
    assert hit[0] == tries
    assert mock_sleep_time[0] == sum(
        delay * backoff ** i for i in range(tries - 1))


def test_tries_inf():
    hit = [0]
    target = 10

    @retry(tries=float('inf'))
    def f():
        hit[0] += 1
        if hit[0] == target:
            return target
        else:
            raise ValueError

    assert f() == target


def test_tries_minus1():
    hit = [0]
    target = 10

    @retry(tries=-1)
    def f():
        hit[0] += 1
        if hit[0] == target:
            return target
        else:
            raise ValueError

    assert f() == target


def test_max_delay(monkeypatch):
    mock_sleep_time = [0]

    def mock_sleep(seconds):
        mock_sleep_time[0] += seconds

    monkeypatch.setattr(time, 'sleep', mock_sleep)

    hit = [0]

    tries = 5
    delay = 1
    backoff = 2
    max_delay = delay  # Never increase delay

    @retry(tries=tries, delay=delay, max_delay=max_delay, backoff=backoff)
    def f():
        hit[0] += 1
        1 / 0

    with pytest.raises(ZeroDivisionError):
        f()
    assert hit[0] == tries
    assert mock_sleep_time[0] == delay * (tries - 1)


def test_fixed_jitter(monkeypatch):
    mock_sleep_time = [0]

    def mock_sleep(seconds):
        mock_sleep_time[0] += seconds

    monkeypatch.setattr(time, 'sleep', mock_sleep)

    hit = [0]

    tries = 10
    jitter = 1

    @retry(tries=tries, jitter=jitter)
    def f():
        hit[0] += 1
        1 / 0

    with pytest.raises(ZeroDivisionError):
        f()
    assert hit[0] == tries
    assert mock_sleep_time[0] == sum(range(tries - 1))


def test_retry_call():
    f_mock = MagicMock(side_effect=RuntimeError)
    tries = 2
    try:
        retry_call(f_mock, exceptions=RuntimeError, tries=tries)
    except RuntimeError:
        pass

    assert f_mock.call_count == tries


def test_retry_call_2():
    side_effect = [RuntimeError, RuntimeError, 3]
    f_mock = MagicMock(side_effect=side_effect)
    tries = 5
    result = None
    try:
        result = retry_call(f_mock, exceptions=RuntimeError, tries=tries)
    except RuntimeError:
        pass

    assert result == 3
    assert f_mock.call_count == len(side_effect)


def test_retry_call_with_args():
    def f(value=0):
        if value < 0:
            return value
        else:
            raise RuntimeError

    return_value = -1
    result = None
    f_mock = MagicMock(spec=f, return_value=return_value)
    try:
        result = retry_call(f_mock, fargs=[return_value])
    except RuntimeError:
        pass

    assert result == return_value
    assert f_mock.call_count == 1


def test_retry_call_with_kwargs():
    def f(value=0):
        if value < 0:
            return value
        else:
            raise RuntimeError

    kwargs = {'value': -1}
    result = None
    f_mock = MagicMock(spec=f, return_value=kwargs['value'])
    try:
        result = retry_call(f_mock, fkwargs=kwargs)
    except RuntimeError:
        pass

    assert result == kwargs['value']
    assert f_mock.call_count == 1


def test_call_on_exception():
    exception = RuntimeError()
    f_mock = MagicMock(side_effect=exception)
    callback_mock = MagicMock()
    try:
        retry_call(f_mock, tries=1, on_exception=callback_mock)
    except RuntimeError:
        pass
    callback_mock.assert_called_once_with(exception)


def test_logs_function_details(monkeypatch):
    mock_sleep_time = [0]

    def mock_sleep(seconds):
        mock_sleep_time[0] += seconds

    monkeypatch.setattr(time, 'sleep', mock_sleep)

    hit = [0]

    tries = 3
    fails = 2
    delay = 1
    backoff = 2
    max_delay = delay  # Never increase delay
    logger_name = str(uuid1())
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)
    logging_stream = StringIO()
    handler = logging.StreamHandler(logging_stream)
    logger.addHandler(handler)

    @retry(exceptions=ZeroDivisionError, tries=tries, delay=delay, max_delay=max_delay, backoff=backoff, logger=logger,
           log_traceback=True)
    def f():
        hit[0] += 1
        if hit[0] <= fails:
            1 / 0

    f()
    log_value = logging_stream.getvalue()
    assert log_value.startswith(
        "ZeroDivisionError: division by zero in test_retry.test_logs_function_details.<locals>.f, retrying in 1 seconds...")
    assert log_value.endswith("ZeroDivisionError: division by zero\n\n")
    assert hit[0] == fails + 1
    assert mock_sleep_time[0] == delay * fails
