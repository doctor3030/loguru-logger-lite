# loguru_logger_lite

This simple logger is built on top of [loguru](https://github.com/Delgan/loguru) to make a quick setup for basic
logging.

The logger has four transports (called "sinks" here, same as in loguru):

- stdout
- stderr
- file
- kafka

The standard sinks (stdout, stderr and file) are configured with the same arguments as in loguru (see "add" method
in [loguru documentation](https://loguru.readthedocs.io/en/stable/api/logger.html)).

# Installation

```
pip install loguru-logger-lite
```

# Usage

### get_default_logger() method

The basic logger can be created using **get_default_logger** method. The **get_default_logger** method returns
preconfigured loguru logger with **stdout** and **stderr** sinks. All messages whose **level** is less than **ERROR**
are sent to **stdout** while messages whose **level** is **ERROR** or above are sent to **stderr**.

```python
from loguru_logger_lite import Logger

logger = Logger.get_default_logger()

logger.info('Test log message')
```

The output will be like this:

```
MODULE: example | COMPONENT: __main__ | PID: 230552 | INFO | 2022-04-08T19:59:36.290220-0400 | Test log message
```

> **_NOTE:_** The above log message format will also be a default format if the **format** option is not provided in sink configuration.

### get_logger(sinks) method

The **get_logger** method is used to create a logger with a custom set of sinks. This method expects a list of **Sink**
objects and returns a loguru logger with the configured sinks.

```python
from loguru_logger_lite import Logger, LogLevels, Sink, Sinks, \
    KafkaSinkOptions, FileSinkOptions

logger = Logger.get_logger([
    Sink(name=Sinks.FILE,
         opts=FileSinkOptions(path='test.log', level=LogLevels.DEBUG)),
    Sink(name=Sinks.KAFKA,
         opts=KafkaSinkOptions(level=LogLevels.TRACE,
                               bootstrap_servers=['localhost:9092'],
                               sink_topic='log_topic'))
])

logger.info('Test log message')
```

> **_NOTE:_** When using **file** and **kafka** sinks, the output will be a json with **text** and **record** root items.
> The **text** item is formatted log message and **record** is loguru Record dictionary (see [loguru documentation](https://loguru.readthedocs.io/en/stable/api/logger.html)).

### Kafka sink
The kafka sink, along with the basic loguru options, has additional parameters for kafka producer:

- bootstrap_servers - a list of strings of kafka brokers addresses.
- producer_config - kafka producer configuration (see [kafka-python documentation](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html)).
- sink_topic - a kafka topic name where to send log messages.

### get_kafka_sink(options) method

The **kafka** sink can be used standalone with existing loguru logger:
```python
from loguru import logger
from loguru_logger_lite import Logger, LogLevels, KafkaSinkOptions

kafka_sink = Logger.get_kafka_sink(options=KafkaSinkOptions(
    level=LogLevels.TRACE,
    bootstrap_servers=['localhost:9092'],
    sink_topic='log_topic')
)

logger.add(kafka_sink)

logger.info('Test log message')
```

## LICENSE

MIT

##### AUTHOR: [Dmitry Amanov](https://github.com/doctor3030)