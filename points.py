class Points:
    def __init__(self):
        self.pisteet = 0

    def lisaa_piste(self, maara=1):
        self.pisteet += maara

    def nollaa_pisteet(self):
        self.pisteet = 0

    def hae_pisteet(self):
        return self.pisteet

    def show_score(self, x, y, font, screen):
        score = font.render("Pisteet: " + str(self.hae_pisteet()),
        True, (255, 255, 255))
        screen.blit(score, (x, y))