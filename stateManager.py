import time    
import os
import pickle 

class StateManager:
    def __init__(self):
        # TODO load files from disk or store
        self.data = self.loadState() #{}
    def startRoom(self, roomId, model = "base"): 
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
        data = self.data.get(roomId)
        if data:
            return data.get(timestampId)
        return False

     #nem hasznalom
    def stopRoom(self, roomId, timestampId): 
        print("stop2")
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

    #KIEG
    def listAudioFiles(self, roomId, timestampId):
        room = self.data.get(roomId)
        if not room:
            return []

        entry = room.get(timestampId)
        if not entry:
            return []

        audioFiles = entry.get('audioFiles')
        if not audioFiles:
            return []

        return list(audioFiles.keys())

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
          'transcribed_files': {},
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
    def saveState(self):
        # save state to disk
        data = self.data
        if data: 
            with open('config/state.pkl', 'wb') as f:
                pickle.dump(data, f)

    def loadState(self):
        # load state from disk

        if os.path.exists('config/state.pkl'):
            with open('config/state.pkl', 'rb') as f:
                loaded_dict = pickle.load(f)
                print(loaded_dict)
                return loaded_dict

        return {}

    def debugData(self):
        print(self.data)
        return self.data
    