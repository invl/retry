import sys
import time

from decorator import decorator


class StderrLogger(object):

    def warning(self, msg):
        sys.stderr.write(msg + '\n')


def retry(exceptions=Exception, tries=3, delay=3, backoff=2, logger=StderrLogger()):

    @decorator
    def retry_decorator(f, *args, **kwargs):
        for i in range(tries - 1):
            try:
                return f(*args, **kwargs)
            except exceptions, e:
                round_delay = delay * backoff ** i
                logger.warning('{}, retrying in {} seconds...'.format(e, round_delay))
                time.sleep(round_delay)
        return f(*args, **kwargs)

    return retry_decorator
