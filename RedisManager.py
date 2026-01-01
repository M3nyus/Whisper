import sys
import redis
import json
import base64
import numpy as np
from pydub import AudioSegment
import soundfile as sf
import os
import time

class Redis_Manager():
    def __init__(self):
        self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        self.mp3_name = None

    def generate_MP3(self):
        hang_kulcs = "audio_stream"
        mp3_szamlalo_kulcs = "db_mp3"
        room_id = self.client.get("room_id")
        room_id = room_id.decode("utf-8")
        kimeneti_mappa = os.path.join(os.getcwd(), "mp3_audiok")
        mintavetelezes = 48000

        mp3_index = self.client.get(mp3_szamlalo_kulcs)
        if mp3_index is None:
            mp3_index = 0
            self.client.set(mp3_szamlalo_kulcs, mp3_index)
        else:
            mp3_index = int(mp3_index)
            mp3_index += 1
            self.client.set(mp3_szamlalo_kulcs, mp3_index)

        utolso_id = "0-0"
        pcm_lista = []

        while True:
            valasz = self.client.xread({hang_kulcs: utolso_id}, count=1000, block=500)
            if not valasz:
                break
            for _, uzenetek in valasz:
                for uzenet_id, mezok in uzenetek:
                    utolso_id = uzenet_id.decode()
                    pcm_b64 = mezok[b'pcm'].decode()
                    pcm_bytes = base64.b64decode(pcm_b64)
                    pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16)
                    pcm_lista.append(pcm_array)

        if not pcm_lista:
            logger.logging("Nincs audio adat a Redis-ben!")
            return

        teljes_pcm = np.concatenate(pcm_lista)

        wav_fajl = f"{kimeneti_mappa}/{room_id}_hivas_{mp3_index}.wav"
        mp3_fajl = f"{kimeneti_mappa}/{room_id}_hivas_{mp3_index}.mp3"

        sf.write(wav_fajl, teljes_pcm, samplerate=mintavetelezes, bitrate_mode="CONSTANT", subtype='PCM_16', format='WAV', endian='LITTLE')
        self.mp3_name = wav_fajl

        audio = AudioSegment.from_wav(wav_fajl)
        audio.export(mp3_fajl, format="mp3")

        self.mp3_name = mp3_fajl

        logger.logging(f"MP3 elkészült: {mp3_fajl}")

    def redis_ell(self):
        info1 = self.client.xinfo_stream("audio_stream")
        info2 = self.client.get("room_id")
        try:
            if ("lenght" in info1 and info1["lenght"] == 0) or info2 is None:
                return "Nincs hang a Redis-ben az MP3 fájl létrehozásához!"
        except redis.exceptions.ResponseError:
            return "Nincs hang a Redis-ben az MP3 fájl létrehozásához!"

    def test(self):
        vissza = self.client.get("hang")
        if vissza is None:
            logger.logging("Nincs 'hang' kulcshoz tartozó file!")
            return

        mp3_szamlalo_kulcs = 'mp3_counter'

        counter = self.client.get(mp3_szamlalo_kulcs)
        if counter is None:
            counter = 0
            self.client.set(mp3_szamlalo_kulcs, counter)
        else:
            counter = int(counter)
            counter += 1
            self.client.set(mp3_szamlalo_kulcs, counter)

        mp3_mappa = os.path.join(os.getcwd(), "mp3_audiok")
        mp3_mentesi_ut = os.path.join(mp3_mappa, f"vissza_{counter}.mp3")

        with open(mp3_mentesi_ut, "wb") as f:
            f.write(vissza)

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
                logger.logging("Redis szerver él.")
                print("Redis szerver él.")
                break
            except:
                logger.logging("Nem fut a Redis szerver, újrapróbálkozás 5 másodperc múlva.")
                print("Nem fut a Redis szerver, újrapróbálkozás 5 másodperc múlva.")
                time.sleep(5)