import sys
import time
from itertools import count

from decorator import decorator


class StderrLogger(object):

    def warning(self, msg):
        sys.stderr.write(msg + '\n')


def retry(exceptions=Exception, tries=None, delay=3, backoff=2, logger=StderrLogger()):

    @decorator
    def retry_decorator(f, *args, **kwargs):
        for i in count():
            try:
                return f(*args, **kwargs)
            except exceptions, e:
                if tries is not None and i >= tries:
                    raise
                round_delay = delay * backoff ** i
                logger.warning('{}, retrying in {} seconds...'.format(e, round_delay))
                time.sleep(round_delay)

    return retry_decorator

if __name__ == '__main__':
    @retry(tries=3, delay=1)
    def f():
        1 / 0
    f()
