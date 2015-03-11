retry
=====

.. image:: https://pypip.in/d/retry/badge.png
        :target: https://pypi.python.org/pypi/retry/

.. image:: https://pypip.in/v/retry/badge.png
        :target: https://pypi.python.org/pypi/retry/

.. image:: https://pypip.in/license/retry/badge.png
        :target: https://pypi.python.org/pypi/retry/


easy to use retry decorator.


Features
--------

- No external dependency (stdlib only).
- (Optionally) Preserve function signatures (`pip install decorator`).
- Original traceback, easy to debug.


Installation
------------

.. code-block:: bash

    $ pip install retry


API
---

.. code:: python

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

various retrying logic can be achieved by combination of arguments.


Examples
--------

.. code:: python

    from retry import retry

.. code:: python

    @retry()
    def make_trouble():
        '''Retry until succeed'''

.. code:: python

    @retry(ZeroDivisionError, tries=3, delay=2)
    def make_trouble():
        '''Retry on ZeroDivisionError, raise error after 3 attempts, sleep 2 seconds between attempts.'''

.. code:: python

    @retry((ValueError, TypeError), delay=1, backoff=2)
    def make_trouble():
        '''Retry on ValueError or TypeError, sleep 1, 2, 4, 8, ... seconds between attempts.'''

.. code:: python

    @retry((ValueError, TypeError), delay=1, backoff=2, max_delay=4)
    def make_trouble():
        '''Retry on ValueError or TypeError, sleep 1, 2, 4, 4, ... seconds between attempts.'''

.. code:: python

    @retry(ValueError, delay=1, jitter=1)
    def make_trouble():
        '''Retry on ValueError, sleep 1, 2, 3, 4, ... seconds between attempts.'''

.. code:: python

    # If you enable logging, you can get warnings like 'ValueError, retrying in
    # 1 seconds'
    if __name__ == '__main__':
        import logging
        logging.basicConfig()
        make_trouble()
