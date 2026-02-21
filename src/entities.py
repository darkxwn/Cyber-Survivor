import pygame
import math
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from abc import ABC, abstractmethod
import random
from config import *

@dataclass
class Particle:
    pos: pygame.Vector2
    vel: pygame.Vector2
    color: Tuple[int, int, int]
    lifetime: float
    max_lifetime: float
    size: float

class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []
    
    def emit(self, pos: pygame.Vector2, count: int, color: Tuple[int, int, int], 
             speed_range: Tuple[float, float] = (2, 8)):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(*speed_range)
            vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            lifetime = random.uniform(0.3, 0.8)
            size = random.uniform(2, 5)
            self.particles.append(Particle(
                pos=pygame.Vector2(pos),
                vel=vel,
                color=color,
                lifetime=lifetime,
                max_lifetime=lifetime,
                size=size
            ))
    
    def update(self, dt: float):
        for p in self.particles[:]:
            p.pos += p.vel
            p.vel *= 0.95
            p.lifetime -= dt
            if p.lifetime <= 0:
                self.particles.remove(p)
    
    def draw(self, surf: pygame.Surface, offset: pygame.Vector2):
        for p in self.particles:
            alpha = int((p.lifetime / p.max_lifetime) * 255)
            color = (*p.color, alpha)
            s = pygame.Surface((int(p.size * 2), int(p.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (int(p.size), int(p.size)), int(p.size))
            surf.blit(s, (p.pos.x + offset.x - p.size, p.pos.y + offset.y - p.size))

class GameObject(ABC):
    def __init__(self, pos: pygame.Vector2):
        self.pos = pos
        self.dead = False
    
    @abstractmethod
    def update(self, dt: float):
        pass
    
    @abstractmethod
    def draw(self, surf: pygame.Surface, offset: pygame.Vector2):
        pass


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
        
        self.fire_rate = max(100, 250 - modules.get("fire_rate", 0) * 5)
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
        self.regen_accumulator = 0.0  # Накопитель для дробной регенерации
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
        elif self.skin_id == "pink":
            self.dash_speed *= 1.20
        elif self.skin_id == "dark":
            self.dmg = int(self.dmg * 1.15)
            self.speed *= 0.95
    
    def take_damage(self, damage: int) -> bool:
        if self.invulnerable > 0:
            return False
        
        if self.shield > 0:
            self.shield -= damage
            if self.shield < 0:
                self.hp += self.shield
                self.shield = 0
        else:
            self.hp -= damage
        
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
        if self.regen > 0 and self.hp < self.max_hp:
            self.regen_accumulator += self.regen * dt
            if self.regen_accumulator >= 1.0:
                heal_amount = int(self.regen_accumulator)
                self.heal(heal_amount)
                self.regen_accumulator -= heal_amount
        
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
            # Массивная защитная форма
            pts = [
                pygame.Vector2(28, 0), pygame.Vector2(18, -14),
                pygame.Vector2(-8, -20), pygame.Vector2(-18, -10),
                pygame.Vector2(-18, 10), pygame.Vector2(-8, 20),
                pygame.Vector2(18, 14),
            ]
        elif self.skin_id == "green":
            # Острая хищная форма
            pts = [
                pygame.Vector2(38, 0), pygame.Vector2(25, -5),
                pygame.Vector2(12, -15), pygame.Vector2(-12, -12),
                pygame.Vector2(-18, 0), pygame.Vector2(-12, 12),
                pygame.Vector2(12, 15), pygame.Vector2(25, 5),
            ]
        elif self.skin_id == "cyan":
            # Хакер: ромб с вырезом — угловатый сканер
            pts = [
                pygame.Vector2(36, 0), pygame.Vector2(18, -12),
                pygame.Vector2(6, -6), pygame.Vector2(-14, -18),
                pygame.Vector2(-10, 0), pygame.Vector2(-14, 18),
                pygame.Vector2(6, 6), pygame.Vector2(18, 12),
            ]
        elif self.skin_id == "orange":
            # Огненный танк: широкий приземистый корпус
            pts = [
                pygame.Vector2(22, 0), pygame.Vector2(14, -20),
                pygame.Vector2(-4, -24), pygame.Vector2(-20, -16),
                pygame.Vector2(-20, 16), pygame.Vector2(-4, 24),
                pygame.Vector2(14, 20),
            ]
        elif self.skin_id == "white":
            # Призрак войны: 10-лучевая звезда
            pts = []
            for _i in range(10):
                _r = 32 if _i % 2 == 0 else 16
                _a = math.radians(-90 + _i * 36)
                pts.append(pygame.Vector2(math.cos(_a) * _r, math.sin(_a) * _r))
        elif self.skin_id == "pink":
            # Ниндзя: острые сужающиеся крылья
            pts = [
                pygame.Vector2(40, 0), pygame.Vector2(22, -3),
                pygame.Vector2(4, -20), pygame.Vector2(-8, -8),
                pygame.Vector2(-18, 0), pygame.Vector2(-8, 8),
                pygame.Vector2(4, 20), pygame.Vector2(22, 3),
            ]
        elif self.skin_id == "dark":
            # Тёмный воин: угловой восьмиугольник
            pts = [
                pygame.Vector2(28, -14), pygame.Vector2(28, 14),
                pygame.Vector2(14, 26), pygame.Vector2(-10, 22),
                pygame.Vector2(-24, 8), pygame.Vector2(-24, -8),
                pygame.Vector2(-10, -22), pygame.Vector2(14, -26),
            ]
        else:
            pts = [
                pygame.Vector2(32, 0), pygame.Vector2(20, -8),
                pygame.Vector2(-18, -15), pygame.Vector2(-12, -4),
                pygame.Vector2(-12, 0), pygame.Vector2(-12, 4),
                pygame.Vector2(-18, 15), pygame.Vector2(20, 8),
            ]
        
        rotated = [p.rotate(self.facing_angle) + self.pos + offset for p in pts]
        
        if self.shield > 0:
            glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*COLORS["shield"], 30), (40, 40), 35)
            surf.blit(glow_surf, (self.pos.x + offset.x - 40, self.pos.y + offset.y - 40))
        
        color = self.color
        if self.hit_flash > 0:
            flash_intensity = int((self.hit_flash / 200) * 255)
            color = (255, flash_intensity, flash_intensity)
        
        pygame.draw.polygon(surf, color, rotated)
        pygame.draw.polygon(surf, self.glow_color, rotated, 2)
        
        # Орбитальные пули
        if hasattr(self, 'orbital_bullets') and self.orbital_bullets > 0:
            time_ms = pygame.time.get_ticks()
            orbit_radius = 50
            for i in range(self.orbital_bullets):
                angle = (time_ms / 1000 + i * (6.28 / self.orbital_bullets)) % 6.28
                orb_x = self.pos.x + offset.x + math.cos(angle) * orbit_radius
                orb_y = self.pos.y + offset.y + math.sin(angle) * orbit_radius
                pygame.draw.circle(surf, COLORS["player"], (int(orb_x), int(orb_y)), 8)
                pygame.draw.circle(surf, COLORS["player_glow"], (int(orb_x), int(orb_y)), 8, 2)

class EnemyShape(Enum):
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE = "triangle"
    HEXAGON = "hexagon"
    DIAMOND = "diamond"

class Enemy(GameObject):
    def __init__(self, pos: pygame.Vector2, enemy_type: str = "basic", 
                 difficulty_mult: float = 1.0, shape: Optional[EnemyShape] = None):
        super().__init__(pos)
        self.type = enemy_type
        self.hit_flash = 0
        self.rotation = 0
        
        # Таблица имён, уровней и фракций
        _ENEMY_META = {
            "basic":    ("Дрон",         1, "Рой"),
            "swarm":    ("Личинка",      1, "Рой"),
            "fast":     ("Стремительный",1, "Рой"),
            "sniper":   ("Охотник",      2, "Элита"),
            "ghost":    ("Фантом",       2, "Теневые"),
            "leech":    ("Паразит",      2, "Теневые"),
            "tank":     ("Бронетанк",    3, "Элита"),
            "bruiser":  ("Берсерк",      3, "Элита"),
            "bomber":   ("Камикадзе",    3, "Элита"),
            "sentinel": ("Часовой",      4, "Командиры"),
            "boss":     ("Повелитель",   5, "Командиры"),
            "ranger":   ("Рейнджер",     2, "Элита"),
            "mortar":   ("Мортирщик",    3, "Элита"),
            "shielder": ("Щитоносец",    3, "Командиры"),
        }
        _meta = _ENEMY_META.get(enemy_type, (enemy_type.capitalize(), 1, "?"))
        self.display_name = _meta[0]
        self.tier = _meta[1]
        self.faction = _meta[2]
        self.is_miniboss = False  # будет выставлено извне
        
        # Базовая статистика в зависимости от типа
        if enemy_type == "basic":
            self.max_hp = int(30 * difficulty_mult)
            self.speed = 2.5 + difficulty_mult * 0.3
            self.dmg = 8 + int(difficulty_mult * 1.5)
            self.exp_value = 10
            self.color = COLORS["enemy"]
            self.size = 20
            self.shape = EnemyShape.CIRCLE
        elif enemy_type == "fast":
            self.max_hp = int(20 * difficulty_mult)
            self.speed = 5.0 + difficulty_mult * 0.5
            self.dmg = 5 + int(difficulty_mult * 1)
            self.exp_value = 15
            self.color = (255, 255, 100)
            self.size = 15
            self.shape = EnemyShape.TRIANGLE
        elif enemy_type == "tank":
            self.max_hp = int(100 * difficulty_mult)
            self.speed = 1.5 + difficulty_mult * 0.2
            self.dmg = 10 + int(difficulty_mult * 2)
            self.exp_value = 30
            self.color = COLORS["elite_enemy"]
            self.size = 30
            self.shape = EnemyShape.SQUARE
        elif enemy_type == "boss":
            self.max_hp = int(500 * difficulty_mult)
            self.speed = 2.0 + difficulty_mult * 0.3
            self.dmg = 18 + int(difficulty_mult * 4)
            self.exp_value = 200
            self.color = COLORS["boss"]
            self.size = 50
            self.shape = EnemyShape.HEXAGON
        elif enemy_type == "sniper":
            # Медленный, мощный, далеко держится
            self.max_hp = int(45 * difficulty_mult)
            self.speed = 1.2 + difficulty_mult * 0.15
            self.dmg = 14 + int(difficulty_mult * 3)
            self.exp_value = 25
            self.color = (220, 80, 255)   # Фиолетово-розовый
            self.size = 18
            self.shape = EnemyShape.DIAMOND
        elif enemy_type == "swarm":
            # Маленький, быстрый, много HP, рой
            self.max_hp = int(12 * difficulty_mult)
            self.speed = 6.5 + difficulty_mult * 0.6
            self.dmg = 3 + int(difficulty_mult * 0.5)
            self.exp_value = 8
            self.color = (255, 160, 60)   # Оранжевый
            self.size = 11
            self.shape = EnemyShape.CIRCLE
        elif enemy_type == "ghost":
            # Призрак: проходит сквозь других врагов, высокий урон
            self.max_hp = int(35 * difficulty_mult)
            self.speed = 3.5 + difficulty_mult * 0.4
            self.dmg = 12 + int(difficulty_mult * 2)
            self.exp_value = 20
            self.color = (150, 255, 220)  # Голубовато-белый
            self.size = 22
            self.shape = EnemyShape.HEXAGON
        elif enemy_type == "bruiser":
            # Крепкий, средняя скорость, большой урон
            self.max_hp = int(160 * difficulty_mult)
            self.speed = 2.2 + difficulty_mult * 0.25
            self.dmg = 15 + int(difficulty_mult * 3)
            self.exp_value = 45
            self.color = (200, 50, 50)
            self.size = 35
            self.shape = EnemyShape.SQUARE
        elif enemy_type == "leech":
            # Пиявка: лечится при атаке игрока
            self.max_hp = int(55 * difficulty_mult)
            self.speed = 3.0 + difficulty_mult * 0.3
            self.dmg = 7 + int(difficulty_mult * 1.5)
            self.exp_value = 20
            self.color = (190, 80, 200)   # Пурпурный
            self.size = 18
            self.shape = EnemyShape.TRIANGLE
        elif enemy_type == "bomber":
            # Бомбардировщик: медленный, при смерти взрывается
            self.max_hp = int(50 * difficulty_mult)
            self.speed = 1.8 + difficulty_mult * 0.2
            self.dmg = 25 + int(difficulty_mult * 4)
            self.exp_value = 35
            self.color = (255, 100, 30)   # Оранжевый
            self.size = 27
            self.shape = EnemyShape.CIRCLE
        elif enemy_type == "sentinel":
            # Страж: медленный, высокое HP, огромный урон
            self.max_hp = int(280 * difficulty_mult)
            self.speed = 0.7 + difficulty_mult * 0.1
            self.dmg = 20 + int(difficulty_mult * 4)
            self.exp_value = 80
            self.color = (60, 120, 255)   # Синий
            self.size = 40
            self.shape = EnemyShape.HEXAGON
        elif enemy_type == "ranger":
            # Рейнджер: держится на дистанции, стреляет снарядами
            self.max_hp = int(50 * difficulty_mult)
            self.speed = 1.5 + difficulty_mult * 0.15
            self.dmg = 16 + int(difficulty_mult * 2.5)
            self.exp_value = 30
            self.color = (100, 220, 120)   # Зелёный
            self.size = 20
            self.shape = EnemyShape.DIAMOND
            self.preferred_range = 350    # дистанция, на которой держится
            self.shoot_cooldown = 0
            self.shoot_interval = 2000    # мс между выстрелами
        elif enemy_type == "mortar":
            # Мортирщик: стоит, бьёт по AoE в позицию игрока
            self.max_hp = int(70 * difficulty_mult)
            self.speed = 0.6 + difficulty_mult * 0.05
            self.dmg = 22 + int(difficulty_mult * 3)
            self.exp_value = 40
            self.color = (180, 100, 40)   # Коричневый
            self.size = 28
            self.shape = EnemyShape.SQUARE
            self.preferred_range = 500
            self.shoot_cooldown = 0
            self.shoot_interval = 3500
        elif enemy_type == "shielder":
            # Щитоносец: медленный, у всех ближних врагов щит от урона
            self.max_hp = int(200 * difficulty_mult)
            self.speed = 1.0 + difficulty_mult * 0.1
            self.dmg = 8 + int(difficulty_mult * 1.5)
            self.exp_value = 60
            self.color = (80, 200, 255)   # Голубой
            self.size = 35
            self.shape = EnemyShape.HEXAGON
            self.aura_radius = 200        # радиус бафа
            self.aura_timer = 0
        else:
            # Fallback
            self.max_hp = int(30 * difficulty_mult)
            self.speed = 2.5
            self.dmg = 8
            self.exp_value = 10
            self.color = COLORS["enemy"]
            self.size = 20
            self.shape = EnemyShape.CIRCLE

        self.hp = self.max_hp

        # Поля для эффектов
        self.poison_damage = 0
        self.poison_duration = 0
        self.frozen_duration = 0
        self.chain_lightning_target = False
        self.chain_lightning_timer = 0
        self.explosion_marked = False
        # Специальные поля новых врагов
        if not hasattr(self, 'is_bomber'):
            self.is_bomber = (enemy_type == "bomber")
        if not hasattr(self, 'leech_heal'):
            self.leech_heal = 8 if enemy_type == "leech" else 0
    
    def take_damage(self, dmg: int) -> bool:
        # Щит от Щитоносца поглощает часть урона
        if hasattr(self, 'shield_buff') and self.shield_buff > 0:
            absorbed = min(self.shield_buff, dmg)
            dmg -= absorbed
            self.shield_buff -= absorbed
        self.hp -= dmg
        self.hit_flash = 100
        return self.hp <= 0
    
    def update(self, dt: float, target_pos: pygame.Vector2 = None):
        # Обработка яда
        if self.poison_duration > 0:
            self.poison_duration -= dt * 1000
            self.hp -= int(self.poison_damage * dt)
            if self.hp <= 0:
                return  # Враг умер от яда
        
        # Обработка заморозки
        if self.frozen_duration > 0:
            self.frozen_duration -= dt * 1000
            # Не двигаемся пока заморожены
        else:
            # Особое поведение дальнобойных врагов
            if self.type in ("ranger", "mortar") and target_pos:
                pref_range = getattr(self, 'preferred_range', 300)
                direction = target_pos - self.pos
                dist = direction.length()
                if dist > pref_range + 40:
                    # Подойти ближе
                    self.pos += direction.normalize() * self.speed
                elif dist < pref_range - 40:
                    # Отступить
                    self.pos -= direction.normalize() * self.speed
                # Иначе стоим на месте, стреляем
            elif target_pos:
                direction = target_pos - self.pos
                if direction.length() > 0:
                    self.pos += direction.normalize() * self.speed
        
        # Обновляем кулдаун стрельбы дальнобойных
        if self.type in ("ranger", "mortar"):
            if hasattr(self, 'shoot_cooldown') and self.shoot_cooldown > 0:
                self.shoot_cooldown -= dt * 1000
        
        # Аура щитоносца
        if self.type == "shielder":
            self.aura_timer = max(0, self.aura_timer - dt * 1000)
        
        # Обработка молнии
        if self.chain_lightning_timer > 0:
            self.chain_lightning_timer -= dt * 1000
            if self.chain_lightning_timer <= 0:
                self.chain_lightning_target = False
        
        self.rotation += dt * 50  # Вращение для некоторых форм
        
        if self.hit_flash > 0:
            self.hit_flash -= dt * 1000
    
    def draw(self, surf: pygame.Surface, offset: pygame.Vector2):
        x = int(self.pos.x + offset.x)
        y = int(self.pos.y + offset.y)
        
        color = self.color
        if self.hit_flash > 0:
            color = (255, 255, 255)
        
        # ===== ВИЗУАЛЬНЫЕ ЭФФЕКТЫ =====
        time_ms = pygame.time.get_ticks()
        
        # Эффект яда - зелёное свечение
        if self.poison_duration > 0:
            poison_surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
            pygame.draw.circle(poison_surf, (50, 255, 50, 60), (self.size * 1.5, self.size * 1.5), self.size + 5)
            surf.blit(poison_surf, (x - self.size * 1.5, y - self.size * 1.5))
            
            # Капли яда вокруг
            for i in range(3):
                angle = (time_ms / 300 + i * 2.1) % 6.28
                drop_x = x + int(math.cos(angle) * (self.size + 8))
                drop_y = y + int(math.sin(angle) * (self.size + 8))
                pygame.draw.circle(surf, (0, 200, 0), (drop_x, drop_y), 3)
        
        # Эффект заморозки - голубое свечение
        if self.frozen_duration > 0:
            freeze_surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
            pygame.draw.circle(freeze_surf, (100, 200, 255, 80), (self.size * 1.5, self.size * 1.5), self.size + 6)
            surf.blit(freeze_surf, (x - self.size * 1.5, y - self.size * 1.5))
            
            # Кристаллы льда
            for i in range(4):
                angle = i * 1.57  # 90 градусов
                ice_x = x + int(math.cos(angle) * (self.size + 10))
                ice_y = y + int(math.sin(angle) * (self.size + 10))
                pts = [
                    (ice_x, ice_y - 5),
                    (ice_x - 3, ice_y + 3),
                    (ice_x + 3, ice_y + 3)
                ]
                pygame.draw.polygon(surf, (150, 220, 255), pts)
        
        # Эффект молнии - жёлтые искры
        if self.chain_lightning_target and self.chain_lightning_timer > 0:
            # Искры вокруг
            for i in range(5):
                angle = random.uniform(0, 6.28)
                dist = random.uniform(self.size, self.size + 15)
                spark_x = x + int(math.cos(angle) * dist)
                spark_y = y + int(math.sin(angle) * dist)
                pygame.draw.circle(surf, (255, 255, 0), (spark_x, spark_y), 2)
            
            # Линии молнии от центра
            for i in range(3):
                angle = (time_ms / 50 + i * 2.1) % 6.28
                end_x = x + int(math.cos(angle) * (self.size + 12))
                end_y = y + int(math.sin(angle) * (self.size + 12))
                pygame.draw.line(surf, (255, 255, 100), (x, y), (end_x, end_y), 2)
        
        # Эффект взрыва - пульсирующее красное свечение
        if self.explosion_marked:
            pulse = abs(math.sin(time_ms / 200)) * 100 + 50
            exp_surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
            pygame.draw.circle(exp_surf, (255, 0, 0, int(pulse)), (self.size * 1.5, self.size * 1.5), self.size + 8)
            surf.blit(exp_surf, (x - self.size * 1.5, y - self.size * 1.5))
        
        # Аура Щитоносца
        if self.type == "shielder":
            aura_r = getattr(self, 'aura_radius', 200)
            aura_surf = pygame.Surface((aura_r*2+4, aura_r*2+4), pygame.SRCALPHA)
            pulse_a = int(25 + 15 * abs(math.sin(time_ms / 600)))
            pygame.draw.circle(aura_surf, (80, 200, 255, pulse_a), (aura_r+2, aura_r+2), aura_r)
            pygame.draw.circle(aura_surf, (80, 200, 255, 80), (aura_r+2, aura_r+2), aura_r, 2)
            surf.blit(aura_surf, (x - aura_r - 2, y - aura_r - 2))
        
        # Рисуем в зависимости от формы
        if self.shape == EnemyShape.CIRCLE:
            pygame.draw.circle(surf, color, (x, y), self.size)
        
        elif self.shape == EnemyShape.SQUARE:
            rect = pygame.Rect(x - self.size, y - self.size, self.size * 2, self.size * 2)
            pygame.draw.rect(surf, color, rect)
        
        elif self.shape == EnemyShape.TRIANGLE:
            pts = [
                (x, y - self.size),
                (x - self.size, y + self.size),
                (x + self.size, y + self.size)
            ]
            pygame.draw.polygon(surf, color, pts)
        
        elif self.shape == EnemyShape.HEXAGON:
            pts = []
            for i in range(6):
                angle = math.radians(60 * i + self.rotation)
                px = x + self.size * math.cos(angle)
                py = y + self.size * math.sin(angle)
                pts.append((px, py))
            pygame.draw.polygon(surf, color, pts)
        
        elif self.shape == EnemyShape.DIAMOND:
            pts = [
                (x, y - self.size),
                (x + self.size, y),
                (x, y + self.size),
                (x - self.size, y)
            ]
            pygame.draw.polygon(surf, color, pts)
        
        # HP бар для всех врагов
        hp_ratio = max(0.0, self.hp / self.max_hp)
        show_bar = (hp_ratio < 1.0) or self.type in ("tank", "boss", "sentinel", "bruiser") or getattr(self, 'is_miniboss', False)
        if show_bar:
            bar_w = max(self.size * 2, 28)
            bar_h = 5 if not getattr(self, 'is_miniboss', False) else 7
            bar_x = x - bar_w // 2
            bar_y = y - self.size - 10
            # Background
            pygame.draw.rect(surf, (25, 25, 25), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), border_radius=2)
            pygame.draw.rect(surf, (60, 20, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
            hp_w = max(1, int(hp_ratio * bar_w))
            # Color: green -> yellow -> red
            r = int(min(255, 510 * (1.0 - hp_ratio)))
            g = int(min(255, 510 * hp_ratio))
            pygame.draw.rect(surf, (r, g, 30), (bar_x, bar_y, hp_w, bar_h), border_radius=2)
            # Miniboss: gold border + name label
            if getattr(self, 'is_miniboss', False):
                pygame.draw.rect(surf, (255, 215, 0), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), 1, border_radius=2)
                try:
                    _nf = pygame.font.Font(None, 17)
                    _nt = _nf.render(f"[МИНИ-БОСС] {getattr(self, 'display_name', '')}", True, (255, 215, 0))
                    surf.blit(_nt, (x - _nt.get_width() // 2, bar_y - 15))
                except:
                    pass

class Bullet(GameObject):
    def __init__(self, pos: pygame.Vector2, angle: float, speed: float, dmg: int, 
                 piercing: int, size: float, lifetime: float, is_crit: bool = False):
        super().__init__(pygame.Vector2(pos))
        self.velocity = pygame.Vector2(
            math.cos(math.radians(angle)) * speed,
            math.sin(math.radians(angle)) * speed
        )
        self.dmg = dmg
        self.piercing = piercing
        self.size = size
        self.lifetime = lifetime
        self.birth_time = pygame.time.get_ticks()
        self.is_crit = is_crit
    
    def update(self, dt: float) -> bool:
        self.pos += self.velocity
        return pygame.time.get_ticks() - self.birth_time > self.lifetime
    
    def draw(self, surf: pygame.Surface, offset: pygame.Vector2):
        color = (255, 255, 100) if self.is_crit else COLORS["bullet"]
        radius = int(6 * self.size) if self.is_crit else int(4 * self.size)
        pygame.draw.circle(surf, color, 
                         (int(self.pos.x + offset.x), int(self.pos.y + offset.y)), radius)