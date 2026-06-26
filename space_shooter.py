import pygame
import random
import json
import os
import sys
import math

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)

DIFFICULTY = {
    'easy': {'meteor_spawn_rate': 80, 'meteor_speed_min': 1, 'meteor_speed_max': 3, 'label': '简单'},
    'normal': {'meteor_spawn_rate': 50, 'meteor_speed_min': 2, 'meteor_speed_max': 5, 'label': '普通'},
    'hard': {'meteor_spawn_rate': 30, 'meteor_speed_min': 3, 'meteor_speed_max': 7, 'label': '困难'}
}

SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'high_score.json')


def load_high_score():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0)
        except (json.JSONDecodeError, IOError):
            return 0
    return 0


def save_high_score(score):
    try:
        with open(SCORE_FILE, 'w') as f:
            json.dump({'high_score': score}, f)
    except IOError:
        pass


class Star:
    def __init__(self):
        self.reset(True)

    def reset(self, initial=False):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT) if initial else -5
        self.size = random.choice([1, 1, 2, 2, 3])
        self.speed = random.uniform(0.5, 2.0)
        self.brightness = random.randint(100, 255)

    def update(self, speed_multiplier=1.0):
        self.y += self.speed * speed_multiplier
        if self.y > SCREEN_HEIGHT:
            self.reset(False)

    def draw(self, screen):
        color = (self.brightness, self.brightness, self.brightness)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)


class Player:
    def __init__(self):
        self.width = 50
        self.height = 50
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - self.height - 20
        self.speed = 6
        self.shoot_cooldown = 0
        self.shoot_delay = 20
        self.power_up = False
        self.power_up_timer = 0
        self.power_up_duration = FPS * 10
        self.shield = False
        self.shield_timer = 0
        self.shield_duration = FPS * 8
        self.shield_phase = 0
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed

        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.power_up:
            self.power_up_timer -= 1
            if self.power_up_timer <= 0:
                self.power_up = False

        if self.shield:
            self.shield_timer -= 1
            self.shield_phase += 0.1
            if self.shield_timer <= 0:
                self.shield = False

        self.rect.x = self.x
        self.rect.y = self.y

    def shoot(self):
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = self.shoot_delay
            bullets = []
            if self.power_up:
                bullets.append(Bullet(self.x + self.width // 2, self.y, 0, -10))
                bullets.append(Bullet(self.x + self.width // 2 - 15, self.y + 10, -2, -10))
                bullets.append(Bullet(self.x + self.width // 2 + 15, self.y + 10, 2, -10))
            else:
                bullets.append(Bullet(self.x + self.width // 2, self.y, 0, -10))
            return bullets
        return []

    def activate_power_up(self):
        self.power_up = True
        self.power_up_timer = self.power_up_duration

    def activate_shield(self):
        self.shield = True
        self.shield_timer = self.shield_duration
        self.shield_phase = 0

    def draw(self, screen):
        pygame.draw.polygon(screen, BLUE, [
            (self.x + self.width // 2, self.y),
            (self.x, self.y + self.height),
            (self.x + self.width, self.y + self.height)
        ])
        pygame.draw.rect(screen, GREEN, (self.x + self.width // 2 - 5, self.y + 10, 10, 20))

        if self.power_up:
            pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2, self.y + self.height // 2),
                               self.width // 2 + 3, 2)

        if self.shield:
            cx = self.x + self.width // 2
            cy = self.y + self.height // 2
            radius = self.width // 2 + 8 + int(3 * math.sin(self.shield_phase))
            alpha = 180 if self.shield_timer > FPS else int(180 * (self.shield_timer / FPS))
            shield_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (80, 150, 255, alpha), (radius + 2, radius + 2), radius, 3)
            pygame.draw.circle(shield_surf, (150, 200, 255, alpha // 2), (radius + 2, radius + 2), radius - 3, 1)
            screen.blit(shield_surf, (cx - radius - 2, cy - radius - 2))


class Bullet:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 4
        self.rect = pygame.Rect(x - self.radius, y - self.radius, self.radius * 2, self.radius * 2)
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.x = self.x - self.radius
        self.rect.y = self.y - self.radius
        if self.y < -10 or self.y > SCREEN_HEIGHT + 10 or self.x < -10 or self.x > SCREEN_WIDTH + 10:
            self.active = False

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)


class Meteor:
    def __init__(self, x=None, y=None, size='large'):
        self.size = size
        if size == 'large':
            self.radius = 35
            self.score = 20
        elif size == 'medium':
            self.radius = 22
            self.score = 50
        else:
            self.radius = 12
            self.score = 100

        self.x = x if x is not None else random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = y if y is not None else -self.radius
        self.speed_y = random.uniform(DIFFICULTY['normal']['meteor_speed_min'],
                                      DIFFICULTY['normal']['meteor_speed_max'])
        self.speed_x = random.uniform(-1.5, 1.5)
        self.rotation = 0
        self.rotation_speed = random.uniform(-2, 2)
        self.active = True
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def set_speed_range(self, min_speed, max_speed):
        self.speed_y = random.uniform(min_speed, max_speed)

    def update(self, speed_multiplier=1.0):
        self.y += self.speed_y * speed_multiplier
        self.x += self.speed_x
        self.rotation += self.rotation_speed

        if self.x < self.radius or self.x > SCREEN_WIDTH - self.radius:
            self.speed_x *= -1

        if self.y > SCREEN_HEIGHT + self.radius:
            self.active = False

        self.rect.x = self.x - self.radius
        self.rect.y = self.y - self.radius

    def split(self):
        if self.size == 'large':
            return [
                Meteor(self.x - 10, self.y, 'medium'),
                Meteor(self.x + 10, self.y, 'medium')
            ]
        elif self.size == 'medium':
            return [
                Meteor(self.x - 8, self.y, 'small'),
                Meteor(self.x + 8, self.y, 'small')
            ]
        return []

    def draw(self, screen):
        color = (139, 90, 43)
        if self.size == 'small':
            color = (160, 110, 60)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (100, 60, 30), (int(self.x) - 5, int(self.y) - 5), self.radius // 3)
        pygame.draw.circle(screen, (100, 60, 30), (int(self.x) + 8, int(self.y) + 3), self.radius // 4)


class PowerUp:
    def __init__(self):
        self.radius = 12
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = -self.radius
        self.speed_y = 2
        self.active = True
        self.pulse_phase = 0
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self):
        self.y += self.speed_y
        self.pulse_phase += 0.15
        if self.y > SCREEN_HEIGHT + self.radius:
            self.active = False
        self.rect.x = self.x - self.radius
        self.rect.y = self.y - self.radius

    def draw(self, screen):
        pulse = int(4 * abs(self.pulse_phase % 1 - 0.5) * 2)
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius + pulse, 2)
        all_points = []
        for i in range(10):
            angle = i * 36 - 90
            rad = angle * math.pi / 180
            if i % 2 == 0:
                r = (self.radius - 2) * 0.9
            else:
                r = (self.radius - 6) * 0.9
            px = self.x + r * math.cos(rad)
            py = self.y + r * math.sin(rad)
            all_points.append((int(px), int(py)))
        pygame.draw.polygon(screen, RED, all_points)


class Particle:
    def __init__(self, x, y, color=None):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 5.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.randint(15, 40)
        self.max_lifetime = self.lifetime
        self.size = random.randint(2, 5)
        if color is None:
            self.color = random.choice([
                (255, 200, 50), (255, 150, 30), (255, 100, 20),
                (200, 80, 20), (255, 255, 100)
            ])
        else:
            self.color = color
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.97
        self.vy *= 0.97
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False

    def draw(self, screen):
        alpha_ratio = self.lifetime / self.max_lifetime
        r = min(255, int(self.color[0] * alpha_ratio))
        g = min(255, int(self.color[1] * alpha_ratio))
        b = min(255, int(self.color[2] * alpha_ratio))
        s = max(1, int(self.size * alpha_ratio))
        pygame.draw.rect(screen, (r, g, b), (int(self.x), int(self.y), s, s))


class ShieldPowerUp:
    def __init__(self):
        self.radius = 12
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = -self.radius
        self.speed_y = 2
        self.active = True
        self.pulse_phase = 0
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self):
        self.y += self.speed_y
        self.pulse_phase += 0.15
        if self.y > SCREEN_HEIGHT + self.radius:
            self.active = False
        self.rect.x = self.x - self.radius
        self.rect.y = self.y - self.radius

    def draw(self, screen):
        pulse = int(4 * abs(self.pulse_phase % 1 - 0.5) * 2)
        pygame.draw.circle(screen, (80, 150, 255), (int(self.x), int(self.y)), self.radius + pulse, 2)
        all_points = []
        for i in range(10):
            angle = i * 36 - 90
            rad = angle * math.pi / 180
            if i % 2 == 0:
                r = (self.radius - 2) * 0.9
            else:
                r = (self.radius - 6) * 0.9
            px = self.x + r * math.cos(rad)
            py = self.y + r * math.sin(rad)
            all_points.append((int(px), int(py)))
        pygame.draw.polygon(screen, (80, 150, 255), all_points)
        pygame.draw.circle(screen, (150, 200, 255), (int(self.x), int(self.y)), 4)


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, screen, font):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8)
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('2D 打飞机')
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont('microsoftyahei', 48)
        self.font_medium = pygame.font.SysFont('microsoftyahei', 32)
        self.font_small = pygame.font.SysFont('microsoftyahei', 24)
        self.high_score = load_high_score()
        self.state = 'menu'
        self.difficulty = 'normal'
        self.menu_buttons = []
        self.gameover_buttons = []
        self.reset_game()

    def reset_game(self):
        self.player = Player()
        self.bullets = []
        self.meteors = []
        self.power_ups = []
        self.shield_power_ups = []
        self.particles = []
        self.stars = [Star() for _ in range(150)]
        self.score = 0
        self.game_time = 0
        self.meteor_spawn_timer = 0
        self.power_up_spawn_timer = 0

    def get_speed_multiplier(self):
        return 1.0 + (self.game_time / (FPS * 60)) * 1.5

    def spawn_meteor(self):
        diff = DIFFICULTY[self.difficulty]
        m = Meteor()
        min_s = diff['meteor_speed_min'] * self.get_speed_multiplier()
        max_s = diff['meteor_speed_max'] * self.get_speed_multiplier()
        m.set_speed_range(min_s, max_s)
        self.meteors.append(m)

    def spawn_power_up(self):
        self.power_ups.append(PowerUp())

    def spawn_shield_power_up(self):
        self.shield_power_ups.append(ShieldPowerUp())

    def spawn_particles(self, x, y, count=12, color=None):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def check_collisions(self):
        for bullet in self.bullets:
            if not bullet.active:
                continue
            for meteor in self.meteors:
                if not meteor.active:
                    continue
                if bullet.rect.colliderect(meteor.rect):
                    bullet.active = False
                    meteor.active = False
                    self.score += meteor.score
                    count = 15 if meteor.size == 'large' else (10 if meteor.size == 'medium' else 6)
                    self.spawn_particles(meteor.x, meteor.y, count)
                    new_meteors = meteor.split()
                    for nm in new_meteors:
                        diff = DIFFICULTY[self.difficulty]
                        min_s = diff['meteor_speed_min'] * self.get_speed_multiplier()
                        max_s = diff['meteor_speed_max'] * self.get_speed_multiplier()
                        nm.set_speed_range(min_s, max_s)
                        self.meteors.append(nm)
                    break

        for power_up in self.power_ups:
            if not power_up.active:
                continue
            if power_up.rect.colliderect(self.player.rect):
                power_up.active = False
                self.player.activate_power_up()

        for shield_pu in self.shield_power_ups:
            if not shield_pu.active:
                continue
            if shield_pu.rect.colliderect(self.player.rect):
                shield_pu.active = False
                self.player.activate_shield()

        for meteor in self.meteors:
            if not meteor.active:
                continue
            if meteor.rect.colliderect(self.player.rect):
                if self.player.shield:
                    self.player.shield = False
                    self.player.shield_timer = 0
                    meteor.active = False
                    self.spawn_particles(meteor.x, meteor.y, 10, (80, 150, 255))
                else:
                    self.state = 'gameover'
                    self.spawn_particles(self.player.x + self.player.width // 2,
                                         self.player.y + self.player.height // 2, 25)
                    if self.score > self.high_score:
                        self.high_score = self.score
                        save_high_score(self.high_score)
                break

    def update_menu(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.menu_buttons:
            btn.update(mouse_pos)
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self.menu_buttons):
                    if btn.is_clicked(event.pos):
                        if i < 3:
                            self.difficulty = list(DIFFICULTY.keys())[i]
                        elif i == 3:
                            self.reset_game()
                            self.state = 'playing'
                        elif i == 4:
                            return False
        return True

    def draw_menu(self):
        self.screen.fill(BLACK)
        for star in self.stars:
            star.update()
            star.draw(self.screen)

        title = self.font_large.render('2D 打飞机', True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)

        diff_label = self.font_medium.render(f'当前难度: {DIFFICULTY[self.difficulty]["label"]}', True, WHITE)
        diff_rect = diff_label.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(diff_label, diff_rect)

        high_score_text = self.font_small.render(f'历史最高分: {self.high_score}', True, GREEN)
        hs_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, 190))
        self.screen.blit(high_score_text, hs_rect)

        self.menu_buttons = []
        btn_w, btn_h = 200, 50
        btn_x = SCREEN_WIDTH // 2 - btn_w // 2
        y_start = 240
        spacing = 65

        for i, (key, val) in enumerate(DIFFICULTY.items()):
            btn = Button(btn_x, y_start + i * spacing, btn_w, btn_h, val['label'],
                         GRAY if self.difficulty != key else BLUE, BLUE)
            self.menu_buttons.append(btn)

        start_btn = Button(btn_x, y_start + 3 * spacing, btn_w, btn_h, '开始游戏', GREEN, (100, 255, 100))
        self.menu_buttons.append(start_btn)

        exit_btn = Button(btn_x, y_start + 4 * spacing, btn_w, btn_h, '退出游戏', RED, (255, 100, 100))
        self.menu_buttons.append(exit_btn)

        for btn in self.menu_buttons:
            btn.draw(self.screen, self.font_small)

        hint = self.font_small.render('方向键或A/D移动，空格键发射', True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(hint, hint_rect)

    def update_playing(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                return False

        keys = pygame.key.get_pressed()
        self.player.update(keys)

        if keys[pygame.K_SPACE]:
            new_bullets = self.player.shoot()
            self.bullets.extend(new_bullets)

        speed_mult = self.get_speed_multiplier()

        for star in self.stars:
            star.update(speed_mult)

        for bullet in self.bullets:
            bullet.update()

        for meteor in self.meteors:
            meteor.update(speed_mult)

        for power_up in self.power_ups:
            power_up.update()

        for shield_pu in self.shield_power_ups:
            shield_pu.update()

        for particle in self.particles:
            particle.update()

        self.game_time += 1

        diff = DIFFICULTY[self.difficulty]
        spawn_rate = max(10, int(diff['meteor_spawn_rate'] / speed_mult))
        self.meteor_spawn_timer += 1
        if self.meteor_spawn_timer >= spawn_rate:
            self.meteor_spawn_timer = 0
            self.spawn_meteor()

        self.power_up_spawn_timer += 1
        if self.power_up_spawn_timer >= FPS * 15:
            self.power_up_spawn_timer = 0
            if random.random() < 0.5:
                self.spawn_power_up()
            elif random.random() < 0.5:
                self.spawn_shield_power_up()

        self.bullets = [b for b in self.bullets if b.active]
        self.meteors = [m for m in self.meteors if m.active]
        self.power_ups = [p for p in self.power_ups if p.active]
        self.shield_power_ups = [s for s in self.shield_power_ups if s.active]
        self.particles = [p for p in self.particles if p.active]

        self.check_collisions()

        return True

    def draw_playing(self):
        self.screen.fill(BLACK)

        for star in self.stars:
            star.draw(self.screen)

        for bullet in self.bullets:
            bullet.draw(self.screen)

        for meteor in self.meteors:
            meteor.draw(self.screen)

        for power_up in self.power_ups:
            power_up.draw(self.screen)

        for shield_pu in self.shield_power_ups:
            shield_pu.draw(self.screen)

        for particle in self.particles:
            particle.draw(self.screen)

        self.player.draw(self.screen)

        score_text = self.font_small.render(f'分数: {self.score}', True, WHITE)
        self.screen.blit(score_text, (10, 10))

        hs_text = self.font_small.render(f'最高分: {self.high_score}', True, GREEN)
        self.screen.blit(hs_text, (10, 40))

        if self.player.power_up:
            time_left = self.player.power_up_timer // FPS
            pu_text = self.font_small.render(f'三连发: {time_left}s', True, YELLOW)
            self.screen.blit(pu_text, (SCREEN_WIDTH - 150, 10))

        if self.player.shield:
            time_left = self.player.shield_timer // FPS
            sh_text = self.font_small.render(f'护盾: {time_left}s', True, (80, 150, 255))
            self.screen.blit(sh_text, (SCREEN_WIDTH - 150, 40))

        minutes = self.game_time // (FPS * 60)
        seconds = (self.game_time // FPS) % 60
        time_text = self.font_small.render(f'时间: {minutes:02d}:{seconds:02d}', True, WHITE)
        self.screen.blit(time_text, (SCREEN_WIDTH - 150, 70))

    def update_gameover(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.gameover_buttons:
            btn.update(mouse_pos)
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self.gameover_buttons):
                    if btn.is_clicked(event.pos):
                        if i == 0:
                            self.reset_game()
                            self.state = 'playing'
                        elif i == 1:
                            self.state = 'menu'
                        elif i == 2:
                            return False
        return True

    def draw_gameover(self):
        self.screen.fill(BLACK)
        for star in self.stars:
            star.update()
            star.draw(self.screen)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        gameover_text = self.font_large.render('游戏结束', True, RED)
        go_rect = gameover_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(gameover_text, go_rect)

        score_text = self.font_medium.render(f'本局得分: {self.score}', True, WHITE)
        s_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 230))
        self.screen.blit(score_text, s_rect)

        is_new = self.score >= self.high_score and self.score > 0
        hs_color = YELLOW if is_new else GREEN
        hs_text = self.font_medium.render(f'历史最高: {self.high_score}', True, hs_color)
        hs_rect = hs_text.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(hs_text, hs_rect)

        if is_new:
            new_text = self.font_small.render('新纪录！', True, YELLOW)
            n_rect = new_text.get_rect(center=(SCREEN_WIDTH // 2, 320))
            self.screen.blit(new_text, n_rect)

        self.gameover_buttons = []
        btn_w, btn_h = 200, 50
        btn_x = SCREEN_WIDTH // 2 - btn_w // 2

        replay_btn = Button(btn_x, 380, btn_w, btn_h, '再来一局', GREEN, (100, 255, 100))
        self.gameover_buttons.append(replay_btn)

        menu_btn = Button(btn_x, 450, btn_w, btn_h, '返回菜单', BLUE, (100, 100, 255))
        self.gameover_buttons.append(menu_btn)

        exit_btn = Button(btn_x, 520, btn_w, btn_h, '退出游戏', RED, (255, 100, 100))
        self.gameover_buttons.append(exit_btn)

        for btn in self.gameover_buttons:
            btn.draw(self.screen, self.font_small)

    def run(self):
        running = True
        while running:
            events = pygame.event.get()

            if self.state == 'menu':
                running = self.update_menu(events)
                self.draw_menu()
            elif self.state == 'playing':
                running = self.update_playing(events)
                self.draw_playing()
            elif self.state == 'gameover':
                running = self.update_gameover(events)
                self.draw_gameover()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = Game()
    game.run()
