import openai
import whisper
import os
from pydub import AudioSegment
from datetime import datetime
from openai import OpenAI
from transformers import pipeline


# Logger
def logging(text):
    curr_time = datetime.now().strftime("%y:%m:%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as l:
        l.write(f"{curr_time}: {text} \n")


#beállítások
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
model = whisper.load_model("base")
summer = pipeline("summarization",model="t5-large")
client = openai.OpenAI(api_key = "sk - proj - rsMCl - M4ncu - LOCZZ4LStNhq4WMp6WsQ5Goyijlt1CCuxw33gi5c1nZMCb2bm2gWEdYf5HJCkWT3BlbkFJwk7RfC08vNRWID2WIasbvl1wQHe3S9S50xZv7ln86dqpU - KF9QKoZFKBE7y - VXwF0kjRWC2qwA")

#Elérések
audio_file = r"C:\Users\menyh\Desktop\PRO-M\fisrt_shwisper_setup\audio.mp3"
out_folder = r"C:\Users\menyh\Desktop\PRO-M\fisrt_shwisper_setup\hangok"
log_file = r"C:\Users\menyh\Desktop\PRO-M\fisrt_shwisper_setup\log.txt"
egybefuzott = r"C:\Users\menyh\Desktop\PRO-M\fisrt_shwisper_setup\egybefuzott.txt"
osszesitett = r"C:\Users\menyh\Desktop\PRO-M\fisrt_shwisper_setup\osszesitett.txt"

#Feltételek (logoljuk a darabok hosszát)
audio = AudioSegment.from_file(audio_file)
chunk_len = 10 * 1000
logging(f"Hanghossz: {chunk_len/1000}-mp")

#Globális változók
hang_count = 0
summ_words = ""

#Szeletezés
def chunking(segment, chunk_size):
    start = 1
    while start < len(segment):
        yield segment[start:start+chunk_size]
        start += chunk_size

#Egybefűző
def all_in_one():
    logging("Hangok összesítése!")
    words = ""
    for i in range(hang_count):
        needed_text = os.path.join(out_folder, f"hang_{i}.txt")
        with open(needed_text, "r",encoding="utf-8") as f:
            words = f.read()

        with open(egybefuzott, "a", encoding="utf-8") as b:
            b.write(words + "\n")
            words = ""
            logging(f"A hang_{i} tartalma kiolvasva és hozzáadva.")

        logging("Hangok összesítve.")

#Beolvasó
def get_all_words():
    with open(egybefuzott, "r", encoding="utf-8") as f:
        summ_words = f.read()
    logging("Egész szöveg átadva.")
    return summ_words

#AI összegző
def summ_text(text):
    logging("AI által összegzés megkezdése.")
    ai_summ = summer(text, max_new_tokens=150, min_length=40, do_sample=False)
    with open(osszesitett, "w", encoding="utf-8") as o:
        o.write(ai_summ)
    logging("Sikeres AI összegzés.")


#Feldolgozás
def working():
    for i, chunk in enumerate(chunking(audio, chunk_len)):
        logging(f"hang_{i} feldolgozás megkezdése.")
        tmp_file = os.path.join(out_folder, f"hang_{i}.mp3")
        chunk.export(tmp_file, format="mp3")
        global hang_count
        hang_count += 1


        result = model.transcribe(tmp_file, language="hu")

        output_txt = os.path.join(out_folder, f"hang_{i}.txt")
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(result["text"])

        logging(f"{output_txt} feldolgozva.")
        print(f"{output_txt} feldolgozva.")

#working()
#all_in_one()
#summ_text(get_all_words())


logging("Kész.")
print("Kész.")
