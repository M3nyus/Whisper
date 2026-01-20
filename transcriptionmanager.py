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

            while actual != currKey or self.stateManager.roomStatus(roomId, timestampId)['getting_audio']:
                if actual:
                    await asyncio.sleep(11)
                    print('----')
                    await self.redisManager.redis_stream_to_wav(roomId, chunk)
                    print('++++')
                    await self.transcribeChunk(roomId, chunk)

                    chunk += 1
                    currKey = f"{roomId}:{chunk}"
                else:
                    await asyncio.sleep(5)
                    print('...')
                actual = self.redisManager.get(f"{roomId}_actual")
                print('room_actual', actual)



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