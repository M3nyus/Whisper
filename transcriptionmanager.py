import os.path
import time
import whisper
from stateManager import StateManager
from Logger import *
from RedisManager import *

# starts transcription on the audio recived by the audio manager
class TextManager:
    def __init__(self, WHISPER_MODEL, OUTPUT_DIR,REDIS_HOST,REDIS_PORT,REDIS_DB,LOGFILE):
        # active rooms
        self.data = {}
        self.model = whisper.load_model(WHISPER_MODEL)
        self.OUTPUT_DIR = OUTPUT_DIR
        self.redisManager = Redis_Manager(REDIS_HOST, REDIS_PORT, REDIS_DB)
        self.logger = Logger(LOGFILE)
        self.stateManager = StateManager()

    async def startTranscription(self, roomId, timestampId):
        # get updates from state manager
        # check available data from state manager
        chunk = 0
        print("asdasdasdadsasdasdasdadsasdasdasdadsasdasdasdadsasdasdasdadsasdasdasdadsasdasdasdadsasdasdasdadsasdasdasdads")
        while  True:
            currKey = f"{roomId}:{chunk}"
            nextKey = f"{roomId}:{chunk + 1}"
            self.logger.logging(currKey)

            if self.redisManager.get(currKey) is not None:
                await self.redisManager.redis_stream_to_wav(currKey, roomId, chunk)
                await self.transcribeChunk(f"komplett{roomId}{chunk}", chunk)

                if self.redisManager.get(nextKey) is None and self.stateManager.roomStatus(roomId, timestampId):
                    await asyncio.sleep(1)
                if self.redisManager.get(nextKey) is None:
                    await asyncio.sleep(1)
                else:
                    chunk += 1
            else:
                await asyncio.sleep(1)



    def stopTranscription(self, roomId, timestampId):
        # update stateManager
        self.stateManager.StateManager.stopRoom(roomId, timestampId)

    
    async def transcribeChunk(self, key, chunk):
        self.logger.logging(f"{key} - audio_{chunk} adat betöltés.")
        # roomname+timestamp+audio_{chunk}
        back = self.redisManager.get(key)
        with open(f"back{key}.mp3", "wb") as f:
            f.write(back)

        self.logger.logging(f"{key} - audio_{chunk} feldolgozás megkezdése.")

        result = self.model.transcribe(os.path.join(os.getcwd(),f"back{key}.mp3"), language="hu")
        
        self.logger.logging(f"{key} - audio_{chunk} feldolgozás kész.")
        
        self.redisManager.set(key+'res_'+str(chunk), result)
        
        self.logger.logging(f"{key} - audio_{chunk} feldolgozás redisbe írva [res_{chunk}].")
        
        with open(self.OUTPUT_DIR+key+'res_'+str(chunk), "w", encoding="utf-8") as f:
                f.write(result["text"])