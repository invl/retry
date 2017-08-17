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
from retry.api import retry_generator


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


def test_retry_with_generator():
    """Tests that 3 tries occur and generated result:
    <Initial call>
    <New call due to RuntimeError(0)>
    [1, 2]
    <New call due to RuntimeError(3)>
    [1, 2, 4]
    """
    _vals = [RuntimeError(0), 1, 2, RuntimeError(3), 4]
    f_calls = list()

    @retry(exceptions=RuntimeError, generator=True)
    def f_mock():
        f_calls.append(())
        for v in _vals:
            if isinstance(v, BaseException):
                _vals.remove(v)
                raise v
            else:
                yield v

    tries = 3
    expected = [1, 2, 1, 2, 4]
    actual = []
    try:
        actual.extend(x for x in f_mock())
    except RuntimeError:
        pass

    assert len(f_calls) == tries
    assert actual == expected


def mock_generator(*vals):
    _vals = list(vals)
    calls = list()

    def tmp_generator(*args, **kwargs):
        calls.append((args, kwargs))
        for v in _vals:
            if isinstance(v, BaseException):
                _vals.remove(v)
                raise v
            else:
                yield v

    return tmp_generator, calls


def test_retry_generator():
    """Tests that 3 tries occur and generated result:
    <Initial call>
    <New call due to RuntimeError(0)>
    <New call due to RuntimeError(1)>
    """
    f_mock, f_calls = mock_generator(RuntimeError(0), RuntimeError(1))
    tries = 3
    expected = []
    actual = []
    try:
        actual.extend(x for x in retry_generator(f_mock,  exceptions=RuntimeError, tries=tries))
    except RuntimeError:
        pass

    assert len(f_calls) == 3
    assert actual == expected


def test_retry_generator_2():
    """Tests that 3 tries occur and generated result:
    <Initial call>
    <New call due to RuntimeError(0)>
    <New call due to RuntimeError(1)>
    [2]
    """
    f_mock, f_calls = mock_generator(RuntimeError(0), RuntimeError(1), 2)
    tries = 5
    expected = [2]
    actual = []
    try:
        actual.extend(x for x in retry_generator(f_mock, exceptions=RuntimeError, tries=tries))
    except RuntimeError:
        pass

    assert len(f_calls) == 3
    assert actual == expected


def test_retry_generator_3():
    """Tests that 3 tries occur and generated result:
    <Initial call>
    [0]
    <New call due to RuntimeError(1)>
    [0]
    <New call due to RuntimeError(2)>
    [0]
    """
    f_mock, f_calls = mock_generator(0, RuntimeError(1), RuntimeError(2))
    tries = 5
    expected = [0, 0, 0]
    actual = []
    try:
        actual.extend(x for x in retry_generator(f_mock, exceptions=RuntimeError, tries=tries))
    except RuntimeError:
        pass

    assert len(f_calls) == 3
    assert actual == expected


def test_retry_generator_4():
    """Tests that 2 tries (vs. 3 for test above, due to parameter tries) occur and generated result:
    <Initial call>
    [0]
    <New call due to RuntimeError(1)>
    [0]
    <New call due to RuntimeError(2)>
    """
    f_mock, f_calls = mock_generator(0, RuntimeError(1), RuntimeError(2))
    tries = 2
    expected = [0, 0]
    actual = []
    try:
        actual.extend(x for x in retry_generator(f_mock, exceptions=RuntimeError, tries=tries))
    except RuntimeError:
        pass

    assert len(f_calls) == 2
    assert actual == expected


def test_retry_generator_with_args():
    """Tests args are used"""
    f_mock, f_calls = mock_generator('test')
    tries = 2
    args = (1, 3)
    try:
        _ = [x for x in retry_generator(f_mock, fargs=args, exceptions=RuntimeError, tries=tries)]
    except RuntimeError:
        pass

    assert len(f_calls) == 1
    assert f_calls[0][0] == args


def test_retry_generator_with_kwargs():
    """Tests kwargs are used"""
    f_mock, f_calls = mock_generator('test')
    tries = 2
    kwargs = {'a': 1, 'b': 3}
    try:
        _ = [x for x in retry_generator(f_mock, fkwargs=kwargs, exceptions=RuntimeError, tries=tries)]
    except RuntimeError:
        pass

    assert len(f_calls) == 1
    assert f_calls[0][1] == kwargs
