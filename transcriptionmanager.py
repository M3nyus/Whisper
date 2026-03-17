import os.path
import time
import whisper
from stateManager import StateManager
from Logger import *
from RedisManager import *

# starts transcription on the audio recived by the audio manager
class TextManager:
    def __init__(self,stateManager, WHISPER_MODEL, OUTPUT_DIR,REDIS_HOST,REDIS_PORT,REDIS_DB,LOGFILE, progressData):
        # active rooms
        self.data = {}
        self.model = whisper.load_model(WHISPER_MODEL)
        self.OUTPUT_DIR = OUTPUT_DIR
        self.redisManager = Redis_Manager(REDIS_HOST, REDIS_PORT, REDIS_DB, LOGFILE)
        self.logger = Logger(LOGFILE)
        self.stateManager = stateManager
        self.progressData = progressData

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
        start = 1

        while start < len(segment):
            yield segment[start:start + chunk_size]
            start += chunk_size

    def working(self, audio, sec):
        hangMappa = os.path.join(os.getcwd(), "mp3", "hang")
        feliratMappa = os.path.join(os.getcwd(), "mp3", "felirat")

        chunks = list(self.chunking(audio, sec))

        self.progressData["total"] = len(chunks)
        self.progressData["curr"] = 0

        for i, chunk in enumerate(self.chunking(audio, sec)):
            self.logger.Logging(f"hang_{i} feldolgozás megkezdése.")
            tmp_file = os.path.join(hangMappa, f"hang_{i}.mp3")
            chunk.export(tmp_file, format="mp3")

            result = self.model.transcribe(tmp_file, language="hu")

            output_txt = os.path.join(feliratMappa, f"felirat.txt")
            with open(output_txt, "a", encoding="utf-8") as f:
                f.write(result["text"] + " ")

            self.progressData["current"] = i + 1

            self.logger.Logging(f"hang_{i} feldolgozva.")
            print(f"hang_{i} feldolgozva.")