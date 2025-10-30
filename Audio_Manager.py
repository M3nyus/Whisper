import os
from datetime import time
import time
from pydub import AudioSegment
from Logger import Logger
from eredeti import hang_count
from Redis_Manager import *


class Audio_Manager:
    def __init__(self, audio_file, out_folder, model, logger, redis_manager,chunk_len=100000):
        self.audio_file = audio_file
        self.out_folder = out_folder
        self.model = model
        self.logger = logger
        self.chunk_len = chunk_len
        self.audio = AudioSegment.from_file(audio_file)
        self.hang_count = 0
        self.redis = redis_manager

    def chunking(self, segment, chunk_size):
        start = 1
        while start < len(segment):
            yield segment[start:start + chunk_size]
            start += chunk_size

    def working(self):
        start_time = time.time()

        for i, chunk in enumerate(self.chunking(self.audio, self.chunk_len)):
            self.logger.logging(f"hang_{i} feldolgozás megkezdése.")
            tmp_file = os.path.join(self.out_folder, f"hang_{i}.mp3")
            chunk.export(tmp_file, format="mp3")
            self.hang_count += 1

            result = self.model.transcribe(tmp_file, language="hu")

            #redis
            self.redis.set(f"hang_{i}", result)

            output_txt = os.path.join(self.out_folder, f"hang_{i}.txt")
            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(result["text"])


            self.logger.logging(f"{output_txt} feldolgozva és Redis-be átadva.")
            print(f"{output_txt} feldolgozva és Redis-be átadva.")

        end_time = time.time()
        self.logger.logging(f"Feliratozás ideje: {(end_time - start_time)}mp")


    def get_hang_count(self):
        self.logger.logging("Hangok száma visszaadva.")
        return self.hang_count