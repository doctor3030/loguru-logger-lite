import sys
import time
from unittest import IsolatedAsyncioTestCase, TestCase
import json
import uuid
from kafka import KafkaConsumer


sys.path.append('../')

from loguru_logger_lite import Logger, LogLevels, Sink, Sinks, \
    BaseSinkOptions, KafkaSinkOptions, FileSinkOptions


consumer_config = {
        'bootstrap_servers': ['10.0.0.74:9092'],
        'group_id': str(uuid.uuid4()),
        'auto_offset_reset': 'earliest',
        'enable_auto_commit': False,
        'value_deserializer': lambda x: json.loads(x.decode('utf-8')),
        'session_timeout_ms': 25000
    }
topic = 'test_topic'


class TestLogger(TestCase):


    sinks = [
        Sink(name=Sinks.STDOUT,
             opts=BaseSinkOptions(level=LogLevels.INFO, colorize=True)),
        Sink(name=Sinks.STDERR,
             opts=BaseSinkOptions(level=LogLevels.ERROR, colorize=True)),
        Sink(name=Sinks.FILE,
             opts=FileSinkOptions(path='./test.log', level=LogLevels.INFO)),
        Sink(name=Sinks.KAFKA,
             opts=KafkaSinkOptions(level=LogLevels.INFO,
                                   bootstrap_servers=consumer_config['bootstrap_servers'],
                                   sink_topic=topic))
    ]
    LOGGER = Logger.get_logger(sinks)

    consumer = KafkaConsumer(**consumer_config)
    consumer.subscribe(topics=[topic])

    def test_default_logger(self):
        self.LOGGER.info('Hello!')
        self.LOGGER.error('Hello with error!')

        time.sleep(2)

        start = time.time()
        while True:
            message_batch = self.consumer.poll()
            for partition_batch in message_batch.values():
                for message in partition_batch:
                    val = message.value
                    record = val['record']
                    print('MODULE: {module} | COMPONENT: {component} | PID: {pid} | {level} | {timestamp} | {msg}'.format(
                        module=record['module'],
                        component=record['name'],
                        pid=record['process']['id'],
                        level=record['level']['name'],
                        timestamp=record['time']['repr'],
                        msg=record['message']
                    ))
            self.consumer.commit()

            if time.time() - start > 10:
                # self.loguru_logger_lite.info('Shutting down..')
                self.consumer.close()
                break

            # await asyncio.sleep(0.5)
