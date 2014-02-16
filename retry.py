import logging
import time
from itertools import count

from decorator import decorator


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def retry(exceptions=Exception, tries=None, delay=0, backoff=2):

    @decorator
    def retry_decorator(f, *args, **kwargs):
        for i in count():
            try:
                return f(*args, **kwargs)
            except exceptions, e:
                if tries is not None and i >= tries:
                    raise
                round_delay = delay * backoff ** i
                log.warning('{}, retrying in {} seconds...'.format(e, round_delay))
                time.sleep(round_delay)

    return retry_decorator

if __name__ == '__main__':
    logging.basicConfig()

    @retry(tries=3, delay=1)
    def f():
        1 / 0
    f()
