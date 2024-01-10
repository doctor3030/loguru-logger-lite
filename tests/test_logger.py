import sys
import time
from unittest import TestCase
import json
from kafka import KafkaConsumer
from loguru import logger as loguru_base
from dateutil import parser

sys.path.append('../')
from loguru_logger_lite import Logger, LogLevels, Sink, Sinks, \
    BaseSinkOptions, KafkaSinkOptions, FileSinkOptions


def kafka_value_serializer(data):
    formatted = {
        'module': data.split('|')[0].split(':')[1].strip(),
        'component': data.split('|')[1].split(':')[1].strip(),
        'pid': data.split('|')[2].split(':')[1].strip(),
        'level': data.split('|')[3].strip(),
        'timestamp': str(parser.parse(data.split('|')[4].strip()).timestamp() * 1000),
        'message': data.split('|')[5].strip(),
    }
    return json.dumps(formatted).encode('utf-8')


class TestLogger(TestCase):
    kafka_bootstrap_servers = ['127.0.0.1:29092']

    # kafka_bootstrap_servers = ['192.168.2.190:9092']

    def test_default_logger(self):
        print('\nTESTING DEFAULT LOGGER')
        logger = Logger.get_default_logger()
        logger.trace('Hello with trace!')
        logger.debug('Hello with debug!')
        logger.info('Hello with info!')
        logger.warning('Hello with warning!')
        logger.error('Hello with error!')
        logger.critical('Hello with critical!')

    def test_textio_logger(self):
        print('\nTESTING TEXTIO LOGGER')
        sinks = [
            Sink(name=Sinks.STDOUT,
                 opts=BaseSinkOptions(level=LogLevels.TRACE.value))
        ]

        logger = Logger.get_logger(sinks)
        logger.trace('Hello with trace!')
        logger.debug('Hello with debug!')
        logger.info('Hello with info!')
        logger.warning('Hello with warning!')
        logger.error('Hello with error!')
        logger.critical('Hello with critical!')

    def test_file_logger(self):
        print('\nTESTING FILE LOGGER')
        path = './test.log'
        sinks = [
            Sink(name=Sinks.FILE,
                 opts=FileSinkOptions(path=path, level=LogLevels.TRACE.value, serialize=False))
        ]

        logger = Logger.get_logger(sinks)
        logger.trace('Hello with trace!')
        logger.debug('Hello with debug!')
        logger.info('Hello with info!')
        logger.warning('Hello with warning!')
        logger.error('Hello with error!')
        logger.critical('Hello with critical!')
        print('Written: {}'.format(path))

    def test_kafka_logger(self):
        print('\nTESTING KAFKA LOGGER')

        consumer_config = {
            'bootstrap_servers': self.kafka_bootstrap_servers,
            'group_id': 'test_group',
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': False,
            'value_deserializer': lambda x: json.loads(x.decode('utf-8')),
            'session_timeout_ms': 25000
        }
        topic = 'test_topic'

        sinks = [
            Sink(name=Sinks.KAFKA,
                 opts=KafkaSinkOptions(
                     level=LogLevels.TRACE.value,
                     # serialize=False,
                     bootstrap_servers=consumer_config['bootstrap_servers'],
                     sink_topic=topic,
                     producer_config={
                         "value_serializer": kafka_value_serializer,
                     }
                 ))
        ]

        logger = Logger.get_logger(sinks)
        consumer = KafkaConsumer(**consumer_config)
        consumer.subscribe(topics=[topic])

        logger.trace('Hello with trace!')
        logger.debug('Hello with debug!')
        logger.info('Hello with info!')
        logger.warning('Hello with warning!')
        logger.error('Hello with error!')
        logger.critical('Hello with critical!')

        time.sleep(2)

        start = time.time()
        while True:
            message_batch = consumer.poll()
            for partition_batch in message_batch.values():
                for message in partition_batch:
                    val = message.value
                    # print(val['text'])
                    print(val)
            consumer.commit()

            if time.time() - start > 5:
                print('Closing cnsumer..')
                consumer.close()
                break

    def test_kafka_sink_standalone(self):
        print('\nTESTING KAFKA SINK STANDALONE')

        consumer_config = {
            'bootstrap_servers': self.kafka_bootstrap_servers,
            'group_id': 'test_group',
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': False,
            'value_deserializer': lambda x: json.loads(x.decode('utf-8')),
            'session_timeout_ms': 25000
        }
        topic = 'test_topic'

        kafka_sink = Logger.get_kafka_sink(options=KafkaSinkOptions(
            level=LogLevels.TRACE.value,
            bootstrap_servers=consumer_config['bootstrap_servers'],
            sink_topic=topic,
            producer_config={
                "value_serializer": kafka_value_serializer,
            }
        ),

        )

        logger = loguru_base
        logger.add(kafka_sink.sink, **kafka_sink.opts.model_dump(exclude_unset=True))

        consumer = KafkaConsumer(**consumer_config)
        consumer.subscribe(topics=[topic])

        logger.trace('Hello with trace!')
        logger.debug('Hello with debug!')
        logger.info('Hello with info!')
        logger.warning('Hello with warning!')
        logger.error('Hello with error!')
        logger.critical('Hello with critical!')

        time.sleep(2)

        start = time.time()
        while True:
            message_batch = consumer.poll()
            for partition_batch in message_batch.values():
                for message in partition_batch:
                    val = message.value
                    # print(val['text'])
                    print(val)
            consumer.commit()

            if time.time() - start > 5:
                print('Closing cnsumer..')
                consumer.close()
                break
