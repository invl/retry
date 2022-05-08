from unittest.mock import MagicMock

import asyncio

import pytest
from reretry.api import _is_async, retry, retry_call



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
        await asyncio.sleep(0.01)
        nonlocal attempts, raised
        if attempts:
            raised = True
            attempts -= 1
            raise RuntimeError
        return True

    assert await f()
    assert raised
    assert attempts == 0


@pytest.mark.asyncio
async def test_async_fail_and_callback():
    cb_called = False

    async def cb(exception: Exception):
        nonlocal cb_called
        cb_called = True
        assert exception.args[0] == 1

    attempts = 3

    @retry(tries=2, fail_callback=cb)
    async def f():
        await asyncio.sleep(0.01)
        nonlocal attempts
        if attempts:
            attempts -= 1
            raise RuntimeError(1)
        return True

    with pytest.raises(RuntimeError):
        await f()

    assert cb_called


def test_check_params():
    with pytest.raises(AssertionError):
        retry_call(lambda: None, show_traceback=True, logger=None)

    async def async_func():
        pass

    def non_async_func():
        pass

    with pytest.raises(AssertionError):
        retry_call(async_func, fail_callback=non_async_func)
