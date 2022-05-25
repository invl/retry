import asyncio
from importlib import reload
from unittest.mock import MagicMock
import pytest
import time
import logging

logging_logger = logging.Logger(__name__)

class MockCondition(object):
    mock_sleep_time = [0]
    def acquire(self):
        logging_logger.warning('in acquire')
        return True
        
    def release(self):
        logging_logger.warning('in release')
        
    def wait(self, seconds):
        logging_logger.warning('in wait')
        print('\n'*10+'in wait'+'\n')
        MockCondition.mock_sleep_time[0] += seconds


import threading
threading.Condition = MockCondition
from reretry.api import _is_async, retry, retry_call
import reretry.api

thread_loops = 0
total_thread_loops = 1000

def test_threaded_retry(monkeypatch):
    '''
    For this thread actual threading is used, threading condition is
    remocked at the end.
    '''
    reload(threading)
    hit = [0]

    tries = 5
    delay = 0.01
    backoff = 2

    @retry(tries=tries, delay=delay, backoff=backoff)
    def f():
        hit[0] += 1
        1 / 0

    def run():
        global thread_loops
        c = threading.Condition()
        c.acquire()
        thread_delay = delay / total_thread_loops
        for a in range(total_thread_loops):
            c.wait(thread_delay)
            thread_loops += 1
        c.release()

    test_thread = threading.Thread(target=run)
    test_thread.start()
    c = threading.Condition()
    # waiting for the test to start
    c.acquire()
    c.wait(.01)
    c.release()

    num_loops = thread_loops
    with pytest.raises(ZeroDivisionError):
        f()

    num_loops = thread_loops - num_loops
    test_thread.join()

    assert num_loops > 0 and num_loops < total_thread_loops
    threading.Condition = MockCondition
    assert hit[0] == tries
    assert mock_sleep_time[0] == sum(delay * backoff**i for i in range(tries - 1))




def test_retry(monkeypatch):
    MockCondition.mock_sleep_time = [0]

    monkeypatch.setattr(reretry.api.threading, 'Condition', MockCondition)

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
    assert MockCondition.mock_sleep_time[0] == \
        sum(delay * backoff**i for i in range(tries - 1))


def test_tries_inf():
    hit = [0]
    target = 10

    @retry(tries=float("inf"))
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
    MockCondition.mock_sleep_time = [0]

    monkeypatch.setattr(reretry.api.threading, 'Condition', MockCondition)
    
    print(':: condition', reretry.api.threading.Condition)

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
    assert MockCondition.mock_sleep_time[0] == delay * (tries - 1)


def test_fixed_jitter(monkeypatch):
    MockCondition.mock_sleep_time = [0]

    monkeypatch.setattr(reretry.api.threading, 'Condition', MockCondition)

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
    assert MockCondition.mock_sleep_time[0] == sum(range(tries - 1))


def test_retry_call():
    f_mock = MagicMock(side_effect=RuntimeError)
    tries = 2
    try:
        retry_call(f_mock, exceptions=RuntimeError, tries=tries
            , condition=MockCondition()
        )
    except RuntimeError:
        pass

    assert f_mock.call_count == tries


def test_retry_call_2():
    side_effect = [RuntimeError, RuntimeError, 3]
    f_mock = MagicMock(side_effect=side_effect)
    tries = 5
    result = None
    try:
        result = retry_call(f_mock, exceptions=RuntimeError, tries=tries
            , condition=MockCondition()
        )
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
        result = retry_call(f_mock, fargs=[return_value]
            , condition=MockCondition()
        )
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

    kwargs = {"value": -1}
    result = None
    f_mock = MagicMock(spec=f, return_value=kwargs["value"])
    try:
        result = retry_call(f_mock, fkwargs=kwargs
            , condition=MockCondition()
        )
    except RuntimeError:
        pass

    assert result == kwargs["value"]
    assert f_mock.call_count == 1


def test_retry_call_with_fail_callback():
    def f():
        raise RuntimeError

    def cb(error):
        pass

    callback_mock = MagicMock(spec=cb)
    try:
        retry_call(f, fail_callback=callback_mock, tries=2
            , condition=MockCondition()
        )
    except RuntimeError:
        pass

    assert callback_mock.called


def test_is_async():
    async def async_func():
        pass

    def non_async_func():
        pass

    def generator():
        yield


    assert _is_async(async_func)
    assert not _is_async(non_async_func)
    assert not _is_async(generator)
    assert not _is_async(generator())
    assert not _is_async(MagicMock(spec=non_async_func, return_value=-1))


@pytest.mark.asyncio
async def test_async():
    attempts = 1
    raised = False

    @retry(tries=2)
    async def f():
        await asyncio.sleep(0.1)
        nonlocal attempts, raised
        if attempts:
            raised = True
            attempts -= 1
            raise RuntimeError
        return True

    assert await f()
    assert raised
    assert attempts == 0


def test_check_params():
    with pytest.raises(AssertionError):
        retry_call(lambda: None, show_traceback=True, logger=None)

    async def async_func():
        pass

    def non_async_func():
        pass

    with pytest.raises(AssertionError):
        retry_call(async_func, fail_callback=non_async_func)
