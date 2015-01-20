import time
import logging
from itertools import count

from decorator import decorator

log = logging.getLogger(__name__)


def retry(exceptions=Exception, tries=float('inf'), delay=0, backoff=1):
    """Return a decorator for retrying.

    :param exceptions: an exception or a tuple of exceptions to catch
    :param tries: the maximum number of attempts
    :param delay: how many seconds to wait between attmpts
    :param backoff: delay growth factor
    """

    @decorator
    def retry_decorator(f, *args, **kwargs):
        for i in count():
            try:
                return f(*args, **kwargs)
            except exceptions as e:
                if i >= tries:
                    raise
                round_delay = delay * backoff ** i
                log.warning('%s, retrying in %s seconds...', e, round_delay)
                time.sleep(round_delay)

    return retry_decorator
