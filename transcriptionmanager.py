import os.path
import time
import whisper
from stateManager import StateManager
from Logger import *
from RedisManager import *

# starts transcription on the audio recived by the audio manager
class TextManager:
    def __init__(self,stateManager, WHISPER_MODEL, OUTPUT_DIR,REDIS_HOST,REDIS_PORT,REDIS_DB,LOGFILE):
        # active rooms
        self.data = {}
        self.model = whisper.load_model(WHISPER_MODEL)
        self.OUTPUT_DIR = OUTPUT_DIR
        self.redisManager = Redis_Manager(REDIS_HOST, REDIS_PORT, REDIS_DB)
        self.logger = Logger(LOGFILE)
        self.stateManager = stateManager

    async def startTranscription(self, roomId, timestampId):
        # get updates from state manager
        # check available data from state manager
        chunk = 0
        print("asdasdasdadsasdasdasdadsasdasdasdadsasdasdasdadsasdasdasdadsasdasdasdadsasdasdasdadsasdasdasdadsasdasdasdads")
        while  True:
            # mark:0
            currKey = f"{roomId}:{chunk}"
            nextKey = f"{roomId}:{chunk + 1}"
            self.logger.logging(currKey)

            # mark:10
            actual = self.redisManager.get(f"{roomId}_actual")
            print('room_actual', actual)
            errCounter = 0
            # ha az utolso transcribeolt audio az az aktuális és a getting audio az false
            #while actual != currKey or self.stateManager.roomStatus(roomId, timestampId)['getting_audio']:
            while True:
                if actual == currKey and self.stateManager.roomStatus(roomId, timestampId)['getting_audio']==False:
                    # elértuk az utolsó audiót és leált a rögzítés
                    break
                elif actual is None:
                    # még nincs audio file
                    await asyncio.sleep(5)
                    print('...')
                    errCounter += 1
                    if errCounter > 5:
                        break
                elif actual == currKey and self.stateManager.roomStatus(roomId, timestampId)['getting_audio']==True:
                    await asyncio.sleep(1)
                elif actual != currKey and self.stateManager.roomStatus(roomId, timestampId)['getting_audio']==True:
                    print('room_actual', actual)
                    errCounter = 0
                    # van audio, de lehet hogy még írás közben van
                    await asyncio.sleep(1)
                    print('----')
                    await self.redisManager.redis_stream_to_wav(roomId, chunk)
                    print('++++')
                    await self.transcribeChunk(roomId, chunk)
                    chunk += 1
                    currKey = f"{roomId}:{chunk}"
                else:
                    print('ezmiez')

                actual = self.redisManager.get(f"{roomId}_actual")





    def stopTranscription(self, roomId, timestampId):
        # update stateManager
        self.stateManager.StateManager.stopRoom(roomId, timestampId)

    
    async def transcribeChunk(self, roomId, chunk):
        key = f"{roomId}{chunk}"
        self.logger.logging(f"{roomId}{chunk} - audio adat betöltés.")
        # roomname+timestamp+audio_{chunk}
        mp3_fajl = f"{roomId}{chunk}.mp3"
        self.logger.logging(f"{key} - audio_{chunk} feldolgozás megkezdése.")
        result = self.model.transcribe(os.path.join(os.getcwd(), mp3_fajl), language="hu")
        self.logger.logging(f"{key} - audio_{chunk} feldolgozás kész.")
        self.redisManager.set(key+'res_'+str(chunk), result)
        self.logger.logging(f"{key} - audio_{chunk} feldolgozás redisbe írva [res_{chunk}].")
        with open(self.OUTPUT_DIR+key+'res_'+str(chunk), "w", encoding="utf-8") as f:
                f.write(result["text"])
        self.stateManager.addText(roomId, chunk, result["text"])