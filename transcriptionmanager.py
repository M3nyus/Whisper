import os.path
import time
import whisper
from dotenv import get_key

from stateManager import StateManager
from Logger import *
from RedisManager import *

# starts transcription on the audio recived by the audio manager
class TextManager:
    def __init__(self,stateManager, WHISPER_MODEL, OUTPUT_DIR,REDIS_HOST,REDIS_PORT,REDIS_DB,LOGFILE):
        # active rooms
        self.data = {}

        if WHISPER_MODEL:
            self.model = whisper.load_model(WHISPER_MODEL)
        else:
            self.model = None

        self.OUTPUT_DIR = OUTPUT_DIR
        self.redisManager = Redis_Manager(REDIS_HOST, REDIS_PORT, REDIS_DB, LOGFILE)
        self.logger = Logger(LOGFILE)
        self.stateManager = stateManager

    def changeMode(self, model):
        if model:
            self.logger.Logging(f"Live modell betöltése: {model}")
            self.model = whisper.load_model(model)
        else:
            self.logger.Logging("Demo mód aktiválva, nincs betöltve modell.")
            self.model = None

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

    #Getmp3-hoz szükséges modulok

    def chunking(self, segment, chunkSizeSec):
        chunk_size = chunkSizeSec * 1000
        start = 0

        while start < len(segment):
            yield segment[start:start + chunk_size]
            start += chunk_size

    def getKey(self, name):
        key = name
        i = 0

        while self.redisManager.get(key) is not None:
            i += 1
            key = f"{name}_{i}"

        self.redisManager.set(key, "")
        return key

    def working(self, audio, sec, fileName):
        if self.model is not None:
            mp3Mappa = os.path.join(os.getcwd(), "mp3")
            hangMappa = os.path.join(os.getcwd(), "mp3", "hang")
            chunks = list(self.chunking(audio, sec))
            existKey = self.getKey(fileName)
            progressKey = f"progress:{existKey}"

            if not os.path.exists(mp3Mappa):
                os.makedirs(mp3Mappa)

            if not os.path.exists(hangMappa):
                os.makedirs(hangMappa)

            self.redisManager.delete_key(f"{progressKey}:total")
            self.redisManager.delete_key(f"{progressKey}:curr")
            self.redisManager.set(f"{progressKey}:total", len(chunks))
            self.redisManager.set(f"{progressKey}:curr", 0)

            for i, chunk in enumerate(chunks):
                self.logger.Logging(f"hang_{i} feldolgozás megkezdése.")
                tmp_file = os.path.join(hangMappa, f"hang_{i}.mp3")
                chunk.export(tmp_file, format="mp3")

                result = self.model.transcribe(tmp_file, language="hu")

                self.redisManager.append(existKey, result["text"] + " ")

                self.redisManager.set(f"{progressKey}:curr", i + 1)

                self.logger.Logging(f"hang_{i} feldolgozva.")
                print(f"hang_{i} feldolgozva.")

            return {"demo": False, "key": existKey}
        else:
            progressKey = f"progress:{fileName}"
            self.redisManager.set(f"{progressKey}:total", 1)
            self.redisManager.set(f"{progressKey}:curr", 1)
            return {"demo": True, "text": "Demo mód futott le, azaz nincs betöltött nyelvi modell a feliratozéshoz."}