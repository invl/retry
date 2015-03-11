import random
import time
import logging

from .compat import decorator


logging_logger = logging.getLogger(__name__)


def retry(exceptions=Exception, tries=-1, delay=0, max_delay=None, backoff=1, jitter=0, logger=logging_logger):
    """Return a retry decorator.

    :param exceptions: an exception or a tuple of exceptions to catch. default: Exception.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param delay: initial delay between attempts. default: 0.
    :param max_delay: the maximum value of delay. default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    """

    @decorator
    def retry_decorator(f, *args, **kwargs):
        _tries, _delay = tries, delay
        while _tries:
            try:
                return f(*args, **kwargs)
            except exceptions as e:
                _tries -= 1
                if not _tries:
                    raise

                if logger is not None:
                    logger.warning('%s, retrying in %s seconds...', e, _delay)

                time.sleep(_delay)
                _delay *= backoff

                if isinstance(jitter, tuple):
                    _delay += random.uniform(*jitter)
                else:
                    _delay += jitter

                if max_delay is not None:
                    _delay = min(_delay, max_delay)

    return retry_decorator
