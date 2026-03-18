import time    
import os
import pickle
from Logger import *

class StateManager:
    def __init__(self, LOGFILE):
        # TODO load files from disk or store
        self.logger = Logger(LOGFILE)
        self.data = self.loadState() #{}

    def startRoom(self, roomId, model = "base"): 
        fallback_ct = self.getCurrentTime()
        room = self.data.get(roomId)
        self.logger.Logging(f"Szoba létrehozva, Név: {roomId}, model: {model}")
        # create new dict

        if not room:
            self.data[roomId] =  {fallback_ct: self.createEntry(model)}
            return fallback_ct
        # dict exists add new entry if current is not active
        else: 
            entry, data = self.latest_for_room_entry(roomId)
            if entry:
                if data.get('active'):
                    return entry
            # create new entry on existing room
            self.data[roomId][fallback_ct] = self.createEntry(model)
            return fallback_ct

    def roomStatus(self, roomId, timestampId):
        data = self.data.get(roomId)
        if data:
            return data.get(timestampId)
        return False

     #nem hasznalom
    def stopRoom(self, roomId, timestampId):
        room = self.data.get(roomId)

        if room:
            entry = room.get(timestampId)
            if entry:
                self.data[roomId][timestampId].update({'active': False})
                self.logger.Logging(f"Szoba leállítva. {roomId}, {timestampId}")
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
    
    def addText(self, roomId, chunk, text):
        print('addText', roomId, chunk, text)
        print(self.data.get(roomId))
        entry, data = self.latest_for_room_entry(roomId)
        print('addText2', entry, data)
        key = f"{chunk}"
        if entry:
            self.data[roomId][entry]['transcribed_files'][key] = text
            self.logger.Logging("Szöveg hozzáadva (addText).")
        else:
            # error?
            print('invalid state?')
    
    
    def getLastText(self, roomId):
        entry, data = self.latest_for_room_entry(roomId)
        text_data = self.data[roomId][entry]['transcribed_files']
        if len(text_data) > 0:
            ts = max(text_data)
            if ts:
                self.logger.Logging(f"Utolsó feliratozott szöveg lekérve: {text_data[ts]}")
                return text_data[ts]
        return '...'
    
    def createEntry(self, model):
        self.model_ = {
            'audio_files': {},
            'transcribed_files': {},
            'active': True,
            'getting_audio': False,
            'transcribing': False,
            'transcribing_done': False,
            'transcribing_model': model
        }
        entry = self.model_
        self.logger.Logging(f"Entry létrehozva. {entry}")
        return entry
        
    def getCurrentTime(self):
        # epoch_time
        self.logger.Logging(f"Epoch time lekérve: {time.time()}")
        return int(time.time())

    def saveState(self):
        # save state to disk
        data = self.data
        if data: 
            with open('config/state.pkl', 'wb') as f:
                pickle.dump(data, f)

        self.logger.Logging("Állapot elmentve.")

    def loadState(self):
        # load state from disk

        if os.path.exists('config/state.pkl'):
            with open('config/state.pkl', 'rb') as f:
                loaded_dict = pickle.load(f)
                print(loaded_dict)
                self.logger.Logging(f"Állapotbetöltés sikeres: {loaded_dict}")
                return loaded_dict

        return {}

    def debugData(self):
        print(self.data)
        self.logger.Logging(f"DebugData: {self.data}")
        return self.data