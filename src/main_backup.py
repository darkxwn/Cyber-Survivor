import pygame
import random
import math
import sys

from src.core.game import Game
from src.core.config import screen


def main():
    pygame.init()
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

class SaveSystem:
    def __init__(self):
        # Сохранение в папку data/
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "data")
        
        # Создаем папку data если её нет
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        self.save_file = os.path.join(data_dir, "save.json")
        self.data = self.load()
    
    def load(self) -> dict:
        default = self.default_data()
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Объединяем с default для добавления новых полей
                    self._merge_dicts(default, loaded_data)
            except:
                pass
        return default
    
    def _merge_dicts(self, default: dict, loaded: dict):
        """Добавляет отсутствующие ключи из loaded в default"""
        for key, value in loaded.items():
            if key in default and isinstance(value, dict) and isinstance(default[key], dict):
                self._merge_dicts(default[key], value)
            else:
                default[key] = value
    
    def default_data(self) -> dict:
        return {
            "stats": {
                "total_kills": 0,
                "total_playtime": 0,
                "best_score": 0,
                "best_time": 0,
                "max_level": 0,
                "games_played": 0,
                "max_wave": 0
            },
            "modules": {
                "health": 0,
                "damage": 0,
                "speed": 0,
                "fire_rate": 0,
                "crit": 0
            },
            "unlocked_skins": ["default"],
            "current_skin": "default",
            "controls": {
                "up": pygame.K_w,
                "down": pygame.K_s,
                "left": pygame.K_a,
                "right": pygame.K_d,
                "dash": pygame.K_SPACE,
                "auto_fire_toggle": pygame.K_TAB
            },
            "settings": {
                "auto_fire": False,
                "screen_shake": True,
                "particles": True,
                "damage_numbers": True,
                "wave_break_duration": 10  # секунды между волнами (3-30)
            },
            "currency": 0,
            "achievements": {
                "first_blood": False,
                "survivor_10": False,
                "survivor_25": False,
                "killer_100": False,
                "killer_500": False,
                "killer_1000": False,
                "wave_master_5": False,
                "wave_master_10": False,
                "wave_master_20": False,
                "level_expert_10": False,
                "level_expert_20": False,
                "collector": False,
                "spender": False,
                "perfectionist": False,
                "speed_demon": False,
                "tank": False,
                "glass_cannon": False
            }
        }
    
    def save(self):
        with open(self.save_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def update_stats(self, kills, playtime, score, level, wave, count_stats=True):
        if count_stats:  # Только для режима волн
            self.data["stats"]["total_kills"] += kills
            self.data["stats"]["total_playtime"] += playtime
            self.data["stats"]["best_score"] = max(self.data["stats"]["best_score"], score)
            self.data["stats"]["best_time"] = max(self.data["stats"]["best_time"], playtime)
            self.data["stats"]["max_level"] = max(self.data["stats"]["max_level"], level)
            self.data["stats"]["max_wave"] = max(self.data["stats"]["max_wave"], wave)
            self.data["stats"]["games_played"] += 1
        
        # Валюта начисляется всегда
        earned = kills + level * 10 + wave * 20
        self.data["currency"] += earned
        self.save()
        return earned

# ============================================================================
# СИСТЕМА ЧАСТИЦ
# ============================================================================

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

# ============================================================================
# БАЗОВЫЕ ИГРОВЫЕ СУЩНОСТИ
# ============================================================================

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

# ============================================================================
# СИСТЕМА ИГРОКА
# ============================================================================

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

# ============================================================================
# СИСТЕМА ВРАГОВ С РАЗНЫМИ ФОРМАМИ
# ============================================================================

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
        
        # Базовая статистика в зависимости от типа
        if enemy_type == "basic":
            self.max_hp = int(30 * difficulty_mult)
            self.speed = 2.5 + difficulty_mult * 0.3
            self.dmg = 8 + int(difficulty_mult * 2)
            self.exp_value = 10
            self.color = COLORS["enemy"]
            self.size = 20
            self.shape = EnemyShape.CIRCLE
        elif enemy_type == "fast":
            self.max_hp = int(20 * difficulty_mult)
            self.speed = 5.0 + difficulty_mult * 0.5
            self.dmg = 6 + int(difficulty_mult * 1.5)
            self.exp_value = 15
            self.color = (255, 255, 100)
            self.size = 15
            self.shape = EnemyShape.TRIANGLE
        elif enemy_type == "tank":
            self.max_hp = int(100 * difficulty_mult)
            self.speed = 1.5 + difficulty_mult * 0.2
            self.dmg = 15 + int(difficulty_mult * 3)
            self.exp_value = 30
            self.color = COLORS["elite_enemy"]
            self.size = 30
            self.shape = EnemyShape.SQUARE
        elif enemy_type == "boss":
            self.max_hp = int(500 * difficulty_mult)
            self.speed = 2.0 + difficulty_mult * 0.3
            self.dmg = 25 + int(difficulty_mult * 5)
            self.exp_value = 200
            self.color = COLORS["boss"]
            self.size = 50
            self.shape = EnemyShape.HEXAGON
        
        self.hp = self.max_hp
        
        # Поля для эффектов
        self.poison_damage = 0
        self.poison_duration = 0
        self.frozen_duration = 0
        self.chain_lightning_target = False
        self.chain_lightning_timer = 0
        self.explosion_marked = False
    
    def take_damage(self, dmg: int) -> bool:
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
            # Обычное движение
            if target_pos:
                direction = target_pos - self.pos
                if direction.length() > 0:
                    self.pos += direction.normalize() * self.speed
        
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
        
        # HP бар для элитных и боссов
        if self.type in ["tank", "boss"]:
            bar_w = self.size * 2
            bar_h = 5
            bar_x = x - bar_w // 2
            bar_y = y - self.size - 10
            
            pygame.draw.rect(surf, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
            hp_w = int((self.hp / self.max_hp) * bar_w)
            pygame.draw.rect(surf, COLORS["health"], (bar_x, bar_y, hp_w, bar_h))

# ============================================================================
# СИСТЕМА ПУЛЬ
# ============================================================================

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

# ============================================================================
# СИСТЕМА ДОСТИЖЕНИЙ
# ============================================================================

@dataclass
class Achievement:
    id: str
    name: str
    description: str
    check: callable
    reward: int = 50  # Валюта за выполнение
    
    def get_progress(self, engine) -> float:
        """Возвращает прогресс от 0.0 до 1.0"""
        try:
            # Специальная логика прогресса для каждого типа достижения
            if "killer" in self.id:
                target = int(self.id.split("_")[1])
                return min(1.0, engine.kills / target)
            elif "survivor" in self.id:
                target = int(self.id.split("_")[1]) * 60
                return min(1.0, engine.time_survived / target)
            elif "wave_master" in self.id:
                target = int(self.id.split("_")[2]) + 1
                return min(1.0, engine.wave_system.current_wave / target)
            elif "level_expert" in self.id:
                target = int(self.id.split("_")[2])
                return min(1.0, engine.player.level / target)
            elif self.id == "first_blood":
                return 1.0 if engine.kills >= 1 else 0.0
            elif self.id == "collector":
                return min(1.0, engine.save_system.data["currency"] / 1000)
            elif self.id == "spender":
                spent = sum(engine.save_system.data["modules"].values())
                return min(1.0, spent / 25)
            elif self.id == "tank":
                return min(1.0, engine.player.max_hp / 200)
            elif self.id == "speed_demon":
                return min(1.0, engine.player.upgrades.get("speed", 0) / 10)
            elif self.id == "glass_cannon":
                if engine.player.max_hp < 100 and engine.player.dmg >= 50:
                    return 1.0
                return min(1.0, engine.player.dmg / 50)
            else:
                return 1.0 if self.check(engine) else 0.0
        except:
            return 0.0

class AchievementSystem:
    ACHIEVEMENTS = {
        "first_blood": Achievement(
            "first_blood", "Первая кровь", "Убейте первого врага",
            lambda engine: engine.kills >= 1, 25
        ),
        "survivor_10": Achievement(
            "survivor_10", "Выживший", "Продержитесь 10 минут",
            lambda engine: engine.time_survived >= 600, 100
        ),
        "survivor_25": Achievement(
            "survivor_25", "Мастер выживания", "Продержитесь 25 минут",
            lambda engine: engine.time_survived >= 1500, 250
        ),
        "killer_100": Achievement(
            "killer_100", "Убийца", "Убейте 100 врагов за игру",
            lambda engine: engine.kills >= 100, 100
        ),
        "killer_500": Achievement(
            "killer_500", "Серийный убийца", "Убейте 500 врагов за игру",
            lambda engine: engine.kills >= 500, 250
        ),
        "killer_1000": Achievement(
            "killer_1000", "Геноцид", "Убейте 1000 врагов за игру",
            lambda engine: engine.kills >= 1000, 500
        ),
        "wave_master_5": Achievement(
            "wave_master_5", "Воин волн", "Пройдите 5 волн",
            lambda engine: engine.wave_system.current_wave >= 6, 100
        ),
        "wave_master_10": Achievement(
            "wave_master_10", "Мастер волн", "Пройдите 10 волн",
            lambda engine: engine.wave_system.current_wave >= 11, 200
        ),
        "wave_master_20": Achievement(
            "wave_master_20", "Легенда волн", "Пройдите 20 волн",
            lambda engine: engine.wave_system.current_wave >= 21, 500
        ),
        "level_expert_10": Achievement(
            "level_expert_10", "Эксперт", "Достигните 10 уровня",
            lambda engine: engine.player.level >= 10, 150
        ),
        "level_expert_20": Achievement(
            "level_expert_20", "Легенда", "Достигните 20 уровня",
            lambda engine: engine.player.level >= 20, 300
        ),
        "collector": Achievement(
            "collector", "Коллекционер", "Накопите 1000 валюты",
            lambda engine: engine.save_system.data["currency"] >= 1000, 200
        ),
        "spender": Achievement(
            "spender", "Транжира", "Потратьте 500 валюты на модули",
            lambda engine: sum(engine.save_system.data["modules"].values()) >= 25, 150
        ),
        "perfectionist": Achievement(
            "perfectionist", "Перфекционист", "Пройдите волну без получения урона",
            lambda engine: hasattr(engine, 'no_damage_wave') and engine.no_damage_wave, 300
        ),
        "speed_demon": Achievement(
            "speed_demon", "Демон скорости", "Наберите 10+ к скорости",
            lambda engine: engine.player.upgrades.get("speed", 0) >= 10, 200
        ),
        "tank": Achievement(
            "tank", "Танк", "Наберите 200+ HP",
            lambda engine: engine.player.max_hp >= 200, 150
        ),
        "glass_cannon": Achievement(
            "glass_cannon", "Стеклянная пушка", "Имейте 50+ урона при <100 HP",
            lambda engine: engine.player.dmg >= 50 and engine.player.max_hp < 100, 250
        ),
    }
    
    @staticmethod
    def check_achievements(engine, save_system):
        """Проверяет и разблокирует достижения"""
        newly_unlocked = []
        total_reward = 0
        
        for ach_id, achievement in AchievementSystem.ACHIEVEMENTS.items():
            if not save_system.data["achievements"].get(ach_id, False):
                try:
                    if achievement.check(engine):
                        save_system.data["achievements"][ach_id] = True
                        save_system.data["currency"] += achievement.reward
                        total_reward += achievement.reward
                        newly_unlocked.append(achievement)
                except:
                    pass
        
        if newly_unlocked:
            save_system.save()
        
        return newly_unlocked, total_reward

# ============================================================================
# СИСТЕМА ВОЛН
# ============================================================================

class WaveSystem:
    def __init__(self, break_duration: int = 10, endless_mode: bool = False):
        self.current_wave = 1
        self.enemies_in_wave = 0
        self.enemies_spawned = 0
        self.wave_active = endless_mode  # В endless режиме сразу активна
        self.wave_break_time = 0
        self.break_duration = break_duration  # секунд между волнами (настраиваемый)
        self.endless_mode = endless_mode  # Бесконечный режим
    
    def start_wave(self):
        self.wave_active = True
        if not self.endless_mode:
            self.enemies_in_wave = 10 + self.current_wave * 5
            self.enemies_spawned = 0
    
    def should_spawn_enemy(self) -> bool:
        if self.endless_mode:
            return True  # В бесконечном режиме всегда спавним
        if not self.wave_active:
            return False
        if self.enemies_spawned >= self.enemies_in_wave:
            return False
        return True
    
    def enemy_spawned(self):
        if not self.endless_mode:
            self.enemies_spawned += 1
    
    def get_difficulty(self) -> float:
        if self.endless_mode:
            # В бесконечном режиме сложность растет плавнее
            return 1.0 + (self.current_wave - 1) * 0.08
        return 1.0 + (self.current_wave - 1) * 0.15
    
    def wave_complete(self):
        if self.endless_mode:
            return  # В бесконечном режиме волны не завершаются
        self.wave_active = False
        self.wave_break_time = self.break_duration
        self.current_wave += 1
    
    def update_break(self, dt: float) -> bool:
        """Возвращает True если перерыв закончился"""
        if self.wave_break_time > 0:
            self.wave_break_time -= dt
            if self.wave_break_time <= 0:
                return True
        return False

# ============================================================================
# ИГРОВЫЕ СПОСОБНОСТИ (ПЕРКИ)
# ============================================================================

@dataclass
class PerkOption:
    id: str
    name: str
    description: str
    icon: str
    rarity: str

class PerkManager:
    # Одноразовые перки (выдаются только один раз)
    ONE_TIME_PERKS = {
        "orbital", "explosion", "freeze", "poison", "chain", 
        "reflect", "thorns", "heal"
    }
    
    @staticmethod
    def get_available_perks(player: 'Player' = None) -> List[PerkOption]:
        all_perks = [
            # ===== БАЗОВЫЕ ХАРАКТЕРИСТИКИ =====
            PerkOption("hp", "+25 MAX HP", "Увеличивает максимальное здоровье", "[+]", "common"),
            PerkOption("hp_big", "+50 MAX HP", "Значительно увеличивает здоровье", "[++]", "uncommon"),
            PerkOption("dmg", "+5 УРОН", "Увеличивает урон от пуль", "[!]", "common"),
            PerkOption("dmg_big", "+15 УРОН", "Значительно увеличивает урон", "[!!]", "uncommon"),
            PerkOption("fire_rate", "+15% СКОРОСТРЕЛЬНОСТЬ", "Стреляйте быстрее", "[>>]", "common"),
            PerkOption("fire_rate_big", "+30% СКОРОСТРЕЛЬНОСТЬ", "Стреляйте намного быстрее", "[>>>]", "rare"),
            PerkOption("speed", "+10% СКОРОСТЬ", "Двигайтесь быстрее", "[>]", "common"),
            PerkOption("speed_big", "+25% СКОРОСТЬ", "Значительно увеличивает скорость", "[>>]", "uncommon"),
            
            # ===== КРИТЫ И МНОЖИТЕЛИ =====
            PerkOption("crit", "+5% КРИТ ШАНС", "Больше критических ударов", "[*]", "uncommon"),
            PerkOption("crit_big", "+15% КРИТ ШАНС", "Намного больше критов", "[**]", "rare"),
            PerkOption("crit_damage", "+50% КРИТ УРОН", "Критические удары сильнее", "[***]", "epic"),
            
            # ===== ВЫСТРЕЛЫ И ПРОБИТИЕ =====
            PerkOption("multishot", "+1 ВЫСТРЕЛ", "Стреляйте несколькими пулями", "[|||]", "rare"),
            PerkOption("multishot_big", "+3 ВЫСТРЕЛА", "Массированный огонь", "[|||||]", "epic"),
            PerkOption("piercing", "+1 ПРОБИТИЕ", "Пули пробивают врагов", "[->]", "uncommon"),
            PerkOption("piercing_big", "+3 ПРОБИТИЕ", "Пули пробивают много врагов", "[->>]", "rare"),
            
            # ===== ЗАЩИТА И ВЫЖИВАНИЕ =====
            PerkOption("shield", "+50 ЩИТ", "Дополнительная защита", "[#]", "common"),
            PerkOption("shield_big", "+100 ЩИТ", "Мощный щит", "[##]", "uncommon"),
            PerkOption("lifesteal", "+10% ВАМПИРИЗМ", "Восстанавливайте HP от урона", "[<3]", "uncommon"),
            PerkOption("lifesteal_big", "+25% ВАМПИРИЗМ", "Сильный вампиризм", "[<3<3]", "rare"),
            PerkOption("regen", "РЕГЕНЕРАЦИЯ +1 HP/сек", "Постоянно восстанавливает здоровье", "[+~]", "rare"),
            PerkOption("armor", "+20% БРОНЯ", "Уменьшает получаемый урон", "[[]", "epic"),
            
            # ===== МОДИФИКАТОРЫ ПУЛЬ =====
            PerkOption("bullet_size", "+50% РАЗМЕР ПУЛЬ", "Больше пули = легче попасть", "[O]", "common"),
            PerkOption("bullet_speed", "+30% СКОРОСТЬ ПУЛЬ", "Пули летят быстрее", "[=>]", "common"),
            PerkOption("bullet_lifetime", "+50% ДАЛЬНОСТЬ", "Пули летят дальше", "[==>]", "common"),
            
            # ===== ОПЫТ И ПРОГРЕССИЯ =====
            PerkOption("exp_magnet", "МАГНИТ +50%", "Притягивайте опыт издалека", "[<*>]", "uncommon"),
            PerkOption("exp_boost", "БОНУС К ОПЫТУ +25%", "Получайте больше опыта", "[XP+]", "uncommon"),
            PerkOption("exp_multiplier", "МНОЖИТЕЛЬ ОПЫТА x2", "Удваивает получаемый опыт", "[XP*2]", "rare"),
            PerkOption("gold_boost", "+50% ВАЛЮТА", "Получайте больше валюты", "[$+]", "uncommon"),
            
            # ===== ОСОБЫЕ СПОСОБНОСТИ =====
            PerkOption("dash_cooldown", "-30% ПЕРЕЗАРЯДКА DASH", "Чаще используйте рывок", "[<-]", "rare"),
            PerkOption("dash_invuln", "+50% НЕУЯЗВИМОСТЬ DASH", "Дольше неуязвимы при рывке", "[<*-]", "rare"),
            
            # ===== УЛЬТЫ И ЛЕГЕНДАРНЫЕ (ОДНОРАЗОВЫЕ) =====
            PerkOption("heal", "ПОЛНОЕ ВОССТАНОВЛЕНИЕ", "Восстанавливает все HP и щит", "[HEAL]", "epic"),
            PerkOption("orbital", "ОРБИТАЛЬНАЯ ЗАЩИТА", "Пули вращаются вокруг вас", "[ORB]", "legendary"),
            PerkOption("explosion", "ВЗРЫВНЫЕ ПУЛИ", "Пули взрываются при попадании", "[BOOM]", "legendary"),
            PerkOption("freeze", "ЗАМОРАЖИВАНИЕ", "Замедляют врагов на 50%", "[ICE]", "legendary"),
            PerkOption("poison", "ЯДОВИТЫЕ ПУЛИ", "Наносят урон со временем", "[POISON]", "legendary"),
            PerkOption("chain", "ЦЕПНАЯ МОЛНИЯ", "Урон перескакивает на врагов", "[CHAIN]", "legendary"),
            PerkOption("reflect", "ОТРАЖЕНИЕ", "Отражает 25% урона", "[REFLECT]", "legendary"),
            PerkOption("thorns", "ШИПЫ", "Враги получают урон при атаке", "[THORNS]", "legendary"),
        ]
        
        # Фильтруем одноразовые перки, которые уже взяты
        if player and hasattr(player, 'acquired_perks'):
            all_perks = [p for p in all_perks if p.id not in player.acquired_perks or p.id not in PerkManager.ONE_TIME_PERKS]
        
        return random.sample(all_perks, min(3, len(all_perks)))
    
    @staticmethod
    def apply_perk(player: Player, perk_id: str):
        # Добавляем в список приобретенных
        if hasattr(player, 'acquired_perks'):
            player.acquired_perks.add(perk_id)
        
        # ===== БАЗОВЫЕ ХАРАКТЕРИСТИКИ =====
        if perk_id == "hp":
            player.max_hp += 25
            player.hp += 25
            player.upgrades["max_hp"] += 1
        elif perk_id == "hp_big":
            player.max_hp += 50
            player.hp += 50
            player.upgrades["max_hp"] += 2
        elif perk_id == "dmg":
            player.dmg += 5
            player.upgrades["dmg"] += 1
        elif perk_id == "dmg_big":
            player.dmg += 15
            player.upgrades["dmg"] += 3
        elif perk_id == "fire_rate":
            player.fire_rate = max(50, int(player.fire_rate * 0.85))
            player.upgrades["fire_rate"] += 1
        elif perk_id == "fire_rate_big":
            player.fire_rate = max(50, int(player.fire_rate * 0.70))
            player.upgrades["fire_rate"] += 3
        elif perk_id == "speed":
            player.speed *= 1.1
            player.upgrades["speed"] += 1
        elif perk_id == "speed_big":
            player.speed *= 1.25
            player.upgrades["speed"] += 2
        
        # ===== КРИТЫ =====
        elif perk_id == "crit":
            player.crit_chance = min(0.95, player.crit_chance + 0.05)
            player.upgrades["crit_chance"] += 1
        elif perk_id == "crit_big":
            player.crit_chance = min(0.95, player.crit_chance + 0.15)
            player.upgrades["crit_chance"] += 3
        elif perk_id == "crit_damage":
            player.crit_multiplier += 0.5
        
        # ===== ВЫСТРЕЛЫ =====
        elif perk_id == "multishot":
            player.multishot += 1
            player.upgrades["multishot"] += 1
        elif perk_id == "multishot_big":
            player.multishot += 3
            player.upgrades["multishot"] += 3
        elif perk_id == "piercing":
            player.piercing += 1
            player.upgrades["piercing"] += 1
        elif perk_id == "piercing_big":
            player.piercing += 3
            player.upgrades["piercing"] += 3
        
        # ===== ЗАЩИТА =====
        elif perk_id == "shield":
            player.add_shield(50)
            player.upgrades["shield"] += 1
        elif perk_id == "shield_big":
            player.add_shield(100)
            player.upgrades["shield"] += 2
        elif perk_id == "lifesteal":
            player.lifesteal += 0.1
            player.upgrades["lifesteal"] += 1
        elif perk_id == "lifesteal_big":
            player.lifesteal += 0.25
            player.upgrades["lifesteal"] += 2
        elif perk_id == "regen":
            if not hasattr(player, 'regen'):
                player.regen = 0
            player.regen += 1
        elif perk_id == "armor":
            if not hasattr(player, 'armor'):
                player.armor = 0
            player.armor = min(0.75, player.armor + 0.2)
        
        # ===== МОДИФИКАТОРЫ ПУЛЬ =====
        elif perk_id == "bullet_size":
            player.bullet_size *= 1.5
        elif perk_id == "bullet_speed":
            player.bullet_speed *= 1.3
        elif perk_id == "bullet_lifetime":
            player.bullet_lifetime *= 1.5
        
        # ===== ОПЫТ =====
        elif perk_id == "exp_magnet":
            if not hasattr(player, 'exp_magnet_radius'):
                player.exp_magnet_radius = 100
            player.exp_magnet_radius *= 1.5
        elif perk_id == "exp_boost":
            if not hasattr(player, 'exp_multiplier'):
                player.exp_multiplier = 1.0
            player.exp_multiplier *= 1.25
        elif perk_id == "exp_multiplier":
            # Новый перк - удваивает опыт
            if not hasattr(player, 'exp_multiplier'):
                player.exp_multiplier = 1.0
            player.exp_multiplier *= 2.0
        elif perk_id == "gold_boost":
            if not hasattr(player, 'gold_multiplier'):
                player.gold_multiplier = 1.0
            player.gold_multiplier *= 1.5
        
        # ===== СПОСОБНОСТИ =====
        elif perk_id == "dash_cooldown":
            if not hasattr(player, 'dash_cooldown_mult'):
                player.dash_cooldown_mult = 1.0
            player.dash_cooldown_mult *= 0.7
        elif perk_id == "dash_invuln":
            if not hasattr(player, 'dash_invuln_duration'):
                player.dash_invuln_duration = 200
            player.dash_invuln_duration *= 1.5
        
        # ===== УЛЬТЫ =====
        elif perk_id == "heal":
            player.hp = player.max_hp
            player.shield = player.max_shield
        elif perk_id == "orbital":
            if not hasattr(player, 'orbital_bullets'):
                player.orbital_bullets = 0
            player.orbital_bullets += 3
        elif perk_id == "explosion":
            player.explosive_bullets = True
        elif perk_id == "freeze":
            player.freeze_bullets = True
        elif perk_id == "poison":
            player.poison_bullets = True
        elif perk_id == "chain":
            if not hasattr(player, 'chain_lightning'):
                player.chain_lightning = 0
            player.chain_lightning += 2
        elif perk_id == "reflect":
            if not hasattr(player, 'reflect_damage'):
                player.reflect_damage = 0
            player.reflect_damage = min(0.5, player.reflect_damage + 0.25)
        elif perk_id == "thorns":
            if not hasattr(player, 'thorns_damage'):
                player.thorns_damage = 0
            player.thorns_damage += 10

# ============================================================================
# ИГРОВОЙ ДВИЖОК
# ============================================================================

# ============================================================================
# МЕНЕДЖЕР ЗВУКОВ И МУЗЫКИ
# ============================================================================

class SoundManager:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
        except:
            self.enabled = False
            print("Звуковая система недоступна")
            return
        
        self.sounds = {}
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        self.music_enabled = True
        self.sfx_enabled = True
        
        self.load_sounds()
    
    def load_sounds(self):
        sound_dir = os.path.join(os.path.dirname(__file__), "assets", "sounds")
        if not os.path.exists(sound_dir):
            return
        
        # Звуковые эффекты
        sfx_files = {
            "shoot": ["shoot.wav"],
            "enemy_hit": ["enemy_hit.wav"],
            "enemy_death": ["enemy_death.wav"],
            "player_hit": ["player_hit.wav"],
            "level_up": ["level_up.wav"],
            "button_click": ["button_click.wav"],
            "dash": ["dash.wav"],
            "powerup": ["powerup.wav"],
            "explosion": ["explosion.wav"],
            "shield_hit": ["shield_hit.wav"],
        }
        
        for key, files in sfx_files.items():
            self.sounds[key] = []
            for filename in files:
                try:
                    path = os.path.join(sound_dir, filename)
                    if os.path.exists(path):
                        sound = pygame.mixer.Sound(path)
                        self.sounds[key].append(sound)
                except Exception as e:
                    pass  # Игнорируем ошибки загрузки отдельных звуков
    
    def play_sound(self, sound_name):
        if not self.enabled or not self.sfx_enabled:
            return
        
        if sound_name in self.sounds and self.sounds[sound_name]:
            sound = random.choice(self.sounds[sound_name])
            sound.set_volume(self.sfx_volume)
            channel = sound.play()
            return channel
    
    def play_music(self, music_name, loop=-1):
        if not self.enabled or not self.music_enabled:
            return
        
        music_dir = os.path.join(os.path.dirname(__file__), "assets", "sounds")
        music_path = os.path.join(music_dir, music_name)
        
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(loop)
            except Exception as e:
                pass  # Игнорируем ошибки загрузки музыки
    
    def stop_music(self):
        if self.enabled:
            pygame.mixer.music.stop()
    
    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        if self.enabled:
            pygame.mixer.music.set_volume(self.music_volume)
    
    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, volume))
    
    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_music()
    
    def toggle_sfx(self):
        self.sfx_enabled = not self.sfx_enabled

# ============================================================================
# ИГРОВОЙ ДВИЖОК
# ============================================================================

class Engine:
    def __init__(self):
        pygame.display.set_caption("CYBER SURVIVOR - REFACTORED")
        self.clock = pygame.time.Clock()
        self.dt = 0
        
        self.save_system = SaveSystem()
        
        # Звуки и музыка
        self.sound_manager = SoundManager()
        
        # Скрываем системный курсор
        pygame.mouse.set_visible(False)
        self.cursor_size = 20
        
        # Загрузка иконок
        self.icons = {}
        self.load_icons()
        
        # Шрифты
        self.font_huge = pygame.font.Font(None, 120)
        self.font_large = pygame.font.Font(None, 80)
        self.font_medium = pygame.font.Font(None, 52)
        self.font_small = pygame.font.Font(None, 36)
        self.font_tiny = pygame.font.Font(None, 28)
        
        self.state = GameState.MENU
        self.menu_page = "main"
        self.game_mode = GameMode.WAVES  # По умолчанию режим волн
        
        self.reset_game()
        
        # UI состояния
        self.pause_click_handled = False
        self.level_up_click_handled = False
        self.rebinding_key = None
        self.achievements_scroll_offset = 0  # Прокрутка для меню достижений
        self.show_stats_reset_confirmation = False  # Подтверждение сброса статистики
        
        # Анимации меню (5 & 6)
        self.menu_time = 0
        self.button_press_effect = {}  # {button_id: time_pressed}
        self.menu_particles = []  # Динамические частицы фона
        
        # Система волн
        wave_break = self.save_system.data["settings"].get("wave_break_duration", 10)
        endless_mode = (self.game_mode == GameMode.ENDLESS)
        self.wave_system = WaveSystem(wave_break, endless_mode)
        
        # Запуск музыки в меню
        self.sound_manager.play_music("menu_theme.ogg")
    
    def load_icons(self):
        """Загрузка иконок из assets/icons"""
        icon_dir = os.path.join(os.path.dirname(__file__), "assets", "icons")
        
        if not os.path.exists(icon_dir):
            return  # Если папки нет, работаем без иконок
        
        icon_files = {
            # Главное меню
            "play": "play.png",
            "achievements": "achievements.png",
            "modules": "modules.png",
            "skins": "skins.png",
            "settings": "settings.png",
            "stats": "stats.png",
            "exit": "exit.png",
            
            # Модули
            "health": "health.png",
            "damage": "damage.png",
            "speed": "speed.png",
            "firerate": "firerate.png",
            "crit": "crit.png",
            
            # Управление
            "arrow_up": "arrow_up.png",
            "arrow_down": "arrow_down.png",
            "arrow_left": "arrow_left.png",
            "arrow_right": "arrow_right.png",
            "dash": "dash.png",
            "autofire": "autofire.png",
            
            # Режимы
            "waves": "waves.png",
            "endless": "endless.png",
            
            # Статистика
            "games": "games.png",
            "kills": "kills.png",
            "time": "time.png",
            "score": "score.png",
            "besttime": "besttime.png",
            "level": "level.png",
            "wave": "wave.png",
            
            # Дополнительно
            "currency": "currency.png",
            "lock": "lock.png",
        }
        
        for key, filename in icon_files.items():
            try:
                path = os.path.join(icon_dir, filename)
                if os.path.exists(path):
                    icon = pygame.image.load(path).convert_alpha()
                    icon = pygame.transform.scale(icon, (48, 48))  # Стандартный размер
                    self.icons[key] = icon
            except Exception as e:
                pass  # Игнорируем ошибки загрузки отдельных иконок
    
    def draw_icon(self, icon_name, x, y, size=48):
        """Отрисовка иконки если есть, иначе возвращает False"""
        if icon_name in self.icons:
            icon = self.icons[icon_name]
            if icon.get_width() != size:
                icon = pygame.transform.scale(icon, (size, size))
            screen.blit(icon, (x - size // 2, y - size // 2))
            return True
        return False
    
    def draw_cursor(self):
        """Кастомный курсор-прицел"""
        mouse_pos = pygame.mouse.get_pos()
        x, y = mouse_pos
        
        # Внешний круг (прицел)
        pygame.draw.circle(screen, COLORS["player"], (x, y), self.cursor_size, 2)
        
        # Внутренний круг
        pygame.draw.circle(screen, COLORS["player"], (x, y), 3)
        
        # Крестик
        line_length = self.cursor_size + 5
        pygame.draw.line(screen, COLORS["player"], (x - line_length, y), (x - self.cursor_size - 2, y), 2)
        pygame.draw.line(screen, COLORS["player"], (x + self.cursor_size + 2, y), (x + line_length, y), 2)
        pygame.draw.line(screen, COLORS["player"], (x, y - line_length), (x, y - self.cursor_size - 2), 2)
        pygame.draw.line(screen, COLORS["player"], (x, y + self.cursor_size + 2), (x, y + line_length), 2)
    
    def reset_game(self):
        modules = self.save_system.data["modules"]
        skin = self.save_system.data["current_skin"]
        self.player = Player(modules, skin)
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []
        self.exp_gems: List[pygame.Vector2] = []
        self.particle_system = ParticleSystem()
        
        self.cam = pygame.Vector2(0, 0)
        self.score = 0
        self.kills = 0
        self.time_survived = 0
        
        self.last_enemy_spawn = 0
        self.spawn_rate = 1000
        
        # Сброс системы волн
        wave_break = self.save_system.data["settings"].get("wave_break_duration", 10)
        endless_mode = (self.game_mode == GameMode.ENDLESS)
        self.wave_system = WaveSystem(wave_break, endless_mode)
        self.wave_system.start_wave()
        
        # Перки для level up
        if hasattr(self, 'current_perks'):
            delattr(self, 'current_perks')
    
    def update_player_input(self):
        keys = pygame.key.get_pressed()
        controls = self.save_system.data["controls"]
        
        move = pygame.Vector2(0, 0)
        if keys[controls["left"]]:
            move.x -= 1
        if keys[controls["right"]]:
            move.x += 1
        if keys[controls["up"]]:
            move.y -= 1
        if keys[controls["down"]]:
            move.y += 1
        
        if move.length() > 0:
            self.player.pos += move.normalize() * self.player.speed
        
        self.player.pos += self.player.velocity
        
        # Dash
        if keys[controls["dash"]]:
            if self.player.dash(move):
                self.particle_system.emit(self.player.pos, 20, self.player.color, (5, 12))
                # Звук дэша
                self.sound_manager.play_sound("dash")
    
    def update_shooting(self):
        auto_fire = self.save_system.data["settings"]["auto_fire"]
        
        # Автострельба или зажатие ЛКМ
        should_shoot = False
        if auto_fire:
            # При автострельбе стреляем всегда
            should_shoot = True
        else:
            # При ручной стрельбе только при зажатой ЛКМ
            should_shoot = pygame.mouse.get_pressed()[0]
        
        if should_shoot:
            now = pygame.time.get_ticks()
            if now - self.player.last_shot > self.player.fire_rate:
                self.player.last_shot = now
                
                m_pos = pygame.mouse.get_pos()
                rel = pygame.Vector2(m_pos) - (self.player.pos + self.cam)
                if rel.length() > 0:
                    base_angle = math.degrees(math.atan2(rel.y, rel.x))
                    
                    spread = 15 if self.player.multishot > 1 else 0
                    start_angle = base_angle - (spread * (self.player.multishot - 1) / 2)
                    
                    for i in range(self.player.multishot):
                        angle = start_angle + i * spread
                        is_crit = random.random() < self.player.crit_chance
                        dmg = int(self.player.dmg * (self.player.crit_multiplier if is_crit else 1))
                        
                        self.bullets.append(Bullet(
                            self.player.pos, angle, self.player.bullet_speed,
                            dmg, self.player.piercing, self.player.bullet_size,
                            self.player.bullet_lifetime, is_crit
                        ))
                    
                    # Звук выстрела
                    self.sound_manager.play_sound("shoot")
    
    def spawn_enemies(self):
        if not self.wave_system.should_spawn_enemy():
            return
        
        now = pygame.time.get_ticks()
        difficulty = self.wave_system.get_difficulty()
        
        if now - self.last_enemy_spawn > self.spawn_rate / difficulty:
            self.last_enemy_spawn = now
            
            angle = random.uniform(0, math.tau)
            distance = random.uniform(800, 1200)
            spawn_pos = self.player.pos + pygame.Vector2(
                math.cos(angle) * distance,
                math.sin(angle) * distance
            )
            
            # Типы врагов зависят от волны или времени (endless)
            rand = random.random()
            
            if self.game_mode == GameMode.ENDLESS:
                # В бесконечном режиме используем время
                time_elapsed = self.time_survived
                
                if time_elapsed < 60:  # Первая минута
                    enemy_type = "basic"
                elif time_elapsed < 120:  # 1-2 минуты
                    enemy_type = "basic" if rand < 0.65 else "fast"
                elif time_elapsed < 180:  # 2-3 минуты
                    if rand < 0.45:
                        enemy_type = "basic"
                    elif rand < 0.80:
                        enemy_type = "fast"
                    else:
                        enemy_type = "tank"
                elif time_elapsed < 300:  # 3-5 минут
                    if rand < 0.30:
                        enemy_type = "basic"
                    elif rand < 0.65:
                        enemy_type = "fast"
                    elif rand < 0.92:
                        enemy_type = "tank"
                    else:
                        enemy_type = "boss"
                else:  # После 5 минут
                    if rand < 0.20:
                        enemy_type = "basic"
                    elif rand < 0.50:
                        enemy_type = "fast"
                    elif rand < 0.85:
                        enemy_type = "tank"
                    else:
                        enemy_type = "boss"
            else:
                # Режим волн
                wave_num = self.wave_system.current_wave
                
                if wave_num <= 2:
                    enemy_type = "basic"
                elif wave_num <= 5:
                    enemy_type = "basic" if rand < 0.7 else "fast"
                elif wave_num <= 10:
                    if rand < 0.5:
                        enemy_type = "basic"
                    elif rand < 0.8:
                        enemy_type = "fast"
                    else:
                        enemy_type = "tank"
                else:
                    if rand < 0.4:
                        enemy_type = "basic"
                    elif rand < 0.7:
                        enemy_type = "fast"
                    elif rand < 0.95:
                        enemy_type = "tank"
                    else:
                        enemy_type = "boss"
            
            self.enemies.append(Enemy(spawn_pos, enemy_type, difficulty))
            self.wave_system.enemy_spawned()
    
    def update_combat(self):
        # Пули попадают во врагов (оптимизация: проверяем квадрат расстояния)
        for bullet in self.bullets[:]:
            hit_count = 0
            bullet_pos = bullet.pos
            collision_dist_sq = (bullet.size * 4) ** 2  # Квадрат расстояния
            
            for enemy in self.enemies[:]:
                # Оптимизация: сначала проверяем квадрат расстояния (без sqrt)
                dx = bullet_pos.x - enemy.pos.x
                dy = bullet_pos.y - enemy.pos.y
                dist_sq = dx * dx + dy * dy
                required_dist_sq = (enemy.size + bullet.size * 4) ** 2
                
                if dist_sq < required_dist_sq:
                    if enemy.take_damage(bullet.dmg):
                        self.particle_system.emit(enemy.pos, 15, enemy.color)
                        self.exp_gems.append(pygame.Vector2(enemy.pos))
                        self.enemies.remove(enemy)
                        self.kills += 1
                        self.score += enemy.exp_value
                        
                        # Звук смерти врага (не каждый раз для оптимизации)
                        if random.random() < 0.3:  # 30% шанс звука
                            self.sound_manager.play_sound("enemy_death")
                        
                        # Вампиризм
                        if self.player.lifesteal > 0:
                            heal = int(bullet.dmg * self.player.lifesteal)
                            self.player.heal(heal)
                    else:
                        # Звук попадания (не каждый раз)
                        if random.random() < 0.2:  # 20% шанс звука
                            self.sound_manager.play_sound("enemy_hit")
                        
                        # ====== ПРИМЕНЕНИЕ ЭФФЕКТОВ ======
                        # Яд
                        if hasattr(self.player, 'poison_bullets') and self.player.poison_bullets:
                            enemy.poison_damage = 5  # урон в секунду
                            enemy.poison_duration = 3000  # миллисекунды
                        
                        # Заморозка
                        if hasattr(self.player, 'freeze_bullets') and self.player.freeze_bullets:
                            enemy.frozen_duration = 2000  # миллисекунды
                        
                        # Цепная молния
                        if hasattr(self.player, 'chain_lightning') and self.player.chain_lightning > 0:
                            # Находим ближайших врагов для цепи
                            chain_targets = []
                            for other in self.enemies:
                                if other != enemy and (other.pos - enemy.pos).length() < 300:
                                    chain_targets.append(other)
                            
                            # Бьем до N ближайших врагов
                            chain_targets.sort(key=lambda e: (e.pos - enemy.pos).length())
                            for i, target in enumerate(chain_targets[:self.player.chain_lightning]):
                                target.take_damage(int(bullet.dmg * 0.5))  # 50% урона
                                target.chain_lightning_target = True
                                target.chain_lightning_timer = 500  # миллисекунды
                        
                        # Взрыв
                        if hasattr(self.player, 'explosive_bullets') and self.player.explosive_bullets:
                            # Взрыв при смерти врага - маркируем врага
                            enemy.explosion_marked = True
                    
                    hit_count += 1
                    if hit_count > bullet.piercing:
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break
        
        # Враги атакуют игрока (оптимизация)
        player_pos = self.player.pos
        player_size = self.player.size
        
        # Орбитальные пули наносят урон врагам
        if hasattr(self.player, 'orbital_bullets') and self.player.orbital_bullets > 0:
            time_ms = pygame.time.get_ticks()
            orbit_radius = 50
            for i in range(self.player.orbital_bullets):
                angle = (time_ms / 1000 + i * (6.28 / self.player.orbital_bullets)) % 6.28
                orb_pos = pygame.Vector2(
                    player_pos.x + math.cos(angle) * orbit_radius,
                    player_pos.y + math.sin(angle) * orbit_radius
                )
                
                for enemy in self.enemies[:]:
                    if (enemy.pos - orb_pos).length() < 15:  # Радиус столкновения
                        if enemy.take_damage(int(self.player.dmg * 0.3)):  # 30% урона игрока
                            self.particle_system.emit(enemy.pos, 10, enemy.color)
                            self.exp_gems.append(pygame.Vector2(enemy.pos))
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
                            self.kills += 1
                            self.score += enemy.exp_value
        
        for enemy in self.enemies[:]:
            dx = enemy.pos.x - player_pos.x
            dy = enemy.pos.y - player_pos.y
            dist_sq = dx * dx + dy * dy
            required_dist_sq = (enemy.size + player_size) ** 2
            
            if dist_sq < required_dist_sq:
                if self.player.take_damage(enemy.dmg):
                    self.state = GameState.GAME_OVER
                    # Статистика учитывается только в режиме волн
                    count_stats = (self.game_mode == GameMode.WAVES)
                    earned = self.save_system.update_stats(
                        self.kills,
                        int(self.time_survived),
                        self.score,
                        self.player.level,
                        self.wave_system.current_wave,
                        count_stats
                    )
                else:
                    # Звук получения урона
                    self.sound_manager.play_sound("player_hit")
                    
                    # Шипы - урон врагу при касании
                    if hasattr(self.player, 'thorns') and self.player.thorns > 0:
                        if enemy.take_damage(self.player.thorns):
                            self.particle_system.emit(enemy.pos, 15, enemy.color)
                            self.exp_gems.append(pygame.Vector2(enemy.pos))
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
                            self.kills += 1
                            self.score += enemy.exp_value
                    
                    # Отражение урона
                    if hasattr(self.player, 'reflect_damage') and self.player.reflect_damage > 0:
                        reflected = int(enemy.dmg * self.player.reflect_damage)
                        if enemy.take_damage(reflected):
                            self.particle_system.emit(enemy.pos, 15, enemy.color)
                            self.exp_gems.append(pygame.Vector2(enemy.pos))
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
                            self.kills += 1
                            self.score += enemy.exp_value
                
                self.particle_system.emit(self.player.pos, 10, COLORS["health"])
    
    def update_exp_gems(self):
        # Радиус притяжения опыта
        magnet_radius = getattr(self.player, 'exp_magnet_radius', 100)
        
        for gem in self.exp_gems[:]:
            to_player = self.player.pos - gem
            if to_player.length() < magnet_radius:
                # Скорость притяжения увеличивается при приближении
                pull_speed = 8 + (1 - to_player.length() / magnet_radius) * 12
                gem += to_player.normalize() * pull_speed
            
            if to_player.length() < 20:
                self.exp_gems.remove(gem)
                # Применяем множитель опыта если есть
                exp_gain = 10
                if hasattr(self.player, 'exp_multiplier'):
                    exp_gain = int(exp_gain * self.player.exp_multiplier)
                self.player.exp += exp_gain
                
                if self.player.exp >= self.player.exp_to_next:
                    self.player.level += 1
                    self.player.exp = 0
                    self.player.exp_to_next = int(self.player.exp_to_next * 1.2)
                    self.state = GameState.LEVEL_UP
                    # Блокируем немедленный выбор — игрок должен сначала отпустить кнопку
                    self.level_up_click_handled = True
                    # Звук повышения уровня
                    self.sound_manager.play_sound("level_up")
    
    def update_wave_system(self):
        # Проверяем окончание волны
        if self.wave_system.wave_active:
            if (self.wave_system.enemies_spawned >= self.wave_system.enemies_in_wave 
                and len(self.enemies) == 0):
                self.wave_system.wave_complete()
                self.state = GameState.WAVE_COMPLETE
        
        # Обновляем перерыв
        if not self.wave_system.wave_active:
            if self.wave_system.update_break(self.dt):
                self.wave_system.start_wave()
    
    def draw_background(self):
        screen.fill(COLORS["bg"])
        
        grid_size = 50
        offset_x = int(self.cam.x) % grid_size
        offset_y = int(self.cam.y) % grid_size
        
        for x in range(0, WIDTH + grid_size, grid_size):
            sx = x + offset_x
            pygame.draw.line(screen, COLORS["grid"], (sx, 0), (sx, HEIGHT), 1)
        
        for y in range(0, HEIGHT + grid_size, grid_size):
            sy = y + offset_y
            pygame.draw.line(screen, COLORS["grid"], (0, sy), (WIDTH, sy), 1)
    
    def draw_ui(self):
        margin = 30
        
        # HP бар с улучшенным дизайном
        bar_w, bar_h = 380, 35
        bar_x, bar_y = margin, margin
        
        # Подложка с тенью
        shadow_rect = pygame.Rect(bar_x + 2, bar_y + 2, bar_w, bar_h)
        pygame.draw.rect(screen, (0, 0, 0, 60), shadow_rect, border_radius=8)
        
        # Фон бара
        pygame.draw.rect(screen, (25, 30, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        
        # HP заполнение с градиентом
        hp_w = int((self.player.hp / self.player.max_hp) * bar_w)
        if hp_w > 0:
            hp_rect = pygame.Rect(bar_x, bar_y, hp_w, bar_h)
            # Градиент от темно-красного к яркому
            for i in range(hp_w):
                progress = i / bar_w
                r = int(200 + (255 - 200) * progress)
                g = int(60 + (80 - 60) * progress)
                b = int(60 + (80 - 60) * progress)
                pygame.draw.line(screen, (r, g, b), 
                               (bar_x + i, bar_y + 2), 
                               (bar_x + i, bar_y + bar_h - 2))
            pygame.draw.rect(screen, COLORS["health"], (bar_x, bar_y, hp_w, bar_h), 3, border_radius=8)
        
        # Обводка
        pygame.draw.rect(screen, COLORS["card_border"], (bar_x, bar_y, bar_w, bar_h), 2, border_radius=8)
        
        # Текст HP
        hp_text = self.font_small.render(f"HP: {int(self.player.hp)} / {self.player.max_hp}", 
                                         True, COLORS["ui"])
        screen.blit(hp_text, (bar_x + bar_w // 2 - hp_text.get_width() // 2, bar_y + 7))
        
        current_y = bar_y + bar_h + 10
        
        # Щит (если есть)
        if self.player.max_shield > 0:
            shield_h = 25
            pygame.draw.rect(screen, (20, 25, 35), (bar_x, current_y, bar_w, shield_h), border_radius=6)
            shield_w = int((self.player.shield / self.player.max_shield) * bar_w)
            if shield_w > 0:
                pygame.draw.rect(screen, COLORS["shield"], (bar_x, current_y, shield_w, shield_h), border_radius=6)
            pygame.draw.rect(screen, COLORS["card_border"], (bar_x, current_y, bar_w, shield_h), 2, border_radius=6)
            current_y += shield_h + 8
        
        # EXP бар с улучшенным дизайном
        exp_h = 30
        pygame.draw.rect(screen, (20, 25, 35), (bar_x, current_y, bar_w, exp_h), border_radius=7)
        exp_w = int((self.player.exp / self.player.exp_to_next) * bar_w)
        if exp_w > 0:
            # Градиент для опыта
            for i in range(exp_w):
                progress = i / bar_w
                r = int(0 + (0 - 0) * progress)
                g = int(180 + (220 - 180) * progress)
                b = int(230 + (255 - 230) * progress)
                pygame.draw.line(screen, (r, g, b), 
                               (bar_x + i, current_y + 2), 
                               (bar_x + i, current_y + exp_h - 2))
            pygame.draw.rect(screen, COLORS["exp"], (bar_x, current_y, exp_w, exp_h), 3, border_radius=7)
        
        pygame.draw.rect(screen, COLORS["card_border"], (bar_x, current_y, bar_w, exp_h), 2, border_radius=7)
        
        # Процентный индикатор опыта
        exp_percent = int((self.player.exp / self.player.exp_to_next) * 100)
        exp_text = self.font_small.render(f"EXP: {exp_percent}%", True, COLORS["ui"])
        screen.blit(exp_text, (bar_x + bar_w // 2 - exp_text.get_width() // 2, current_y + 5))
        
        # Уровень справа от бара
        lvl_text = self.font_medium.render(f"LVL {self.player.level}", True, COLORS["player"])
        screen.blit(lvl_text, (bar_x + bar_w + 20, current_y - 5))
        
        current_y += exp_h + 20
        
        # Статистика в красивых карточках
        stats_data = [
            ("СЧЁТ", self.score, COLORS["warning"]),
            ("УБИЙСТВ", self.kills, COLORS["enemy"]),
        ]
        
        # Для волнового режима показываем волну
        if self.game_mode == GameMode.WAVES:
            stats_data.append(("ВОЛНА", self.wave_system.current_wave, COLORS["player"]))
        
        stats_data.append(("ВРЕМЯ", f"{int(self.time_survived)}s", COLORS["exp"]))
        
        for label, value, color in stats_data:
            stat_card = pygame.Rect(bar_x, current_y, bar_w, 45)
            pygame.draw.rect(screen, (30, 35, 50), stat_card, border_radius=8)
            pygame.draw.rect(screen, color, stat_card, 2, border_radius=8)
            
            label_text = self.font_small.render(label, True, (180, 180, 200))
            screen.blit(label_text, (stat_card.x + 15, stat_card.y + 12))
            
            value_text = self.font_small.render(str(value), True, color)
            value_rect = value_text.get_rect(right=stat_card.right - 15, centery=stat_card.centery)
            screen.blit(value_text, value_rect)
            
            current_y += 50
        
        # Информация о волне в центре сверху (только для режима волн)
        if self.game_mode == GameMode.WAVES:
            if not self.wave_system.wave_active:
                wave_bg = pygame.Rect(WIDTH // 2 - 200, 20, 400, 50)
                pygame.draw.rect(screen, (40, 45, 65), wave_bg, border_radius=10)
                pygame.draw.rect(screen, COLORS["warning"], wave_bg, 3, border_radius=10)
                
                wave_text = self.font_medium.render(
                    f"ПЕРЕРЫВ: {int(self.wave_system.wave_break_time)}s",
                    True, COLORS["warning"]
                )
                wave_rect = wave_text.get_rect(center=wave_bg.center)
                screen.blit(wave_text, wave_rect)
            else:
                # Осталось заспавнить + уже на карте
                remaining = (self.wave_system.enemies_in_wave - self.wave_system.enemies_spawned) + len(self.enemies)
                remaining = max(0, remaining)  # Не может быть отрицательным
                
                wave_bg = pygame.Rect(WIDTH // 2 - 200, 20, 400, 50)
                pygame.draw.rect(screen, (40, 45, 65), wave_bg, border_radius=10)
                pygame.draw.rect(screen, COLORS["player"], wave_bg, 3, border_radius=10)
                
                wave_text = self.font_small.render(
                    f"Врагов осталось: {remaining}",
                    True, COLORS["ui"]
                )
                wave_rect = wave_text.get_rect(center=wave_bg.center)
                screen.blit(wave_text, wave_rect)
        else:
            # Для бесконечного режима показываем индикатор режима
            mode_bg = pygame.Rect(WIDTH // 2 - 160, 20, 320, 50)
            pygame.draw.rect(screen, (40, 45, 65), mode_bg, border_radius=10)
            pygame.draw.rect(screen, COLORS["exp"], mode_bg, 3, border_radius=10)
            
            mode_text = self.font_small.render("БЕСКОНЕЧНЫЙ", True, COLORS["exp"])
            mode_rect = mode_text.get_rect(center=mode_bg.center)
            screen.blit(mode_text, mode_rect)
        
        # Dash индикатор в красивом стиле
        dash_w = 180
        dash_h = 50
        dash_x = WIDTH // 2 - dash_w // 2
        dash_y = HEIGHT - 70
        
        dash_bg = pygame.Rect(dash_x, dash_y, dash_w, dash_h)
        
        if self.player.dash_ready:
            pygame.draw.rect(screen, (40, 50, 65), dash_bg, border_radius=10)
            pygame.draw.rect(screen, COLORS["player"], dash_bg, 3, border_radius=10)
            dash_text = self.font_small.render("DASH ГОТОВ", True, COLORS["player"])
        else:
            pygame.draw.rect(screen, (30, 35, 45), dash_bg, border_radius=10)
            pygame.draw.rect(screen, (80, 80, 90), dash_bg, 2, border_radius=10)
            cooldown = max(0, self.player.dash_cooldown / 1000)
            dash_text = self.font_small.render(f"DASH: {cooldown:.1f}s", True, (120, 120, 130))
        
        dash_rect = dash_text.get_rect(center=dash_bg.center)
        screen.blit(dash_text, dash_rect)
        
        # Панель активных перков (слева вверху)
        p = self.player
        active_perks = []
        
        # Собираем все активные перки
        if hasattr(p, 'regen') and p.regen > 0:
            active_perks.append(("Регенерация", f"{p.regen}/s", COLORS["health"]))
        if hasattr(p, 'armor') and p.armor > 0:
            active_perks.append(("Броня", f"{int(p.armor*100)}%", COLORS["shield"]))
        if hasattr(p, 'lifesteal') and p.lifesteal > 0:
            active_perks.append(("Вампиризм", f"{int(p.lifesteal*100)}%", COLORS["health"]))
        if hasattr(p, 'exp_multiplier') and p.exp_multiplier > 1:
            active_perks.append(("Опыт", f"x{p.exp_multiplier:.1f}", COLORS["exp"]))
        if hasattr(p, 'exp_magnet_radius') and p.exp_magnet_radius > 100:
            active_perks.append(("Магнит", f"{int(p.exp_magnet_radius)}px", COLORS["exp"]))
        if hasattr(p, 'gold_multiplier') and p.gold_multiplier > 1:
            active_perks.append(("Валюта", f"x{p.gold_multiplier:.1f}", COLORS["warning"]))
        
        # Отображаем в виде компактных плашек
        if active_perks:
            perk_x = 15
            perk_y = 15
            perk_w = 140
            perk_h = 35
            perk_gap = 5
            
            for perk_name, perk_value, perk_color in active_perks:
                perk_rect = pygame.Rect(perk_x, perk_y, perk_w, perk_h)
                
                # Полупрозрачный фон
                perk_surf = pygame.Surface((perk_w, perk_h), pygame.SRCALPHA)
                pygame.draw.rect(perk_surf, (20, 25, 35, 200), perk_surf.get_rect(), border_radius=8)
                pygame.draw.rect(perk_surf, (*perk_color, 180), perk_surf.get_rect(), 2, border_radius=8)
                screen.blit(perk_surf, perk_rect)
                
                # Текст
                name_text = self.font_tiny.render(perk_name, True, perk_color)
                value_text = self.font_tiny.render(perk_value, True, COLORS["ui"])
                
                screen.blit(name_text, (perk_x + 8, perk_y + 5))
                screen.blit(value_text, (perk_x + perk_w - value_text.get_width() - 8, perk_y + 15))
                
                perk_y += perk_h + perk_gap
    
    def draw_menu(self):
        screen.fill(COLORS["bg"])
        
        if self.menu_page == "main":
            self.draw_main_menu()
        elif self.menu_page == "stats":
            self.draw_stats_menu()
        elif self.menu_page == "settings":
            self.draw_settings_menu()
        elif self.menu_page == "modules":
            self.draw_modules_menu()
        elif self.menu_page == "skins":
            self.draw_skins_menu()
        elif self.menu_page == "achievements":
            self.draw_achievements_menu()
    
    def draw_main_menu(self):
        # Улучшенный градиентный фон с более плавными переходами
        for i in range(HEIGHT):
            progress = i / HEIGHT
            # Более темный и атмосферный градиент
            r = int(5 + (15 - 5) * progress)
            g = int(8 + (20 - 8) * progress)
            b = int(18 + (35 - 18) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))
        
        # Анимированные декоративные линии
        time_offset = pygame.time.get_ticks() // 50
        for i in range(30):
            x = (WIDTH // 30) * i + (time_offset % 100)
            alpha = 8 + (i % 4) * 4
            y_wave = int(math.sin((i + time_offset / 100) * 0.5) * 20)
            color = (*COLORS["grid"], alpha)
            s = pygame.Surface((2, HEIGHT), pygame.SRCALPHA)
            s.fill(color)
            screen.blit(s, (x, y_wave))
        
        # Плавающие частицы в фоне
        if len(self.menu_particles) < 50:
            self.menu_particles.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(0, HEIGHT),
                'speed': random.uniform(10, 30),
                'size': random.randint(2, 4),
                'alpha': random.randint(40, 100)
            })
        
        for particle in self.menu_particles[:]:
            particle['y'] -= particle['speed'] * self.dt
            if particle['y'] < -10:
                particle['y'] = HEIGHT + 10
                particle['x'] = random.randint(0, WIDTH)
            
            # Рисуем частицу
            surf = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*COLORS["player"], particle['alpha']), 
                             (particle['size'], particle['size']), particle['size'])
            screen.blit(surf, (int(particle['x']), int(particle['y'])))
        
        # Заголовок с усиленным эффектом свечения
        title = self.font_huge.render("CYBER SURVIVOR", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 6))
        
        # Многослойное свечение заголовка
        glow_surf = pygame.Surface((title_rect.width + 60, title_rect.height + 60), pygame.SRCALPHA)
        for i in range(5):
            alpha = 40 - i * 8
            offset = i * 3
            glow_title = self.font_huge.render("CYBER SURVIVOR", True, (*COLORS["player_glow"], alpha))
            glow_surf.blit(glow_title, (30 + offset, 30 + offset))
        screen.blit(glow_surf, (title_rect.x - 30, title_rect.y - 30))
        screen.blit(title, title_rect)
        
        # Анимированный подзаголовок
        pulse = abs(math.sin(self.menu_time * 2)) * 30 + 200
        subtitle = self.font_small.render("v3.1 - Улучшенный дизайн", True, (int(pulse), int(pulse), 255))
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 6 + 70))
        screen.blit(subtitle, subtitle_rect)
        
        # Карточки - сетка 2x4 с улучшенным дизайном
        card_width, card_height = 360, 100
        gap = 25
        grid_cols = 2
        
        start_x = WIDTH // 2 - (card_width * grid_cols + gap * (grid_cols - 1)) // 2
        start_y = HEIGHT // 2 - 120  # Немного поднято вверх
        
        buttons = [
            {"text": "НАЧАТЬ ИГРУ", "action": "play", "desc": "Новая игра", "id": "play", "icon": ">"},
            {"text": "ДОСТИЖЕНИЯ", "action": "achievements", "desc": "Ваши награды", "id": "ach", "icon": "*"},
            {"text": "МОДУЛИ", "action": "modules", "desc": "Улучшения", "id": "mod", "icon": "+"},
            {"text": "СКИНЫ", "action": "skins", "desc": "Внешний вид", "id": "skin", "icon": "#"},
            {"text": "НАСТРОЙКИ", "action": "settings", "desc": "Конфигурация", "id": "set", "icon": "="},
            {"text": "СТАТИСТИКА", "action": "stats", "desc": "Ваши рекорды", "id": "stat", "icon": "~"},
            {"text": "ВЫХОД", "action": "quit", "desc": "Выйти из игры", "id": "quit", "icon": "X"}
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        for i, btn_data in enumerate(buttons):
            row = i // grid_cols
            col = i % grid_cols
            
            card_rect = pygame.Rect(
                start_x + col * (card_width + gap),
                start_y + row * (card_height + gap),
                card_width,
                card_height
            )
            
            is_hover = card_rect.collidepoint(mouse_pos)
            
            # Эффект нажатия
            btn_id = btn_data.get("id", str(i))
            press_time = self.button_press_effect.get(btn_id, 0)
            if press_time > 0:
                self.button_press_effect[btn_id] = max(0, press_time - self.dt)
                press_factor = press_time / 0.2
                card_rect = card_rect.inflate(-int(6 * press_factor), -int(6 * press_factor))
            
            # Карточка с улучшенной тенью и свечением при наведении
            if is_hover:
                # Тень
                shadow_rect = card_rect.copy()
                shadow_rect.y += 6
                shadow_surf = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surf, (0, 0, 0, 60), shadow_surf.get_rect(), border_radius=15)
                screen.blit(shadow_surf, shadow_rect)
                
                # Свечение
                glow_rect = card_rect.inflate(8, 8)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*COLORS["player"], 30), glow_surf.get_rect(), border_radius=17)
                screen.blit(glow_surf, glow_rect)
            
            # Основная карточка
            card_color = (50, 55, 75) if is_hover else (30, 35, 55)
            pygame.draw.rect(screen, card_color, card_rect, border_radius=15)
            title_color = COLORS["player"] if is_hover else COLORS["ui"]
            border_color = COLORS["player"] if is_hover else COLORS["card_border"]
            border_width = 3 if is_hover else 2
            pygame.draw.rect(screen, border_color, card_rect, border_width, border_radius=15)
            
            # Иконка слева (56x56 зона)
            icon_zone_w = 70
            icon_cx = card_rect.x + icon_zone_w // 2
            icon_cy = card_rect.centery  # точно по центру карточки
            
            if not self.draw_icon(btn_data["action"], icon_cx, icon_cy, 36):
                # Fallback на символ
                icon_text = self.font_medium.render(btn_data.get("icon", ">"), True, title_color)
                icon_rect = icon_text.get_rect(center=(icon_cx, icon_cy))
                screen.blit(icon_text, icon_rect)
            
            # Разделитель иконки
            sep_x = card_rect.x + icon_zone_w
            pygame.draw.line(screen, border_color,
                             (sep_x, card_rect.y + 15),
                             (sep_x, card_rect.bottom - 15), 1)
            
            # Текст названия и описания справа от иконки
            text_x = sep_x + 18
            button_text = self.font_medium.render(btn_data["text"], True, title_color)
            screen.blit(button_text, (text_x, card_rect.centery - button_text.get_height() - 2))
            
            desc_text = self.font_tiny.render(btn_data["desc"], True, (150, 155, 175))
            screen.blit(desc_text, (text_x, card_rect.centery + 4))
            
            if is_hover and mouse_clicked:
                self.button_press_effect[btn_id] = 0.2  # Запускаем эффект нажатия
                # Звук клика
                self.sound_manager.play_sound("button_click")
                
                if btn_data["action"] == "play":
                    self.state = GameState.MODE_SELECT  # Переходим к выбору режима
                elif btn_data["action"] == "achievements":
                    self.menu_page = "achievements"
                elif btn_data["action"] == "modules":
                    self.menu_page = "modules"
                elif btn_data["action"] == "skins":
                    self.menu_page = "skins"
                elif btn_data["action"] == "settings":
                    self.menu_page = "settings"
                elif btn_data["action"] == "stats":
                    self.menu_page = "stats"
                elif btn_data["action"] == "quit":
                    pygame.quit()
                    sys.exit()
                pygame.time.delay(200)
        
        # Валюта
        currency_card = pygame.Rect(30, HEIGHT - 100, 250, 60)
        pygame.draw.rect(screen, COLORS["card"], currency_card, border_radius=10)
        pygame.draw.rect(screen, COLORS["warning"], currency_card, 2, border_radius=10)
        
        currency_text = self.font_medium.render(
            f"Валюта: {self.save_system.data['currency']}", 
            True, COLORS["warning"]
        )
        currency_rect = currency_text.get_rect(center=currency_card.center)
        screen.blit(currency_text, currency_rect)
    
    def draw_mode_select(self):
        """Экран выбора режима игры"""
        # Тот же красивый фон что и в главном меню
        for i in range(HEIGHT):
            progress = i / HEIGHT
            r = int(5 + (15 - 5) * progress)
            g = int(8 + (20 - 8) * progress)
            b = int(18 + (35 - 18) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))
        
        # Заголовок
        title = self.font_huge.render("ВЫБОР РЕЖИМА", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        
        # Свечение заголовка
        glow_surf = pygame.Surface((title_rect.width + 60, title_rect.height + 60), pygame.SRCALPHA)
        for i in range(5):
            alpha = 40 - i * 8
            offset = i * 3
            glow_title = self.font_huge.render("ВЫБОР РЕЖИМА", True, (*COLORS["player_glow"], alpha))
            glow_surf.blit(glow_title, (30 + offset, 30 + offset))
        screen.blit(glow_surf, (title_rect.x - 30, title_rect.y - 30))
        screen.blit(title, title_rect)
        
        # Две большие карточки режимов (увеличены)
        card_width = 520
        card_height = 380
        gap = 70
        start_x = WIDTH // 2 - (card_width * 2 + gap) // 2
        card_y = HEIGHT // 2 - card_height // 2 + 30
        
        modes = [
            {
                "title": "ВОЛНЫ",
                "mode": GameMode.WAVES,
                "icon": "~",
                "desc": "Классический режим",
                "features": [
                    "Волны врагов с перерывами",
                    "Растущая сложность",
                    "Учитывается в статистике",
                    "Разблокировка достижений"
                ]
            },
            {
                "title": "БЕСКОНЕЧНЫЙ",
                "mode": GameMode.ENDLESS,
                "icon": "8",
                "desc": "Режим выживания",
                "features": [
                    "Постоянный спавн врагов",
                    "Без перерывов между волнами",
                    "Не учитывается в статистике",
                    "Только для практики"
                ]
            }
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        for i, mode_data in enumerate(modes):
            card_x = start_x + i * (card_width + gap)
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            is_hover = card_rect.collidepoint(mouse_pos)
            
            # Эффекты при наведении
            if is_hover:
                # Тень
                shadow_rect = card_rect.copy()
                shadow_rect.y += 8
                shadow_surf = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(), border_radius=20)
                screen.blit(shadow_surf, shadow_rect)
                
                # Свечение
                glow_rect = card_rect.inflate(12, 12)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*COLORS["player"], 40), glow_surf.get_rect(), border_radius=22)
                screen.blit(glow_surf, glow_rect)
            
            # Основная карточка
            card_color = (55, 60, 80) if is_hover else (35, 40, 60)
            pygame.draw.rect(screen, card_color, card_rect, border_radius=20)
            
            border_color = COLORS["player"] if is_hover else COLORS["card_border"]
            border_width = 4 if is_hover else 3
            pygame.draw.rect(screen, border_color, card_rect, border_width, border_radius=20)
            
            # Иконка режима
            icon_text = self.font_huge.render(mode_data["icon"], True, COLORS["player"])
            icon_rect = icon_text.get_rect(center=(card_rect.centerx, card_rect.y + 80))
            screen.blit(icon_text, icon_rect)
            
            # Название режима
            title_text = self.font_large.render(mode_data["title"], True, COLORS["player"] if is_hover else COLORS["ui"])
            title_rect = title_text.get_rect(center=(card_rect.centerx, card_rect.y + 160))
            screen.blit(title_text, title_rect)
            
            # Описание
            desc_text = self.font_small.render(mode_data["desc"], True, (180, 180, 200))
            desc_rect = desc_text.get_rect(center=(card_rect.centerx, card_rect.y + 200))
            screen.blit(desc_text, desc_rect)
            
            # Особенности режима
            feature_y = card_rect.y + 240
            for feature in mode_data["features"]:
                feature_text = self.font_tiny.render(f"• {feature}", True, (150, 150, 170))
                screen.blit(feature_text, (card_rect.x + 30, feature_y))
                feature_y += 25
            
            # Обработка нажатия
            if is_hover and mouse_clicked:
                self.game_mode = mode_data["mode"]
                self.reset_game()
                self.state = GameState.PLAY
                pygame.time.delay(200)
        
        # Кнопка назад
        back_rect = pygame.Rect(50, HEIGHT - 100, 200, 60)
        is_hover_back = back_rect.collidepoint(mouse_pos)
        
        color = COLORS["player"] if is_hover_back else COLORS["card_border"]
        pygame.draw.rect(screen, color, back_rect, 3, border_radius=8)
        
        text = self.font_small.render("НАЗАД", True, COLORS["player"])
        text_rect = text.get_rect(center=back_rect.center)
        screen.blit(text, text_rect)
        
        if is_hover_back and mouse_clicked:
            self.state = GameState.MENU
            pygame.time.delay(200)
    
    def draw_stats_menu(self):
        """Улучшенное меню статистики с красивым дизайном"""
        # Градиентный фон
        for i in range(HEIGHT):
            progress = i / HEIGHT
            r = int(8 + (18 - 8) * progress)
            g = int(10 + (22 - 10) * progress)
            b = int(20 + (38 - 20) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))
        
        # Заголовок с эффектом свечения
        title = self.font_large.render("СТАТИСТИКА", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, 70))
        
        glow_surf = pygame.Surface((title_rect.width + 40, title_rect.height + 40), pygame.SRCALPHA)
        for i in range(3):
            alpha = 35 - i * 10
            offset = i * 2
            glow_title = self.font_large.render("СТАТИСТИКА", True, (*COLORS["player_glow"], alpha))
            glow_surf.blit(glow_title, (20 + offset, 20 + offset))
        screen.blit(glow_surf, (title_rect.x - 20, title_rect.y - 20))
        screen.blit(title, title_rect)
        
        # Контейнер
        container_w = 900
        container_h = 600
        container_x = WIDTH // 2 - container_w // 2
        container_y = 160
        
        stats = self.save_system.data["stats"]
        
        # Статистика в красивых карточках
        stats_list = [
            ("Всего игр", f"{stats['games_played']}", COLORS["player"]),
            ("Всего убийств", f"{stats['total_kills']}", COLORS["enemy"]),
            ("Время игры", f"{stats['total_playtime']}s", COLORS["exp"]),
            ("Лучший счёт", f"{stats['best_score']}", COLORS["warning"]),
            ("Лучшее время", f"{stats['best_time']}s", COLORS["shield"]),
            ("Макс. уровень", f"{stats['max_level']}", COLORS["player"]),
            ("Макс. волна", f"{stats['max_wave']}", COLORS["health"])
        ]
        
        y = container_y
        card_h = 75
        gap = 12
        
        for label, value, color in stats_list:
            card_rect = pygame.Rect(container_x, y, container_w, card_h)
            
            # Тень
            shadow_rect = card_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            pygame.draw.rect(screen, (0, 0, 0, 30), shadow_rect, border_radius=12)
            
            # Фон карточки
            pygame.draw.rect(screen, (40, 50, 70), card_rect, border_radius=12)
            pygame.draw.rect(screen, color, card_rect, 3, border_radius=12)
            
            # Текст слева
            label_text = self.font_medium.render(label, True, COLORS["ui"])
            screen.blit(label_text, (card_rect.x + 30, card_rect.centery - label_text.get_height() // 2))
            
            # Значение справа в отдельной карточке
            value_card_w = 200
            value_card_h = 50
            value_card_x = card_rect.right - value_card_w - 20
            value_card_y = card_rect.centery - value_card_h // 2
            value_card_rect = pygame.Rect(value_card_x, value_card_y, value_card_w, value_card_h)
            
            pygame.draw.rect(screen, (55, 65, 85), value_card_rect, border_radius=10)
            pygame.draw.rect(screen, color, value_card_rect, 2, border_radius=10)
            
            value_text = self.font_medium.render(value, True, color)
            value_rect = value_text.get_rect(center=value_card_rect.center)
            screen.blit(value_text, value_rect)
            
            y += card_h + gap
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Кнопка сброса статистики
        reset_button_rect = pygame.Rect(WIDTH - 280, HEIGHT - 95, 230, 55)
        reset_hover = reset_button_rect.collidepoint(mouse_pos)
        
        pygame.draw.rect(screen, (50, 20, 20) if reset_hover else (35, 15, 15), reset_button_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["enemy"], reset_button_rect, 2, border_radius=10)
        
        # Иконка слева в кнопке
        icon_x = reset_button_rect.x + 28
        icon_y_c = reset_button_rect.centery
        if not self.draw_icon("reset", icon_x, icon_y_c, 28):
            sym = self.font_small.render("X", True, COLORS["enemy"])
            screen.blit(sym, (icon_x - sym.get_width()//2, icon_y_c - sym.get_height()//2))
        
        reset_text = self.font_small.render("СБРОСИТЬ", True, COLORS["enemy"])
        screen.blit(reset_text, (reset_button_rect.x + 52, icon_y_c - reset_text.get_height()//2))
        
        if reset_hover and pygame.mouse.get_pressed()[0] and not self.show_stats_reset_confirmation:
            self.show_stats_reset_confirmation = True
            pygame.time.delay(200)
        
        # Диалог подтверждения сброса статистики
        if self.show_stats_reset_confirmation:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))
            
            dialog_w, dialog_h = 660, 360
            dialog_x = WIDTH // 2 - dialog_w // 2
            dialog_y = HEIGHT // 2 - dialog_h // 2
            dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_w, dialog_h)
            
            pygame.draw.rect(screen, (35, 20, 20), dialog_rect, border_radius=15)
            pygame.draw.rect(screen, COLORS["enemy"], dialog_rect, 3, border_radius=15)
            
            warn_title = self.font_large.render("СБРОС СТАТИСТИКИ", True, COLORS["enemy"])
            screen.blit(warn_title, warn_title.get_rect(center=(WIDTH // 2, dialog_y + 58)))
            
            for li, line in enumerate([
                "Все счётчики будут обнулены.",
                "Все разблокированные скины будут",
                "заблокированы (кроме стандартного).",
                "Это действие нельзя отменить!"
            ]):
                col = COLORS["enemy"] if li == 3 else (210, 210, 230)
                t = self.font_small.render(line, True, col)
                screen.blit(t, t.get_rect(center=(WIDTH // 2, dialog_y + 130 + li * 38)))
            
            btn_y = dialog_y + dialog_h - 80
            btn_w, btn_h = 210, 55
            
            yes_rect = pygame.Rect(dialog_x + 80, btn_y, btn_w, btn_h)
            yes_hover = yes_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (180, 40, 40) if yes_hover else (130, 30, 30), yes_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["enemy"], yes_rect, 3, border_radius=10)
            yt = self.font_medium.render("ДА, СБРОСИТЬ", True, (255, 255, 255))
            screen.blit(yt, yt.get_rect(center=yes_rect.center))
            
            no_rect = pygame.Rect(dialog_x + dialog_w - 80 - btn_w, btn_y, btn_w, btn_h)
            no_hover = no_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (45, 55, 75) if no_hover else (35, 42, 60), no_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["player"], no_rect, 3, border_radius=10)
            nt = self.font_medium.render("ОТМЕНА", True, COLORS["ui"])
            screen.blit(nt, nt.get_rect(center=no_rect.center))
            
            if yes_hover and pygame.mouse.get_pressed()[0]:
                # Сброс статистики
                default_stats = {
                    "games_played": 0, "total_kills": 0, "total_playtime": 0,
                    "best_score": 0, "best_time": 0, "max_level": 0, "max_wave": 0
                }
                self.save_system.data["stats"] = default_stats
                # Блокировка всех скинов кроме default
                self.save_system.data["unlocked_skins"] = ["default"]
                self.save_system.data["current_skin"] = "default"
                self.save_system.save()
                self.show_stats_reset_confirmation = False
                pygame.time.delay(200)
            
            if no_hover and pygame.mouse.get_pressed()[0]:
                self.show_stats_reset_confirmation = False
                pygame.time.delay(200)
        
        self.draw_back_button()
    
    def draw_settings_menu(self):
        """Улучшенное меню настроек с красивым дизайном"""
        # Градиентный фон
        for i in range(HEIGHT):
            progress = i / HEIGHT
            r = int(8 + (18 - 8) * progress)
            g = int(10 + (22 - 10) * progress)
            b = int(20 + (38 - 20) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))
        
        # Заголовок с эффектом свечения
        title = self.font_large.render("НАСТРОЙКИ", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, 70))
        
        glow_surf = pygame.Surface((title_rect.width + 40, title_rect.height + 40), pygame.SRCALPHA)
        for i in range(3):
            alpha = 35 - i * 10
            offset = i * 2
            glow_title = self.font_large.render("НАСТРОЙКИ", True, (*COLORS["player_glow"], alpha))
            glow_surf.blit(glow_title, (20 + offset, 20 + offset))
        screen.blit(glow_surf, (title_rect.x - 20, title_rect.y - 20))
        screen.blit(title, title_rect)
        
        container_w = 950
        container_x = WIDTH // 2 - container_w // 2
        container_y = 160
        
        # Секция управления
        section_y = container_y
        section_bg = pygame.Rect(container_x - 15, section_y - 10, container_w + 30, 45)
        pygame.draw.rect(screen, (35, 45, 60), section_bg, border_radius=10)
        section_title = self.font_medium.render("УПРАВЛЕНИЕ", True, COLORS["player"])
        screen.blit(section_title, (container_x + 20, section_y))
        
        controls = self.save_system.data["controls"]
        control_names = {
            "up": ("ВВЕРХ", COLORS["player"]),
            "down": ("ВНИЗ", COLORS["player"]),
            "left": ("ВЛЕВО", COLORS["player"]),
            "right": ("ВПРАВО", COLORS["player"]),
            "dash": ("РЫВОК", COLORS["warning"]),
            "auto_fire_toggle": ("АВТОСТРЕЛЬБА", COLORS["exp"])
        }
        
        y = section_y + 55
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        for key, (name, color) in control_names.items():
            key_name = pygame.key.name(controls[key]).upper()
            
            # Карточка для кнопки управления
            card_rect = pygame.Rect(container_x, y, container_w, 60)
            pygame.draw.rect(screen, (40, 50, 70), card_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["card_border"], card_rect, 2, border_radius=10)
            
            # Название действия
            label_text = self.font_small.render(name, True, color)
            screen.blit(label_text, (card_rect.x + 25, card_rect.centery - label_text.get_height() // 2))
            
            # Кнопка привязки клавиши
            button_w = 160
            button_h = 45
            button_x = card_rect.right - button_w - 15
            button_y = card_rect.centery - button_h // 2
            button_rect = pygame.Rect(button_x, button_y, button_w, button_h)
            is_hover = button_rect.collidepoint(mouse_pos)
            
            if is_hover:
                pygame.draw.rect(screen, (55, 65, 85), button_rect, border_radius=8)
                pygame.draw.rect(screen, COLORS["player"], button_rect, 3, border_radius=8)
                
                if mouse_clicked and self.rebinding_key is None:
                    self.rebinding_key = key
                    pygame.time.delay(200)
            else:
                pygame.draw.rect(screen, (45, 55, 75), button_rect, border_radius=8)
                pygame.draw.rect(screen, color, button_rect, 2, border_radius=8)
            
            if self.rebinding_key == key:
                value_text = self.font_tiny.render("▶ Нажмите клавишу ◀", True, COLORS["warning"])
            else:
                value_text = self.font_small.render(key_name, True, COLORS["player"])
            
            value_rect = value_text.get_rect(center=button_rect.center)
            screen.blit(value_text, value_rect)
            
            y += 65
        
        # Секция геймплея
        settings = self.save_system.data["settings"]
        section_y = y + 30
        section_bg = pygame.Rect(container_x - 15, section_y - 10, container_w + 30, 45)
        pygame.draw.rect(screen, (35, 45, 60), section_bg, border_radius=10)
        section_title = self.font_medium.render("ГЕЙМПЛЕЙ", True, COLORS["player"])
        screen.blit(section_title, (container_x + 20, section_y - 5))
        
        y = section_y + 55
        
        # Автострельба в карточке
        auto_card = pygame.Rect(container_x, y, container_w, 60)
        pygame.draw.rect(screen, (40, 50, 70), auto_card, border_radius=10)
        pygame.draw.rect(screen, COLORS["card_border"], auto_card, 2, border_radius=10)
        
        label_text = self.font_small.render("АВТОСТРЕЛЬБА:", True, COLORS["ui"])
        screen.blit(label_text, (auto_card.x + 25, auto_card.centery - label_text.get_height() // 2))
        
        # Toggle кнопка
        button_w, button_h = 80, 40
        button_x = auto_card.right - button_w - 15
        button_y = auto_card.centery - button_h // 2
        button_rect = pygame.Rect(button_x, button_y, button_w, button_h)
        is_hover = button_rect.collidepoint(mouse_pos)
        is_on = settings["auto_fire"]
        
        # Фон кнопки
        if is_on:
            bg_color = (0, 180, 140) if is_hover else (0, 160, 120)
        else:
            bg_color = (70, 70, 90) if is_hover else (50, 50, 70)
        
        pygame.draw.rect(screen, bg_color, button_rect, border_radius=20)
        border_color = COLORS["player"] if is_on else (100, 100, 110)
        pygame.draw.rect(screen, border_color, button_rect, 3 if is_hover else 2, border_radius=20)
        
        # Переключатель внутри кнопки
        toggle_radius = 15
        toggle_padding = 5
        if is_on:
            toggle_x = button_rect.right - toggle_radius - toggle_padding
            toggle_color = (255, 255, 255)
        else:
            toggle_x = button_rect.left + toggle_radius + toggle_padding
            toggle_color = (150, 150, 160)
        
        toggle_y = button_rect.centery
        pygame.draw.circle(screen, toggle_color, (toggle_x, toggle_y), toggle_radius)
        
        if is_hover and mouse_clicked:
            settings["auto_fire"] = not settings["auto_fire"]
            self.save_system.save()
            pygame.time.delay(200)
        
        y += 70
        
        # Интервал между волнами в карточке
        interval_card = pygame.Rect(container_x, y, container_w, 70)
        pygame.draw.rect(screen, (40, 50, 70), interval_card, border_radius=10)
        pygame.draw.rect(screen, COLORS["card_border"], interval_card, 2, border_radius=10)
        
        label_text = self.font_small.render("ИНТЕРВАЛ ВОЛН:", True, COLORS["ui"])
        screen.blit(label_text, (interval_card.x + 25, interval_card.y + 15))
        
        # Ползунок
        slider_w = 400
        slider_h = 10
        slider_x = interval_card.x + 25
        slider_y = interval_card.y + 45
        slider_rect = pygame.Rect(slider_x, slider_y, slider_w, slider_h)
        
        # Фон ползунка
        pygame.draw.rect(screen, (30, 35, 45), slider_rect, border_radius=5)
        
        # Текущее значение (3-30 секунд)
        current_duration = settings.get("wave_break_duration", 10)
        slider_pos = (current_duration - 3) / 27  # нормализовано 0-1
        
        # Заполненная часть ползунка
        filled_w = int(slider_w * slider_pos)
        if filled_w > 0:
            filled_rect = pygame.Rect(slider_x, slider_y, filled_w, slider_h)
            pygame.draw.rect(screen, COLORS["player"], filled_rect, border_radius=5)
        
        # Кружок ползунка
        handle_x = slider_x + int(slider_pos * slider_w)
        handle_rect = pygame.Rect(handle_x - 12, slider_y - 8, 24, 26)
        handle_hover = handle_rect.collidepoint(mouse_pos)
        
        if mouse_clicked and (handle_hover or slider_rect.collidepoint(mouse_pos)):
            # Перетаскивание ползунка
            new_pos = max(0, min(1, (mouse_pos[0] - slider_x) / slider_w))
            new_duration = int(3 + new_pos * 27)
            settings["wave_break_duration"] = new_duration
            self.save_system.save()
        
        # Рисуем handle
        handle_color = COLORS["player"] if handle_hover else COLORS["ui"]
        pygame.draw.circle(screen, handle_color, (handle_x, slider_y + slider_h // 2), 12)
        pygame.draw.circle(screen, (255, 255, 255), (handle_x, slider_y + slider_h // 2), 5)
        
        # Значение справа
        value_bg = pygame.Rect(interval_card.right - 100, interval_card.y + 12, 85, 45)
        pygame.draw.rect(screen, (50, 60, 80), value_bg, border_radius=8)
        pygame.draw.rect(screen, COLORS["player"], value_bg, 2, border_radius=8)
        
        duration_text = self.font_medium.render(f"{current_duration}с", True, COLORS["player"])
        duration_rect = duration_text.get_rect(center=value_bg.center)
        screen.blit(duration_text, duration_rect)
        
        self.draw_back_button()
    
    def draw_modules_menu(self):
        """Улучшенное меню модулей с красивым дизайном"""
        # Градиентный фон
        for i in range(HEIGHT):
            progress = i / HEIGHT
            r = int(8 + (18 - 8) * progress)
            g = int(10 + (22 - 10) * progress)
            b = int(20 + (38 - 20) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))
        
        # Заголовок с эффектом свечения
        title = self.font_large.render("МОДУЛИ УЛУЧШЕНИЙ", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, 60))
        
        glow_surf = pygame.Surface((title_rect.width + 40, title_rect.height + 40), pygame.SRCALPHA)
        for i in range(3):
            alpha = 35 - i * 10
            offset = i * 2
            glow_title = self.font_large.render("МОДУЛИ УЛУЧШЕНИЙ", True, (*COLORS["player_glow"], alpha))
            glow_surf.blit(glow_title, (20 + offset, 20 + offset))
        screen.blit(glow_surf, (title_rect.x - 20, title_rect.y - 20))
        screen.blit(title, title_rect)
        
        # Валюта в красивой карточке
        currency = self.save_system.data["currency"]
        currency_card = pygame.Rect(WIDTH // 2 - 180, 120, 360, 55)
        pygame.draw.rect(screen, (40, 50, 65), currency_card, border_radius=12)
        pygame.draw.rect(screen, COLORS["warning"], currency_card, 3, border_radius=12)
        
        currency_text = self.font_medium.render(f"Валюта: {currency}", True, COLORS["warning"])
        currency_rect = currency_text.get_rect(center=currency_card.center)
        screen.blit(currency_text, currency_rect)
        
        # Суммарный эффект модулей в карточках
        modules = self.save_system.data["modules"]
        total_hp = 100 + modules.get("health", 0) * 10
        total_dmg = 10 + modules.get("damage", 0) * 2
        total_speed = 6.5 + modules.get("speed", 0) * 0.5
        total_fire_rate = max(100, 250 - modules.get("fire_rate", 0) * 15)
        total_crit = 0.1 + modules.get("crit", 0) * 0.02
        
        # Панель суммарных характеристик
        summary_y = 195
        summary_w = 1000
        summary_h = 65
        summary_x = WIDTH // 2 - summary_w // 2
        summary_rect = pygame.Rect(summary_x, summary_y, summary_w, summary_h)
        
        pygame.draw.rect(screen, (35, 40, 58), summary_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["player"], summary_rect, 2, border_radius=12)
        
        summary_stats = [
            (f"HP: {total_hp}", COLORS["health"]),
            (f"УРОН: {total_dmg}", COLORS["enemy"]),
            (f"СКОРОСТЬ: {total_speed:.1f}", COLORS["player"]),
            (f"ОГОНЬ: {total_fire_rate}мс", COLORS["warning"]),
            (f"КРИТ: {int(total_crit*100)}%", COLORS["exp"])
        ]
        
        stat_x_spacing = summary_w / len(summary_stats)
        for i, (stat_text, color) in enumerate(summary_stats):
            stat_x = summary_x + int(i * stat_x_spacing + stat_x_spacing / 2)
            text = self.font_tiny.render(stat_text, True, color)
            text_rect = text.get_rect(center=(stat_x, summary_rect.centery))
            screen.blit(text, text_rect)
        
        # Контейнер для модулей
        container_w = 1000
        container_h = 450
        container_x = WIDTH // 2 - container_w // 2
        container_y = 280
        
        # Иконки для модулей
        module_info = {
            "health": {
                "name": "ЗДОРОВЬЕ", 
                "cost": 50, 
                "desc": "+10 макс. HP", 
                "icon": "+",
                "color": COLORS["health"]
            },
            "damage": {
                "name": "УРОН", 
                "cost": 50, 
                "desc": "+2 урон за выстрел", 
                "icon": "!",
                "color": COLORS["enemy"]
            },
            "speed": {
                "name": "СКОРОСТЬ", 
                "cost": 50, 
                "desc": "+0.5 скорость движения", 
                "icon": ">",
                "color": COLORS["player"]
            },
            "fire_rate": {
                "name": "СКОРОСТРЕЛЬНОСТЬ", 
                "cost": 75, 
                "desc": "-15мс перезарядка", 
                "icon": ">>",
                "color": COLORS["warning"]
            },
            "crit": {
                "name": "КРИТ", 
                "cost": 100, 
                "desc": "+2% крит шанс", 
                "icon": "*",
                "color": COLORS["exp"]
            }
        }
        
        y = container_y
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        for mod_id, info in module_info.items():
            level = modules.get(mod_id, 0)
            cost = info["cost"] * (level + 1)
            can_afford = currency >= cost
            
            # Карточка модуля
            card_w = container_w
            card_h = 82
            button_rect = pygame.Rect(container_x, y, card_w, card_h)
            is_hover = button_rect.collidepoint(mouse_pos)
            
            # Тень при наведении
            if is_hover and can_afford:
                shadow_rect = button_rect.copy()
                shadow_rect.x += 3
                shadow_rect.y += 3
                pygame.draw.rect(screen, (0, 0, 0, 40), shadow_rect, border_radius=12)
            
            # Фон карточки
            if is_hover and can_afford:
                card_color = (55, 65, 85)
            elif can_afford:
                card_color = (40, 50, 70)
            else:
                card_color = (30, 35, 50)
            
            pygame.draw.rect(screen, card_color, button_rect, border_radius=12)
            
            # Обводка
            if is_hover and can_afford:
                border_color = info["color"]
                border_width = 4
            else:
                border_color = COLORS["card_border"] if can_afford else (60, 60, 70)
                border_width = 2
            
            pygame.draw.rect(screen, border_color, button_rect, border_width, border_radius=12)
            
            # Иконка модуля
            icon_text = self.font_large.render(info["icon"], True, info["color"])
            screen.blit(icon_text, (button_rect.x + 25, button_rect.y + 18))
            
            # Название и уровень
            name_text = self.font_medium.render(f"{info['name']} [Ур. {level}]", 
                                               True, COLORS["ui"] if can_afford else (120, 120, 130))
            screen.blit(name_text, (button_rect.x + 90, button_rect.y + 15))
            
            # Описание
            desc_text = self.font_tiny.render(info['desc'], True, (170, 170, 190) if can_afford else (100, 100, 110))
            screen.blit(desc_text, (button_rect.x + 90, button_rect.y + 50))
            
            # Цена в карточке
            cost_card_w = 140
            cost_card_h = 45
            cost_card_x = button_rect.right - cost_card_w - 15
            cost_card_y = button_rect.centery - cost_card_h // 2
            cost_card_rect = pygame.Rect(cost_card_x, cost_card_y, cost_card_w, cost_card_h)
            
            cost_bg_color = (50, 60, 75) if can_afford else (35, 40, 50)
            pygame.draw.rect(screen, cost_bg_color, cost_card_rect, border_radius=8)
            
            cost_color = COLORS["player"] if can_afford else COLORS["enemy"]
            pygame.draw.rect(screen, cost_color, cost_card_rect, 2, border_radius=8)
            
            cost_text = self.font_small.render(f"{cost}", True, cost_color)
            cost_rect = cost_text.get_rect(center=cost_card_rect.center)
            screen.blit(cost_text, cost_rect)
            
            # Обработка клика
            if is_hover and mouse_clicked and can_afford:
                modules[mod_id] = level + 1
                self.save_system.data["currency"] -= cost
                self.save_system.save()
                pygame.time.delay(200)
            
            y += card_h + 12
        
        self.draw_back_button()
    
    def draw_skins_menu(self):
        """Детальный список скинов с полной информацией для открытых (4)"""
        title = self.font_large.render("СКИНЫ ПЕРСОНАЖА", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, 60))
        screen.blit(title, title_rect)
        
        # Проверка разблокировок
        unlocked = self.save_system.data["unlocked_skins"]
        current = self.save_system.data["current_skin"]
        stats = self.save_system.data["stats"]
        
        if stats["total_kills"] >= 100 and "red" not in unlocked:
            unlocked.append("red")
            self.save_system.save()
        if stats["max_level"] >= 10 and "purple" not in unlocked:
            unlocked.append("purple")
            self.save_system.save()
        if stats["best_score"] >= 5000 and "gold" not in unlocked:
            unlocked.append("gold")
            self.save_system.save()
        if stats["best_time"] >= 300 and "green" not in unlocked:
            unlocked.append("green")
            self.save_system.save()
        
        # Детальный список
        y = 140
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        for skin_id, skin_data in PLAYER_SKINS.items():
            is_unlocked = skin_id in unlocked
            is_current = skin_id == current
            
            # Карточка скина
            card_w = 900
            card_h = 120 if is_unlocked else 80
            card_x = WIDTH // 2 - card_w // 2
            card_rect = pygame.Rect(card_x, y, card_w, card_h)
            
            card_color = (45, 50, 70) if is_unlocked else (25, 30, 40)
            pygame.draw.rect(screen, card_color, card_rect, border_radius=12)
            border_color = COLORS["player"] if is_current else COLORS["card_border"]
            pygame.draw.rect(screen, border_color, card_rect, 3 if is_current else 2, border_radius=12)
            
            # Превью корабля
            preview_x = card_x + 60
            preview_y = y + card_h // 2
            self.draw_ship_preview(preview_x, preview_y, skin_id, skin_data, 0.8)
            
            # Название
            name_text = self.font_medium.render(skin_data["name"], True, skin_data["color"] if is_unlocked else (120, 120, 120))
            screen.blit(name_text, (card_x + 130, y + 15))
            
            # Условие получения
            cond_text = self.font_tiny.render(skin_data["condition"], True, (180, 180, 200))
            screen.blit(cond_text, (card_x + 130, y + 50))
            
            # Эффект (только для открытых)
            if is_unlocked:
                effect_text = self.font_tiny.render(f"Эффект: {skin_data['effect']}", True, COLORS["warning"])
                screen.blit(effect_text, (card_x + 130, y + 75))
            
            # Кнопка выбора
            if is_unlocked:
                button_rect = pygame.Rect(card_x + card_w - 150, y + card_h // 2 - 20, 120, 40)
                is_hover = button_rect.collidepoint(mouse_pos)
                
                if is_current:
                    pygame.draw.rect(screen, COLORS["player"], button_rect, border_radius=8)
                    btn_text = self.font_tiny.render("АКТИВЕН", True, COLORS["bg"])
                else:
                    btn_color = (50, 55, 75) if is_hover else (40, 45, 65)
                    pygame.draw.rect(screen, btn_color, button_rect, border_radius=8)
                    pygame.draw.rect(screen, COLORS["player"] if is_hover else COLORS["card_border"], 
                                   button_rect, 2, border_radius=8)
                    btn_text = self.font_tiny.render("ВЫБРАТЬ", True, COLORS["player"])
                
                btn_rect = btn_text.get_rect(center=button_rect.center)
                screen.blit(btn_text, btn_rect)
                
                if is_hover and mouse_clicked and not is_current:
                    self.save_system.data["current_skin"] = skin_id
                    self.save_system.save()
                    pygame.time.delay(200)
            else:
                # Иконка замка и текст
                lock_x = card_x + card_w - 60
                lock_y = y + card_h // 2
                
                if not self.draw_icon("lock", lock_x, lock_y, 28):
                    # Fallback на текст вместо эмодзи
                    lock_text = self.font_tiny.render("ЗАКРЫТ", True, (120, 120, 120))
                    screen.blit(lock_text, (card_x + card_w - 85, lock_y - 8))
            
            y += card_h + 15
            if y > HEIGHT - 100:
                break
        
        self.draw_back_button()
    
    def draw_ship_preview(self, x, y, skin_id, skin_data, scale=1.0):
        """Отрисовка превью корабля"""
        center = pygame.Vector2(x, y)
        
        # Разные формы для каждого скина
        if skin_id == "default":
            pts = [pygame.Vector2(28, 0), pygame.Vector2(18, -6), pygame.Vector2(-15, -12), 
                   pygame.Vector2(-10, 0), pygame.Vector2(-15, 12), pygame.Vector2(18, 6)]
        elif skin_id == "red":
            pts = [pygame.Vector2(30, 0), pygame.Vector2(12, -10), pygame.Vector2(-12, -15), 
                   pygame.Vector2(-8, 0), pygame.Vector2(-12, 15), pygame.Vector2(12, 10)]
        elif skin_id == "purple":
            pts = [pygame.Vector2(26, 0), pygame.Vector2(18, -5), pygame.Vector2(8, -8), 
                   pygame.Vector2(-16, -6), pygame.Vector2(-16, 6), pygame.Vector2(8, 8), pygame.Vector2(18, 5)]
        elif skin_id == "gold":
            pts = [pygame.Vector2(24, 0), pygame.Vector2(15, -12), pygame.Vector2(-6, -16), 
                   pygame.Vector2(-15, -8), pygame.Vector2(-15, 8), pygame.Vector2(-6, 16), pygame.Vector2(15, 12)]
        elif skin_id == "green":
            pts = [pygame.Vector2(32, 0), pygame.Vector2(20, -4), pygame.Vector2(10, -12), 
                   pygame.Vector2(-10, -10), pygame.Vector2(-15, 0), pygame.Vector2(-10, 10), 
                   pygame.Vector2(10, 12), pygame.Vector2(20, 4)]
        else:
            pts = [pygame.Vector2(28, 0), pygame.Vector2(18, -6), pygame.Vector2(-15, -12), 
                   pygame.Vector2(-10, 0), pygame.Vector2(-15, 12), pygame.Vector2(18, 6)]
        
        scaled_pts = [(p * scale) + center for p in pts]
        pygame.draw.polygon(screen, skin_data["color"], scaled_pts)
        pygame.draw.polygon(screen, skin_data["glow"], scaled_pts, 2)
    
    def draw_achievements_menu(self):
        """Меню достижений с прокруткой"""
        title = self.font_large.render("ДОСТИЖЕНИЯ", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, 60))
        screen.blit(title, title_rect)
        
        # Прогресс выполнения
        completed = sum(1 for v in self.save_system.data["achievements"].values() if v)
        total = len(AchievementSystem.ACHIEVEMENTS)
        progress_text = self.font_small.render(f"Выполнено: {completed}/{total}", True, COLORS["warning"])
        screen.blit(progress_text, (WIDTH // 2 - progress_text.get_width() // 2, 120))
        
        # Контейнер со скроллом
        container_w = 1100
        container_h = HEIGHT - 330
        container_x = WIDTH // 2 - container_w // 2
        container_y = 180
        container_rect = pygame.Rect(container_x, container_y, container_w, container_h)
        
        # Фон контейнера
        pygame.draw.rect(screen, (15, 18, 25), container_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["card_border"], container_rect, 2, border_radius=12)
        
        # Вычисление полной высоты контента
        card_height = 90
        spacing = 15
        achievements_list = list(AchievementSystem.ACHIEVEMENTS.items())
        total_content_height = len(achievements_list) * (card_height + spacing)
        max_scroll = max(0, total_content_height - container_h + 40)
        
        # Обработка прокрутки колесиком мыши
        mouse_pos = pygame.mouse.get_pos()
        if container_rect.collidepoint(mouse_pos):
            keys = pygame.key.get_pressed()
            # Прокрутка колесиком (обрабатывается в event loop, здесь используем клавиши)
            if keys[pygame.K_UP]:
                self.achievements_scroll_offset = max(0, self.achievements_scroll_offset - 5)
            if keys[pygame.K_DOWN]:
                self.achievements_scroll_offset = min(max_scroll, self.achievements_scroll_offset + 5)
        
        # Создание поверхности для скролла
        scroll_surface = pygame.Surface((container_w - 4, container_h - 4), pygame.SRCALPHA)
        
        y_offset = 20 - self.achievements_scroll_offset
        
        for ach_id, achievement in achievements_list:
            is_unlocked = self.save_system.data["achievements"].get(ach_id, False)
            
            # Пропускаем, если карточка за пределами видимости
            if y_offset + card_height < 0 or y_offset > container_h:
                y_offset += card_height + spacing
                continue
            
            # Карточка достижения
            card_rect = pygame.Rect(10, y_offset, container_w - 30, card_height)
            card_color = (40, 50, 60) if is_unlocked else (25, 30, 40)
            pygame.draw.rect(scroll_surface, card_color, card_rect, border_radius=10)
            border_color = COLORS["player"] if is_unlocked else (60, 70, 90)
            pygame.draw.rect(scroll_surface, border_color, card_rect, 2, border_radius=10)
            
            # Название и описание
            name_text = self.font_small.render(achievement.name, True, COLORS["player"] if is_unlocked else (150, 150, 170))
            scroll_surface.blit(name_text, (card_rect.x + 20, card_rect.y + 15))
            
            desc_text = self.font_tiny.render(achievement.description, True, (180, 180, 200))
            scroll_surface.blit(desc_text, (card_rect.x + 20, card_rect.y + 48))
            
            # Награда
            reward_text = self.font_tiny.render(f"+{achievement.reward} валюты", True, COLORS["warning"])
            scroll_surface.blit(reward_text, (card_rect.right - 140, card_rect.y + 32))
            
            # Кнопка получения награды для выполненных достижений
            if is_unlocked:
                # Проверяем, была ли награда уже получена
                reward_claimed_key = f"{achievement.id}_claimed"
                is_claimed = self.save_system.data.get("achievement_rewards_claimed", {}).get(achievement.id, False)
                
                if not is_claimed:
                    # Кнопка "ПОЛУЧИТЬ"
                    button_w, button_h = 120, 35
                    button_x = card_rect.right - button_w - 15
                    button_y = card_rect.y + 60
                    button_rect = pygame.Rect(button_x, button_y, button_w, button_h)
                    
                    # Проверяем наведение (относительно scroll_surface)
                    mouse_pos = pygame.mouse.get_pos()
                    # Переводим координаты мыши в координаты scroll_surface
                    scroll_mouse_x = mouse_pos[0] - container_x - 2
                    scroll_mouse_y = mouse_pos[1] - container_y - 2 + self.achievements_scroll_offset
                    button_hover = button_rect.collidepoint(scroll_mouse_x, scroll_mouse_y)
                    
                    button_color = (60, 140, 60) if button_hover else (40, 100, 40)
                    pygame.draw.rect(scroll_surface, button_color, button_rect, border_radius=8)
                    pygame.draw.rect(scroll_surface, COLORS["warning"], button_rect, 2, border_radius=8)
                    
                    btn_text = self.font_tiny.render("ПОЛУЧИТЬ", True, COLORS["warning"])
                    btn_text_rect = btn_text.get_rect(center=button_rect.center)
                    scroll_surface.blit(btn_text, btn_text_rect)
                    
                    # Обработка клика
                    if button_hover and pygame.mouse.get_pressed()[0]:
                        if not hasattr(self, '_reward_claim_handled'):
                            self._reward_claim_handled = True
                            # Начисляем награду
                            self.save_system.data["currency"] += achievement.reward
                            # Отмечаем как полученную
                            if "achievement_rewards_claimed" not in self.save_system.data:
                                self.save_system.data["achievement_rewards_claimed"] = {}
                            self.save_system.data["achievement_rewards_claimed"][achievement.id] = True
                            self.save_system.save()
                            self.sound_manager.play_sound("powerup")
                            pygame.time.delay(200)
                            self._reward_claim_handled = False
                else:
                    # Текст "ПОЛУЧЕНО"
                    claimed_text = self.font_tiny.render("✓ ПОЛУЧЕНО", True, (100, 180, 100))
                    scroll_surface.blit(claimed_text, (card_rect.right - 140, card_rect.y + 65))
            
            # Прогресс-бар если не выполнено
            if not is_unlocked:
                try:
                    progress = achievement.get_progress(self)
                    bar_w = 120
                    bar_x = card_rect.right - 320
                    bar_y = card_rect.y + 38
                    pygame.draw.rect(scroll_surface, (40, 40, 50), (bar_x, bar_y, bar_w, 18), border_radius=9)
                    progress_w = int(bar_w * progress)
                    if progress_w > 0:
                        pygame.draw.rect(scroll_surface, COLORS["exp"], (bar_x, bar_y, progress_w, 18), border_radius=9)
                    percent_text = self.font_tiny.render(f"{int(progress*100)}%", True, COLORS["ui"])
                    scroll_surface.blit(percent_text, (bar_x + bar_w + 10, bar_y))
                except:
                    pass
            
            y_offset += card_height + spacing
        
        # Отрисовка scroll_surface на экран
        screen.blit(scroll_surface, (container_x + 2, container_y + 2))
        
        # Полоса прокрутки
        if max_scroll > 0:
            scrollbar_height = max(40, int((container_h / total_content_height) * container_h))
            scrollbar_y = container_y + int((self.achievements_scroll_offset / max_scroll) * (container_h - scrollbar_height))
            scrollbar_rect = pygame.Rect(container_x + container_w - 15, scrollbar_y, 10, scrollbar_height)
            pygame.draw.rect(screen, COLORS["player"], scrollbar_rect, border_radius=5)
        
        # Подсказка о прокрутке
        hint_text = self.font_tiny.render("Используйте ↑↓ или колесико мыши для прокрутки", True, (120, 120, 140))
        screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT - 130))
        
        self.draw_back_button()
    
    def draw_back_button(self):
        button_rect = pygame.Rect(50, HEIGHT - 100, 200, 60)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = button_rect.collidepoint(mouse_pos)
        
        color = COLORS["player"] if is_hover else COLORS["card_border"]
        pygame.draw.rect(screen, color, button_rect, 3, border_radius=8)
        
        text = self.font_small.render("НАЗАД", True, COLORS["player"])
        text_rect = text.get_rect(center=button_rect.center)
        screen.blit(text, text_rect)
        
        if is_hover and pygame.mouse.get_pressed()[0]:
            self.menu_page = "main"
            pygame.time.delay(200)
    
    def draw_level_up(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        title = self.font_huge.render("ПОВЫШЕНИЕ УРОВНЯ!", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render(f"Уровень {self.player.level}", True, COLORS["ui"])
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, 230))
        screen.blit(subtitle, subtitle_rect)
        
        if not hasattr(self, 'current_perks'):
            self.current_perks = PerkManager.get_available_perks(self.player)
        
        card_width, card_height = 350, 200
        total_width = len(self.current_perks) * card_width + (len(self.current_perks) - 1) * 40
        start_x = (WIDTH - total_width) // 2
        card_y = HEIGHT // 2 - card_height // 2
        
        mouse_pos = pygame.mouse.get_pos()
        # Выбираем перк только если кнопка была отпущена ПОСЛЕ появления экрана
        # (level_up_click_handled == False означает что со времени открытия экрана кнопку отпускали)
        can_select = not self.level_up_click_handled
        
        for i, perk in enumerate(self.current_perks):
            card_x = start_x + i * (card_width + 40)
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            is_hover = card_rect.collidepoint(mouse_pos)
            
            rarity_color = RARITY_COLORS.get(perk.rarity, COLORS["card_border"])
            
            card_color = COLORS["card"] if not is_hover else (40, 45, 65)
            pygame.draw.rect(screen, card_color, card_rect, border_radius=15)
            
            # Свечение для редких перков
            if perk.rarity in ["epic", "legendary"]:
                glow_rect = card_rect.inflate(8, 8)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                glow_alpha = 40 if perk.rarity == "epic" else 60
                pygame.draw.rect(glow_surf, (*rarity_color, glow_alpha), glow_surf.get_rect(), border_radius=17)
                screen.blit(glow_surf, glow_rect)
            
            border_width = 5 if is_hover else 3
            pygame.draw.rect(screen, rarity_color, card_rect, border_width, border_radius=15)
            
            # Плашка редкости сверху карточки
            rarity_names = {
                "common": "ОБЫЧНЫЙ", "uncommon": "НЕОБЫЧНЫЙ",
                "rare": "РЕДКИЙ", "epic": "ЭПИЧЕСКИЙ", "legendary": "ЛЕГЕНДАРНЫЙ"
            }
            rarity_label = self.font_tiny.render(rarity_names.get(perk.rarity, ""), True, rarity_color)
            rarity_bg = pygame.Rect(card_rect.x + 8, card_rect.y - 14, rarity_label.get_width() + 16, 22)
            pygame.draw.rect(screen, (20, 22, 38), rarity_bg, border_radius=5)
            pygame.draw.rect(screen, rarity_color, rarity_bg, 1, border_radius=5)
            screen.blit(rarity_label, (rarity_bg.x + 8, rarity_bg.y + 1))  # +1 вместо +3
            
            icon_text = self.font_large.render(perk.icon, True, rarity_color)
            icon_rect = icon_text.get_rect(center=(card_rect.centerx, card_rect.y + 48))
            screen.blit(icon_text, icon_rect)
            
            name_text = self.font_small.render(perk.name, True, COLORS["ui"])
            name_rect = name_text.get_rect(center=(card_rect.centerx, card_rect.y + 105))
            screen.blit(name_text, name_rect)
            
            words = perk.description.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if self.font_tiny.size(test_line)[0] < card_width - 20:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            desc_y = card_rect.y + 135
            for line in lines[:2]:
                desc_text = self.font_tiny.render(line, True, (180, 180, 200))
                desc_rect = desc_text.get_rect(center=(card_rect.centerx, desc_y))
                screen.blit(desc_text, desc_rect)
                desc_y += 22
            
            # Подсказка "НАЖМИТЕ" если можно выбрать, иначе "ОТПУСТИТЕ КНОПКУ"
            if is_hover:
                if can_select:
                    hint = self.font_tiny.render("НАЖМИТЕ ДЛЯ ВЫБОРА", True, rarity_color)
                    pygame.draw.rect(screen, (20, 22, 38),
                                     pygame.Rect(card_rect.x, card_rect.bottom - 28, card_rect.width, 28),
                                     border_radius=12)
                else:
                    hint = self.font_tiny.render("ОТПУСТИТЕ КНОПКУ МЫШИ", True, (180, 180, 200))
                    pygame.draw.rect(screen, (30, 30, 30),
                                     pygame.Rect(card_rect.x, card_rect.bottom - 28, card_rect.width, 28),
                                     border_radius=12)
                hint_rect = hint.get_rect(center=(card_rect.centerx, card_rect.bottom - 14))
                screen.blit(hint, hint_rect)
            
            # Выбор только если кнопка была предварительно отпущена
            if is_hover and can_select and pygame.mouse.get_pressed()[0]:
                self.level_up_click_handled = True
                PerkManager.apply_perk(self.player, perk.id)
                delattr(self, 'current_perks')
                self.state = GameState.PLAY
                self.sound_manager.play_sound("powerup")
                return
    
    def draw_wave_complete(self):
        # Просто показываем таймер вверху экрана
        timer_text = self.font_large.render(
            f"Следующая волна через: {int(self.wave_system.wave_break_time)}s",
            True, COLORS["warning"]
        )
        timer_rect = timer_text.get_rect(center=(WIDTH // 2, 60))
        
        # Полупрозрачный фон для текста
        bg_rect = pygame.Rect(timer_rect.x - 20, timer_rect.y - 10, 
                              timer_rect.width + 40, timer_rect.height + 20)
        pygame.draw.rect(screen, (0, 0, 0, 200), bg_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["warning"], bg_rect, 3, border_radius=10)
        
        screen.blit(timer_text, timer_rect)
    
    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        pause_text = self.font_huge.render("ПАУЗА", True, COLORS["ui"])
        pause_rect = pause_text.get_rect(center=(WIDTH // 2, 100))
        screen.blit(pause_text, pause_rect)
        
        # Собираем список активных перков
        upgrade_texts = []
        p = self.player
        if p.upgrades["max_hp"] > 0:
            upgrade_texts.append(f"❤ +{p.upgrades['max_hp'] * 25} HP")
        if p.upgrades["dmg"] > 0:
            upgrade_texts.append(f"⚔ +{p.upgrades['dmg'] * 5} урона")
        if p.upgrades["fire_rate"] > 0:
            upgrade_texts.append(f"🔥 +{p.upgrades['fire_rate'] * 15}% скорострел.")
        if p.upgrades["speed"] > 0:
            upgrade_texts.append(f"⚡ +{p.upgrades['speed'] * 10}% скорости")
        if p.upgrades["crit_chance"] > 0:
            upgrade_texts.append(f"💥 +{p.upgrades['crit_chance'] * 5}% крит")
        if p.upgrades["multishot"] > 0:
            upgrade_texts.append(f"🎯 {p.multishot} пуль")
        if p.upgrades["piercing"] > 0:
            upgrade_texts.append(f"→ Пробитие {p.piercing}")
        if p.upgrades["lifesteal"] > 0:
            upgrade_texts.append(f"🩸 {int(p.lifesteal * 100)}% вампиризм")
        if p.upgrades["shield"] > 0:
            upgrade_texts.append(f"🛡 +{p.upgrades['shield'] * 50} щита")
        
        # Специальные способности
        if hasattr(p, 'regen') and p.regen > 0:
            upgrade_texts.append(f"💚 {p.regen} HP/сек")
        if hasattr(p, 'armor') and p.armor > 0:
            upgrade_texts.append(f"🛡 {int(p.armor * 100)}% брони")
        if hasattr(p, 'exp_magnet_mult') and p.exp_magnet_mult > 1:
            upgrade_texts.append(f"🧲 +{int((p.exp_magnet_mult - 1) * 100)}% магнит")
        if hasattr(p, 'orbital_bullets'):
            upgrade_texts.append("🌀 Орбита")
        if hasattr(p, 'explosive_bullets'):
            upgrade_texts.append("💣 Взрывы")
        if hasattr(p, 'freeze_bullets'):
            upgrade_texts.append("❄ Заморозка")
        if hasattr(p, 'poison_bullets'):
            upgrade_texts.append("☠ Яд")
        if hasattr(p, 'chain_lightning'):
            upgrade_texts.append("⚡ Молния")
        if hasattr(p, 'reflect_damage') and p.reflect_damage > 0:
            upgrade_texts.append(f"↩ {int(p.reflect_damage * 100)}% отраж.")
        if hasattr(p, 'thorns') and p.thorns > 0:
            upgrade_texts.append(f"🌵 {p.thorns} шипов")
        if p.crit_multiplier > 2.0:
            upgrade_texts.append(f"💥 x{p.crit_multiplier:.1f} крит")
        if p.bullet_size > 1.0:
            upgrade_texts.append(f"⬤ +{int((p.bullet_size - 1) * 100)}% размер")
        
        if not upgrade_texts:
            upgrade_texts = ["Пока нет улучшений"]
        
        # Отрисовка в 2 колонки справа от центра
        upgrades_title = self.font_small.render("АКТИВНЫЕ ПЕРКИ:", True, COLORS["player"])
        title_x = WIDTH - 480
        screen.blit(upgrades_title, (title_x, 180))
        
        col_width = 220
        y_start = 220
        line_height = 32
        max_rows = 12  # Максимум строк в колонке
        
        for i, text in enumerate(upgrade_texts):
            col = i // max_rows
            row = i % max_rows
            x = title_x + col * col_width
            y = y_start + row * line_height
            rendered = self.font_tiny.render(text, True, COLORS["ui"])
            screen.blit(rendered, (x, y))
        
        button_width, button_height = 450, 80
        start_y = HEIGHT // 2 + 50  # Поднято выше
        spacing = 100
        
        buttons = [
            {"text": "ПРОДОЛЖИТЬ", "action": "resume"},
            {"text": "ГЛАВНОЕ МЕНЮ", "action": "menu"}
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        for i, btn_data in enumerate(buttons):
            button_rect = pygame.Rect(
                WIDTH // 2 - button_width // 2,
                start_y + i * spacing,
                button_width,
                button_height
            )
            
            is_hover = button_rect.collidepoint(mouse_pos)
            
            button_color = COLORS["card"] if not is_hover else (40, 45, 65)
            pygame.draw.rect(screen, button_color, button_rect, border_radius=12)
            
            border_color = COLORS["player"] if is_hover else COLORS["card_border"]
            border_width = 4 if is_hover else 2
            pygame.draw.rect(screen, border_color, button_rect, border_width, border_radius=12)
            
            text_color = COLORS["player"] if is_hover else COLORS["ui"]
            button_text = self.font_medium.render(btn_data["text"], True, text_color)
            text_rect = button_text.get_rect(center=button_rect.center)
            screen.blit(button_text, text_rect)
            
            if is_hover and mouse_clicked and not self.pause_click_handled:
                self.pause_click_handled = True
                if btn_data["action"] == "resume":
                    self.state = GameState.PLAY
                elif btn_data["action"] == "menu":
                    self.state = GameState.MENU
                    self.menu_page = "main"
                pygame.time.delay(200)
        
        hint = self.font_small.render("ESC - продолжить", True, (150, 150, 170))
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 80))
        screen.blit(hint, hint_rect)
    
    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        title = self.font_huge.render("GAME OVER", True, COLORS["enemy"])
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 3 - 40))
        screen.blit(title, title_rect)
        
        earned = self.kills + self.player.level * 10 + self.wave_system.current_wave * 20
        earned_text = self.font_medium.render(f"+{earned} валюты заработано", True, COLORS["warning"])
        earned_rect = earned_text.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 40))
        screen.blit(earned_text, earned_rect)
        
        stats = [
            f"СЧЁТ: {self.score}",
            f"УРОВЕНЬ: {self.player.level}",
            f"ВОЛНА: {self.wave_system.current_wave}",
            f"УБИЙСТВ: {self.kills}",
            f"ВЫЖИЛ: {int(self.time_survived)} секунд"
        ]
        
        y_offset = HEIGHT // 2 + 20
        for stat in stats:
            text = self.font_medium.render(stat, True, COLORS["ui"])
            text_rect = text.get_rect(center=(WIDTH // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 60
        
        button_width, button_height = 400, 90
        button_rect = pygame.Rect(
            WIDTH // 2 - button_width // 2,
            HEIGHT - 220,
            button_width,
            button_height
        )
        
        mouse_pos = pygame.mouse.get_pos()
        is_hover = button_rect.collidepoint(mouse_pos)
        
        button_color = COLORS["player"] if is_hover else COLORS["card_border"]
        pygame.draw.rect(screen, button_color, button_rect, 3, border_radius=12)
        
        button_text = self.font_medium.render("ВЕРНУТЬСЯ В МЕНЮ", True, COLORS["player"])
        text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, text_rect)
        
        if is_hover and pygame.mouse.get_pressed()[0]:
            self.state = GameState.MENU
            self.menu_page = "main"
            pygame.time.delay(200)
    
    def game_loop(self):
        self.time_survived += self.dt
        
        self.player.update(self.dt)
        self.update_player_input()
        self.update_shooting()
        
        target_cam = pygame.Vector2(WIDTH // 2, HEIGHT // 2) - self.player.pos
        self.cam += (target_cam - self.cam) * 0.1
        
        self.spawn_enemies()
        self.update_wave_system()
        
        for enemy in self.enemies[:]:
            enemy.update(self.dt, self.player.pos)
        
        for bullet in self.bullets[:]:
            if bullet.update(self.dt):
                self.bullets.remove(bullet)
        
        self.update_combat()
        self.update_exp_gems()
        self.particle_system.update(self.dt)
        
        # РИСОВАНИЕ
        self.draw_background()
        self.particle_system.draw(screen, self.cam)
        
        for gem in self.exp_gems:
            glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*COLORS["exp_glow"], 80), (15, 15), 12)
            screen.blit(glow_surf, (gem.x + self.cam.x - 15, gem.y + self.cam.y - 15))
            pygame.draw.circle(screen, COLORS["exp"], 
                             (int(gem.x + self.cam.x), int(gem.y + self.cam.y)), 5)
        
        for enemy in self.enemies:
            enemy.draw(screen, self.cam)
        
        for bullet in self.bullets:
            bullet.draw(screen, self.cam)
        
        self.player.draw(screen, self.cam)
        self.draw_ui()
    
    def run(self):
        while True:
            self.dt = self.clock.tick(FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if self.rebinding_key is not None:
                        self.save_system.data["controls"][self.rebinding_key] = event.key
                        self.save_system.save()
                        self.rebinding_key = None
                    
                    if event.key == pygame.K_ESCAPE:
                        if self.state == GameState.PLAY:
                            self.state = GameState.PAUSE
                            self.pause_click_handled = False
                        elif self.state == GameState.PAUSE:
                            self.state = GameState.PLAY
                        elif self.state == GameState.WAVE_COMPLETE:
                            self.state = GameState.PAUSE
                            self.pause_click_handled = False
                    
                    # Переключение автострельбы настраиваемой кнопкой
                    auto_fire_key = self.save_system.data["controls"].get("auto_fire_toggle", pygame.K_TAB)
                    if event.key == auto_fire_key and self.state in [GameState.PLAY, GameState.WAVE_COMPLETE]:
                        self.save_system.data["settings"]["auto_fire"] = not self.save_system.data["settings"]["auto_fire"]
                        self.save_system.save()
                
                # Прокрутка колесиком мыши для меню достижений
                if event.type == pygame.MOUSEWHEEL:
                    if self.state == GameState.MENU and self.menu_page == "achievements":
                        # Вычисляем максимальную прокрутку
                        achievements_count = len(AchievementSystem.ACHIEVEMENTS)
                        card_height = 90
                        spacing = 15
                        container_h = HEIGHT - 330
                        total_content_height = achievements_count * (card_height + spacing)
                        max_scroll = max(0, total_content_height - container_h + 40)
                        
                        # Прокрутка (event.y положительное = вверх, отрицательное = вниз)
                        scroll_speed = 30
                        self.achievements_scroll_offset -= event.y * scroll_speed
                        self.achievements_scroll_offset = max(0, min(max_scroll, self.achievements_scroll_offset))
                
                if event.type == pygame.MOUSEBUTTONUP:
                    self.pause_click_handled = False
                    self.level_up_click_handled = False
            
            if self.state == GameState.MENU:
                self.menu_time += self.dt
                self.draw_menu()
            
            elif self.state == GameState.MODE_SELECT:
                self.draw_mode_select()
            
            elif self.state == GameState.PLAY:
                self.game_loop()
            
            elif self.state == GameState.LEVEL_UP:
                self.draw_background()
                for enemy in self.enemies:
                    enemy.draw(screen, self.cam)
                self.player.draw(screen, self.cam)
                self.draw_level_up()
            
            elif self.state == GameState.WAVE_COMPLETE:
                # Игра продолжается, только не спавнятся враги
                self.time_survived += self.dt
                
                self.player.update(self.dt)
                self.update_player_input()
                self.update_shooting()
                
                target_cam = pygame.Vector2(WIDTH // 2, HEIGHT // 2) - self.player.pos
                self.cam += (target_cam - self.cam) * 0.1
                
                for enemy in self.enemies[:]:
                    enemy.update(self.dt, self.player.pos)
                
                for bullet in self.bullets[:]:
                    if bullet.update(self.dt):
                        self.bullets.remove(bullet)
                
                self.update_combat()
                self.update_exp_gems()
                self.particle_system.update(self.dt)
                
                # Рисование
                self.draw_background()
                self.particle_system.draw(screen, self.cam)
                
                for gem in self.exp_gems:
                    glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*COLORS["exp_glow"], 80), (15, 15), 12)
                    screen.blit(glow_surf, (gem.x + self.cam.x - 15, gem.y + self.cam.y - 15))
                    pygame.draw.circle(screen, COLORS["exp"], 
                                     (int(gem.x + self.cam.x), int(gem.y + self.cam.y)), 5)
                
                for enemy in self.enemies:
                    enemy.draw(screen, self.cam)
                
                for bullet in self.bullets:
                    bullet.draw(screen, self.cam)
                
                self.player.draw(screen, self.cam)
                self.draw_ui()
                self.draw_wave_complete()
                
                # Автоматически обновляем перерыв
                if self.wave_system.update_break(self.dt):
                    self.wave_system.start_wave()
                    self.state = GameState.PLAY
            
            elif self.state == GameState.PAUSE:
                self.draw_background()
                for gem in self.exp_gems:
                    pygame.draw.circle(screen, COLORS["exp"], 
                                     (int(gem.x + self.cam.x), int(gem.y + self.cam.y)), 5)
                for enemy in self.enemies:
                    enemy.draw(screen, self.cam)
                for bullet in self.bullets:
                    bullet.draw(screen, self.cam)
                self.player.draw(screen, self.cam)
                self.draw_ui()
                self.draw_pause()
            
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over()
            
            # Рисуем курсор поверх всего
            self.draw_cursor()
            
            pygame.display.flip()

# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

if __name__ == "__main__":
    engine = Engine()
    engine.run()
