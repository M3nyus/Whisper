import os

import openai
import whisper
from transformers import pipeline
from openai import OpenAI

#Beállítások
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
#OPEN_AI fordításhoz - client = openai.OpenAI(api_key = "sk - proj - rsMCl - M4ncu - LOCZZ4LStNhq4WMp6WsQ5Goyijlt1CCuxw33gi5c1nZMCb2bm2gWEdYf5HJCkWT3BlbkFJwk7RfC08vNRWID2WIasbvl1wQHe3S9S50xZv7ln86dqpU - KF9QKoZFKBE7y - VXwF0kjRWC2qwA")

#Moddellek
model = whisper.load_model("base")
summer = pipeline("summarization",model="t5-large")

#Elérések
utak = {
    "audio_file": r"audio.mp3",
    "out_folder": r"hangok",
    "log_file": r"log.txt",
    "egybefuzott": r"output/egybefuzott.txt",
    "osszesitett": r"output/osszesitett.txt",
    "redisbol_ossz" : r"all_text_from_redis.txt"
}