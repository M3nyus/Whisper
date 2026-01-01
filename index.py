
# import env
from dotenv import load_dotenv
import os

from flask import Flask, render_template, jsonify

from Logger import *
from stateManager import *


load_dotenv()
global REDIS_HOST, REDIS_PORT, REDIS_DB
LOGFILE = os.getenv("LOGFILE")
REDIS_HOST= os.getenv("REDIS_HOST")
REDIS_PORT= os.getenv("REDIS_PORT")
REDIS_DB= os.getenv("REDIS_DB")

# start logger 
global logger
logger = Logger(LOGFILE)

#redisManager = Redis_Manager()
stateManager = StateManager()

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
    # IF NOT in PROGRESS 
    # create_entry
    # start getting audio 
    # start checking for available audio files in redis 
    # return timestampID for roomId
    return jsonify(stateManager.startRoom(roomId))

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
    # if stopped return true 
    # else false 
    return jsonify({'status': stateManager.stopRoom(roomId,timestampId)})

@app.route("/API/listRooms", methods=["GET", "POST"])
def listRooms():
    # [<roomId>,<roomId>, ...]
    return jsonify(list(stateManager.listRooms()))

@app.route("/API/listRoom/<roomId>", methods=["GET", "POST"])
def listRoom(roomId):
    # [<roomId>: [<timestampId>, ...]]
    return jsonify(list(stateManager.listRoom(roomId)))    

@app.route("/API/listAudioFiles/<roomId>/<int:timestampId>", methods=["GET", "POST"])
def listAudioFiles(roomId, timestampId):
    # [<roomId>-<timestampId>: [audio-0, ...]]
    return jsonify(list(stateManager.listAudioFiles(roomId, timestampId)))

APP_HOST= os.getenv("APP_HOST")
APP_PORT= os.getenv("APP_PORT")
APP_DEBUG= os.getenv("APP_DEBUG")
app.run(host=APP_HOST, port=APP_PORT, debug=APP_DEBUG)
logger.logging("Flask szerver elindult.")
