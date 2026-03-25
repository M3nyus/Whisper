import sys
import redis as redis
import asyncio
import json
import base64
import numpy as np
from pydub import AudioSegment
import soundfile as sf
import os
import time

from redis.cluster import ClusterNode
from redis.cluster import RedisCluster as Redis

from Logger import *
import wave

SAMPLE_RATE = 48000
CHANNELS = 2
SAMPLE_WIDTH = 2
FRAME_SAMPLES = 960
FRAME_BYTES = FRAME_SAMPLES * SAMPLE_WIDTH
FRAMES_PER_SECOND = 50



class Redis_Manager():
    #DB0, ahova mentünk Redis-ben
    def __init__(self, host, port, db, LOGFILE):
        self.client = redis.Redis(host=host, port=port, db=db)
        self.mp3_name = None
        self.logger = Logger(LOGFILE)

        # self.client = redis.Redis(Host=host,port=port,db=db)
        #nodes = [ClusterNode('localhost', 7003), ClusterNode('localhost', 7004)]
        #self.client = Redis(startup_nodes=nodes)

    async def redis_stream_to_wav(self, roomId, chunk, seconds=10,):
        self.logger.Logging(f"Audió fájl létrehozása. Szoba:{roomId}, Chunk:{chunk}")

        mp3_szamlalo_kulcs = "db_mp3"
        mintavetelezes = 48000
        key = f"{roomId}:{chunk}"

        utolso_id = "0-0"
        pcm_lista = {}  # dict
        while True:
            valasz = self.client.xread({key: utolso_id})
            # print(valasz)
            if not valasz:
                break
            for _, uzenetek in valasz:
                for uzenet_id, mezok in uzenetek:
                    utolso_id = uzenet_id.decode()
                    pcm_b64 = mezok[b'pcm'].decode()
                    pcm_bytes = base64.b64decode(pcm_b64)
                    pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16)
                    pcm_lista[utolso_id] = pcm_array

        if not pcm_lista:
            print("Nincs audio adat a Redis-ben!")
            return
        wav_fajl = f"{roomId}{chunk}.wav"

        with wave.open(wav_fajl, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(SAMPLE_RATE)
            for key, value in pcm_lista.items():
                print(key)
                wf.writeframes(value)

        audio = AudioSegment.from_wav(wav_fajl)
        mp3_fajl = f"{roomId}{chunk}.mp3"
        audio.export(mp3_fajl, format="mp3")
        self.logger.Logging(f"Audió fájl létrehozva: {mp3_fajl}")

        return await asyncio.sleep(1)

    def set(self, kulcs, ertek):
        if isinstance(ertek, (dict, list)):
            ertek = json.dumps(ertek, ensure_ascii=False)
        self.client.set(kulcs, ertek)
        self.logger.Logging(f"Redis - Set: {kulcs} - {ertek}")

    def get(self, kulcs):
        self.logger.Logging(f"Redis - Get: {kulcs}")
        return self.client.get(kulcs)

    def append(self, key, value):
        self.client.append(key, value)
        self.logger.Logging("Append - {key}")

    def delete_aktualis_db(self):
        aktualisDb = self.client.connection_pool.connection_kwargs.get("db")
        self.client.flushdb()
        self.logger.Logging(f"Aktuális Redis DB törölve ({aktualisDb}).")

    def delete_all_db(self):
        self.client.flushall()
        self.logger.Logging("Teljes Redis törölve.")

    def delete_key(self, key):
        self.client.delete(key)
        self.logger.Logging(f"Redis kulcs törölve: {key}")

    def fut_e(self):
        while True:
            try:
                self.client.ping()
                self.logger.Logging("Redis szerver él.")
                print("Redis szerver él.")
                break
            except:
                self.logger.Logging("Nem fut a Redis szerver, újrapróbálkozás 5 másodperc múlva.")
                print("Nem fut a Redis szerver, újrapróbálkozás 5 másodperc múlva.")
                time.sleep(5)