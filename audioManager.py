# gets audio from the room and puts it in the redis store
class AudioManger:
    def __init__(self):
        # active rooms
        self.data = {}
        
    def startRoomAudioRecording(self, roomId, timestampId):
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
        
    def stopRoomAudioRecording(self, roomId, timestampId):
        # stop getting audio from room.