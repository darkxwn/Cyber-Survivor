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
        # Фракции и их цвета:
        # "Рой" (Swarm) - красно-оранжевые оттенки: базовые враги, рои, быстрые
        # "Теневые" (Shadow) - пурпурно-тёмные: призраки, паразиты, снайперы
        # "Элита" (Elite) - синие/бирюзовые: рейнджеры, танки, берсерки
        # "Командиры" (Command) - золото/фиолетовые: щитоносцы, часовые, боссы
        # "Поддержка" (Support) - зелёные/жёлтые: хилеры, усилители
        _ENEMY_META = {
            "basic":    ("Дрон",         1, "Рой"),
            "swarm":    ("Личинка",      1, "Рой"),
            "fast":     ("Стремительный",1, "Рой"),
            "sniper":   ("Охотник",      2, "Теневые"),
            "ghost":    ("Фантом",       2, "Теневые"),
            "leech":    ("Паразит",      2, "Теневые"),
            "tank":     ("Бронетанк",    3, "Элита"),
            "bruiser":  ("Берсерк",      3, "Элита"),
            "ranger":   ("Рейнджер",     2, "Элита"),
            "lancer":   ("Ланцет",       2, "Элита"),
            "bomber":   ("Камикадзе",    3, "Рой"),
            "sentinel": ("Часовой",      4, "Командиры"),
            "boss":     ("Повелитель",   5, "Командиры"),
            "mortar":   ("Мортирщик",    3, "Командиры"),
            "shielder": ("Щитоносец",    3, "Командиры"),
            "healer":   ("Регенератор",  3, "Поддержка"),
            "buffer":   ("Усилитель",    3, "Поддержка"),
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
            self.color = (255, 46, 99)    # Красный — Рой
            self.size = 20
            self.shape = EnemyShape.CIRCLE
            # Особая способность с ранга 3+: при смерти ускоряет ближних врагов
            self.on_death_buff = (difficulty_mult >= 3.0)
        elif enemy_type == "fast":
            self.max_hp = int(20 * difficulty_mult)
            self.speed = 5.0 + difficulty_mult * 0.5
            self.dmg = 5 + int(difficulty_mult * 1)
            self.exp_value = 15
            self.color = (255, 200, 40)   # Жёлто-оранжевый — Рой
            self.size = 15
            self.shape = EnemyShape.TRIANGLE
            # Особая способность с ранга 2: уклонение при низком HP
            self.evade_hp_threshold = 0.25 if difficulty_mult >= 2.0 else 0
        elif enemy_type == "tank":
            self.max_hp = int(100 * difficulty_mult)
            self.speed = 1.5 + difficulty_mult * 0.2
            self.dmg = 10 + int(difficulty_mult * 2)
            self.exp_value = 30
            self.color = (40, 140, 255)   # Синий — Элита
            self.size = 30
            self.shape = EnemyShape.SQUARE
            # Особая способность: тяжёлая броня снижает 20% урона
            self.damage_reduction = 0.20
        elif enemy_type == "boss":
            self.max_hp = int(500 * difficulty_mult)
            self.speed = 2.0 + difficulty_mult * 0.3
            self.dmg = 18 + int(difficulty_mult * 4)
            self.exp_value = 200
            self.color = (150, 0, 255)    # Фиолетовый — Командиры
            self.size = 50
            self.shape = EnemyShape.HEXAGON
            # Особая способность: периодически призывает рой
            self.summon_timer = 0
            self.summon_interval = 5000
        elif enemy_type == "sniper":
            # Снайпер: держится далеко, стреляет прицельными снарядами
            self.max_hp = int(45 * difficulty_mult)
            self.speed = 1.2 + difficulty_mult * 0.15
            self.dmg = 18 + int(difficulty_mult * 3)
            self.exp_value = 25
            self.color = (180, 40, 220)   # Тёмно-фиолетовый — Теневые
            self.size = 18
            self.shape = EnemyShape.DIAMOND
            self.preferred_range = 500
            self.shoot_cooldown = 0
            self.shoot_interval = 2500
            # Особая способность с ранга 2: пуля пробивает неуязвимость
            self.armor_pierce = (difficulty_mult >= 2.0)
        elif enemy_type == "swarm":
            self.max_hp = int(12 * difficulty_mult)
            self.speed = 6.5 + difficulty_mult * 0.6
            self.dmg = 3 + int(difficulty_mult * 0.5)
            self.exp_value = 8
            self.color = (255, 120, 30)   # Оранжевый — Рой
            self.size = 11
            self.shape = EnemyShape.CIRCLE
        elif enemy_type == "ghost":
            # Призрак: периодически входит в фазу неуязвимости
            self.max_hp = int(35 * difficulty_mult)
            self.speed = 3.5 + difficulty_mult * 0.4
            self.dmg = 12 + int(difficulty_mult * 2)
            self.exp_value = 20
            self.color = (140, 50, 200)   # Тёмно-пурпурный — Теневые
            self.size = 22
            self.shape = EnemyShape.HEXAGON
            # Фазирование
            self.phase_timer = 0
            self.phase_interval = 3000
            self.phase_duration = 800
            self.is_phasing = False
        elif enemy_type == "bruiser":
            # Берсерк: ускоряется при низком HP
            self.max_hp = int(160 * difficulty_mult)
            self.speed = 2.2 + difficulty_mult * 0.25
            self.base_speed = 2.2 + difficulty_mult * 0.25
            self.dmg = 15 + int(difficulty_mult * 3)
            self.exp_value = 45
            self.color = (60, 160, 240)   # Синий — Элита
            self.size = 35
            self.shape = EnemyShape.SQUARE
            # Берсерк-режим при <40% HP
            self.berserk_triggered = False
        elif enemy_type == "leech":
            self.max_hp = int(55 * difficulty_mult)
            self.speed = 3.0 + difficulty_mult * 0.3
            self.dmg = 7 + int(difficulty_mult * 1.5)
            self.exp_value = 20
            self.color = (220, 50, 200)   # Пурпурный — Теневые
            self.size = 18
            self.shape = EnemyShape.TRIANGLE
            self.leech_heal = 8 + int(difficulty_mult * 2)
        elif enemy_type == "bomber":
            self.max_hp = int(50 * difficulty_mult)
            self.speed = 1.8 + difficulty_mult * 0.2
            self.dmg = 25 + int(difficulty_mult * 4)
            self.exp_value = 35
            self.color = (255, 80, 20)    # Оранжево-красный — Рой
            self.size = 27
            self.shape = EnemyShape.CIRCLE
            self.is_bomber = True
        elif enemy_type == "sentinel":
            self.max_hp = int(280 * difficulty_mult)
            self.speed = 0.7 + difficulty_mult * 0.1
            self.dmg = 20 + int(difficulty_mult * 4)
            self.exp_value = 80
            self.color = (100, 50, 255)   # Фиолетово-синий — Командиры
            self.size = 40
            self.shape = EnemyShape.HEXAGON
            # Пульс страха при атаке
            self.knockback_strength = 5.0
        elif enemy_type == "ranger":
            self.max_hp = int(50 * difficulty_mult)
            self.speed = 1.5 + difficulty_mult * 0.15
            self.dmg = 16 + int(difficulty_mult * 2.5)
            self.exp_value = 30
            self.color = (60, 200, 220)   # Бирюзовый — Элита
            self.size = 20
            self.shape = EnemyShape.DIAMOND
            self.preferred_range = 350
            self.shoot_cooldown = 0
            self.shoot_interval = 2000
            # Тройной выстрел с ранга 3
            self.triple_shot = (difficulty_mult >= 3.0)
        elif enemy_type == "lancer":
            # Ланцет: стреляет пробивающими снарядами с дальней дистанции
            self.max_hp = int(40 * difficulty_mult)
            self.speed = 2.0 + difficulty_mult * 0.2
            self.dmg = 12 + int(difficulty_mult * 2)
            self.exp_value = 28
            self.color = (80, 220, 180)   # Зелено-бирюзовый — Элита
            self.size = 16
            self.shape = EnemyShape.TRIANGLE
            self.preferred_range = 400
            self.shoot_cooldown = 0
            self.shoot_interval = 3000
            self.piercing_shot = True
        elif enemy_type == "mortar":
            self.max_hp = int(70 * difficulty_mult)
            self.speed = 0.6 + difficulty_mult * 0.05
            self.dmg = 22 + int(difficulty_mult * 3)
            self.exp_value = 40
            self.color = (120, 80, 200)   # Тёмно-синий — Командиры
            self.size = 28
            self.shape = EnemyShape.SQUARE
            self.preferred_range = 500
            self.shoot_cooldown = 0
            self.shoot_interval = 3500
        elif enemy_type == "shielder":
            # Щитоносец — теперь со своим щитом!
            self.max_hp = int(200 * difficulty_mult)
            self.speed = 1.0 + difficulty_mult * 0.1
            self.dmg = 8 + int(difficulty_mult * 1.5)
            self.exp_value = 60
            self.color = (80, 200, 255)   # Голубой — Командиры
            self.size = 35
            self.shape = EnemyShape.HEXAGON
            self.aura_radius = 220
            self.aura_timer = 0
            # Персональный щит щитоносца
            self.personal_shield = int(100 * difficulty_mult)
            self.max_personal_shield = self.personal_shield
        elif enemy_type == "healer":
            # Хилер: лечит союзников в ауре каждые 2 сек
            self.max_hp = int(65 * difficulty_mult)
            self.speed = 1.8 + difficulty_mult * 0.15
            self.dmg = 6 + int(difficulty_mult * 1)
            self.exp_value = 50
            self.color = (50, 220, 100)   # Зелёный — Поддержка
            self.size = 22
            self.shape = EnemyShape.CIRCLE
            self.heal_radius = 200
            self.heal_timer = 0
            self.heal_interval = 2000
            self.heal_amount = int(8 * difficulty_mult)
        elif enemy_type == "buffer":
            # Усилитель: даёт союзникам +40% к скорости и урону
            self.max_hp = int(55 * difficulty_mult)
            self.speed = 1.5 + difficulty_mult * 0.1
            self.dmg = 5 + int(difficulty_mult * 0.8)
            self.exp_value = 55
            self.color = (220, 200, 50)   # Жёлтый — Поддержка
            self.size = 20
            self.shape = EnemyShape.DIAMOND
            self.buff_radius = 180
            self.buff_timer = 0
            self.buff_interval = 3000
            self.buff_active = False
        else:
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
        # Бафф от щитоносца (накапливается извне)
        self.shield_buff = 0
        # Бафф от усилителя (скорость)
        self.speed_buff_timer = 0
    
    def take_damage(self, dmg: int) -> bool:
        # Персональный щит щитоносца (сначала)
        if self.type == "shielder" and hasattr(self, 'personal_shield') and self.personal_shield > 0:
            absorbed = min(self.personal_shield, dmg)
            dmg -= absorbed
            self.personal_shield -= absorbed
            if dmg <= 0:
                self.hit_flash = 100
                return False
        # Щит от Щитоносца-союзника поглощает часть урона
        if hasattr(self, 'shield_buff') and self.shield_buff > 0:
            absorbed = min(self.shield_buff, dmg)
            dmg -= absorbed
            self.shield_buff -= absorbed
        # Броня танка
        if hasattr(self, 'damage_reduction') and self.damage_reduction > 0 and dmg > 0:
            dmg = max(1, int(dmg * (1.0 - self.damage_reduction)))
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
            # --- Берсерк-режим при <40% HP ---
            if self.type == "bruiser" and not self.berserk_triggered and self.hp < self.max_hp * 0.4:
                self.berserk_triggered = True
                self.speed = self.base_speed * 1.8
                self.dmg = int(self.dmg * 1.5)
                self.color = (240, 60, 40)  # Красный берсерк
            
            # --- Фазирование призрака ---
            if self.type == "ghost":
                self.phase_timer += dt * 1000
                if not self.is_phasing and self.phase_timer >= self.phase_interval:
                    self.is_phasing = True
                    self.phase_timer = 0
                elif self.is_phasing and self.phase_timer >= self.phase_duration:
                    self.is_phasing = False
                    self.phase_timer = 0
            
            # --- Бафф скорости от усилителя ---
            if self.speed_buff_timer > 0:
                self.speed_buff_timer -= dt * 1000
            
            # Особое поведение дальнобойных врагов
            if self.type in ("ranger", "mortar", "sniper", "lancer") and target_pos:
                pref_range = getattr(self, 'preferred_range', 300)
                direction = target_pos - self.pos
                dist = direction.length()
                if dist > pref_range + 40:
                    self.pos += direction.normalize() * self.speed
                elif dist < pref_range - 40:
                    self.pos -= direction.normalize() * self.speed
            elif target_pos:
                direction = target_pos - self.pos
                if direction.length() > 0:
                    self.pos += direction.normalize() * self.speed
        
        # Обновляем кулдаун стрельбы дальнобойных
        if self.type in ("ranger", "mortar", "sniper", "lancer"):
            if hasattr(self, 'shoot_cooldown') and self.shoot_cooldown > 0:
                self.shoot_cooldown -= dt * 1000
        
        # Аура щитоносца
        if self.type == "shielder":
            self.aura_timer = max(0, self.aura_timer - dt * 1000)
        
        # Хилер: таймер исцеления
        if self.type == "healer":
            self.heal_timer = max(0, self.heal_timer - dt * 1000)
        
        # Усилитель: таймер баффа
        if self.type == "buffer":
            self.buff_timer = max(0, self.buff_timer - dt * 1000)
        
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
        
        # Призрак в фазе — полупрозрачный
        if self.type == "ghost" and getattr(self, 'is_phasing', False):
            ghost_surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
            pygame.draw.circle(ghost_surf, (*self.color, 60), 
                             (self.size*1.5, self.size*1.5), self.size)
            surf.blit(ghost_surf, (x - self.size*1.5, y - self.size*1.5))
            return  # Не рисуем обычное тело в фазе
        
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
            # Показываем персональный щит
            if hasattr(self, 'personal_shield') and self.personal_shield > 0:
                shield_ratio = self.personal_shield / max(1, self.max_personal_shield)
                sh_r = self.size + 8
                sh_surf = pygame.Surface((sh_r*2+4, sh_r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(sh_surf, (80, 200, 255, int(80 * shield_ratio)), 
                                 (sh_r+2, sh_r+2), sh_r)
                pygame.draw.circle(sh_surf, (80, 200, 255, 180), (sh_r+2, sh_r+2), sh_r, 3)
                surf.blit(sh_surf, (x - sh_r - 2, y - sh_r - 2))
        
        # Аура Хилера (зелёная)
        if self.type == "healer":
            heal_r = getattr(self, 'heal_radius', 200)
            h_surf = pygame.Surface((heal_r*2+4, heal_r*2+4), pygame.SRCALPHA)
            pulse_a = int(20 + 15 * abs(math.sin(time_ms / 500)))
            pygame.draw.circle(h_surf, (50, 220, 100, pulse_a), (heal_r+2, heal_r+2), heal_r)
            pygame.draw.circle(h_surf, (50, 220, 100, 70), (heal_r+2, heal_r+2), heal_r, 2)
            surf.blit(h_surf, (x - heal_r - 2, y - heal_r - 2))
        
        # Аура Усилителя (жёлтая)
        if self.type == "buffer":
            buff_r = getattr(self, 'buff_radius', 180)
            b_surf = pygame.Surface((buff_r*2+4, buff_r*2+4), pygame.SRCALPHA)
            pulse_a = int(20 + 15 * abs(math.sin(time_ms / 400)))
            pygame.draw.circle(b_surf, (220, 200, 50, pulse_a), (buff_r+2, buff_r+2), buff_r)
            pygame.draw.circle(b_surf, (220, 200, 50, 70), (buff_r+2, buff_r+2), buff_r, 2)
            surf.blit(b_surf, (x - buff_r - 2, y - buff_r - 2))
        
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