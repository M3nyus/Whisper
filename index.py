# import env
import asyncio
import threading
from dotenv import load_dotenv
import os
from flask import Flask, render_template, jsonify, request
from pydub import AudioSegment
import uuid
from Logger import *
from stateManager import StateManager
from RedisManager import Redis_Manager
from transcriptionmanager import TextManager
from Bot import *

def getEnv():
    load_dotenv()

    DEMO = os.getenv("DEMO")

    global REDIS_HOST, REDIS_PORT, REDIS_PASS, REDIS_DB, OUTPUT_DIR, WHISPER_MODEL, APP_HOST, APP_PORT, APP_DEBUG

    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_PASS = os.getenv("REDIS_PASS").strip()
    REDIS_DB = os.getenv("REDIS_DB")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR")
    APP_HOST = os.getenv("APP_HOST")
    APP_PORT = os.getenv("APP_PORT")
    APP_DEBUG = os.getenv("APP_DEBUG")

    if DEMO == "False":
        WHISPER_MODEL = os.getenv("WHISPER_MODEL")
    else:
        WHISPER_MODEL = None

def deleteMp3Hang():
    hangMappa = os.path.join(os.getcwd(), "mp3", "hang")

    if os.path.exists(hangMappa) and os.path.isdir(hangMappa):
        for f in os.listdir(hangMappa):
            file = os.path.join(hangMappa, f)
            try:
                if os.path.isfile(file) or os.path.islink(file):
                    os.unlink(file)
            except Exception as e:
                print(f"Hiba a {file} törlése közben: {e}")
                logger.Logging(f"Hiba a {file} törlése közben: {e}")

getEnv()
global logger
LOGFILE = os.getenv("LOGFILE")
logger = Logger(LOGFILE)
global bot

redisManager = Redis_Manager(REDIS_HOST, REDIS_PORT,REDIS_PASS, LOGFILE=LOGFILE)
redisManager.fut_e()
#redisManager.delete_aktualis_db()
stateManager = StateManager(LOGFILE)
transcriptionManager = TextManager(stateManager,WHISPER_MODEL, OUTPUT_DIR,REDIS_HOST,REDIS_PORT,REDIS_PASS,LOGFILE)
bots = {}

deleteMp3Hang()

uuid = str(uuid.uuid4())
logger.Logging(f"Példány UUID: {uuid}")

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

    #szál1: start bot
    threading.Thread(target=startBot, args=(roomId,)).start()
    logger.Logging(f"1. szál: Bot({roomId}) elkezdi a feladatát.")

    #szal2: start feliratozás
    threading.Thread(target=startTranscriptThread, args=(roomId,timestampId)).start()
    logger.Logging(f"2. szál: Feliratorás megkezdése ({roomId}).")

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
            loop = aktiveBot._loop
            if loop.is_running():
                fut = asyncio.run_coroutine_threadsafe(aktiveBot.close(), loop)
                fut.result(timeout=5)
            else:
                loop.run_until_complete(aktiveBot.close())

            del bots[roomId]
            logger.Logging("Bot leállítva.")
        except Exception as e:
            logger.Logging(f"Hiba a bot leállításában: {e}")

    stateManager.data[roomId][timestampId]['getting_audio'] = False
    return jsonify({'status': 'Leállítva.'})

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
    data = request.json
    uuidSent = data.get("uuid")

    if uuidSent != uuid:
        logger.Logging(f"Nem megfelelő UUID-val próbálták leállítani: {uuidSent}")
        return jsonify({"error": "Nem megfelelő UUID"})

    logger.Logging(f"Példány leállítása UUID: {uuid}")

    threading.Thread(target=lambda: (time.sleep(1), os._exit(0))).start()

    return jsonify({"status": "Leállítás."})

@app.route("/API/stopped")
def stoppedPage():
    return render_template("shutdown.html")

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
def recorderPause(roomId):
    aktiveBot = bots.get(roomId)
    if aktiveBot:
        aktiveBot.pauseRecord()

@app.route("/API/recorderResume/<roomId>", methods=["GET", "POST"])
def resumeRecording(roomId):
    aktiveBot = bots.get(roomId)
    if aktiveBot:
        aktiveBot.resumeRecording()

@app.route("/API/getUuid", methods=["GET"])
def getUuid():
    return jsonify({"uuid": uuid})

#mp3 DEMO innen

@app.route("/API/getMp3", methods=["GET", "POST"])
def getMp3():
    mp3_folder = os.path.join(os.getcwd(), "mp3")
    mp3_files = []

    if os.path.exists(mp3_folder):
        for f in os.listdir(mp3_folder):
            if f.endswith(".mp3"):
                file_path = os.path.join(mp3_folder, f)
                try:
                    audio = AudioSegment.from_file(file_path)
                    sec = int(audio.duration_seconds)
                    minutes = sec // 60
                    seconds = sec % 60
                    mp3_files.append({"name": f, "duration": f"{minutes}:{seconds:02d}"})
                except Exception as e:
                    logger.Logging(f"Hiba a {f} betöltésekor: {e}")
                    mp3_files.append({"name": f, "duration": "??:??"})

    return render_template("getMP3.html", mp3_files=mp3_files)

@app.route("/API/getMp3/translate", methods=["GET", "POST"])
def translate():
    fileName = request.json.get("fileName")
    if not fileName:
        return jsonify({"error": "Nincs kiválasztva fájl!"})

    mp3_path = os.path.join(os.getcwd(), "mp3", fileName)
    if not os.path.exists(mp3_path):
        return jsonify({"error": "Fájl nem található!"})

    audio = AudioSegment.from_mp3(mp3_path)

    global redisKey
    redisResult = transcriptionManager.working(audio, 10, fileName)
    print(redisResult)

    #DEMO
    if isinstance(redisResult, dict) and redisResult.get("demo"):
        return jsonify({"text": redisResult["text"], "key": None})

    #NORMÁL
    redisKey = redisResult["key"]
    bytesText = redisManager.get(redisKey) or ""
    text = bytesText

    return jsonify({"text": text, "key": redisKey})

@app.route("/API/getMp3/pause", methods=["POST"])
def pauseTranscription():
    transcriptionManager.pause()
    return jsonify({"status": "pause"})

@app.route("/API/getMp3/resume", methods=["POST"])
def resumeTranscription():
    transcriptionManager.resume()
    return jsonify({"status": "resume"})

@app.route("/API/getMp3/clear", methods=["GET", "POST"])
def clear():
    data = request.json
    key = data.get("key")

    if not key:
        return jsonify({"error": "Nincs megadva kulcs!"})

    # törlés progress-ből
    progressKey = f"progress:{key}"
    redisManager.delete_key(f"{progressKey}:total")
    redisManager.delete_key(f"{progressKey}:curr")

    # torlés /mp3/hang mappabol
    hangMappa = os.path.join(os.getcwd(), "mp3", "hang")

    if os.path.exists(hangMappa) and os.path.isdir(hangMappa):
        for f in os.listdir(hangMappa):
            file = os.path.join(hangMappa, f)
            try:
                if os.path.isfile(file) or os.path.islink(file):
                    os.unlink(file)
            except Exception as e:
                print(f"Hiba a {file} törlése közben: {e}")
                logger.Logging(f"Hiba a {file} törlése közben: {e}")

    return jsonify({"status": "cleared"})

@app.route("/API/changeMode", methods=["POST"])
def changeMode():
    mode = request.json.get("mode")

    if mode not in ["demo", "live"]:
        return jsonify({"error": "Érvénytelen mód. Csak 'demo' vagy 'live' lehet."}), 400

    global  WHISPER_MODEL

    if mode == "live":
        WHISPER_MODEL = os.getenv("WHISPER_MODEL")
        transcriptionManager.changeMode(os.getenv("WHISPER_MODEL"))
        logger.Logging(f"Mód: {os.getenv('WHISPER_MODEL')}")
    else:
        WHISPER_MODEL = None
        transcriptionManager.changeMode(None)
        logger.Logging(f"Mód: Demo")

    return jsonify({"status": "OK", "mode": mode})

@app.route("/API/getMode", methods=["GET"])
def getMode():
    global WHISPER_MODEL
    mode = "live" if WHISPER_MODEL else "demo"
    return jsonify({"mode": mode})

@app.route("/API/getMp3/progress/<fileName>", methods=["GET"])
def get_progress(fileName):
    key = f"progress:{fileName}"

    current = redisManager.get(f"{key}:curr") or 0
    total = redisManager.get(f"{key}:total") or 0

    return jsonify({
        "curr": int(current),
        "total": int(total)
    })

def startBot(roomId):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = Demo(roomId=roomId, LOGFILE=LOGFILE, player=None, recorder=MediaBlackhole(), loop=loop)
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

app.run(host=APP_HOST, port=APP_PORT, debug=APP_DEBUG)