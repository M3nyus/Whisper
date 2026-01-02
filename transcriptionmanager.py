import time
# starts transcription on the audio recived by the audio manager
class TextManager:
    def __init__(self):
        # active rooms
        self.data = {}
        self.model = whisper.load_model(WHISPER_MODEL)

    def startTranscription(self, roomId, timestampId):
        # get updates from state manager
        # check available data from state manager
        while True:
            
            data = stateManager.roomStatus(roomId, timestampId)
            if data:
                a_lenght = len(data.get('audio_files'))
                t_lenght = len(data.get('audio_files'))
                getting_audio = data.get('getting_audio')
                
                if a_lenght > t_lenght:
                    self.transcribeChunk((roomId+str(timestampId)),t_lenght+1)
                elif getting_audio:
                    # we need to keep waiting
                    time.sleep(1)
                    continue
                else:
                    break
            else: 
                # data is false. Room does not exist something is wrong
                break    
    def stopTranscription(self, roomId, timestampId):
        # update stateManager
    
    def transcribeChunk(self, key, chunk):
        logger.logging(f"{key} - audio_{chunk} adat betöltés.")
        # roomname+timestamp+audio_{chunk}
        mp3 = redisManager.get(key+'audio_'+str(chunk))

        logger.logging(f"{key} - audio_{chunk} feldolgozás megkezdése.")

        result = self.model.transcribe(mp3, language="hu")
        
        logger.logging(f"{key} - audio_{chunk} feldolgozás kész.")
        
        self.redis.set(key+'res_'+str(chunk), result)
        
        logger.logging(f"{key} - audio_{chunk} feldolgozás redisbe írva [res_{chunk}].")
        
        with open(OUTPUT_DIR+key+'res_'+str(chunk), "w", encoding="utf-8") as f:
                f.write(result["text"])
        
