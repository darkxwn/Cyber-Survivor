import pygame
import random
import math
from typing import List, Tuple
from .base_entity import GameObject

class Enemy(GameObject):
    def __init__(self, pos: pygame.Vector2, enemy_type: str = "basic"):
        super().__init__(pos)
        self.type = enemy_type
        self.size = 20
        self.speed = 2.0
        self.health = 10
        self.max_health = 10
        self.damage = 5
        self.color = (255, 46, 99)
        self.glow_color = (200, 30, 80)
        self.velocity = pygame.Vector2(0, 0)
        
        # Типы врагов
        if enemy_type == "basic":
            self.health = 10
            self.max_health = 10
            self.damage = 5
            self.speed = 2.0
            self.color = (255, 46, 99)
            self.score_value = 10
        elif enemy_type == "fast":
            self.health = 5
            self.max_health = 5
            self.damage = 3
            self.speed = 4.0
            self.color = (255, 100, 100)
            self.score_value = 15
        elif enemy_type == "tank":
            self.health = 30
            self.max_health = 30
            self.damage = 10
            self.speed = 1.0
            self.color = (200, 50, 50)
            self.score_value = 25
        elif enemy_type == "elite":
            self.health = 25
            self.max_health = 25
            self.damage = 8
            self.speed = 2.5
            self.color = (255, 140, 0)
            self.glow_color = (200, 100, 0)
            self.score_value = 40
        elif enemy_type == "boss":
            self.health = 100
            self.max_health = 100
            self.damage = 15
            self.speed = 1.2
            self.size = 40
            self.color = (150, 0, 255)
            self.glow_color = (100, 0, 200)
            self.score_value = 100
        
        self.max_speed = self.speed
        self.rotation = 0
        self.rotation_speed = random.uniform(-2, 2)
        self.wave_offset = random.uniform(0, 2 * math.pi)
        self.wave_frequency = random.uniform(0.02, 0.05)
        self.wave_amplitude = random.uniform(1, 3)
        
    def update(self, dt: float, player_pos: pygame.Vector2):
        # Вычисляем направление к игроку
        direction = player_pos - self.pos
        distance = direction.length()
        
        if distance > 0:
            direction = direction.normalize()
            
            # Движение к игроку
            self.velocity = direction * self.speed
            
            # Добавляем волновое движение
            wave_direction = pygame.Vector2(-direction.y, direction.x)  # Перпендикуляр к направлению
            wave_offset = math.sin(pygame.time.get_ticks() * self.wave_frequency + self.wave_offset) * self.wave_amplitude
            self.velocity += wave_direction * wave_offset
        
        self.pos += self.velocity * dt
        self.rotation += self.rotation_speed * dt
        
        # Проверка на столкновение с игроком (очень близко)
        if distance < self.size + 20:  # Размер игрока примерно 20
            return self.damage  # Возвращаем нанесённый урон
        
        return 0
    
    def take_damage(self, damage: int):
        self.health -= damage
        if self.health <= 0:
            self.dead = True
            return self.score_value
        return 0
    
    def draw(self, surf: pygame.Surface, offset: pygame.Vector2):
        # Рисуем врага как круг с деталями
        screen_pos = (int(self.pos.x + offset.x), int(self.pos.y + offset.y))
        
        # Основной круг
        pygame.draw.circle(surf, self.color, screen_pos, self.size)
        
        # Свечение для элитных и боссов
        if self.type in ["elite", "boss"]:
            glow_surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
            for i in range(3):
                alpha = 50 - i * 15
                size = self.size + i * 2
                pygame.draw.circle(glow_surf, (*self.glow_color, alpha), 
                                 (self.size * 1.5, self.size * 1.5), size)
            surf.blit(glow_surf, (screen_pos[0] - self.size * 1.5, screen_pos[1] - self.size * 1.5))
        
        # Индикатор здоровья
        health_ratio = self.health / self.max_health
        bar_width = self.size * 2
        bar_height = 4
        pygame.draw.rect(surf, (60, 60, 60), 
                        (screen_pos[0] - bar_width//2, screen_pos[1] - self.size - 10, bar_width, bar_height))
        pygame.draw.rect(surf, (255, 80, 80) if health_ratio > 0.3 else (255, 200, 0),
                        (screen_pos[0] - bar_width//2, screen_pos[1] - self.size - 10, 
                         int(bar_width * health_ratio), bar_height))

class EnemySpawner:
    def __init__(self):
        self.spawn_timer = 0
        self.spawn_delay = 2000  # миллисекунд
        self.wave_number = 1
        self.enemies_spawned = 0
        self.max_enemies_in_wave = 5
        self.difficulty_factor = 1.0
        
    def update(self, dt: float, enemies_list: List[Enemy]):
        self.spawn_timer += dt * 1000  # преобразуем dt в миллисекунды
        
        # Увеличиваем сложность с каждой волной
        if len(enemies_list) == 0 and self.enemies_spawned > 0:
            self.wave_number += 1
            self.enemies_spawned = 0
            self.max_enemies_in_wave = min(5 + self.wave_number, 30)
            self.difficulty_factor = 1.0 + (self.wave_number - 1) * 0.1
            self.spawn_delay = max(500, 2000 - self.wave_number * 100)  # spawn faster as waves increase
        
        # Спаун врагов если прошло достаточно времени и не превышено ограничение
        if (self.spawn_timer >= self.spawn_delay and 
            self.enemies_spawned < self.max_enemies_in_wave):
            self.spawn_enemy(enemies_list)
            self.spawn_timer = 0
            self.enemies_spawned += 1
    
    def spawn_enemy(self, enemies_list: List[Enemy]):
        # Определяем границы экрана для спауна врагов за пределами видимой области
        border_margin = 50
        side = random.randint(0, 3)  # 0: top, 1: right, 2: bottom, 3: left
        
        if side == 0:  # top
            x = random.randint(border_margin, 1000 - border_margin)
            y = -border_margin
        elif side == 1:  # right
            x = 1000 + border_margin
            y = random.randint(border_margin, 700 - border_margin)
        elif side == 2:  # bottom
            x = random.randint(border_margin, 1000 - border_margin)
            y = 700 + border_margin
        else:  # left
            x = -border_margin
            y = random.randint(border_margin, 700 - border_margin)
        
        # Определяем тип врага на основе сложности
        enemy_types = ["basic"]
        if self.wave_number > 3:
            enemy_types.append("fast")
        if self.wave_number > 5:
            enemy_types.append("tank")
        if self.wave_number > 8:
            enemy_types.extend(["elite", "elite"])
        if self.wave_number > 15:
            enemy_types.append("boss")
        
        enemy_type = random.choice(enemy_types)
        enemy = Enemy(pygame.Vector2(x, y), enemy_type)
        
        # Увеличиваем параметры врага в зависимости от сложности
        enemy.health = int(enemy.health * self.difficulty_factor)
        enemy.max_health = enemy.health
        enemy.damage = int(enemy.damage * self.difficulty_factor)
        
        enemies_list.append(enemy)