# -*- coding: utf-8 -*-

import time
import json

from pprint import pprint

from thrift.transport import TTransport, TSocket
from thrift.protocol import TCompactProtocol

from thrift_gen.flume import ThriftSourceProtocol
from thrift_gen.flume.ttypes import ThriftFlumeEvent


class TestPipeline(object):

    def process_item(self, item, spider):
        pprint(item)
        return item


class FlumePipeline(object):

    def __init__(self, conf):
        self.host = conf['host']
        self.port = conf['port']
        self.unix_socket = conf.get('unix_socket', None)
        self.timeout = conf.get('timeout', None)
        self.batch_size = conf.get('batch_size', 10)
        self.events = []

    @classmethod
    def from_crawler(cls, crawler):
        flume_conf = crawler.settings.get('flume_conf')
        return cls(flume_conf)

    def open_spider(self, spider):
        self._socket = TSocket.TSocket(self.host, self.port, self.unix_socket)
        self._ts_factory = TTransport.TFramedTransportFactory()
        self._transport = self._ts_factory.getTransport(self._socket)
        self._protocol = TCompactProtocol.TCompactProtocol(self._transport)
        self.client = ThriftSourceProtocol.Client(
            iprot=self._protocol, oprot=self._protocol)
        self.connect()

    def connect(self):
        self._socket.setTimeout(self.timeout)

    def close_spider(self, spider):
        self._transport.close()

    def process_item(self, item, spider):
        event = ThriftFlumeEvent(
            headers={'timestamp': int(time.time())},
            body=json.dumps(dict(item))
        )
        self.events.append(event)
        if len(self.events) >= self.batch_size:
            self.batch()
        return item

    def batch(self):
        self.client.appendBatch(self.events)
