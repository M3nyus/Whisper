import redis
from Logger import *
import json

class Redis_Manager():
    def __init__(self, logger, host="127.0.0.1", port=6379, db=0, decode_responses=True):
        self.logger = logger
        self.client = redis.Redis(host=host, port=port, db=db)

    def set(self, kulcs, ertek):
        if isinstance(ertek, (dict, list)):
            ertek = json.dumps(ertek, ensure_ascii=False)
        self.client.set(kulcs, ertek)

    def get(self, kulcs):
        return self.client.get(kulcs)

    def delete_aktualis_db(self):
        self.client.flushdb()

    def delete_all_db(self):
        self.client.flushdb()