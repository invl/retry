retry
=====

.. image:: https://pypip.in/d/retry/badge.png
        :target: https://pypi.python.org/pypi/retry/

.. image:: https://pypip.in/v/retry/badge.png
        :target: https://pypi.python.org/pypi/retry/

.. image:: https://pypip.in/license/retry/badge.png
        :target: https://pypi.python.org/pypi/retry/

retry is a decorator for isolating retrying logic, with logging intergraton.


Installation
------------

.. code-block:: bash

    $ pip install retry


API
---

.. code:: python

    def retry(exceptions=Exception, tries=float('inf'), delay=0, backoff=1, logger=logging.getLogger(__name__)):
        """Return a decorator for retrying.

        :param exceptions: an exception or a tuple of exceptions to catch
        :param tries: the maximum number of attempts
        :param delay: how many seconds to wait between attmpts
        :param backoff: delay growth factor
        :param logger: logger.warning(fmt, error, delay) will be called on failed attempts
        """

various retrying logic can be achieved by combination of arguments.


Examples
--------

.. code:: python

    from retry import retry

    # Retry until succeed
    @retry()
    def make_trouble():
        ...

    # Retry on ZeroDivisionError, fail after 3 attmpts, sleep 2 seconds per
    # attmpt
    @retry(ZeroDivisionError, tries=3, delay=2)
    def make_trouble():
        ...

    # Retry on ValueError and TypeError, sleep 1, 2, 4, 8, etc.. seconds
    @retry((ValueError, TypeError), delay=1, backoff=2)
    def make_trouble():
        ...

    # If you enable logging, you can get warnings like 'ValueError, retrying in
    # 1 seconds'
    if __name__ == '__main__':
        import logging
        logging.basicConfig()
        make_trouble()

