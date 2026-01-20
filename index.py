# import env
import asyncio
import threading
from dotenv import load_dotenv
import os
from flask import Flask, render_template, jsonify
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

redisManager = Redis_Manager(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
stateManager = StateManager()
transcriptionManager = TextManager(WHISPER_MODEL, OUTPUT_DIR,REDIS_HOST,REDIS_PORT,REDIS_DB,LOGFILE)
bots = {}

app = Flask(__name__)
# flask definitions
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/API/startRoom/<roomId>", methods=["GET", "POST"])
def startRoom(roomId):
    # [<roomId>: [<timestampId>]]
    # check for active recording 
    # false or timestampId
    timestampId = stateManager.isRoomActive(roomId)
    if timestampId!=False:
        # RETURN ALREADY EXISTING 
        return jsonify({'timestampId': timestampId})

    #KIEG
    timestampId = stateManager.startRoom(roomId)
    stateManager.data[roomId][timestampId]['getting_audio']=True

    redisManager.set(f"{roomId}:{timestampId}:audio:index", 0)

    #start bot
    threading.Thread(target=startBot, args=(roomId,)).start()

    threading.Thread(target=startTranscriptThread(roomId, timestampId), args=(roomId,timestampId)).start()
    # IF NOT in PROGRESS 
    # create_entry
    # start getting audio 
    # start checking for available audio files in redis 
    # return timestampID for roomId
    return jsonify({'timestampId': timestampId})

@app.route("/API/isRoomActive/<roomId>", methods=["GET", "POST"])
def isRoomActive(roomId):
    # [<roomId>: [<timestampId>]]
    # check for active recording 
    # false or timestampId
    timestampId = stateManager.isRoomActive(roomId)
    if timestampId!=False:
        # RETURN ALREADY EXISTING 
        return jsonify({'timestampId': timestampId})
    # IF NOT in PROGRESS 
    # create_entry
    # start getting audio 
    # start checking for available audio files in redis 
    # return timestampID for roomId
    #KIEG
    return jsonify({'active':False})

@app.route("/API/roomStatus/<roomId>/<int:timestampId>", methods=["GET", "POST"])
def roomStatus(roomId,timestampId):
    # audio files : array
    # state active - true/false 
    # state getting_audio : true / false  
    # state transcribeing : true / false  
    # state transcribeing_model :  modelname 
    status = stateManager.roomStatus(roomId,timestampId)
    return jsonify(status)
'''
@app.route("/API/roomProgress/<roomId>/<int:timestampId>", methods=["GET", "POST"])
def roomProgress(roomId,timestampId):
    # audio files : array
    # state active - true/false 
    # state getting_audio : true / false  
    # state transcribeing : true / false  
    # state transcribeing_model :  modelname 
    status = stateManager.getProgress(roomId,timestampId)
    return jsonify(status)
'''
@app.route("/API/stopRoom/<roomId>/<int:timestampId>", methods=["GET", "POST"])
def stopRoom(roomId,timestampId):
    aktiveBot = bots.get(roomId)
    print("stop1")
    if aktiveBot:
        try:
            asyncio.run(aktiveBot.close())
        except Exception as e:
            logger.logging(f"Hiba a bot leállításában, {roomId}, {timestampId}")

        del bots[roomId]

    stateManager.data[roomId][timestampId]['getting_audio'] = False
    return jsonify({'status': room})

@app.route("/API/listRooms", methods=["GET", "POST"])
def listRooms():
    # [<roomId>,<roomId>, ...]
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

@app.route("/API/listRoom/<roomId>", methods=["GET", "POST"])
def listRoom(roomId):
    # [<roomId>: [<timestampId>, ...]]
    return jsonify(list(stateManager.listRoom(roomId)))    

@app.route("/API/listAudioFiles/<roomId>/<int:timestampId>", methods=["GET", "POST"])
def listAudioFiles(roomId, timestampId):
    # [<roomId>-<timestampId>: [audio-0, ...]]
    return jsonify(list(stateManager.listAudioFiles(roomId, timestampId)))

def startBot(roomId):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = Demo(roomdId=roomId, player=None, recorder=MediaBlackhole(), loop=loop)
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
logger.logging("Flask szerver elindult.")
