from datetime import datetime
from networkx.classes import selfloop_edges
import os

class Logger:
    def __init__(self, log_file):
        self.log_file = log_file

        eleres = os.path.dirname(self.log_file)

        if eleres and not os.path.exists(eleres):
            os.makedirs(eleres)

    def Logging(self, text):
        curr_time = datetime.now().strftime("%y:%m:%d %H:%M:%S")

        with open(self.log_file, "a", encoding="utf-8") as l:
            l.write(f"{curr_time}: {text} \n")