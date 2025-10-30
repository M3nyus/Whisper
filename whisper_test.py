from Forrasok import *
from Logger import *
from Audio_Manager import *
from Text_manager import *
from AI_Summer import *
from Flask_Manager import *

class App:
    def __init__(self):
        self.logger = Logger(utak["log_file"])
        self.redis = Redis_Manager(self.logger)
        self.audio_manager = Audio_Manager(utak["audio_file"], utak["out_folder"], model, self.logger, self.redis, 10000)
        self.text_manager = Text_manager(self.audio_manager, utak["out_folder"], utak["egybefuzott"], utak["osszesitett"], utak["redisbol_ossz"], self.logger, self.redis)
        self.ai_summer = AI_Summer(summer, utak["osszesitett"], self.logger)
        self.flask = Flask_Manager(self.logger, self.redis, self.audio_manager, self.text_manager, self.ai_summer)



    #Itt adjuk meg mi/hogy fusson
    def run(self):
        #self.audio_manager.working()
        #self.text_manager.all_in_one()
        #self.text_manager.get_all_text_from_all_hang_from_redis_to_txt()

        #self.text_manager.get_hang_from_redis("hang_4")
        #self.ai_summer.summ_text(self.text_manager.get_all_words())

        #self.flask.run()
        #self.flask.test()
        self.flask.run()

        self.logger.logging("Kész.")
        print("Kész.")


if __name__ == "__main__":
    app = App()
    app.run()