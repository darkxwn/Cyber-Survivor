import pygame
import math
import sys
from typing import List

from .config import FPS, screen, GameState, GameMode
from ..entities.player import Player
from ..entities.enemies import Enemy, EnemySpawner
from ..entities.bullets import BulletManager
from ..systems.particle_system import ParticleSystem
from ..systems.save_system import SaveSystem
from ..ui.hud import HUD


class Game:
    def __init__(self):
        self.state = GameState.MENU
        self.mode = GameMode.WAVES
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Игровые объекты
        self.player = None
        self.enemies: List[Enemy] = []
        self.enemy_spawner = EnemySpawner()
        self.bullets = BulletManager()
        self.particles = ParticleSystem()
        self.save_system = SaveSystem()
        self.hud = HUD()
        
        # Игровые переменные
        self.score = 0
        self.wave = 1
        self.play_time = 0
        self.last_time = pygame.time.get_ticks()
        
        # Настройки управления
        self.keys_pressed = set()
        self.auto_fire = self.save_system.data["settings"]["auto_fire"]
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
                
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAY:
                        self.state = GameState.PAUSE
                    elif self.state == GameState.PAUSE:
                        self.state = GameState.PLAY
                
                elif event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                    self.restart_game()
                
                elif event.key == pygame.K_TAB:
                    self.auto_fire = not self.auto_fire
                    self.save_system.data["settings"]["auto_fire"] = self.auto_fire
            
            elif event.type == pygame.KEYUP:
                if event.key in self.keys_pressed:
                    self.keys_pressed.remove(event.key)
        
        # Обработка движения игрока
        if self.state == GameState.PLAY:
            self.handle_player_movement()
    
    def handle_player_movement(self):
        if not self.player:
            return
            
        self.player.velocity.x = 0
        self.player.velocity.y = 0
        
        controls = self.save_system.data["controls"]
        
        keys = pygame.key.get_pressed()
        if keys[controls["up"]]:
            self.player.velocity.y -= self.player.speed
        if keys[controls["down"]]:
            self.player.velocity.y += self.player.speed
        if keys[controls["left"]]:
            self.player.velocity.x -= self.player.speed
        if keys[controls["right"]]:
            self.player.velocity.x += self.player.speed
        
        # Проверка дэша
        if pygame.K_SPACE in self.keys_pressed:
            mouse_pos = pygame.mouse.get_pos()
            mouse_world_pos = pygame.Vector2(mouse_pos[0], mouse_pos[1])
            direction = mouse_world_pos - pygame.Vector2(self.player.pos.x, self.player.pos.y)
            self.player.dash(direction)
    
    def update(self):
        current_time = pygame.time.get_ticks()
        dt = (current_time - self.last_time) / 1000.0  # Преобразуем в секунды
        self.last_time = current_time
        
        if self.state != GameState.PLAY:
            return
        
        self.play_time += dt
        
        # Обновляем игрока
        if self.player:
            self.player.update(dt)
            
            # Ограничиваем игрока пределами экрана
            self.player.pos.x = max(30, min(self.player.pos.x, 1000 - 30))
            self.player.pos.y = max(30, min(self.player.pos.y, 700 - 30))
        
        # Обновляем врагов
        for enemy in self.enemies[:]:
            if enemy.dead:
                self.enemies.remove(enemy)
                continue
            
            # Обновляем врага и проверяем на столкновение с игроком
            damage = enemy.update(dt, self.player.pos if self.player else pygame.Vector2(0, 0))
            if damage > 0 and self.player:
                if self.player.take_damage(damage):
                    self.state = GameState.GAME_OVER
        
        # Обновляем пули
        self.bullets.update(dt)
        
        # Обновляем частицы
        self.particles.update(dt)
        
        # Обновляем спавнер врагов
        self.enemy_spawner.update(dt, self.enemies)
        
        # Проверяем столкновения пуль с врагами
        scores = self.bullets.check_collisions(self.enemies)
        for score in scores:
            self.score += score
        
        # Авто-огонь если включен
        if self.auto_fire and self.player:
            self.handle_auto_fire(dt)
    
    def handle_auto_fire(self, dt: float):
        if not self.player or self.player.last_shot >= self.player.fire_rate:
            mouse_pos = pygame.mouse.get_pos()
            direction = pygame.Vector2(mouse_pos[0], mouse_pos[1]) - self.player.pos
            if direction.length() > 0:
                # Вычисляем базовое направление
                direction = direction.normalize()
                
                # Определяем параметры выстрела
                damage = self.player.dmg
                if random.random() < self.player.crit_chance:
                    damage = int(damage * self.player.crit_multiplier)
                
                # Выстрел с учетом мультивыстрела
                self.bullets.multi_shoot(
                    self.player.pos,
                    direction,
                    damage,
                    count=self.player.multishot,
                    spread=0.2,
                    speed=self.player.bullet_speed,
                    lifetime=self.player.bullet_lifetime,
                    size=self.player.bullet_size,
                    piercing=self.player.piercing
                )
                
                # Восстановление после выстрела
                self.player.last_shot = 0
                
                # Эффекты от выстрела
                if self.player.lifesteal > 0 and self.player.hp < self.player.max_hp:
                    self.player.heal(self.player.dmg * self.player.lifesteal)
        else:
            self.player.last_shot += 1000 * dt  # прибавляем миллисекунды
    
    def render(self):
        # Заливка фона
        screen.fill((8, 10, 20))
        
        # Смещение для камеры (в данном случае не используется, но может быть реализовано)
        offset = pygame.Vector2(0, 0)
        
        # Рендерим врагов
        for enemy in self.enemies:
            enemy.draw(screen, offset)
        
        # Рендерим пули
        self.bullets.draw(screen, offset)
        
        # Рендерим игрока
        if self.player:
            self.player.draw(screen, offset)
        
        # Рендерим частицы
        self.particles.draw(screen, offset)
        
        # Рендерим HUD
        self.hud.draw(screen, self.player, self.enemies, self.state, self.score, self.wave, 0)
        
        pygame.display.flip()
    
    def start_new_game(self, mode: GameMode = GameMode.WAVES):
        self.mode = mode
        self.state = GameState.PLAY
        self.score = 0
        self.wave = 1
        self.play_time = 0
        self.enemies.clear()
        self.bullets.bullets.clear()
        
        # Создаем нового игрока с сохраненными модулями и скином
        modules = self.save_system.data["modules"]
        skin_id = self.save_system.data["current_skin"]
        self.player = Player(modules, skin_id)
    
    def restart_game(self):
        self.start_new_game(self.mode)
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        # Сохраняем перед выходом
        self.save_system.update_stats(
            kills=0,  # Количество убитых врагов за последнюю сессию
            playtime=self.play_time,
            score=self.score,
            level=self.player.level if self.player else 0,
            wave=self.wave,
            count_stats=(self.mode == GameMode.WAVES)
        )
        
        pygame.quit()
        sys.exit()


# Необходимо импортировать random для работы с вероятностями
import random