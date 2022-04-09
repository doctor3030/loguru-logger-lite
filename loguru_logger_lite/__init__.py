from __future__ import absolute_import

__title__ = 'loguru-loguru_logger_lite-lite'
__author__ = 'Dmitry Amanov'
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

from loguru_logger_lite.logger import Logger, Sinks, LogLevels, Sink, BaseSinkOptions, KafkaSinkOptions, FileSinkOptions

__all__ = [
    'Logger', 'Sinks', 'LogLevels', 'Sink', 'BaseSinkOptions', 'KafkaSinkOptions', 'FileSinkOptions'
]
