import time    

class StateManager:
    def __init__(self):
        # TODO load files from disk or store 
        self.data = {}
    def startRoom(self, roomId, model = 'base'): 
        fallback_ct = self.get_current_time()
        room = self.data.get(roomId)
        # create new dict
        if not room:
            self.data[roomId] =  {fallback_ct: self.create_entry(model)}
            return fallback_ct
        # dict exists add new entry if current is not active
        else: 
            entry, data = self.latest_for_room_entry(roomId)
            if entry:
                if data.get('active'):
                    return entry
            # create new entry on existing room
            self.data[roomId][fallback_ct] = self.create_entry(model)
            return fallback_ct
    def roomStatus(self, roomId, timestampId):
        '''if timestampId==None:
            entry, data = self.latest_for_room_entry(roomId)
            if entry:
                print('e,d', entry, data)
                if data.get('active'): 
                    return data
                return False
        '''
        data = self.data.get(roomId)
        if data:
            return data.get(timestampId)
            
    def stopRoom(self, roomId, timestampId): 
        room = self.data.get(roomId)

        if room:
            entry = room.get(timestampId)
            if entry:
                # TODO stop processes
                self.data[roomId][timestampId].update({'active': False})
                return 'Done'
                

    def listRooms(self):
        data = self.data.keys()
        if data:
            return data
        return {}

    def listRoom(self, roomId):
        data = self.data.get(roomId)
        if data:
            return data.keys()
        return {}

    def isRoomActive(self, roomId):
        entry, data = self.latest_for_room_entry(roomId)
        if entry:
            if data.get('active'): 
                return entry
        return False

    def latest_for_room_entry(self, room_id):
        room = self.data.get(room_id)
        if not room:
            return None, None

        ts = max(room)
        return ts, room.get(ts)
    
    def create_entry(self, model):
        entry = {
          'audio_files': {},
          'active': True,
          'getting_audio': False,
          'transcribing': False,
          'transcribing_done': False,
          'transcribing_model': model
        }
        return entry
        
    def get_current_time(self):
        # epoch_time
        return int(time.time())
