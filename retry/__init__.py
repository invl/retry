__all__ = ['retry', 'retry_call']

import logging

from .api import retry, retry_call
from .compat import NullHandler


# Set default logging handler to avoid "No handler found" warnings.
log = logging.getLogger(__name__)
log.addHandler(NullHandler())
