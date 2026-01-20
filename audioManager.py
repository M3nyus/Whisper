import RedisManager
from stateManager import *
from RedisManager import Redis_Manager

# gets audio from the room and puts it in the redis store
class AudioManger:
    def __init__(self):
        # active rooms
        self.data = {}
        self.statemanager = StateManager
        self.redis = RedisManager.Redis_Manager #kerdes
        
    async def startRoomAudioRecording(self, roomId, timestampId):
        # TODO add host
        # TODO separate as a service
        # set getting_audio to True
        # asyncio.run? 
        # join room
        # get audio mix 
        # put it in redis 
        # update state with chunk number
        # update state Manager with audio file
        # on finish set getting_audio to false



        #KIEG
        self.statemanager.data[roomId][timestampId]['getting_audio'] = True

        chunk_i = 0

        while self.statemanager.data[roomId][timestampId]['active']:
            chunk = get_audio_chunk_from_host(roomId) #kerdes ez hogy legyen
            if chunk is None:
                break

            key = f"{roomId}:{timestampId}:audio_{chunk_i}"
            self.redis.set(key, chunk)

            #audio frissit
            self.statemanager.data[roomId][timestampId]['audio_files'][f'audio_{chunk_i}'] = key
            chunk_i += 1

        self.statemanager.data[roomId][timestampId]['getting_audio'] = False

    def stopRoomAudioRecording(self, roomId, timestampId):
        # stop getting audio from room.

        #KIEG
        if roomId in self.statemanager.data and timestampId in self.statemanager.data[roomId]:
            tmp_allapot = self.statemanager.data[roomId][timestampId]
            tmp_allapot['active'] = False
            tmp_allapot['getting_audio'] = False