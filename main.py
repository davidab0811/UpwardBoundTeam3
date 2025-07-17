import pygame, sys, os, random

pygame.init()

# --- Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = -10
ENEMY_SPEED = 3
BOSS_SPEED, BOSS_HP = 2, 10
POWERUP_INTERVAL = 15000  # 15 seconds
INVINCIBILITY_TIME = 5000  # 5 seconds
FREEZE_DURATION = 5000  # 5 seconds

# --- Setup ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ooga Booga Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 30)

# --- Asset Loader ---
def load_image(name, size):
    return pygame.transform.scale(pygame.image.load(os.path.join("assets", name)), size)

images = {
    "player1": load_image("player1.png", (60, 60)),
    "player2": load_image("player2.png", (60, 60)),
    "enemy": load_image("enemy.png", (50, 50)),
    "boss": load_image("enemy.png", (150, 80)),  # reuse image
    "invincible": load_image("invincible.png", (30, 30)),
    "freeze": load_image("potionBottle.png", (30, 30)),
}

background = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background.png")), (WIDTH, HEIGHT))
pygame.mixer.music.load(os.path.join("assets", "music.mp3"))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# --- Sounds ---
laser_sound = pygame.mixer.Sound(os.path.join("assets", "coin.mp3"))
powerup_sound = pygame.mixer.Sound(os.path.join("assets", "coin.mp3"))
explode_sound = pygame.mixer.Sound(os.path.join("assets", "coin.mp3"))

laser_sound.set_volume(0.5)
powerup_sound.set_volume(0.6)
explode_sound.set_volume(0.6)

# --- Global Freeze Timer ---
enemy_frozen_until = 0

# --- Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image, controls):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.controls = controls
        self.last_shot = 0
        self.shoot_delay = 300  # milliseconds
        self.lives = 3
        self.invincible = False
        self.inv_timer = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[self.controls['left']]: self.rect.x -= PLAYER_SPEED
        if keys[self.controls['right']]: self.rect.x += PLAYER_SPEED
        if keys[self.controls['up']]: self.rect.y -= PLAYER_SPEED
        if keys[self.controls['down']]: self.rect.y += PLAYER_SPEED
        self.rect.clamp_ip(screen.get_rect())

        # Reset invincibility
        if self.invincible and pygame.time.get_ticks() - self.inv_timer > INVINCIBILITY_TIME:
            self.invincible = False
            self.image.set_alpha(255)

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            bullets.add(Bullet(self.rect.centerx, self.rect.top))
            laser_sound.play()
            self.last_shot = now

    def take_damage(self):
        if self.invincible: return
        self.lives -= 1
        explode_sound.play()
        self.invincible = True
        self.inv_timer = pygame.time.get_ticks()
        self.image.set_alpha(100)

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        x = random.randint(50, WIDTH - 50)
        self.image = images["enemy"]
        self.rect = self.image.get_rect(center=(x, -40))
        self.speed = ENEMY_SPEED

    def update(self):
        if pygame.time.get_ticks() < enemy_frozen_until:
            return
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = images["boss"]
        self.rect = self.image.get_rect(center=(WIDTH // 2, -80))
        self.speed = BOSS_SPEED
        self.hp = BOSS_HP
        self.dir = 1

    def update(self):
        if pygame.time.get_ticks() < enemy_frozen_until:
            return
        if self.rect.top < 50:
            self.rect.y += self.speed
        else:
            self.rect.x += self.dir * self.speed
            if self.rect.left <= 0 or self.rect.right >= WIDTH:
                self.dir *= -1

    def take_damage(self):
        self.hp -= 1
        return self.hp <= 0

#Code for both bullet colors
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((6, 20))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=(x, y))
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((6, 20))
        self.image.fill((107, 41, 129))
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.y += BULLET_SPEED
        if self.rect.bottom < 0:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.kind = random.choice(["invincible", "freeze"])
        x = random.randint(50, WIDTH - 50)
        self.image = images[self.kind]
        self.rect = self.image.get_rect(center=(x, -30))
        self.speed = 2

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()

# --- Groups ---
players = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bosses = pygame.sprite.Group()
powerups = pygame.sprite.Group()

# --- Game State Setup ---
def reset_game():
    global p1, p2, score, wave, game_state, enemy_frozen_until
    players.empty(); bullets.empty(); enemies.empty(); bosses.empty(); powerups.empty()
    p1 = Player(WIDTH//3, HEIGHT-60, images["player1"], {
        "up":pygame.K_w,"down":pygame.K_s,"left":pygame.K_a,"right":pygame.K_d,"shoot":pygame.K_f})
    p2 = Player(2*WIDTH//3, HEIGHT-60, images["player2"], {
        "up":pygame.K_UP,"down":pygame.K_DOWN,"left":pygame.K_LEFT,"right":pygame.K_RIGHT,"shoot":pygame.K_RETURN})
    players.add(p1, p2)
    score, wave = 0, 0
    game_state = "play"
    enemy_frozen_until = 0

reset_game()

# --- Waves ---
boss_waves = {1: 10, 2: 20}

# --- Timers ---
ENEMY_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(ENEMY_EVENT, 800)

PU_EVENT = pygame.USEREVENT + 2
pygame.time.set_timer(PU_EVENT, POWERUP_INTERVAL)

# --- Game Loop ---
running = True
while running:
    clock.tick(FPS)
    screen.blit(background, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "play":
            if event.type == ENEMY_EVENT and not bosses:
                wave += 1
                if wave in boss_waves:
                    bosses.add(Boss())
                else:
                    for _ in range(5 + wave):
                        enemies.add(Enemy())

            if event.type == PU_EVENT:
                powerups.add(PowerUp())

        elif game_state == "gameover":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                reset_game()

    if game_state == "play":
        keys = pygame.key.get_pressed()
        if keys[p1.controls["shoot"]]: p1.shoot()
        if keys[p2.controls["shoot"]]: p2.shoot()

        players.update(); bullets.update()
        enemies.update(); bosses.update(); powerups.update()

        for b in bullets:
            hitE = pygame.sprite.spritecollideany(b, enemies)
            if hitE:
                hitE.kill(); b.kill(); score += 1
            hitB = pygame.sprite.spritecollideany(b, bosses)
            if hitB:
                b.kill()
                if hitB.take_damage():
                    bosses.empty()
                    score += 5

        for pl in players:
            if pygame.sprite.spritecollideany(pl, enemies) or pygame.sprite.spritecollideany(pl, bosses):
                pl.take_damage()

        for pl in players:
            collided = pygame.sprite.spritecollideany(pl, powerups)
            if collided:
                if collided.kind == "invincible":
                    pl.invincible = True
                    pl.inv_timer = pygame.time.get_ticks()
                    pl.image.set_alpha(100)
                elif collided.kind == "freeze":
                    enemy_frozen_until = pygame.time.get_ticks() + FREEZE_DURATION
                collided.kill()
                powerup_sound.play()

        if p1.lives <= 0 and p2.lives <= 0:
            game_state = "gameover"

        #Code to kill players when lives are 0.
        if p1.lives == 0:
            p1.kill()

        if p2.lives == 0:
            p2.kill()


        players.draw(screen); bullets.draw(screen)
        enemies.draw(screen); bosses.draw(screen); powerups.draw(screen)

        screen.blit(font.render(f"Score: {score}", True, (255,255,255)), (20, 20))
        screen.blit(font.render(f"Wave: {wave}", True, (255,255,255)), (20, 60))
        screen.blit(font.render(f"P1 Lives: {p1.lives}", True, (0,200,255)), (20, 100))
        screen.blit(font.render(f"P2 Lives: {p2.lives}", True, (255,50,50)), (20, 140))

        if pygame.time.get_ticks() < enemy_frozen_until:
            screen.blit(font.render("Enemies Frozen!", True, (0, 255, 255)), (WIDTH - 250, 20))

    elif game_state == "gameover":
        screen.blit(font.render("GAME OVER", True, (255, 0, 0)), (WIDTH//2 - 100, HEIGHT//2 - 40))
        screen.blit(font.render("Press R to Restart", True, (255, 255, 255)), (WIDTH//2 - 130, HEIGHT//2 + 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
