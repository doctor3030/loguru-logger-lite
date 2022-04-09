from loguru import logger
from kafka import KafkaProducer
import pydantic
import sys
import enum
from typing import List, Optional, Union, Dict, Callable, TypedDict, TextIO, Awaitable
from datetime import time, timedelta
from logging import Handler


class Message(str):
    record: TypedDict


class Sinks(enum.Enum):
    STDOUT = 'stdout'
    STDERR = 'stderr'
    KAFKA = 'kafka'
    FILE = 'file'


class LogLevels(enum.Enum):
    TRACE = 5
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class DefaultFormats(enum.Enum):
    STDOUT_FORMAT = "MODULE: <green>{module}</green> | COMPONENT: <yellow>{name}</yellow> | " \
                    "PID: {process} | <level>{level}</level> | {time} | <level>{message}</level>",
    STDERR_FORMAT = "<blink>MODULE:</blink> <green>{module}</green> <blink>| " \
                    "COMPONENT:</blink> <yellow>{name}</yellow> <blink>| PID: {process} |" \
                    "</blink> <level>{level}</level> <blink>| {time} |</blink> <level>{message}</level>",
    PLAIN_FORMAT = "MODULE: {module} | COMPONENT: {name} | PID: {process} | {level} | {time} | {message}"


class BaseSinkOptions(pydantic.BaseModel):
    level: LogLevels
    format: Optional[str]
    filter: Optional[Union[str, Callable[[TypedDict], bool], Dict[Union[str, None], Union[str, int, bool]]]]
    colorize: Optional[bool]
    serialize: Optional[bool]
    backtrace: Optional[bool]
    diagnose: Optional[bool]
    enqueue: Optional[bool]
    catch: Optional[bool]


class KafkaSinkOptions(BaseSinkOptions):
    bootstrap_servers: List[str]
    producer_config: Optional[Dict]
    sink_topic: str


class FileSinkOptions(BaseSinkOptions):
    path: str
    rotation: Optional[Union[str, int, time, timedelta, Callable[[Message, TextIO], bool]]]
    retention: Optional[Union[str, int, timedelta, Callable[[List[str]], None]]]
    compression: Optional[Union[str, Callable[[str], None]]]
    delay: Optional[bool]
    mode: Optional[str]
    buffering: Optional[int]
    encoding: Optional[str]


class Sink(pydantic.BaseModel):
    name: Sinks
    opts: Union[BaseSinkOptions, KafkaSinkOptions, FileSinkOptions]
    sink: Optional[Union[TextIO, Callable[[Message], None], Handler, Callable[[Message], Awaitable[None]], str]]

    class Config:
        arbitrary_types_allowed = True


class Logger:

    def __init__(self, sinks: Optional[List[Sink]]):
        self.producer = None
        self.sink_topic = None

        if sinks:
            for sink in sinks:
                if sink.name == Sinks.KAFKA:
                    self.producer = Logger._get_producer(sink.opts.bootstrap_servers, sink.opts.producer_config)
                    self.sink_topic = sink.opts.sink_topic

    def __del__(self):
        if self.producer:
            self.producer.flush()
            self.producer.close()

    def _log_kafka_sink(self, msg):
        self.producer.send(self.sink_topic, value=msg.encode('utf-8'))

    @staticmethod
    def _get_producer(bootstrap_servers: List[str], producer_config: Dict = None):
        config = {
            'bootstrap_servers': bootstrap_servers,
            'value_serializer': lambda x: x,
        }
        if producer_config:
            for key in producer_config.keys():
                config[key] = producer_config.get(key)

        return KafkaProducer(**config)

    @staticmethod
    def _filter_stdout(msg) -> bool:
        if msg['level'].no > 30:
            return False
        else:
            return True

    @staticmethod
    def get_default_logger() -> logger:
        logger.remove()
        logger.add(sys.stdout,
                   format=DefaultFormats.STDOUT_FORMAT.value[0],
                   level=LogLevels.TRACE.value, filter=Logger._filter_stdout)
        logger.add(sys.stderr,
                   format=DefaultFormats.STDERR_FORMAT.value[0],
                   level=LogLevels.ERROR.value)
        return logger

    @staticmethod
    def get_logger(sinks: List[Sink]):
        _logger = Logger(sinks)
        return _logger._get_logger(sinks)

    @staticmethod
    def get_kafka_sink(options: KafkaSinkOptions):
        _logger = Logger(None)
        return _logger._get_kafka_sink(options)

    def _get_logger(self, sinks: List[Sink]) -> logger:
        logger.remove()

        for sink in sinks:
            sink_opts = sink.opts
            if sink.name == Sinks.STDOUT:
                logger.add(sys.stdout,
                           level=sink_opts.level.value,
                           format=(sink_opts.format if sink_opts.format else DefaultFormats.STDOUT_FORMAT.value[0]),
                           filter=(sink_opts.filter if sink_opts.filter else None),
                           colorize=(sink_opts.colorize if sink_opts.colorize else True),
                           serialize=(sink_opts.serialize if sink_opts.serialize else False),
                           backtrace=(sink_opts.backtrace if sink_opts.backtrace else False),
                           diagnose=(sink_opts.diagnose if sink_opts.diagnose else False),
                           enqueue=(sink_opts.enqueue if sink_opts.enqueue else False),
                           catch=(sink_opts.catch if sink_opts.catch else False))

            if sink.name == Sinks.STDERR:
                logger.add(sys.stderr,
                           format=(sink_opts.format if sink_opts.format else DefaultFormats.STDERR_FORMAT.value[0]),
                           level=sink_opts.level.value,
                           filter=(sink_opts.filter if sink_opts.filter else None),
                           colorize=(sink_opts.colorize if sink_opts.colorize else True),
                           serialize=(sink_opts.serialize if sink_opts.serialize else False),
                           backtrace=(sink_opts.backtrace if sink_opts.backtrace else False),
                           diagnose=(sink_opts.diagnose if sink_opts.diagnose else False),
                           enqueue=(sink_opts.enqueue if sink_opts.enqueue else False),
                           catch=(sink_opts.catch if sink_opts.catch else False))

            if sink.name == Sinks.KAFKA:
                logger.add(self._log_kafka_sink,
                           format=(sink_opts.format if sink_opts.format else DefaultFormats.PLAIN_FORMAT.value),
                           level=sink_opts.level.value,
                           filter=(sink_opts.filter if sink_opts.filter else None),
                           colorize=(sink_opts.colorize if sink_opts.colorize else False),
                           serialize=(sink_opts.serialize if sink_opts.serialize else True),
                           backtrace=(sink_opts.backtrace if sink_opts.backtrace else False),
                           diagnose=(sink_opts.diagnose if sink_opts.diagnose else False),
                           enqueue=(sink_opts.enqueue if sink_opts.enqueue else False),
                           catch=(sink_opts.catch if sink_opts.catch else False))

            if sink.name == Sinks.FILE.value:
                opts = {
                    'format': (sink_opts.format if sink_opts.format else DefaultFormats.PLAIN_FORMAT.value),
                    'level': sink_opts.level.value,
                    'filter': (sink_opts.filter if sink_opts.filter else None),
                    'colorize': (sink_opts.colorize if sink_opts.colorize else False),
                    'serialize': (sink_opts.serialize if sink_opts.serialize else True),
                    'backtrace': (sink_opts.backtrace if sink_opts.backtrace else False),
                    'diagnose': (sink_opts.diagnose if sink_opts.diagnose else False),
                    'enqueue': (sink_opts.enqueue if sink_opts.enqueue else False),
                    'catch': (sink_opts.catch if sink_opts.catch else False)
                }

                if sink_opts.rotation:
                    opts['rotation'] = sink_opts.rotation
                if sink_opts.retention:
                    opts['retention'] = sink_opts.retention
                if sink_opts.compression:
                    opts['compression'] = sink_opts.compression
                if sink_opts.delay:
                    opts['delay'] = sink_opts.delay
                if sink_opts.mode:
                    opts['mode'] = sink_opts.mode
                if sink_opts.buffering:
                    opts['buffering'] = sink_opts.buffering
                if sink_opts.encoding:
                    opts['encoding'] = sink_opts.encoding

                logger.add(sink_opts.path, **opts)

        return logger

    def _get_kafka_sink(self, options: KafkaSinkOptions):
        self.producer = Logger._get_producer(options.bootstrap_servers, options.producer_config)
        self.sink_topic = options.sink_topic

        opts = BaseSinkOptions(
            format=(options.format if options.format else DefaultFormats.PLAIN_FORMAT.value),
            level=options.level.value,
            filter=(options.filter if options.filter else None),
            colorize=(options.colorize if options.colorize else False),
            serialize=(options.serialize if options.serialize else True),
            backtrace=(options.backtrace if options.backtrace else False),
            diagnose=(options.diagnose if options.diagnose else False),
            enqueue=(options.enqueue if options.enqueue else False),
            catch=(options.catch if options.catch else False)
        )

        return Sink(name=Sinks.KAFKA,
                    sink=self._log_kafka_sink,
                    opts=opts)
