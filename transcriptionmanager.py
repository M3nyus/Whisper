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
        self.redisManager = Redis_Manager(REDIS_HOST, REDIS_PORT, REDIS_DB, LOGFILE)
        self.logger = Logger(LOGFILE)
        self.stateManager = stateManager

    async def startTranscription(self, roomId, timestampId):
        self.logger.logging(f"Feliratozás megkezdése ({roomId}, {timestampId}).")
        chunk = 0

        while  True:
            currKey = f"{roomId}:{chunk}"
            nextKey = f"{roomId}:{chunk + 1}"
            self.logger.Logging(currKey)

            actual = self.redisManager.get(f"{roomId}_actual")
            print('room_actual', actual)
            errCounter = 0

            while True:
                if actual == currKey and self.stateManager.roomStatus(roomId, timestampId)['getting_audio']==False:
                    break
                elif actual is None:
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
                    await asyncio.sleep(1)

                    await self.redisManager.redis_stream_to_wav(roomId, chunk)

                    await self.transcribeChunk(roomId, chunk)
                    chunk += 1
                    currKey = f"{roomId}:{chunk}"
                else:
                    print('')

                actual = self.redisManager.get(f"{roomId}_actual")

    def stopTranscription(self, roomId, timestampId):
        self.stateManager.StateManager.stopRoom(roomId, timestampId)

    async def transcribeChunk(self, roomId, chunk):
        key = f"{roomId}{chunk}"
        self.logger.Logging(f"{roomId}{chunk} - audio adat betöltés.")
        # roomname+timestamp+audio_{chunk}
        mp3_fajl = f"{roomId}{chunk}.mp3"
        self.logger.Logging(f"{key} feldolgozás megkezdése.")
        result = self.model.transcribe(os.path.join(os.getcwd(), mp3_fajl), language="hu")
        self.logger.Logging(f"{key} feldolgozás kész.")
        self.redisManager.set(key+'res_'+str(chunk), result)
        self.logger.Logging(f"{key} feldolgozás redisbe írva [res_{chunk}].")
        with open(self.OUTPUT_DIR+key+'res_'+str(chunk), "w", encoding="utf-8") as f:
                f.write(result["text"])
        self.stateManager.addText(roomId, chunk, result["text"])