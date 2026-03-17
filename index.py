# import env
import asyncio
import threading
from dotenv import load_dotenv
import os
from flask import Flask, render_template, jsonify, request
from pydub import AudioSegment
from Logger import *
from stateManager import StateManager
from RedisManager import Redis_Manager
from transcriptionmanager import TextManager
from Bot import *

load_dotenv()
global REDIS_HOST, REDIS_PORT, REDIS_DB,OUTPUT_DIR,WHISPER_MODEL
REDIS_HOST= os.getenv("REDIS_HOST")
REDIS_PORT= os.getenv("REDIS_PORT")
REDIS_DB= os.getenv("REDIS_DB")
OUTPUT_DIR=os.getenv("OUTPUT_DIR")
WHISPER_MODEL=os.getenv("WHISPER_MODEL")
# start logger 
global logger
LOGFILE = os.getenv("LOGFILE")
logger = Logger(LOGFILE)
global bot
progressData = {"curr": 0, "total": 0}

redisManager = Redis_Manager(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, LOGFILE=LOGFILE)
redisManager.fut_e()
redisManager.delete_aktualis_db()
stateManager = StateManager(LOGFILE)
transcriptionManager = TextManager(stateManager,WHISPER_MODEL, OUTPUT_DIR,REDIS_HOST,REDIS_PORT,REDIS_DB,LOGFILE, progressData)
bots = {}


app = Flask(__name__)
logger.Logging("Flask szerver elindult.")

# flask definitions
@app.route("/", methods=["GET", "POST"])
def index():
    logger.Logging("Az oldal betöltött.")
    return render_template("index.html")

@app.route("/API/startRoom/<roomId>", methods=["GET", "POST"])
def startRoom(roomId):
    # [<roomId>: [<timestampId>]]
    timestampId = stateManager.isRoomActive(roomId)
    if timestampId!=False:
        # RETURN ALREADY EXISTING 
        return jsonify({'timestampId': timestampId})

    timestampId = stateManager.startRoom(roomId)
    stateManager.data[roomId][timestampId]['getting_audio']=True

    redisManager.set(f"{roomId}:{timestampId}:audio:index", 0)

    #szal1: start bot
    threading.Thread(target=startBot, args=(roomId,)).start()
    logger.Logging(f"1. szál: Bot({roomId}) elkezdi a feladatát.")

    #szal2: start transcript
    threading.Thread(target=startTranscriptThread, args=(roomId,timestampId)).start()
    logger.Logging(f"2. szél: Feliratorás megkezdése ({roomId}).")

    return jsonify({'timestampId': timestampId})

@app.route("/API/isRoomActive/<roomId>", methods=["GET", "POST"])
def isRoomActive(roomId):
    timestampId = stateManager.isRoomActive(roomId)

    logger.Logging(f"Azonosító: {roomId}, Állapot: {timestampId}")

    if timestampId!=False:
        # RETURN ALREADY EXISTING 
        return jsonify({'timestampId': timestampId})

    return jsonify({'active':False})

@app.route("/API/roomStatus/<roomId>/<int:timestampId>", methods=["GET", "POST"])
def roomStatus(roomId,timestampId):
    # audio files : array
    # state active - true/false 
    # state getting_audio : true / false  
    # state transcribeing : true / false  
    # state transcribeing_model :  modelname 
    status = stateManager.roomStatus(roomId,timestampId)
    logger.Logging(f"Státusz: {status}")
    return jsonify(status)

@app.route("/API/stopRoom/<roomId>/<int:timestampId>", methods=["GET", "POST"])
def stopRoom(roomId,timestampId):
    aktiveBot = bots.get(roomId)

    if aktiveBot:
        try:
            asyncio.run(aktiveBot.close())
            logger.Logging("Bot leállítva.")
        except Exception as e:
            logger.Logging(f"Hiba a bot leállításában, {roomId}, {timestampId}")

        del bots[roomId]

    stateManager.data[roomId][timestampId]['getting_audio'] = False
    return jsonify({'status': 'OK'})

@app.route("/API/listRooms", methods=["GET", "POST"])
def listRooms():
    # [<roomId>,<roomId>, ...]
    logger.Logging(f"Aktív szóbák listázva: {list(stateManager.listRooms())}")
    return jsonify(list(stateManager.listRooms()))

@app.route("/API/saveState", methods=["GET", "POST"])
def saveState():
    # [<roomId>,<roomId>, ...]
    stateManager.saveState()
    return 'OK'

@app.route("/API/debugData", methods=["GET", "POST"])
def debugData():
    # [<roomId>,<roomId>, ...]
    return jsonify(list(stateManager.debugData()))

@app.route("/API/getLastText/<roomId>", methods=["GET", "POST"])
def getLastText(roomId):
    # [<roomId>: [<timestampId>, ...]]
    return jsonify({'text': stateManager.getLastText(roomId)})

@app.route("/API/listAudioFiles/<roomId>/<int:timestampId>", methods=["GET", "POST"])
def listAudioFiles(roomId, timestampId):
    # [<roomId>-<timestampId>: [audio-0, ...]]
    logger.Logging("Audió fájlok listázva.")
    return jsonify(list(stateManager.listAudioFiles(roomId, timestampId)))

@app.route("/API/programStop", methods=["GET", "POST"])
def shutdown():
    logger.Logging("Program leállítása.")
    os._exit(0)

@app.route("/API/addPlusBot/<roomId>", methods=["GET", "POST"])
def addPlusBot(roomId):
    logger.Logging(f"Új bot létrehozása (Szobanév: {roomId}).")

    timestampId = stateManager.isRoomActive(roomId)
    if timestampId != False:
        return jsonify({'timestampId': timestampId})

    timestampId = stateManager.startRoom(roomId)
    stateManager.data[roomId][timestampId]['getting_audio'] = True

    # szal1: start bot
    threading.Thread(target=startBot, args=(roomId,)).start()
    logger.Logging(f"1. szál: Bot({roomId}) elkezdi a feladatát.")

    # szal2: start transcript
    threading.Thread(target=startTranscriptThread, args=(roomId, timestampId)).start()
    logger.Logging(f"2. szél: Feliratorás megkezdése ({roomId}).")

    return jsonify({'timestampId': timestampId})

@app.route("/API/recorderPause/<roomId>", methods=["GET", "POST"])
def recorderPause(rooId):
    bot.pauseRecord(rooId)

@app.route("/API/recorderResume/<roomId>", methods=["GET", "POST"])
def resumeRecording(rooId):
    bot.resumeRecording(rooId)

@app.route("/API/getMp3", methods=["GET", "POST"])
def getMp3():
    mp3_folder = os.path.join(os.getcwd(), "mp3")
    mp3_files = []

    if os.path.exists(mp3_folder):
        mp3_files = [f for f in os.listdir(mp3_folder) if f.endswith(".mp3")]

    return render_template("getMP3.html", mp3_files=mp3_files)

@app.route("/API/getMp3/translate", methods=["GET", "POST"])
def translate():
    file_name = request.json.get("fileName")
    if not file_name:
        return jsonify({"error": "Nincs kiválasztva fájl!"}), 400

    mp3_path = os.path.join(os.getcwd(), "mp3", file_name)
    if not os.path.exists(mp3_path):
        return jsonify({"error": "Fájl nem található!"}), 404

    audio = AudioSegment.from_mp3(mp3_path)

    transcriptionManager.working(audio, sec=10)  # sec=chunk hossz másodpercben

    felirat_file = os.path.join(os.getcwd(), "mp3", "felirat", "felirat.txt")
    if os.path.exists(felirat_file):
        with open(felirat_file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = ""

    return jsonify({"text": text})

@app.route("/API/getMp3/clear", methods=["GET", "POST"])
def clear():
    feliratFile = os.path.join(os.getcwd(), "mp3", "felirat", "felirat.txt")

    if os.path.exists(feliratFile):
        with open(feliratFile, "w", encoding="utf-8") as f:
            f.write("")

    progressData["current"] = 0
    progressData["total"] = 0

    return jsonify({"status": "cleared"})

@app.route("/API/getMp3/progress", methods=["GET"])
def get_progress():
    return jsonify(progressData)

def startBot(roomId):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = Demo(roomdId=roomId, LOGFILE=LOGFILE, player=None, recorder=MediaBlackhole(), loop=loop)
    logger.Logging("Bot létrehozva.")
    bots[roomId] = bot
    print(bots)

    try:
        loop.run_until_complete(bot.run())
    except Exception as e:
        print("Bot nem aktív.")
    finally:
        loop.run_until_complete(bot.close())
        loop.close()

def startTranscriptThread(roomId, timestampId):
    asyncio.run(transcriptionManager.startTranscription(roomId, timestampId))

APP_HOST= os.getenv("APP_HOST")
APP_PORT= os.getenv("APP_PORT")
APP_DEBUG= os.getenv("APP_DEBUG")
app.run(host=APP_HOST, port=APP_PORT, debug=APP_DEBUG)