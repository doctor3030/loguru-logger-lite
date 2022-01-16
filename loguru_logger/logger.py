from loguru import logger
from kafka import KafkaProducer
import json
import sys
import enum
from typing import List


class Sinks(enum.Enum):
    STDOUT = 'stdout'
    STDERR = 'stderr'
    KAFKA = 'kafka'


def _filter_stdout(msg) -> bool:
    if msg['level'].no > 30:
        return False
    else:
        return True


class Logger:
    """
    Simple wrapper for loguru logger with kafka sink.

        Attributes
            DEFAULT_FORMAT : dict
                Formatted string representation for 'stdout_format', 'stderr_format' and 'plain_format'.
                'stdout_format' and 'stderr_format' are colorized while 'plain_format' is not.
            default_logger: loguru.logger
                Default logger includes stdout and stderr sinks.

        Methods
            get_logger(sinks: Sinks, **kwargs) -> logger
                Returns loguru logger with custom sinks.
    """

    DEFAULT_FORMAT = {
        'stdout_format': "MODULE: <yellow>{module}</yellow> | COMPONENT: <yellow>{name}</yellow> | PID: {process} | <green>{level}</green> | {time} | <cyan>{message}</cyan>",
        'stderr_format': "<blink>MODULE:</blink> <yellow>{module}</yellow> <blink>| COMPONENT:</blink> <yellow>{name}</yellow> <blink>| PID: {process} |</blink> {level} <blink>| {time} |</blink> {message}",
        'plain_format': "MODULE: {module} | COMPONENT: {name} | SERVICE_PID: {process} | SERVICE_ID: {extra[service_id]} | {level} | {time} | {message}"
    }

    def __init__(self, **kwargs):
        self.stdout_format = self.DEFAULT_FORMAT['stdout_format']
        self.stderr_format = self.DEFAULT_FORMAT['stderr_format']
        self.plain_format = self.DEFAULT_FORMAT['plain_format']

        self.producer = None
        self.sink_topic = None

        stdout_format = kwargs.get('stdout_format')
        stderr_format = kwargs.get('stderr_format')
        plain_format = kwargs.get('plain_format')

        if stdout_format is not None:
            self.stdout_format = stdout_format
        if stderr_format is not None:
            self.stderr_format = stderr_format
        if plain_format is not None:
            self.plain_format = plain_format

        self.default_logger = self._get_default_logger()

    def close(self):
        if self.producer is not None:
            self.producer.close()

    def _log_kafka_sink(self, msg):
        self.producer.send(self.sink_topic, value=json.loads(msg))

    def _get_default_logger(self) -> logger:
        logger.remove()
        logger.add(sys.stdout,
                   format=self.stdout_format,
                   level='INFO', filter=_filter_stdout)
        logger.add(sys.stderr,
                   format=self.stderr_format,
                   level='ERROR')
        return logger

    def get_logger(self, sinks: List[Sinks], **kwargs) -> logger:
        """
        Method to get logger with custom sinks.

        Args:
            sinks : Logger sinks
            **kwargs : Arguments

        Possible arguments:
            kafka_bootstrap_servers: List[str] Kafka cluster bootstrap servers for 'kafka' sink.

            kafka_sink_topic: str Topic name where to send logs for 'kafka' sink.

            path: str Path to log-file for 'file' sink.

            rotation: Rotation options for 'file' sink. See loguru docs.

            retention: Retention options for 'file' sink. See loguru docs.

        Returns: Loguru logger
        """

        logger.remove()
        if 'stdout' in sinks:
            logger.add(sys.stdout,
                       format=self.stdout_format,
                       level='INFO', filter=_filter_stdout)
        if 'stderr' in sinks:
            logger.add(sys.stderr,
                       format=self.stderr_format,
                       level='ERROR')
        if 'kafka' in sinks:
            kafka_bootstrap_servers = kwargs.get('kafka_bootstrap_servers')
            kafka_sink_topic = kwargs.get('kafka_sink_topic')

            assert kafka_bootstrap_servers is not None, 'Kafka sink requested but no bootstrap servers provided.'
            assert kafka_sink_topic is not None, 'Kafka sink requested but sink topic provided.'

            self.producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers,
                                          value_serializer=lambda x: json.dumps(x).encode('utf-8'))
            self.sink_topic = kafka_sink_topic

            logger.add(self._log_kafka_sink,
                       format=self.plain_format,
                       level='INFO', serialize=True)

        if 'file' in sinks:
            path = kwargs.get('path')
            rotation = kwargs.get('rotation')
            retention = kwargs.get('retention')

            assert path is not None, 'File sink requested but no path provided.'

            _kwargs = {
                'format': self.plain_format,
                'level': 'INFO',
                'serialize': True
            }
            if rotation is not None:
                _kwargs['rotation'] = rotation
            if retention is not None:
                _kwargs['retention'] = retention

            logger.add(path, **_kwargs)

        return logger
