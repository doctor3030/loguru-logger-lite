from __future__ import absolute_import

__title__ = 'loguru-logger'
__author__ = 'Dmitry Amanov'
__license__ = 'Apache License 2.0'
__copyright__ = 'Copyright 2022 Dmitry Amanov'

# Set default logging handler to avoid "No handler found" warnings.
import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

from logger import Logger, Sinks

__all__ = [
    'Logger', 'Sinks',
]
