reretry
=======

.. image:: https://img.shields.io/pypi/dm/reretry.svg?maxAge=2592000
        :target: https://pypi.python.org/pypi/reretry/

.. image:: https://img.shields.io/pypi/v/reretry.svg?maxAge=2592000
        :target: https://pypi.python.org/pypi/reretry/

.. image:: https://img.shields.io/pypi/l/reretry.svg?maxAge=2592000
        :target: https://pypi.python.org/pypi/reretry/


Easy to use retry decorator.

This package is a fork from the `retry package <https://github.com/invl/retry>`_, with a lot of added community-sourced features.


Features
--------

- Retry on specific exceptions.
- Set a maximum number of retries.
- Set a delay between retries.
- Set a maximum delay between retries.
- Set backoff and jitter parameters.
- Show traceback of an error that lead to a failed attempt.
- Use a custom logger.
- Call a custom callback after each failed attempt.
- Can be used with async functions.

- No external dependencies (stdlib only).
- (Optionally) Preserve function signatures (`pip install decorator`).


Installation
------------

.. code-block:: bash

    $ pip install reretry


API
---

retry decorator
^^^^^^^^^^^^^^^

.. code:: python

    def retry(
        exceptions=Exception, tries=-1, delay=0, max_delay=None, backoff=1,
        jitter=0, show_traceback=False, logger=logging_logger, fail_callback=None
    ):
        """Return a retry decorator.

        Args:
            exceptions: an exception or a tuple of exceptions to catch. default: Exception.
            tries: the maximum number of attempts. default: -1 (infinite).
            delay: initial delay between attempts (in seconds). default: 0.
            max_delay: the maximum value of delay (in seconds). default: None (no limit).
            backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
            jitter: extra seconds added to delay between attempts. default: 0.
                       fixed if a number, random if a range tuple (min, max)
            show_traceback: Print traceback before retrying (Python3 only). default: False.
            logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                       default: retry.logging_logger. if None, logging is disabled.
            fail_callback: fail_callback(e) will be called on failed attempts.
        """

Various retrying logic can be achieved by combination of arguments.


Examples
""""""""

.. code:: python

    from reretry import retry

.. code:: python

    @retry()
    def make_trouble():
        '''Retry until succeeds'''

.. code:: python

    @retry()
    async def async_make_trouble():
        '''Retry an async function until it succeeds'''

.. code:: python

    @retry(ZeroDivisionError, tries=3, delay=2)
    def make_trouble():
        '''Retry on ZeroDivisionError, raise error after 3 attempts,
        sleep 2 seconds between attempts.'''

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

    def callback(e: Exception):
        '''Print error message'''
        print(e)

    @retry(ValueError, fail_callback=callback):
    def make_trouble():
        '''Retry on ValueError, between attempts call callback(e)
        (where e is the Exception raised).'''

.. code:: python

    # If you enable logging, you can get warnings like 'ValueError, retrying in
    # 1 seconds'
    if __name__ == '__main__':
        import logging
        logging.basicConfig()
        make_trouble()

retry_call
^^^^^^^^^^

.. code:: python

    def retry_call(
        f, fargs=None, fkwargs=None, exceptions=Exception, tries=-1, delay=0,
        max_delay=None, backoff=1, jitter=0, show_traceback=False, logger=logging_logger,
        fail_callback=None
    ):

Calls a function and re-executes it if it failed.

This is very similar to the decorator, except that it takes a function and its arguments as parameters. The use case behind it is to be able to dynamically adjust the retry arguments.

.. code:: python

    import requests

    from reretry.api import retry_call


    def make_trouble(service, info=None):
        if not info:
            info = ''
        r = requests.get(service + info)
        return r.text


    def what_is_my_ip(approach=None):
        if approach == "optimistic":
            tries = 1
        elif approach == "conservative":
            tries = 3
        else:
            # skeptical
            tries = -1
        result = retry_call(
            make_trouble,
            fargs=["http://ipinfo.io/"],
            fkwargs={"info": "ip"},
            tries=tries
        )
        print(result)

    what_is_my_ip("conservative")
