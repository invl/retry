import asyncio
from contextlib import contextmanager, AbstractContextManager, ExitStack
import logging
import random
import traceback
import threading
from functools import partial

import inspect

from .compat import decorator

logging_logger = logging.getLogger(__name__)

import inspect

from .compat import decorator

logging_logger = logging.getLogger(__name__)

class ConditionWrappedWait(AbstractContextManager):
    def __init__(self, c):
        self.c = c

    def __enter__(self):
        self.c.acquire()
        return self

    def wait(self, n):
        self.c.wait(n)

    @contextmanager
    def _cleanup_on_error(self):
        with ExitStack() as stack:
            stack.push(self)
            yield
            # The validation check passed and didn't raise an exception
            # Accordingly, we want to keep the resource, and pass it
            # back to our caller
            stack.pop_all()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.c.release()


def __retry_internal(
    f,
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=None,
    backoff=1,
    jitter=0,
    show_traceback=False,
    logger=logging_logger,
    fail_callback=None,
    condition=None,
):
    _tries, _delay = tries, delay

    while _tries:
        try:
            return f()

        except exceptions as e:
            _tries -= 1

            if logger:
                _log_attempt(tries, show_traceback, logger, _tries, _delay, e)

            if not _tries:
                raise

            if fail_callback is not None:
                fail_callback(e)

            with ConditionWrappedWait(condition) as _condition:
                _condition.wait(_delay)

            _delay = _new_delay(max_delay, backoff, jitter, _delay)


async def __retry_internal_async(
    f,
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=None,
    backoff=1,
    jitter=0,
    show_traceback=False,
    logger=logging_logger,
    fail_callback=None,
):
    _tries, _delay = tries, delay

    while _tries:
        try:
            return await f()

        except exceptions as e:
            _tries -= 1

            if logger:
                _log_attempt(tries, show_traceback, logger, _tries, _delay, e)

            if not _tries:
                raise

            if fail_callback is not None:
                await fail_callback(e)

            await asyncio.sleep(_delay)

            _delay = _new_delay(max_delay, backoff, jitter, _delay)


def _log_attempt(tries, show_traceback, logger, _tries, _delay, e):
    if _tries:
        if show_traceback:
            tb_str = "".join(traceback.format_exception(None, e, e.__traceback__))
            logger.warning(tb_str)

        logger.warning(
            "%s, attempt %s/%s failed - retrying in %s seconds...",
            e,
            tries - _tries,
            tries,
            _delay,
        )

    elif tries > 1:
        logger.warning(
            "%s, attempt %s/%s failed - giving up!", e, tries - _tries, tries
        )


def _new_delay(max_delay, backoff, jitter, _delay):
    _delay *= backoff
    _delay += random.uniform(*jitter) if isinstance(jitter, tuple) else jitter

    if max_delay is not None:
        _delay = min(_delay, max_delay)

    return _delay


def _is_async(f):
    return asyncio.iscoroutinefunction(f) and not inspect.isgeneratorfunction(f)


def _get_internal_function(f):
    return __retry_internal_async if _is_async(f) else __retry_internal


def _check_params(f, show_traceback=False, logger=logging_logger, fail_callback=None):
    assert not show_traceback or logger is not None, "`show_traceback` needs `logger`"

    assert not fail_callback or (
        (_is_async(f) and _is_async(fail_callback))
        or (not _is_async(f) and not _is_async(fail_callback))
    ), "If the retried function is async, fail_callback needs to be async as well or vice versa"


def retry(
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=None,
    backoff=1,
    jitter=0,
    show_traceback=False,
    logger=logging_logger,
    fail_callback=None,
    condition=threading.Condition(),
):
    """Returns a retry decorator.

    :param exceptions: an exception or a tuple of exceptions to catch. default: Exception.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param delay: initial delay between attempts (in seconds). default: 0.
    :param max_delay: the maximum value of delay (in seconds). default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param show_traceback: if True, the traceback of the exception will be logged.
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    :param fail_callback: fail_callback(e) will be called on failed attempts.
    :param condition: threading.Condition variable used to .wait, a default one is 
                    provided.  time.sleep is not used since it locks up all threads simultaneously.
    :returns: a retry decorator.
    """

    @decorator
    def retry_decorator(f, *fargs, **fkwargs):
        return retry_call(
            f,
            fargs,
            fkwargs,
            exceptions,
            tries,
            delay,
            max_delay,
            backoff,
            jitter,
            show_traceback,
            logger,
            fail_callback,
            condition=condition,
        )

    return retry_decorator


def retry_call(
    f,
    fargs=None,
    fkwargs=None,
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=None,
    backoff=1,
    jitter=0,
    show_traceback=False,
    logger=logging_logger,
    fail_callback=None,
    condition=None,
):
    """
    Calls a function and re-executes it if it failed.

    :param f: the function to execute.
    :param fargs: the positional arguments of the function to execute.
    :param fkwargs: the named arguments of the function to execute.
    :param exceptions: an exception or a tuple of exceptions to catch. default: Exception.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param delay: initial delay between attempts (in seconds). default: 0.
    :param max_delay: the maximum value of delay (in seconds). default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param show_traceback: if True, the traceback of the exception will be logged.
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    :param fail_callback: fail_callback(e) will be called on failed attempts.
    :returns: the result of the f function.
    """
    
    args = fargs or list()
    kwargs = fkwargs or dict()

    _check_params(f, show_traceback, logger, fail_callback)

    func = _get_internal_function(f)
    args_list = []
    path_through_args = dict(
        exceptions=exceptions,
        tries=tries,
        delay=delay,
        max_delay=max_delay,
        backoff=backoff,
        jitter=jitter,
        show_traceback=show_traceback,
        logger=logger,
        fail_callback=fail_callback,
    )
    if hasattr(inspect, 'getfullargspec'):
        args_list = inspect.getfullargspec(func).args
    else:
        args_list = inspect.getargspec(func).args

    if 'condition' in args_list:
        path_through_args['condition'] = condition
    return func(
        partial(f, *args, **kwargs),
        **path_through_args,
    )
