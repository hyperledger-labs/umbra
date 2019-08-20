import logging

logger = logging.getLogger(__name__)

import json

from elasticsearch import Elasticsearch
from datetime import datetime
from elasticsearch.exceptions import NotFoundError, ConnectionError, TransportError


class ES:
    def __init__(self, hosts='172.17.0.1:9200'):
        self._hosts = [hosts]
        self.es = None
        self.connect()

    def connect(self):
        logger.debug("connect")
        try:
            self.es = Elasticsearch(hosts=self._hosts, sniff_on_start=True)
            logger.debug("es connected")
        except (ConnectionError, TransportError) as e:
            logger.debug("connection error %s", e)
            self.es = None

    def check_es(self):
        if not self.es:
            logger.debug("es not connected")
            self.connect()
        if self.es:
            return True
        else:
            return False

    def to_dict(self, body):
        body_dict = {}
        try:
            body_dict = json.loads(body)
        except:
            body_dict = body
        finally:
            return body_dict

    def add(self, index, type, id, body):
        logger.debug("add")
        if not self.check_es():
            return False
        body = self.to_dict(body)
        try:
            ack = self.es.index(index=index, doc_type=type, id=id, body=body)
            result = ack.get('result', None)
            if result == "created":
                logger.debug("created")
                return True
            elif 'updated' == ack.get('result', None):
                logger.debug("updated")
                return True
            else:
                logger.debug("exception %s", ack)
                return False
        except TransportError as e:
            logger.debug("Error when adding %s", e)
            return False

    def delete(self, index, type, id):
        logger.debug("del")
        if not self.check_es():
            return False
        try:
            ack = self.es.delete(index=index, doc_type=type, id=id)
            if 'deleted' == ack.get('result'):
                logger.debug("deleted")
                return True
            else:
                logger.debug("exception %s", ack)
                return False
        except NotFoundError as e:
            logger.debug("not found %s", e)
            return False

    def get(self, index, type, id):
        logger.debug("get")
        if not self.check_es():
            return None
        try:
            ack = self.es.get(index=index, doc_type=type, id=id)
            if ack.get('found'):
                logger.debug("found")
                return ack["_source"]
        except NotFoundError as e:
            logger.debug("not found %s", e)
            return None

    def get_search(self, index, query):
        logger.debug("get_search")
        if not self.check_es():
            return None
        try:
            ack = self.es.search(index=index, body=query)
            if ack.get('found'):
                logger.debug("found")
                return ack["_source"]
        except NotFoundError as e:
            logger.debug("not found %s", e)
            return None

    def testing(self):
        # time = {'now': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
        # body = {"any": "data", "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'another':time}
        body = {'name': 'Joao'}
        body_json = json.dumps(body)
        reply = self.add(index="my-index", type="test-type", id=42, body=body_json)
        print(reply)
        reply = self.get(index="my-index", type="test-type", id=42)
        print(reply)
        reply = self.delete(index="my-index", type="test-type", id=42)
        return reply


class Storage:
    def __init__(self):
        self.es = ES()

    def _parse(self, item):
        _index = item.get('where', None)
        _type = item.get('what', None)
        _id = item.get('id', None)
        _body = item.get('body', None)
        if all([_index, _type, _id]):
            return (_index, _type, _id, _body)
        else:
            return None

    def add(self, commit):
        parsed = self._parse(commit)
        if parsed:
            _index, _type, _id, _body = parsed
            ok = self.es.add(index=_index, type=_type, id=_id, body=_body)
            return ok
        return False

    def remove(self, commit):
        parsed = self._parse(commit)
        if parsed:
            _index, _type, _id, _ = parsed
            ok = self.es.delete(index=_index, type=_type, id=_id)
            return ok
        return False

    def retrieve(self, commit):
        parsed = self._parse(commit)
        if parsed:
            _index, _type, _id, _ = parsed
            data = self.es.get(index=_index, type=_type, id=_id)
            return data
        return None

    def store(self, where="events", what="metrics", _id=None, body=None):
        logger.debug("Elasticsearch Store VNF-BR")
        body_json = json.dumps(body)
        commit = {'where': where, 'what': what, 'id': _id, 'body': body_json}
        
        if self.add(commit):
            logger.info('ok: info %s stored', where)
        else:
            logger.info('error: info NOT %s stored', where)



if __name__ == "__main__":
    level = logging.DEBUG
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(level)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(level)
    logger = logging.getLogger(__name__)


    hosts = ['localhost:9200']
    feed = ES()
    # print feed.testing()
    # reply = feed.delete(index="0001", type="vnfbr", id=1)
