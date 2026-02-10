import pygame

class Damage:
    def __init__(self, lives):
        self.lives = lives
        self.last_hit_time = 0
        self.invincible_time = 3000  # 3 sekuntia

    def take_damage(self, amount=1):
        # Ottaa damagea, jos kuolemattomuus ei ole päällä
        current_time = pygame.time.get_ticks()

        if current_time - self.last_hit_time >= self.invincible_time:
            self.lives -= amount
            self.last_hit_time = current_time

    def deal_damage(self, target, amount=1):
        # Tekee damagea toiselle olennolle
        target.damage.take_damage(amount)

    def is_dead(self):
        # Tarkistaa onko elämät loppu
        return self.lives <= 0

    def player_laser_hits_enemy(player_lasers, enemy_group):
        # Pelaajan laser osuu viholliseen
        hits = pygame.sprite.groupcollide(enemy_group, player_lasers, False, True)

        for enemy in hits:
            # Pelaaja tekee damagea viholliseen
            enemy.damage.take_damage(1)

            # Vihollinen kuolee yhdestä osumasta
            if enemy.damage.is_dead():
                enemy.kill()

    def enemy_laser_hits_player(enemy_lasers, player):
        # Vihollisen ammus osuu pelaajaan
        if pygame.sprite.spritecollide(player, enemy_lasers, True):
            # Pelaaja ottaa damagea
            player.damage.take_damage(1)

            # Tarkistetaan kuolema
            if player.damage.is_dead():
                print("Pelaaja kuoli")

    def collision_from_meteor(meteor_group, player):
        # Meteoriittiä ei voi tuhota
        # Pelaaja menettää elämän osuessaan meteoriittiin
        # Pelaaja ei ota uutta damagea 3 sekunnin aikana
        if pygame.sprite.spritecollide(player, meteor_group, False):
            player.damage.take_damage(1)

