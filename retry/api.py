import time
import logging

try:
    from decorator import decorator
except ImportError:
    from .compat import decorator

logging_logger = logging.getLogger(__name__)


def retry(exceptions=Exception, tries=-1, delay=0, backoff=1, logger=logging_logger):
    """Return a retry decorator.

    :param exceptions: an exception or a tuple of exceptions to catch. default: Exception.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param delay: initial delay between attempts. default: 0.
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    """

    @decorator
    def retry_decorator(f, *args, **kwargs):
        _tries, _delay = tries, delay
        while _tries:
            _tries -= 1
            try:
                return f(*args, **kwargs)
            except exceptions as e:
                if not _tries:
                    raise
                if logger is not None:
                    logger.warning('%s, retrying in %s seconds...', e, _delay)
            time.sleep(_delay)
            _delay *= backoff

    return retry_decorator
