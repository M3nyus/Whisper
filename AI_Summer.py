from Logger import Logger

class AI_Summer:
    def __init__(self, summer, osszesitett, logger):
        self.summer = summer
        self.osszesitett = osszesitett
        self.logger = logger

    def summ_text(self, text):
        self.logger.logging("AI által összegzés megkezdése.")
        ai_summ = self.summer(text, max_new_tokens=150, min_length=40, do_sample=False)
        with open(self.osszesitett, "w", encoding="utf-8") as o:
            o.write(ai_summ)
        self.logger.logging("Sikeres AI összegzés.")