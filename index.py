import threading
from flask import Flask, render_template, redirect, url_for, request
from Logger import *
from Audio_Manager import *
from Text_manager import *
from AI_Summer import *
import openai
import whisper
from transformers import pipeline
from openai import OpenAI

app = Flask(__name__)

model = whisper.load_model("base")
summer = pipeline("summarization",model="t5-large")

utak = {
    "audio_file": r"hangom.mp3",
    "out_folder": r"hangok",
    "log_file": r"log.txt",
    "egybefuzott": r"egybefuzott.txt",
    "osszesitett": r"osszesitett.txt",
    "redisbol_ossz" : r"all_text_from_redis.txt"
}

logger = Logger(utak["log_file"])
redis = Redis_Manager(logger)
audio_manager = Audio_Manager(utak["audio_file"], utak["out_folder"], model, logger, redis, 10000)
text_manager = Text_manager(audio_manager, utak["out_folder"], utak["egybefuzott"], utak["osszesitett"], utak["redisbol_ossz"], logger, redis)
ai_summer = AI_Summer(summer, utak["osszesitett"], logger)
generated_text = ""
done = False
voltalitt = False

def audio_manager_count():
    return audio_manager.get_hang_count()

def long_task():
    global done, voltalitt, generated_text
    done = False
    voltalitt = False
    audio_manager.working()
    text_manager.all_in_one()
    generated_text = text_manager.get_all_words()
    done = True
    voltalitt = True
    return redirect('status')

def is_done():
    return done

def generated_text_result():
    return generated_text

@app.route("/", methods=["GET", "POST"])
def index():
    mappa = os.getcwd()
    mp3 = [f for f in os.listdir(mappa) if f.lower().endswith(".mp3")]
    selected_file = None

    if request.method == "POST":
        selected_file = request.form.get("selected_file")
        global audio_manager
        audio_manager = Audio_Manager(os.path.join(mappa, selected_file), mappa, model, logger, redis, 10000)
        return redirect(url_for("status"))

    return render_template("index.html", mp3=mp3, selected_file=selected_file, voltalitt=voltalitt)

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
        ret = round(audio_manager.percent_done, 2)
        if ret:
            return str(ret)
        else:
            return str(0)

@app.route("/status")
def status():
    audio_nev = utak["audio_file"]
    return render_template("Subtitle.html", szoveg=generated_text_result(), audio_nev=audio_nev, voltalitt=voltalitt)

@app.route("/onehang", methods=["GET", "POST"])
def onehang():
    hangok_szama = audio_manager_count() - 1

    if request.method == "POST":
        hang_szam = request.form.get("hang_szam")
        szoveg = text_manager.get_hang_from_redis(f"hang_{hang_szam}")

        return render_template("Onehang.html", szoveg=szoveg, hangok_szama=hangok_szama)

    return render_template("Onehang.html", szoveg=None, hangok_szama = hangok_szama)

@app.route("/volt_e")
def volt_e():
    global voltalitt
    voltalitt = True
    return voltalitt

@app.route("/subdone")
def subdone():
    audio_nev = utak["audio_file"]
    return render_template("Sub_Done.html", szoveg = generated_text_result(), audio_nev = audio_nev)

@app.route("/leall", methods=["POST"])
def leall():
    logger.logging("Program leállítása.")
    os._exit(0)

app.run(host="127.0.0.1", port=5000, debug=True)
logger.logging("Flask szerver elindult.")