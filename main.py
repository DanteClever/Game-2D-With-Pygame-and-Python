import pygame
import os
import sys
import random
import pickle
from pygame import mixer

# Initialize pygame
pygame.init()
mixer.init()

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Black Gun")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
ORANGE = (255, 165, 0)

# Game variables
clock = pygame.time.Clock()
FPS = 60
GRAVITY = 0.8
GROUND_HEIGHT = SCREEN_HEIGHT - 50
ATTACK_RANGE = 50

# Game states
MENU = 0
PLAYING = 1
PAUSED = 2
GAME_OVER = 3
OPTIONS = 4
HOW_TO_PLAY = 5
SHOP = 6

# Current game state
game_state = MENU

# Fonts
try:
    title_font = pygame.font.SysFont("Arial", 64, bold=True)
    menu_font = pygame.font.SysFont("Arial", 36)
    button_font = pygame.font.SysFont("Arial", 28)
except:
    title_font = pygame.font.Font(None, 64)
    menu_font = pygame.font.Font(None, 36)
    button_font = pygame.font.Font(None, 28)

# Audio variables
menu_music_playing = False
game_music_playing = False
button_hover_sound = None
button_click_sound = None
attack_sound = None
enemy_death_sound = None
jump_sound = None

# Load sounds
try:
    mixer.music.load("assets/sounds/labby/ok.mp3")
except:
    print("Error loading menu music")

try:
    button_hover_sound = mixer.Sound("assets/sounds/menu/button/click.mp3")
    button_click_sound = mixer.Sound("assets/sounds/menu/button/click.mp3")
except:
    print("Error loading button sounds")

try:
    attack_sound = mixer.Sound("assets/sounds/attack.wav")
    enemy_death_sound = mixer.Sound("assets/sounds/enemy_death.wav") 
    jump_sound = mixer.Sound("assets/sounds/jump.wav")
except:
    print("Error loading game sounds")

# Improved image loading function
def load_image(path, scale=1):
    try:
        image = pygame.image.load(path).convert_alpha()
        if scale != 1:
            width = int(image.get_width() * scale)
            height = int(image.get_height() * scale)
            image = pygame.transform.scale(image, (width, height))
        return image
    except Exception as e:
        print(f"Error loading image {path}: {e}")
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        color = RED if "enemy" in path.lower() else BLUE
        pygame.draw.rect(surf, color, (0, 0, 50, 50))
        return surf

# Load all animation frames from a folder
def load_animation_frames(folder_path, scale=1):
    frames = []
    try:
        files = sorted([f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))],
                      key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))
        
        for filename in files:
            frame = load_image(os.path.join(folder_path, filename), scale)
            frames.append(frame)
    except Exception as e:
        print(f"Error loading animation frames from {folder_path}: {e}")
        frames = [
            pygame.Surface((50, 50), pygame.SRCALPHA),
            pygame.Surface((50, 50), pygame.SRCALPHA)
        ]
    
    return frames

# Button class for menu
class Button:
    def __init__(self, x, y, width, height, text, color=LIGHT_GRAY, hover_color=WHITE, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.was_hovered = False
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)
        
        text_surface = button_font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def check_hover(self, pos):
        self.was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(pos)
        
        if self.is_hovered and not self.was_hovered:
            try:
                button_hover_sound.play()
            except:
                pass
                
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(pos):
                try:
                    button_click_sound.play()
                except:
                    pass
                return True
        return False

# Money System
class MoneySystem:
    def __init__(self):
        self.money = 20000
        self.kill_reward = 10
        self.level_up_bonus = 50
        self.coin_image = None
        
        try:
            self.coin_image = load_image("assets/menu/HUD/MONEY PANEL/Money Icon.png", 3)
        except:
            print("Error loading Money Image offfff")
        
    def add_money(self, amount):
        self.money += amount
        
    def spend_money(self, amount):
        if self.money >= amount:
            self.money -= amount
            return True
        return False
        
    def enemy_killed(self):
        self.add_money(self.kill_reward)
        
    def level_up(self):
        self.add_money(self.level_up_bonus)
        
    def draw(self, surface):
        if self.coin_image:
            coin_rect = self.coin_image.get_rect()
            coin_rect.x = SCREEN_WIDTH - 200
            coin_rect.y = 70
            surface.blit(self.coin_image, coin_rect)
            money_text = menu_font.render(f": ${self.money}", True, YELLOW)
            surface.blit(money_text, (SCREEN_WIDTH - 170, 70))
        else:
            money_text = menu_font.render(f"Money: ${self.money}", True, YELLOW)
            surface.blit(money_text, (SCREEN_WIDTH - 200, 70))

# Weapon Class
class Weapon:
    def __init__(self, name, damage, price, image_path):
        self.name = name
        self.damage = damage
        self.price = price
        self.image = load_image(image_path, 2) if image_path else None
        self.owned = 0
        
    def draw(self, surface, x, y):
        if self.image:
            surface.blit(self.image, (x, y))
        
        text = button_font.render(f"{self.name} (DMG: {self.damage})", True, WHITE)
        surface.blit(text, (x + 60, y + 10))
        
        price_text = button_font.render(f"${self.price}", True, YELLOW)
        surface.blit(price_text, (x + 60, y + 40))
        
        owned_text = button_font.render(f"Owned: {self.owned}", True, GREEN)
        surface.blit(owned_text, (x + 60, y + 70))

# Shop System
class ShopSystem:
    def __init__(self):
        self.weapons = [
            Weapon("Wooden Gun", 0, 50, "assets/menu/HUD/WEAPON ICONS/MG HUD.png"),
            Weapon("Pistol", 20, 100, "assets/menu/HUD/WEAPON ICONS/Pistol HUD.png"),
            Weapon("Shotgun", 30, 200, "assets/menu/HUD/WEAPON ICONS/Flamethrower HUD.png"),
            Weapon("Rifle", 40, 350, "assets/menu/HUD/WEAPON ICONS/RPG HUD.png")
        ]
        
    def buy_weapon(self, index, player, money_system):
        weapon = self.weapons[index]
        if money_system.spend_money(weapon.price):
            weapon.owned += 1
            player.attack_power = weapon.damage
            return True
        return False
        
    def sell_weapon(self, index, money_system):
        weapon = self.weapons[index]
        if weapon.owned > 0:
            weapon.owned -= 1
            money_system.add_money(weapon.price // 2)
            return True
        return False
        
    def draw(self, surface, money_system):
        # Semi-transparent background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        surface.blit(s, (0, 0))
        
        # Shop title
        title = title_font.render("WEAPON SHOP", True, YELLOW)
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Current money
        money_text = menu_font.render(f"Your Money: ${money_system.money}", True, WHITE)
        surface.blit(money_text, (SCREEN_WIDTH//2 - money_text.get_width()//2, 120))
        
        # Weapons list
        for i, weapon in enumerate(self.weapons):
            y_pos = 180 + i * 120
            weapon.draw(surface, SCREEN_WIDTH//2 - 150, y_pos)
            
            # Buy button
            buy_btn = Button(SCREEN_WIDTH//2 + 100, y_pos + 20, 80, 30, "Buy", GREEN)
            buy_btn.draw(surface)
            
            # Sell button
            sell_btn = Button(SCREEN_WIDTH//2 + 100, y_pos + 60, 80, 30, "Sell", RED)
            sell_btn.draw(surface)
        
        # Exit button
        exit_btn = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 80, 200, 50, "Exit Shop")
        exit_btn.draw(surface)
        
        return exit_btn

# Level System
class LevelSystem:
    def __init__(self):
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = 100
        self.total_kills = 0
        
    def add_xp(self, amount):
        self.xp += amount
        self.total_kills += 1
        if self.xp >= self.xp_to_next_level and self.level < 100:
            self.level += 1
            self.xp -= self.xp_to_next_level
            self.xp_to_next_level = int(self.xp_to_next_level * 1.2)
            return True
        return False
    
    def draw(self, surface):
        xp_bar_width = 200
        xp_bar_height = 20
        xp_bar_x = SCREEN_WIDTH - xp_bar_width - 10
        xp_bar_y = 10
        
        pygame.draw.rect(surface, (50, 50, 50), (xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height))
        xp_progress = (self.xp / self.xp_to_next_level) * xp_bar_width
        pygame.draw.rect(surface, YELLOW, (xp_bar_x, xp_bar_y, xp_progress, xp_bar_height))
        
        font = pygame.font.SysFont(None, 30)
        level_text = font.render(f"Level: {self.level}", True, WHITE)
        xp_text = font.render(f"XP: {self.xp}/{self.xp_to_next_level}", True, WHITE)
        kills_text = font.render(f"Kills: {self.total_kills}", True, WHITE)
        
        surface.blit(level_text, (10, 10))
        surface.blit(xp_text, (10, 40))
        surface.blit(kills_text, (10, 70))

# Load background
try:
    background = pygame.image.load("assets/mohit/city 1/10.png").convert()
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
except:
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background.fill((100, 100, 100))

# Menu background
try:
    menu_bg = pygame.image.load("assets/mohit/city 1/10.png").convert()
    menu_bg = pygame.transform.scale(menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
except:
    menu_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    menu_bg.fill((50, 50, 100))

# Menu movement variables
menu_bg_width = menu_bg.get_width()
menu_bg_x = 0
menu_scroll_speed = 1

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.idle_frames = load_animation_frames("assets/player/idle", 2)
        self.run_frames = load_animation_frames("assets/player/walk", 2)
        self.attack_frames = load_animation_frames("assets/player/attack", 2)
        
        self.current_frames = self.idle_frames
        self.current_frame = 0
        self.image = self.current_frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 5
        self.animation_speed = 0.15
        self.animation_time = 0
        self.attack_cooldown = 0
        self.is_running = False
        self.is_attacking = False
        self.facing_right = True
        self.velocity_y = 0
        self.on_ground = False
        self.health = 100
        self.max_health = 100
        self.attack_power = 10
        self.melee_attack_cooldown = 0
        self.current_weapon = None
        self.weapons = []
        
    def add_weapon(self, weapon):
        if weapon not in self.weapons:
            self.weapons.append(weapon)
        self.current_weapon = weapon
        self.attack_power = weapon.damage
        
    def update(self):
        dx = 0
        dy = 0
        self.is_running = False
        
        self.velocity_y += GRAVITY
        dy += self.velocity_y
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = self.speed
            self.is_running = True
            self.facing_right = True
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -self.speed
            self.is_running = True
            self.facing_right = False
        
        self.rect.x += dx
        self.rect.y += dy
        
        if self.rect.bottom > GROUND_HEIGHT:
            self.rect.bottom = GROUND_HEIGHT
            self.velocity_y = 0
            self.on_ground = True
        else:
            self.on_ground = False
        
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            
        self.animation_time += self.animation_speed
        if self.animation_time >= 1:
            if self.is_attacking:
                self.current_frames = self.attack_frames
                if self.current_frame >= len(self.attack_frames) - 1:
                    self.is_attacking = False
            elif self.is_running:
                self.current_frames = self.run_frames
            else:
                self.current_frames = self.idle_frames
            
            self.current_frame = (self.current_frame + 1) % len(self.current_frames)
            self.image = self.current_frames[self.current_frame]
            
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)
            
            self.animation_time = 0
            
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        if self.melee_attack_cooldown > 0:
            self.melee_attack_cooldown -= 1
    
    def ranged_attack(self):
        if self.attack_cooldown == 0 and not self.is_attacking:
            try:
                attack_sound.play()
            except:
                pass
            self.attack_cooldown = 30
            self.is_attacking = True
            self.current_frame = 0
            return True
        return False
        
    def melee_attack(self):
        if self.melee_attack_cooldown == 0:
            try:
                attack_sound.play()
            except:
                pass
            self.melee_attack_cooldown = 20
            self.is_attacking = True
            self.current_frame = 0
            
            for enemy in enemies:
                if not enemy.is_dead and abs(self.rect.x - enemy.rect.x) < ATTACK_RANGE:
                    if enemy.take_damage(self.attack_power * 1.5):
                        if level_system.add_xp(10):
                            player.attack_power += 2
            return True
        return False

    def jump(self):
        if self.on_ground:
            try:
                jump_sound.play()
            except:
                pass
            self.velocity_y = -15
    
    def draw_health(self, surface):
        health_bar_width = 100
        health_bar_height = 10
        health_bar_x = self.rect.x
        health_bar_y = self.rect.y - 15
        
        pygame.draw.rect(surface, (255, 0, 0), (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        health_progress = (self.health / self.max_health) * health_bar_width
        pygame.draw.rect(surface, (0, 255, 0), (health_bar_x, health_bar_y, health_progress, health_bar_height))

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.idle_frames = load_animation_frames("assets/enemy/run", 2)
        self.run_frames = load_animation_frames("assets/enemy/idle", 2)
        self.death_frames = load_animation_frames("assets/enemy/dead", 2)
        self.attack_frames = load_animation_frames("assets/enemy/attack", 2)
        
        self.current_frames = self.idle_frames
        self.current_frame = 0
        self.image = self.current_frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = random.randint(1, 3)
        self.animation_speed = 0.1
        self.animation_time = 0
        self.health = 30
        self.max_health = 30
        self.is_dead = False
        self.death_timer = 42
        self.facing_right = False
        self.attack_cooldown = 0
        self.attack_power = 5
        
    def update(self):
        if self.is_dead:
            self.death_timer -= 1
            if self.death_timer <= 0:
                self.kill()
            
            self.animation_time += self.animation_speed
            if self.animation_time >= 1:
                self.current_frame = (self.current_frame + 1) % len(self.current_frames)
                if self.current_frame >= len(self.current_frames) - 1:
                    self.current_frame = len(self.current_frames) - 1
                self.image = self.current_frames[self.current_frame]
                self.animation_time = 0
        else:
            dx = self.speed if self.rect.x < player.rect.x else -self.speed
            self.facing_right = dx > 0
            
            if abs(self.rect.x - player.rect.x) < ATTACK_RANGE and self.attack_cooldown == 0:
                self.attack()
            else:
                self.rect.x += dx
            
            self.animation_time += self.animation_speed
            if self.animation_time >= 1:
                self.current_frame = (self.current_frame + 1) % len(self.current_frames)
                self.image = self.current_frames[self.current_frame]
                
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image, True, False)
                
                self.animation_time = 0
            
            if self.attack_cooldown > 0:
                self.attack_cooldown -= 1
    
    def attack(self):
        self.attack_cooldown = 60
        self.current_frames = self.attack_frames
        self.current_frame = 0
        
        if abs(self.rect.x - player.rect.x) < ATTACK_RANGE:
            player.health -= self.attack_power
    
    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0 and not self.is_dead:
            money_system.enemy_killed()
            try:
                enemy_death_sound.play()
            except:
                pass
            self.is_dead = True
            self.current_frames = self.death_frames
            self.current_frame = 0
            return True
        return False
    
    def draw_health(self, surface):
        if not self.is_dead:
            health_bar_width = 50
            health_bar_height = 5
            health_bar_x = self.rect.x
            health_bar_y = self.rect.y - 10
            
            pygame.draw.rect(surface, (255, 0, 0), (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
            health_progress = (self.health / self.max_health) * health_bar_width
            pygame.draw.rect(surface, (0, 255, 0), (health_bar_x, health_bar_y, health_progress, health_bar_height))

# Attack class
class Attack(pygame.sprite.Sprite):
    def __init__(self, x, y, facing_right, is_player=True):
        super().__init__()
        self.image = pygame.Surface((30, 10), pygame.SRCALPHA)
        if is_player:
            self.image.fill((0, 255, 0, 200))
        else:
            self.image.fill((255, 0, 0, 200))
        
        self.rect = self.image.get_rect()
        if facing_right:
            self.rect.left = x
        else:
            self.rect.right = x
        self.rect.centery = y
        self.speed = 10
        self.facing_right = facing_right
        self.is_player = is_player
        self.damage = 10 if is_player else 5
        
    def update(self):
        if self.facing_right:
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed
        
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

# Ground class
class Ground(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH, 50))
        self.image.fill((100, 70, 30))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = GROUND_HEIGHT

# Enemy spawner system
class EnemySpawner:
    def __init__(self, max_enemies=5):
        self.max_enemies = max_enemies
        self.spawn_timer = 0
        self.spawn_interval = 400
        
    def update(self):
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval and len(enemies) < self.max_enemies:
            self.spawn_timer = 0
            self.spawn_enemy()
    
    def spawn_enemy(self):
        side = random.choice(["left", "right"])
        if side == "left":
            x = -50
        else:
            x = SCREEN_WIDTH + 50
        
        y = GROUND_HEIGHT - random.randint(150,151)
        enemy = Enemy(x, y)
        all_sprites.add(enemy)
        enemies.add(enemy)

# Ally system
class AllySystem:
    def __init__(self):
        self.allies = pygame.sprite.Group()
        self.convert_timer = 0
        
    def try_convert_enemy(self, enemy):
        if random.random() < 0.3:
            enemy.kill()
            ally = Ally(enemy.rect.x, enemy.rect.y)
            self.allies.add(ally)
            all_sprites.add(ally)
            return True
        return False
    
    def update(self):
        self.convert_timer += 1

# Ally class
class Ally(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.idle_frames = load_animation_frames("assets/enemy/run", 2)
        self.run_frames = load_animation_frames("assets/enemy/idle", 2)
        self.attack_frames = load_animation_frames("assets/enemy/attack", 2)
        
        self.current_frames = self.idle_frames
        self.current_frame = 0
        self.image = self.current_frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 3
        self.animation_speed = 0.1
        self.animation_time = 0
        self.health = 50
        self.max_health = 50
        self.attack_cooldown = 0
        self.target = None
        self.facing_right = True
        
    def update(self):
        closest_enemy = None
        min_distance = float('inf')
        
        for enemy in enemies:
            if not enemy.is_dead:
                distance = abs(self.rect.x - enemy.rect.x)
                if distance < min_distance:
                    min_distance = distance
                    closest_enemy = enemy
        
        if closest_enemy:
            self.target = closest_enemy
            if self.rect.x < closest_enemy.rect.x:
                self.rect.x += self.speed
                self.facing_right = True
            elif self.rect.x > closest_enemy.rect.x:
                self.rect.x -= self.speed
                self.facing_right = False
            
            if abs(self.rect.x - closest_enemy.rect.x) < ATTACK_RANGE and self.attack_cooldown == 0:
                self.attack()
        
        self.animation_time += self.animation_speed
        if self.animation_time >= 1:
            self.current_frame = (self.current_frame + 1) % len(self.current_frames)
            self.image = self.current_frames[self.current_frame]
            
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)
            
            self.animation_time = 0
        
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
    
    def attack(self):
        self.attack_cooldown = 60
        self.current_frames = self.attack_frames
        self.current_frame = 0
        
        if self.target and abs(self.rect.x - self.target.rect.x) < ATTACK_RANGE:
            if self.target.take_damage(5):
                if level_system.add_xp(5):
                    player.attack_power += 1

# Menu functions
def draw_menu():
    global menu_bg_x
    # Draw scrolling background
    menu_bg_x = (menu_bg_x - menu_scroll_speed) % menu_bg_width
    screen.blit(menu_bg, (menu_bg_x - menu_bg_width, 0))
    screen.blit(menu_bg, (menu_bg_x, 0))
    
    # Game title
    title_text = title_font.render("Black Gun", True, YELLOW)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    screen.blit(title_text, title_rect)
    
    # Menu buttons
    play_button.draw(screen)
    options_button.draw(screen)
    how_to_play_button.draw(screen)
    shop_button.draw(screen)
    quit_button.draw(screen)

def draw_pause_menu():
    # Semi-transparent background
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    s.fill((0, 0, 0, 150))
    screen.blit(s, (0, 0))
    
    # Pause title
    title_text = title_font.render("PAUSED", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    screen.blit(title_text, title_rect)
    
    # Pause buttons
    resume_button.draw(screen)
    menu_button.draw(screen)

def draw_options_menu():
    screen.blit(menu_bg, (0, 0))
    
    title_text = title_font.render("OPTIONS", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    screen.blit(title_text, title_rect)
    
    back_button.draw(screen)
    
    volume_text = menu_font.render("Volume: ", True, WHITE)
    screen.blit(volume_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2))

def draw_how_to_play():
    screen.blit(menu_bg, (0, 0))
    
    title_text = title_font.render("HOW TO PLAY", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//6))
    screen.blit(title_text, title_rect)
    
    instructions = [
        "Movement: A/D or Left/Right Arrow Keys"
    ]
    
    for i, line in enumerate(instructions):
        text = menu_font.render(line, True, WHITE)
        screen.blit(text, (SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//3 + i * 40))
    
    back_button.draw(screen)

def draw_game_over():
    screen.blit(menu_bg, (0, 0))
    
    title_text = title_font.render("GAME OVER", True, RED)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    screen.blit(title_text, title_rect)
    
    stats_text = [
        f"Level Reached: {level_system.level}",
        f"Total Kills: {level_system.total_kills}",
        f"Total XP: {level_system.xp}"
    ]
    
    for i, line in enumerate(stats_text):
        text = menu_font.render(line, True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + i * 40))
        screen.blit(text, text_rect)
    
    menu_button.draw(screen)
    quit_button.draw(screen)

# Create sprite groups
all_sprites = pygame.sprite.Group()
ground_group = pygame.sprite.Group()
enemies = pygame.sprite.Group()
attacks = pygame.sprite.Group()

# Create ground
ground = Ground()
ground_group.add(ground)
all_sprites.add(ground)

# Create player
player = Player(50, GROUND_HEIGHT - 100)
all_sprites.add(player)

# Initialize game systems
money_system = MoneySystem()
level_system = LevelSystem()
enemy_spawner = EnemySpawner(max_enemies=4)
ally_system = AllySystem()
shop_system = ShopSystem()

# Menu buttons
play_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 60, 200, 50, "Play")
options_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50, "Options")
how_to_play_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 60, 200, 50, "How to Play")
shop_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 120, 200, 50, "Shop")
quit_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 180, 200, 50, "Quit")

# Pause menu buttons
resume_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 30, 200, 50, "Resume")
menu_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 30, 200, 50, "Main Menu")

# Back button
back_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 100, 200, 50, "Back")

# Save/Load System
class SaveSystem:
    def __init__(self):
        self.save_file = "game_save.dat"
        
    def save_game(self, player, money_system, level_system):
        try:
            with open(self.save_file, 'r') as f:
                pickle.dump({
                    'player_health': player.health,
                    'player_x': player.rect.x,
                    'player_y': player.rect.y,
                    'money': money_system.money,
                    'level': level_system.level,
                    'xp': level_system.xp,
                    'xp_to_next': level_system.xp_to_next_level,
                    'kills': level_system.total_kills,
                    'weapons': [(w.name, w.owned) for w in shop_system.weapons],
                    'attack_power': player.attack_power
                }, f)
            return True
        except:
            return False
            
    def load_game(self):
        try:
            with open(self.save_file, 'rb') as f:
                data = pickle.load(f)
                return data
        except:
            return None

save_system = SaveSystem()

# Enhanced Weapon System
class EnhancedWeapon(Weapon):
    def __init__(self, name, damage, price, image_path, attack_frames=None):
        super().__init__(name, damage, price, image_path)
        self.attack_frames = attack_frames
        self.current_attack_frame = 0
        self.attacking = False
        
    def draw_attack(self, surface, x, y, facing_right):
        if self.attacking and self.attack_frames:
            frame = self.attack_frames[self.current_attack_frame]
            if not facing_right:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, (x, y))
            self.current_attack_frame = (self.current_attack_frame + 1) % len(self.attack_frames)
            if self.current_attack_frame == 0:
                self.attacking = False

# Enhanced Shop System
class EnhancedShopSystem(ShopSystem):
    def __init__(self):
        super().__init__()
        # Load weapon attack animations
        self.weapons = [
            EnhancedWeapon("Wooden Gun", 10, 50, 
                          "assets/menu/HUD/WEAPON ICONS/Pistol HUD.png",
                          load_animation_frames("C:/Users/dani/Desktop/Game Wars/assets/PNG/Explosion/0.png", 2)),
            EnhancedWeapon("Pistol", 20, 100, 
                          "assets/menu/HUD/WEAPON ICONS/RPG HUD.png",
                          load_animation_frames("assets/PNG/Nuclear_explosion/0.png", 2)),
            EnhancedWeapon("Shotgun", 30, 200, 
                          "assets/menu/HUD/WEAPON ICONS/MG HUD.png",
                          load_animation_frames("assets/PNG/Nuclear_explosion/0.png", 2)),
            EnhancedWeapon("Rifle", 40, 350, 
                          "assets/menu/HUD/WEAPON ICONS/Flamethrower HUD.png",
                          load_animation_frames("assets/PNG/Nuclear_explosion/0.png", 2))
        ]
        
    def draw(self, surface, money_system):
        # Semi-transparent background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        surface.blit(s, (0, 0))
        
        # Shop title
        title = title_font.render("WEAPON SHOP", True, YELLOW)
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Current money
        money_text = menu_font.render(f"Your Money: ${money_system.money}", True, WHITE)
        surface.blit(money_text, (SCREEN_WIDTH//2 - money_text.get_width()//2, 120))
        
        # Weapons list
        for i, weapon in enumerate(self.weapons):
            y_pos = 180 + i * 120
            weapon.draw(surface, SCREEN_WIDTH//2 - 150, y_pos)
            
            # Buy button
            buy_btn = Button(SCREEN_WIDTH//2 + 100, y_pos + 20, 80, 30, "Buy", GREEN)
            buy_btn.draw(surface)
            
            # Sell button
            sell_btn = Button(SCREEN_WIDTH//2 + 100, y_pos + 60, 80, 30, "Sell", RED)
            sell_btn.draw(surface)
        
        # Exit button
        exit_btn = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 80, 200, 50, "Exit Shop")
        exit_btn.draw(surface)
        
        return exit_btn

# Enhanced Player Class
class EnhancedPlayer(Player):
    def ranged_attack(self):
        if self.attack_cooldown == 0 and not self.is_attacking and self.current_weapon:
            try:
                attack_sound.play()
            except:
                pass
            self.attack_cooldown = 30
            self.is_attacking = True
            self.current_frame = 0
            self.current_weapon.attacking = True
            
            # Create projectile based on weapon type
            if isinstance(self.current_weapon, EnhancedWeapon):
                attack = EnhancedAttack(
                    self.rect.right if self.facing_right else self.rect.left,
                    self.rect.centery,
                    self.facing_right,
                    damage=self.current_weapon.damage,
                    speed=15,
                    size=(30, 10),
                    color=YELLOW
                )
                all_sprites.add(attack)
                attacks.add(attack)
                return True
        return False

# Enhanced Attack Class
class EnhancedAttack(Attack):
    def __init__(self, x, y, facing_right, damage=10, speed=10, size=(30, 10), color=GREEN):
        super().__init__(x, y, facing_right)
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect()
        if facing_right:
            self.rect.left = x
        else:
            self.rect.right = x
        self.rect.centery = y
        self.speed = speed
        self.facing_right = facing_right
        self.damage = damage

# Initialize enhanced systems
shop_system = EnhancedShopSystem()
player = EnhancedPlayer(50, GROUND_HEIGHT - 100)
all_sprites.add(player)

# Main game loop
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    # Update menu background position
    if game_state == MENU:
        menu_bg_x -= menu_scroll_speed
        if menu_bg_x <= -menu_bg_width:
            menu_bg_x = 0
    
    # Handle music based on game state
    if game_state == MENU and not menu_music_playing:
        try:
            mixer.music.stop()
            mixer.music.load("assets/sounds/menu/button/click.mp3")
            mixer.music.play(-1)
            menu_music_playing = True
            game_music_playing = False
        except:
            menu_music_playing = False

    elif game_state == PLAYING and not game_music_playing:
        try:
            mixer.music.stop()
            mixer.music.load("assets/sounds/game_music.mp3")
            mixer.music.play(-1)
            game_music_playing = True
            menu_music_playing = False
        except:
            game_music_playing = False
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Menu state
        if game_state == MENU:
            play_button.check_hover(mouse_pos)
            options_button.check_hover(mouse_pos)
            how_to_play_button.check_hover(mouse_pos)
            shop_button.check_hover(mouse_pos)
            quit_button.check_hover(mouse_pos)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button.is_clicked(mouse_pos, event):
                    game_state = PLAYING
                    # Reset game
                    player.health = player.max_health
                    level_system = LevelSystem()
                    money_system = MoneySystem()
                    for enemy in enemies:
                        enemy.kill()
                    for attack in attacks:
                        attack.kill()
                    player.rect.x = 50
                    player.rect.y = GROUND_HEIGHT - 100
                elif options_button.is_clicked(mouse_pos, event):
                    game_state = OPTIONS
                elif how_to_play_button.is_clicked(mouse_pos, event):
                    game_state = HOW_TO_PLAY
                elif shop_button.is_clicked(mouse_pos, event):
                    game_state = SHOP
                elif quit_button.is_clicked(mouse_pos, event):
                    running = False
        
        # Shop state
        elif game_state == SHOP:
            exit_btn = shop_system.draw(screen, money_system)
            exit_btn.check_hover(mouse_pos)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check weapon buy/sell buttons
                for i, weapon in enumerate(shop_system.weapons):
                    buy_btn_rect = pygame.Rect(SCREEN_WIDTH//2 + 100, 180 + i * 120 + 20, 80, 30)
                    sell_btn_rect = pygame.Rect(SCREEN_WIDTH//2 + 100, 180 + i * 120 + 60, 80, 30)
                    
                    if buy_btn_rect.collidepoint(mouse_pos):
                        shop_system.buy_weapon(i, player, money_system)
                    elif sell_btn_rect.collidepoint(mouse_pos):
                        shop_system.sell_weapon(i, money_system)
                
                if exit_btn.is_clicked(mouse_pos, event):
                    game_state = MENU
        
        # Playing state
        elif game_state == PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()
                elif event.key == pygame.K_ESCAPE:
                    game_state = PAUSED
                elif event.key == pygame.K_h:
                    for enemy in enemies:
                        if not enemy.is_dead and abs(player.rect.x - enemy.rect.x) < ATTACK_RANGE:
                            if ally_system.try_convert_enemy(enemy):
                                break
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click for melee
                    player.melee_attack()
                elif event.button == 3:  # Right click for ranged
                    player.ranged_attack()
        
        # Paused state
        elif game_state == PAUSED:
            resume_button.check_hover(mouse_pos)
            menu_button.check_hover(mouse_pos)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if resume_button.is_clicked(mouse_pos, event):
                    game_state = PLAYING
                elif menu_button.is_clicked(mouse_pos, event):
                    game_state = MENU
        
        # Options state
        elif game_state == OPTIONS:
            back_button.check_hover(mouse_pos)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.is_clicked(mouse_pos, event):
                    game_state = MENU
        
        # How to Play state
        elif game_state == HOW_TO_PLAY:
            back_button.check_hover(mouse_pos)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.is_clicked(mouse_pos, event):
                    game_state = MENU
        
        # Game Over state
        elif game_state == GAME_OVER:
            menu_button.check_hover(mouse_pos)
            quit_button.check_hover(mouse_pos)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_button.is_clicked(mouse_pos, event):
                    game_state = MENU
                elif quit_button.is_clicked(mouse_pos, event):
                    running = False
    
    # Update game state
    if game_state == PLAYING:
        # Update all game objects
        all_sprites.update()
        enemy_spawner.update()
        ally_system.update()
        
        # Check for collisions
        hits = pygame.sprite.groupcollide(attacks, enemies, True, False)
        for attack, enemies_hit in hits.items():
            for enemy in enemies_hit:
                if not enemy.is_dead and enemy.take_damage(attack.damage):
                    if level_system.add_xp(10):
                        money_system.level_up()
        
        # Check player health
        if player.health <= 0:
            game_state = GAME_OVER
    
    # Drawing
    screen.fill(BLACK)
    
    if game_state == MENU:
        draw_menu()
    elif game_state == PLAYING:
        # Draw background
        screen.blit(background, (0, 0))
        
        # Draw all sprites
        all_sprites.draw(screen)
        
        # Draw HUD
        player.draw_health(screen)
        level_system.draw(screen)
        money_system.draw(screen)
        
        # Draw enemy health bars
        for enemy in enemies:
            enemy.draw_health(screen)
    
    elif game_state == PAUSED:
        # Draw game behind pause menu
        screen.blit(background, (0, 0))
        all_sprites.draw(screen)
        draw_pause_menu()
    
    elif game_state == OPTIONS:
        draw_options_menu()
    
    elif game_state == HOW_TO_PLAY:
        draw_how_to_play()
    
    elif game_state == SHOP:
        # Draw game behind shop
        screen.blit(background, (0, 0))
        all_sprites.draw(screen)
        shop_system.draw(screen, money_system)
    
    elif game_state == GAME_OVER:
        draw_game_over()
    
    # Save game periodically
    if game_state == PLAYING and pygame.time.get_ticks() % 10000 == 0:  # Every 30 seconds
        save_system.save_game(player, money_system, level_system)
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
