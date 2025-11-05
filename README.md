# Whisper

# Architecture
```
whisper_test.py (main)
Audio_Manager.py - hang darabolása és feldolgozása       MEGVAN
Text_manager.py - txt fájlok kezelése                   MEGVAN
AI_Summer.py - ai általi összegzés                       Megvan
Logger.py - logger itt van                               MEGVAN
Redis_Manager.py - ez alapján meg a redis szerver
Forrasok.py - beállítások és elérések vannak itt         MEGVAN
```
## Start
```
pip3 install -r requirements.txt
python3 whisper_test.py
```

## Web
```
/ index site
list - name,id
start -(room/file name, model)> id
status/id (site with progress reloads untill 100% complete)
progress/id : step/steps
data/id - text
subdata/id/number - text for subdata
stop/id
```


## Log 
