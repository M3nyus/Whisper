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
from Logger import *
import wave

SAMPLE_RATE = 48000
CHANNELS = 2
SAMPLE_WIDTH = 2  # bytes (16-bit)
FRAME_SAMPLES = 960  # 20 ms @ 48 kHz
FRAME_BYTES = FRAME_SAMPLES * SAMPLE_WIDTH
FRAMES_PER_SECOND = 50

class Redis_Manager():
    def __init__(self, host, port, db):
        self.client = redis.Redis(host=host, port=port, db=db)
        self.mp3_name = None
        self.logger = Logger

    #kieg awaitek
    async def redis_stream_to_wav(self, roomId, chunk, output_file="redis_audio.wav", seconds=10,):
        roomId = roomId
        chunk = chunk
        mp3_szamlalo_kulcs = "db_mp3"
        room_id = 'room_id'
        mintavetelezes = 48000


        utolso_id = "0-0"
        pcm_lista = {}  # dict

        while True:
            valasz = await self.client.xread({roomId: utolso_id}, count=10000, block=10)
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
        print('sort')
        pcm_list = []
        with wave.open('output.wav', "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(SAMPLE_RATE)
            for key, value in pcm_lista.items():
                print(key)
                pcm_list.append(value)
                wf.writeframes(value)

        print('sort end')
        teljes_pcm = np.concatenate(pcm_list)

        wav_fajl = f"{room_id}{chunk}.wav"
        mp3_fajl = f"{room_id}{chunk}.mp3"

        sf.write(wav_fajl, teljes_pcm, samplerate=mintavetelezes)

        audio = AudioSegment.from_wav(wav_fajl)
        audio.export(mp3_fajl, format="mp3")

        #redisbe az mp3
        with open(mp3_fajl, "rb") as f:
            mp3 = f.read()

        await self.client.set(f"komplett{room_id}{chunk}", mp3)

        await self.client.close()

    def redis_ell(self):
        info1 = self.client.xinfo_stream("audio_stream")
        info2 = self.client.get("room_id")
        try:
            if ("lenght" in info1 and info1["lenght"] == 0) or info2 is None:
                return "Nincs hang a Redis-ben az MP3 fájl létrehozásához!"
        except redis.exceptions.ResponseError:
            return "Nincs hang a Redis-ben az MP3 fájl létrehozásához!"

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

    def fut_e(self):
        while True:
            try:
                self.client.ping()
                self.logger.logging("Redis szerver él.")
                print("Redis szerver él.")
                break
            except:
                self.logger.logging("Nem fut a Redis szerver, újrapróbálkozás 5 másodperc múlva.")
                print("Nem fut a Redis szerver, újrapróbálkozás 5 másodperc múlva.")
                time.sleep(5)