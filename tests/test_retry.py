try:
    from unittest.mock import create_autospec
    from unittest.mock import MagicMock
    from unittest import mock
except ImportError:
    from mock import create_autospec
    from mock import MagicMock
    import mock

import threading

import pytest

import retry.api

import logging

logging_logger = logging.Logger(__name__)

mock_sleep_time = [0]

class mockCondition():
	def acquire(self):
		logging_logger.warning('in acquire')
		return True
		
	def release(self):
		logging_logger.warning('in release')
		
	def wait(self, seconds):
		logging_logger.warning('in wait')
		mock_sleep_time[0] += seconds


def test_retry(monkeypatch):
    global mock_sleep_time
    mock_sleep_time = [0]

    
    monkeypatch.setattr(retry.api.threading, 'Condition', mockCondition)
    hit = [0]

    tries = 5
    delay = 1
    backoff = 2

    @retry.api.retry(tries=tries, delay=delay, backoff=backoff, condition=mockCondition())
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

    @retry.api.retry(tries=float('inf'), condition=mockCondition())
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

    @retry.api.retry(tries=-1)
    def f():
        hit[0] += 1
        if hit[0] == target:
            return target
        else:
            raise ValueError
    assert f() == target


def test_max_delay(monkeypatch):
    global mock_sleep_time
    mock_sleep_time = [0]

    monkeypatch.setattr(retry.api.threading, 'Condition', mockCondition)

    hit = [0]

    tries = 5
    delay = 1
    backoff = 2
    max_delay = delay  # Never increase delay

    @retry.api.retry(tries=tries, delay=delay, max_delay=max_delay, backoff=backoff, condition=mockCondition())
    def f():
        hit[0] += 1
        1 / 0

    with pytest.raises(ZeroDivisionError):
        f()
    assert hit[0] == tries
    assert mock_sleep_time[0] == delay * (tries - 1)


def test_fixed_jitter(monkeypatch):
    global mock_sleep_time
    mock_sleep_time = [0]

    monkeypatch.setattr(retry.api.threading, 'Condition', mockCondition)

    hit = [0]

    tries = 10
    jitter = 1

    @retry.api.retry(tries=tries, jitter=jitter, condition=mockCondition())
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
        retry.api.retry_call(f_mock, exceptions=RuntimeError, tries=tries, condition=mockCondition())
    except RuntimeError:
        pass

    assert f_mock.call_count == tries


def test_retry_call_2():
    side_effect = [RuntimeError, RuntimeError, 3]
    f_mock = MagicMock(side_effect=side_effect)
    tries = 5
    result = None
    try:
        result = retry.api.retry_call(f_mock, exceptions=RuntimeError, tries=tries, condition=mockCondition())
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
        result = retry.api.retry_call(f_mock, fargs=[return_value], condition=mockCondition())
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
        result = retry.api.retry_call(f_mock, fkwargs=kwargs, condition=mockCondition())
    except RuntimeError:
        pass

    assert result == kwargs['value']
    assert f_mock.call_count == 1
