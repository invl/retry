import functools
import time
import logging
from itertools import count

try:
    from decorator import decorator
except ImportError:
    def decorator(caller):
        """ Turns caller into a decorator.
        Unlike decorator module, function signature is not preserved.

        :param caller: caller(f, *args, **kwargs)
        """
        def decor(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                return caller(f, *args, **kwargs)
            return wrapper
        return decor


logging_logger = logging.getLogger(__name__)


def retry(exceptions=Exception, tries=float('inf'), delay=0, backoff=1, logger=logging_logger):
    """Return a decorator for retrying.

    :param exceptions: an exception or a tuple of exceptions to catch
    :param tries: the maximum number of attempts
    :param delay: how many seconds to wait between attmpts
    :param backoff: delay growth factor
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   defaults to retry.logging_logger. If logger=None, logging is disabled.
    """

    @decorator
    def retry_decorator(f, *args, **kwargs):
        for i in count():
            try:
                return f(*args, **kwargs)
            except exceptions as e:
                if i >= tries - 1:
                    raise
                round_delay = delay * backoff ** i
                if logger is not None:
                    logger.warning('%s, retrying in %s seconds...', e, round_delay)
                time.sleep(round_delay)

    return retry_decorator
