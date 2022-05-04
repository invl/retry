import logging
import random
import sys
import time
import traceback
from functools import partial

from .compat import decorator

logging_logger = logging.getLogger(__name__)


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
):
    """
    Executes a function and retries it if it failed.

    :param f: the function to execute.
    :param exceptions: an exception or a tuple of exceptions to catch. default: Exception.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param delay: initial delay between attempts (in seconds). default: 0.
    :param max_delay: the maximum value of delay (in seconds). default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    :param fail_callback: fail_callback(e) will be called on failed attempts.
    :returns: the result of the f function.
    """
    _tries, _delay = tries, delay
    while _tries:
        try:
            return f()

        except exceptions as e:
            _tries -= 1

            if not _tries:
                if logger is not None and tries > 1:
                    logger.warning(
                        "%s, attempt %s/%s failed - giving up!",
                        e,
                        tries - _tries,
                        tries,
                    )
                raise

            assert (
                not show_traceback or logger is not None
            ), "Show traceback needs logger"
            assert (
                not show_traceback or sys.version_info[0] != 2
            ), "Traceback not supported in Python2"

            if logger is not None:
                if show_traceback:
                    tb_str = "".join(
                        traceback.format_exception(None, e, e.__traceback__)
                    )
                    logger.warning(tb_str)
                logger.warning(
                    "%s, attempt %s/%s failed - retrying in %s seconds...",
                    e,
                    tries - _tries,
                    tries,
                    _delay,
                )

            if fail_callback is not None:
                fail_callback(e)

            time.sleep(_delay)
            _delay *= backoff

            _delay += random.uniform(*jitter) if isinstance(jitter, tuple) else jitter

            if max_delay is not None:
                _delay = min(_delay, max_delay)


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
):
    """Returns a retry decorator.

    :param exceptions: an exception or a tuple of exceptions to catch. default: Exception.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param delay: initial delay between attempts (in seconds). default: 0.
    :param max_delay: the maximum value of delay (in seconds). default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    :param fail_callback: fail_callback(e) will be called on failed attempts.
    :returns: a retry decorator.
    """

    @decorator
    def retry_decorator(f, *fargs, **fkwargs):
        args = fargs or list()
        kwargs = fkwargs or dict()
        return __retry_internal(
            partial(f, *args, **kwargs),
            exceptions,
            tries,
            delay,
            max_delay,
            backoff,
            jitter,
            show_traceback,
            logger,
            fail_callback,
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
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    :param fail_callback: fail_callback(e) will be called on failed attempts.
    :returns: the result of the f function.
    """
    args = fargs or list()
    kwargs = fkwargs or dict()
    return __retry_internal(
        partial(f, *args, **kwargs),
        exceptions,
        tries,
        delay,
        max_delay,
        backoff,
        jitter,
        show_traceback,
        logger,
        fail_callback,
    )
