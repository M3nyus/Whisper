import os
from Logger import Logger
from Redis_Manager import *

class Text_manager:
    def __init__(self, audio_manager, out_folder, egybefuzott, osszesitett,redis_ossz, logger, redis_manager):
        self.audio_manager = audio_manager
        self.out_folder = out_folder
        self.egybefuzott = egybefuzott
        self.osszesitett = osszesitett
        self.redis_ossz = redis_ossz
        self.logger = logger
        self.redis = redis_manager


    def all_in_one(self):
        self.logger.logging("Hangok összesítése!")
        self.audio_manager.hang_count = self.audio_manager.get_hang_count()

        words = ""
        for i in range(self.audio_manager.hang_count):
            needed_text = os.path.join(self.out_folder, f"hang_{i}.txt")
            with open(needed_text, "r", encoding="utf-8") as f:
                words = f.read()

            with open(self.egybefuzott, "a", encoding="utf-8") as b:
                b.write(words + "\n")
                words = ""
                self.logger.logging(f"A hang_{i} tartalma kiolvasva és hozzáadva.")

        #Redis-be az egész egyben
        self.redis.set("osszesito", words)

        self.logger.logging("Hangok összesítve és Redis-nek átadva, kulcs: osszesito.")

    def get_all_words(self):
        with open(self.egybefuzott, "r", encoding="utf-8") as f:
            summ_words = f.read()
        self.logger.logging("Egész szöveg átadva.")
        return summ_words

    def get_all_text_from_all_hang_from_redis_to_txt(self):
        self.logger.logging("Redis-ből adatok kinyerése megkezdődött.")
        for i in range(self.audio_manager.hang_count):
            tmp_bytestext_from_redis = self.redis.get(f"hang_{i}")
            str_tmp = tmp_bytestext_from_redis.decode("utf-8")
            good_tmp = json.loads(str_tmp)

            with open(self.redis_ossz, "a", encoding="utf-8") as w:
                w.write(good_tmp["text"])

        self.logger.logging("Az összes hagból Redis-ből a szöveg kinyerve txt-be (all_text_from_redis.txt).")

    def get_hang_from_redis(self, hang):
        self.logger.logging(f"{hang} hangból szövegkinyerés elkezdődött Redis-ből.")
        tmp_bytestext_from_redis = self.redis.get(hang)
        str_tmp = tmp_bytestext_from_redis.decode("utf-8")
        good_tmp = json.loads(str_tmp)
        print(good_tmp["text"])
        self.logger.logging(f"{hang} hang kinyerve Redis-ből.")
        #flaskhoz egy hanghoz
        return good_tmp["text"]