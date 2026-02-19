import pygame
import math
from typing import List
from .base_entity import GameObject

class Bullet(GameObject):
    def __init__(self, pos: pygame.Vector2, direction: pygame.Vector2, damage: int, 
                 speed: float = 15, lifetime: int = 1000, size: float = 1.0, piercing: int = 0):
        super().__init__(pos)
        self.direction = direction.normalize()
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.piercing = piercing
        self.initial_piercing = piercing  # Для отслеживания начального значения пробития
        self.velocity = self.direction * self.speed
        self.color = (255, 255, 200)
        
    def update(self, dt: float):
        self.pos += self.velocity * dt
        self.lifetime -= dt * 1000  # преобразуем dt в миллисекунды
        
        if self.lifetime <= 0:
            self.dead = True
    
    def draw(self, surf: pygame.Surface, offset: pygame.Vector2):
        screen_pos = (int(self.pos.x + offset.x), int(self.pos.y + offset.y))
        
        # Рисуем пулю как маленький прямоугольник или круг
        pygame.draw.circle(surf, self.color, screen_pos, int(self.size * 3))
        
        # Если у пули есть пробитие, рисуем кольцо вокруг
        if self.piercing > 0:
            pygame.draw.circle(surf, (200, 200, 255), screen_pos, int(self.size * 5), 1)

class BulletManager:
    def __init__(self):
        self.bullets: List[Bullet] = []
    
    def shoot(self, pos: pygame.Vector2, direction: pygame.Vector2, damage: int, 
              speed: float = 15, lifetime: int = 1000, size: float = 1.0, piercing: int = 0):
        bullet = Bullet(pos, direction, damage, speed, lifetime, size, piercing)
        self.bullets.append(bullet)
    
    def multi_shoot(self, pos: pygame.Vector2, base_direction: pygame.Vector2, damage: int, 
                   count: int, spread: float = 0.2, **kwargs):
        """Выстрел нескольких пуль с разбросом"""
        for i in range(count):
            if count == 1:
                angle_offset = 0
            elif count % 2 == 1:
                # Нечетное количество пуль
                angle_offset = spread * (i - count // 2)
            else:
                # Четное количество пуль
                center = (count - 1) / 2
                angle_offset = spread * (i - center)
            
            direction = pygame.Vector2(
                base_direction.x * math.cos(angle_offset) - base_direction.y * math.sin(angle_offset),
                base_direction.x * math.sin(angle_offset) + base_direction.y * math.cos(angle_offset)
            )
            
            self.shoot(pos, direction, damage, **kwargs)
    
    def update(self, dt: float):
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if bullet.dead:
                self.bullets.remove(bullet)
    
    def draw(self, surf: pygame.Surface, offset: pygame.Vector2):
        for bullet in self.bullets:
            bullet.draw(surf, offset)
    
    def check_collisions(self, enemies_list: list):
        """Проверяет столкновения пуль с врагами и возвращает список очков за уничтоженных врагов"""
        scores = []
        
        for bullet in self.bullets[:]:
            for enemy in enemies_list[:]:
                # Проверяем расстояние между пулей и врагом
                dist_vec = enemy.pos - bullet.pos
                distance = dist_vec.length()
                
                if distance < enemy.size + bullet.size * 3:  # +3 потому что размер пули это радиус 3
                    # Попадание в врага
                    score = enemy.take_damage(bullet.damage)
                    
                    if score > 0:
                        scores.append(score)
                    
                    # Уменьшаем пробитие
                    bullet.piercing -= 1
                    
                    # Если пробитие закончилось, удаляем пулю
                    if bullet.piercing < 0:
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break  # Переходим к следующей пуле
        
        return scores