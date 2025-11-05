import threading
from flask import Flask, render_template, redirect, url_for
from Logger import *
from Audio_Manager import *
from Text_manager import *
from AI_Summer import *
import openai
import whisper
from transformers import pipeline
from openai import OpenAI

app = Flask(__name__)

progress = 0
model = whisper.load_model("turbo")
summer = pipeline("summarization",model="t5-large")
utak = {
    "audio_file": r"audio.mp3",
    "out_folder": r"hangok",
    "log_file": r"log.txt",
    "egybefuzott": r"output/egybefuzott.txt",
    "osszesitett": r"output/osszesitett.txt",
    "redisbol_ossz" : r"all_text_from_redis.txt"
}

logger = Logger(utak["log_file"])
redis = Redis_Manager(logger)
audio_manager = Audio_Manager(utak["audio_file"], utak["out_folder"], model, logger, redis, 10000)
text_manager = Text_manager(audio_manager, utak["out_folder"], utak["egybefuzott"], utak["osszesitett"], utak["redisbol_ossz"], logger, redis)
ai_summer = AI_Summer(summer, utak["osszesitett"], logger)
generated_text = ""
done = False
def audio_manager_count():
    return audio_manager.get_hang_count()

def long_task():
    global done
    done = False
    audio_manager.working()
    text_manager.all_in_one()
    global generated_text
    generated_text = text_manager.get_all_words()
    done = True

def is_done():
    return done

def generated_text_result():
    return generated_text

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/start")
def start():
    thread = threading.Thread(target=long_task)
    thread.start()
    return redirect('status')

@app.route("/progress")
def progress():
    if is_done():
        return str(100)
    else:
        ret = audio_manager_count()
        if ret:
            return str(ret)
        else:
            return str(0)


@app.route("/status")
def status():
    return render_template("Subtitle.html", szoveg=generated_text_result())
app.run(host="127.0.0.1", port=5000, debug=True)

