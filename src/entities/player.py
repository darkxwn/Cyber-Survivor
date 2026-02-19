import pygame
import math
import random
from typing import Dict, List
from .base_entity import GameObject
from ..core.config import PLAYER_SKINS, WIDTH, HEIGHT

class Player(GameObject):
    def __init__(self, modules: dict, skin_id: str = "default"):
        super().__init__(pygame.Vector2(WIDTH // 2, HEIGHT // 2))
        
        self.max_hp = 100 + modules.get("health", 0) * 10
        self.hp = self.max_hp
        self.shield = 0
        self.max_shield = 0
        self.speed = 6.5 + modules.get("speed", 0) * 0.5
        self.dmg = 10 + modules.get("damage", 0) * 2
        self.velocity = pygame.Vector2(0, 0)
        self.facing_angle = 0
        
        self.fire_rate = max(100, 250 - modules.get("fire_rate", 0) * 15)
        self.last_shot = 0
        self.bullet_speed = 15
        self.bullet_lifetime = 1000
        self.crit_chance = 0.1 + modules.get("crit", 0) * 0.02
        self.crit_multiplier = 2.0
        
        self.level = 1
        self.exp = 0
        self.exp_to_next = 100
        self.exp_multiplier = 1.0  # Множитель опыта (для скинов)
        
        self.multishot = 1
        self.piercing = 0
        self.bullet_size = 1.0
        self.lifesteal = 0.0
        self.dash_cooldown = 0
        self.dash_ready = True
        self.dash_speed = 20
        self.invulnerable = 0
        self.armor = 0  # Броня (для скинов)
        self.regen = 0  # Регенерация HP в секунду
        self.thorns = 0  # Урон при получении урона
        
        self.hit_flash = 0
        self.size = 30
        
        self.skin_id = skin_id
        self.color = PLAYER_SKINS[skin_id]["color"]
        self.glow_color = PLAYER_SKINS[skin_id]["glow"]
        
        # Применение бонусов скина
        self._apply_skin_bonus()
        
        self.upgrades = {
            "max_hp": 0, "dmg": 0, "fire_rate": 0, "speed": 0,
            "crit_chance": 0, "multishot": 0, "piercing": 0,
            "lifesteal": 0, "shield": 0
        }
        
        # Отслеживание приобретенных перков (для одноразовых эффектов)
        self.acquired_perks = set()
    
    def _apply_skin_bonus(self):
        """Применяет бонусы от активного скина"""
        if self.skin_id == "red":
            self.dmg = int(self.dmg * 1.10)
        elif self.skin_id == "purple":
            self.speed *= 1.15
        elif self.skin_id == "gold":
            self.max_hp = int(self.max_hp * 1.20)
            self.hp = self.max_hp
        elif self.skin_id == "green":
            self.fire_rate = int(self.fire_rate * 0.90)  # меньше = быстрее
        elif self.skin_id == "cyan":
            self.exp_multiplier = 1.10
        elif self.skin_id == "orange":
            self.armor = getattr(self, 'armor', 0) + 8
        elif self.skin_id == "white":
            self.dmg = int(self.dmg * 1.05)
            self.speed *= 1.05
            self.max_hp = int(self.max_hp * 1.05)
            self.hp = self.max_hp
            self.fire_rate = int(self.fire_rate * 0.95)
    
    def take_damage(self, damage: int) -> bool:
        if self.invulnerable > 0:
            return False
        
        if self.shield > 0:
            self.shield -= damage
            if self.shield < 0:
                self.hp += self.shield
                self.shield = 0
        else:
            # Применяем броню (если есть)
            actual_damage = max(1, damage - self.armor)
            self.hp -= actual_damage
        
        self.hit_flash = 200
        self.invulnerable = 500
        return self.hp <= 0
    
    def heal(self, amount: float):
        self.hp = min(self.hp + int(amount), self.max_hp)
    
    def add_shield(self, amount: int):
        self.max_shield += amount
        self.shield = min(self.shield + amount, self.max_shield)
    
    def update(self, dt: float):
        if self.invulnerable > 0:
            self.invulnerable -= dt * 1000
        if self.hit_flash > 0:
            self.hit_flash -= dt * 1000
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt * 1000
            if self.dash_cooldown <= 0:
                self.dash_ready = True
        
        # Регенерация HP (восстанавливает каждую секунду)
        if hasattr(self, 'regen') and self.regen > 0:
            # dt в секундах, поэтому просто умножаем regen на dt
            self.heal(self.regen * dt)
        
        self.velocity *= 0.85
    
    def dash(self, direction: pygame.Vector2):
        if self.dash_ready and direction.length() > 0:
            self.velocity = direction.normalize() * self.dash_speed
            self.dash_cooldown = 2000
            self.dash_ready = False
            self.invulnerable = 200
            return True
        return False
    
    def draw(self, surf: pygame.Surface, offset: pygame.Vector2):
        m_pos = pygame.mouse.get_pos()
        rel = pygame.Vector2(m_pos) - (self.pos + offset)
        if rel.length() > 0:
            self.facing_angle = math.degrees(math.atan2(rel.y, rel.x))
        
        if self.invulnerable > 0 and int(self.invulnerable / 100) % 2 == 0:
            return
        
        # Разные формы для разных скинов
        if self.skin_id == "default":
            pts = [
                pygame.Vector2(32, 0), pygame.Vector2(20, -8),
                pygame.Vector2(-18, -15), pygame.Vector2(-12, -4),
                pygame.Vector2(-12, 0), pygame.Vector2(-12, 4),
                pygame.Vector2(-18, 15), pygame.Vector2(20, 8),
            ]
        elif self.skin_id == "red":
            # Агрессивная треугольная форма
            pts = [
                pygame.Vector2(35, 0), pygame.Vector2(15, -12),
                pygame.Vector2(-15, -18), pygame.Vector2(-10, 0),
                pygame.Vector2(-15, 18), pygame.Vector2(15, 12),
            ]
        elif self.skin_id == "purple":
            # Призрачная вытянутая форма
            pts = [
                pygame.Vector2(30, 0), pygame.Vector2(22, -6),
                pygame.Vector2(10, -10), pygame.Vector2(-20, -8),
                pygame.Vector2(-20, 8), pygame.Vector2(10, 10),
                pygame.Vector2(22, 6),
            ]
        elif self.skin_id == "gold":
            # Королевская золотая форма
            pts = [
                pygame.Vector2(32, 0), pygame.Vector2(25, -6),
                pygame.Vector2(15, -12), pygame.Vector2(0, -15),
                pygame.Vector2(-15, -12), pygame.Vector2(-25, -6),
                pygame.Vector2(-32, 0), pygame.Vector2(-25, 6),
                pygame.Vector2(-15, 12), pygame.Vector2(0, 15),
                pygame.Vector2(15, 12), pygame.Vector2(25, 6),
            ]
        elif self.skin_id == "green":
            # Сталкерская форма
            pts = [
                pygame.Vector2(30, 0), pygame.Vector2(20, -10),
                pygame.Vector2(0, -15), pygame.Vector2(-20, -10),
                pygame.Vector2(-30, 0), pygame.Vector2(-20, 10),
                pygame.Vector2(0, 15), pygame.Vector2(20, 10),
            ]
        elif self.skin_id == "cyan":
            # Кибер форма
            pts = [
                pygame.Vector2(32, 0), pygame.Vector2(25, -5),
                pygame.Vector2(15, -10), pygame.Vector2(5, -12),
                pygame.Vector2(-5, -12), pygame.Vector2(-15, -10),
                pygame.Vector2(-25, -5), pygame.Vector2(-32, 0),
                pygame.Vector2(-25, 5), pygame.Vector2(-15, 10),
                pygame.Vector2(-5, 12), pygame.Vector2(5, 12),
                pygame.Vector2(15, 10), pygame.Vector2(25, 5),
            ]
        elif self.skin_id == "orange":
            # Огненная форма
            pts = [
                pygame.Vector2(30, 0), pygame.Vector2(22, -8),
                pygame.Vector2(18, -15), pygame.Vector2(0, -12),
                pygame.Vector2(-18, -15), pygame.Vector2(-22, -8),
                pygame.Vector2(-30, 0), pygame.Vector2(-22, 8),
                pygame.Vector2(-18, 15), pygame.Vector2(0, 12),
                pygame.Vector2(18, 15), pygame.Vector2(22, 8),
            ]
        elif self.skin_id == "white":
            # Призрачная форма
            pts = [
                pygame.Vector2(32, 0), pygame.Vector2(28, -4),
                pygame.Vector2(20, -12), pygame.Vector2(8, -15),
                pygame.Vector2(-8, -15), pygame.Vector2(-20, -12),
                pygame.Vector2(-28, -4), pygame.Vector2(-32, 0),
                pygame.Vector2(-28, 4), pygame.Vector2(-20, 12),
                pygame.Vector2(-8, 15), pygame.Vector2(8, 15),
                pygame.Vector2(20, 12), pygame.Vector2(28, 4),
            ]
        else:
            # Стандартная форма
            pts = [
                pygame.Vector2(32, 0), pygame.Vector2(20, -8),
                pygame.Vector2(-18, -15), pygame.Vector2(-12, -4),
                pygame.Vector2(-12, 0), pygame.Vector2(-12, 4),
                pygame.Vector2(-18, 15), pygame.Vector2(20, 8),
            ]
        
        # Поворачиваем точки относительно угла
        rotated_pts = []
        for pt in pts:
            x = pt.x * math.cos(math.radians(self.facing_angle)) - pt.y * math.sin(math.radians(self.facing_angle))
            y = pt.x * math.sin(math.radians(self.facing_angle)) + pt.y * math.cos(math.radians(self.facing_angle))
            rotated_pts.append((self.pos.x + offset.x + x, self.pos.y + offset.y + y))
        
        # Рисуем основной корабль
        pygame.draw.polygon(surf, self.color, rotated_pts)
        
        # Рисуем свечение
        glow_surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
        for i in range(3):
            alpha = 50 - i * 15
            size = self.size + i * 2
            glow_rect = pygame.Rect(0, 0, size * 2, size * 2)
            glow_rect.center = (self.size * 1.5, self.size * 1.5)
            pygame.draw.polygon(glow_surf, (*self.glow_color, alpha), [
                (pt[0] - (self.pos.x + offset.x - self.size * 1.5), pt[1] - (self.pos.y + offset.y - self.size * 1.5))
                for pt in rotated_pts
            ])
        
        surf.blit(glow_surf, (self.pos.x + offset.x - self.size * 1.5, self.pos.y + offset.y - self.size * 1.5))
        
        # Рисуем щит если есть
        if self.shield > 0:
            shield_radius = self.size + 5 + int(pygame.time.get_ticks() / 100) % 2
            pygame.draw.circle(surf, (100, 200, 255, 100), 
                             (int(self.pos.x + offset.x), int(self.pos.y + offset.y)), 
                             shield_radius, 2)
        
        # Рисуем хит-флеш если был урон
        if self.hit_flash > 0:
            flash_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            alpha = min(200, self.hit_flash)
            pygame.draw.polygon(flash_surf, (255, 100, 100, alpha), [
                (pt[0] - (self.pos.x + offset.x - self.size), pt[1] - (self.pos.y + offset.y - self.size))
                for pt in rotated_pts
            ])
            surf.blit(flash_surf, (self.pos.x + offset.x - self.size, self.pos.y + offset.y - self.size))
    
    def gain_exp(self, amount: int):
        self.exp += int(amount * self.exp_multiplier)
        # Проверка на повышение уровня
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level_up()
    
    def level_up(self):
        self.level += 1
        self.exp_to_next = int(self.exp_to_next * 1.5)
        
        # Увеличиваем максимальное здоровье
        self.max_hp += 20
        self.hp = min(self.hp + 20, self.max_hp)
    
    def can_upgrade(self) -> bool:
        return self.level > len(self.acquired_perks)  # Предполагаем, что уровень равен количеству доступных апгрейдов