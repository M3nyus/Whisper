from flask import Flask, render_template, url_for, redirect, request
import os
from Logger import *
from Forrasok import *
from Audio_Manager import *
from Text_manager import *
from AI_Summer import *
from Redis_Manager import *
import threading

class Flask_Manager:
    def __init__(self, logger, redis, audio_manager, text_manager, ai_summer):
        self.logger = Logger(utak["log_file"])
        self.redis = Redis_Manager(self.logger)
        self.audio_manager = Audio_Manager(utak["audio_file"], utak["out_folder"], model, self.logger, self.redis,10000)
        self.text_manager = Text_manager(self.audio_manager, utak["out_folder"], utak["egybefuzott"], utak["osszesitett"], utak["redisbol_ossz"], self.logger, self.redis)
        self.ai_summer = AI_Summer(summer, utak["osszesitett"], self.logger)

        self.generated_text = ""

        self.flask_app = Flask(__name__, template_folder='templates')

        # URL-ek hozzáadása
        self.flask_app.add_url_rule("/", "index", self.index)
        self.flask_app.add_url_rule("/feliratozas", "feliratozas", self.feliratozas)
        self.flask_app.add_url_rule("/subtitle", "subtitle", self.subtitle)
        self.flask_app.add_url_rule("/onehang", "onehang", self.onehang, methods=["get", "post"])

    def run(self):
        self.logger.logging("Flask szerver elindult.")
        self.flask_app.run(host="127.0.0.1", port=5000, debug=True)

    def index(self):
        return render_template("index.html")

    def onehang(self):
        szoveg = ""

        if request.method == "POST":
            hang_szam = request.form.get("hang_szam")
            szoveg = self.text_manager.get_hang_from_redis(hang_szam)

        return render_template("OneHang.html", szoveg=szoveg)

    def long_task(self):
        self.audio_manager.working()
        self.text_manager.all_in_one()
        self.generated_text = self.text_manager.get_all_words()

    def feliratozas(self):
        thread = threading.Thread(target=self.long_task)
        thread.start()
        return redirect(url_for('subtitle'))

    def subtitle(self):
        return render_template("Subtitle.html", szoveg=self.generated_text)