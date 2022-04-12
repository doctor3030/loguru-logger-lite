import sys
import time
from unittest import TestCase
import json
from kafka import KafkaConsumer
from loguru import logger as loguru_base

sys.path.append('../')
from loguru_logger_lite import Logger, LogLevels, Sink, Sinks, \
    BaseSinkOptions, KafkaSinkOptions, FileSinkOptions


class TestLogger(TestCase):

    kafka_bootstrap_servers = ['10.0.0.74:9092']
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
                 opts=BaseSinkOptions(level=LogLevels.TRACE))
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
                 opts=FileSinkOptions(path=path, level=LogLevels.TRACE))
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
                 opts=KafkaSinkOptions(level=LogLevels.TRACE,
                                       bootstrap_servers=consumer_config['bootstrap_servers'],
                                       sink_topic=topic))
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
                    print(val['text'])
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
            level=LogLevels.TRACE,
            bootstrap_servers=consumer_config['bootstrap_servers'],
            sink_topic=topic)
        )

        logger = loguru_base
        logger.add(kafka_sink.sink, **json.loads(kafka_sink.opts.json(exclude_unset=True)))

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
                    print(val['text'])
            consumer.commit()

            if time.time() - start > 5:
                print('Closing cnsumer..')
                consumer.close()
                break
