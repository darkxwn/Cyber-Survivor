import pygame
from dataclasses import dataclass
import random
import os
from entities import *
import json

class SaveSystem:
    def __init__(self):
        # Сохранение в папку data/
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "../data")
        
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
            "active_ability": "",  # selected active ability
            "owned_abilities": [],  # purchased abilities
            "unlocked_skins": ["default"],
            "current_skin": "default",
            "controls": {
                "up": pygame.K_w,
                "down": pygame.K_s,
                "left": pygame.K_a,
                "right": pygame.K_d,
                "dash": pygame.K_SPACE,
                "auto_fire_toggle": pygame.K_TAB,
                "ability": pygame.K_q
            },
            "settings": {
                "auto_fire": False,
                "screen_shake": True,
                "particles": True,
                "damage_numbers": True,
                "wave_break_duration": 10,  # секунды между волнами (3-30)
                "cursor_mode": "game"  # "game" or "system"
            },
            "currency": 0,
            "achievements": {
                "first_blood": False,
                "killer_10": False, "killer_50": False, "killer_100": False,
                "killer_250": False, "killer_500": False, "killer_1000": False, "killer_2000": False,
                "survivor_1": False, "survivor_5": False, "survivor_10": False,
                "survivor_20": False, "survivor_30": False, "survivor_60": False,
                "wave_master_3": False, "wave_master_5": False, "wave_master_10": False,
                "wave_master_15": False, "wave_master_20": False, "wave_master_30": False,
                "level_expert_5": False, "level_expert_10": False,
                "level_expert_20": False, "level_expert_30": False,
                "collector_1000": False, "collector_5000": False, "collector_10000": False,
                "spender": False, "spender_25": False,
                "perfectionist": False,
                "speed_demon": False, "speed_demon_max": False,
                "tank": False, "tank_2": False,
                "glass_cannon": False,
                "shielder_ach": False, "shielder_2": False,
                "dasher": False, "dasher_50": False, "dasher_200": False,
                "multigunner": False, "multigunner_max": False,
                "poison_master": False, "lightning_master": False,
                "orbital_master": False, "freeze_master": False,
                "explosion_master": False, "reflect_master": False,
                "vampire": False, "sniper_ach": False,
                "games_10": False, "games_50": False, "games_100": False,
                "score_1000": False, "score_5000": False, "score_20000": False,
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
        # === УБИЙСТВА (многоуровневые) ===
        "first_blood": Achievement(
            "first_blood", "Первая кровь", "Убейте первого врага",
            lambda engine: engine.kills >= 1, 25
        ),
        "killer_10": Achievement(
            "killer_10", "Охотник I", "Убейте 10 врагов за игру",
            lambda engine: engine.kills >= 10, 30
        ),
        "killer_50": Achievement(
            "killer_50", "Охотник II", "Убейте 50 врагов за игру",
            lambda engine: engine.kills >= 50, 60
        ),
        "killer_100": Achievement(
            "killer_100", "Убийца I", "Убейте 100 врагов за игру",
            lambda engine: engine.kills >= 100, 100
        ),
        "killer_250": Achievement(
            "killer_250", "Убийца II", "Убейте 250 врагов за игру",
            lambda engine: engine.kills >= 250, 175
        ),
        "killer_500": Achievement(
            "killer_500", "Серийный убийца", "Убейте 500 врагов за игру",
            lambda engine: engine.kills >= 500, 250
        ),
        "killer_1000": Achievement(
            "killer_1000", "Геноцид", "Убейте 1000 врагов за игру",
            lambda engine: engine.kills >= 1000, 500
        ),
        "killer_2000": Achievement(
            "killer_2000", "Истребитель", "Убейте 2000 врагов за игру",
            lambda engine: engine.kills >= 2000, 800
        ),
        
        # === ВЫЖИВАНИЕ (многоуровневые) ===
        "survivor_1": Achievement(
            "survivor_1", "Первые минуты", "Продержитесь 1 минуту",
            lambda engine: engine.time_survived >= 60, 25
        ),
        "survivor_5": Achievement(
            "survivor_5", "Бывалый", "Продержитесь 5 минут",
            lambda engine: engine.time_survived >= 300, 75
        ),
        "survivor_10": Achievement(
            "survivor_10", "Выживший I", "Продержитесь 10 минут",
            lambda engine: engine.time_survived >= 600, 100
        ),
        "survivor_20": Achievement(
            "survivor_20", "Выживший II", "Продержитесь 20 минут",
            lambda engine: engine.time_survived >= 1200, 200
        ),
        "survivor_30": Achievement(
            "survivor_30", "Выживший III", "Продержитесь 30 минут",
            lambda engine: engine.time_survived >= 1800, 350
        ),
        "survivor_60": Achievement(
            "survivor_60", "Мастер выживания", "Продержитесь 60 минут",
            lambda engine: engine.time_survived >= 3600, 700
        ),
        
        # === ВОЛНЫ (многоуровневые) ===
        "wave_master_3": Achievement(
            "wave_master_3", "Новобранец", "Пройдите 3 волны",
            lambda engine: engine.wave_system.current_wave >= 4, 50
        ),
        "wave_master_5": Achievement(
            "wave_master_5", "Воин волн I", "Пройдите 5 волн",
            lambda engine: engine.wave_system.current_wave >= 6, 100
        ),
        "wave_master_10": Achievement(
            "wave_master_10", "Воин волн II", "Пройдите 10 волн",
            lambda engine: engine.wave_system.current_wave >= 11, 200
        ),
        "wave_master_15": Achievement(
            "wave_master_15", "Мастер волн I", "Пройдите 15 волн",
            lambda engine: engine.wave_system.current_wave >= 16, 300
        ),
        "wave_master_20": Achievement(
            "wave_master_20", "Мастер волн II", "Пройдите 20 волн",
            lambda engine: engine.wave_system.current_wave >= 21, 500
        ),
        "wave_master_30": Achievement(
            "wave_master_30", "Легенда волн", "Пройдите 30 волн",
            lambda engine: engine.wave_system.current_wave >= 31, 800
        ),
        
        # === УРОВНИ ИГРОКА (многоуровневые) ===
        "level_expert_5": Achievement(
            "level_expert_5", "Ученик", "Достигните 5 уровня",
            lambda engine: engine.player.level >= 5, 75
        ),
        "level_expert_10": Achievement(
            "level_expert_10", "Эксперт I", "Достигните 10 уровня",
            lambda engine: engine.player.level >= 10, 150
        ),
        "level_expert_20": Achievement(
            "level_expert_20", "Эксперт II", "Достигните 20 уровня",
            lambda engine: engine.player.level >= 20, 300
        ),
        "level_expert_30": Achievement(
            "level_expert_30", "Легенда уровней", "Достигните 30 уровня",
            lambda engine: engine.player.level >= 30, 500
        ),
        
        # === ЭКОНОМИКА ===
        "collector_1000": Achievement(
            "collector_1000", "Коллекционер I", "Накопите 1000 валюты",
            lambda engine: engine.save_system.data["currency"] >= 1000, 200
        ),
        "collector_5000": Achievement(
            "collector_5000", "Коллекционер II", "Накопите 5000 валюты",
            lambda engine: engine.save_system.data["currency"] >= 5000, 400
        ),
        "collector_10000": Achievement(
            "collector_10000", "Магнат", "Накопите 10000 валюты",
            lambda engine: engine.save_system.data["currency"] >= 10000, 700
        ),
        "spender": Achievement(
            "spender", "Транжира I", "Вложите 10+ уровней модулей",
            lambda engine: sum(engine.save_system.data["modules"].values()) >= 10, 150
        ),
        "spender_25": Achievement(
            "spender_25", "Транжира II", "Вложите 25+ уровней модулей",
            lambda engine: sum(engine.save_system.data["modules"].values()) >= 25, 300
        ),
        
        # === БОЕВЫЕ СТИЛИ ===
        "perfectionist": Achievement(
            "perfectionist", "Перфекционист", "Пройдите волну без получения урона",
            lambda engine: hasattr(engine, 'no_damage_wave') and engine.no_damage_wave, 300
        ),
        "speed_demon": Achievement(
            "speed_demon", "Демон скорости I", "Наберите 5+ к скорости",
            lambda engine: engine.player.upgrades.get("speed", 0) >= 5, 150
        ),
        "speed_demon_max": Achievement(
            "speed_demon_max", "Демон скорости II", "Наберите 10+ к скорости",
            lambda engine: engine.player.upgrades.get("speed", 0) >= 10, 250
        ),
        "tank": Achievement(
            "tank", "Танк I", "Наберите 200+ HP",
            lambda engine: engine.player.max_hp >= 200, 150
        ),
        "tank_2": Achievement(
            "tank_2", "Танк II", "Наберите 500+ HP",
            lambda engine: engine.player.max_hp >= 500, 300
        ),
        "glass_cannon": Achievement(
            "glass_cannon", "Стеклянная пушка", "50+ урона при <100 HP",
            lambda engine: engine.player.dmg >= 50 and engine.player.max_hp < 100, 250
        ),
        "shielder_ach": Achievement(
            "shielder_ach", "Щитоносец I", "Наберите 200+ щита",
            lambda engine: engine.player.max_shield >= 200, 150
        ),
        "shielder_2": Achievement(
            "shielder_2", "Щитоносец II", "Наберите 500+ щита",
            lambda engine: engine.player.max_shield >= 500, 300
        ),
        
        # === УМЕНИЯ ===
        "dasher": Achievement(
            "dasher", "Мастер рывка I", "Используйте рывок 25 раз",
            lambda engine: getattr(engine, 'dash_count', 0) >= 25, 75
        ),
        "dasher_50": Achievement(
            "dasher_50", "Мастер рывка II", "Используйте рывок 50 раз",
            lambda engine: getattr(engine, 'dash_count', 0) >= 50, 150
        ),
        "dasher_200": Achievement(
            "dasher_200", "Мастер рывка III", "Используйте рывок 200 раз",
            lambda engine: getattr(engine, 'dash_count', 0) >= 200, 300
        ),
        "multigunner": Achievement(
            "multigunner", "Многозарядный I", "Иметь 3+ пули одновременно",
            lambda engine: engine.player.multishot >= 3, 150
        ),
        "multigunner_max": Achievement(
            "multigunner_max", "Многозарядный II", "Иметь 6 пуль одновременно",
            lambda engine: engine.player.multishot >= 6, 300
        ),
        
        # === СПЕЦИАЛЬНЫЕ ПЕРКИ ===
        "poison_master": Achievement(
            "poison_master", "Отравитель", "Взять перк яда",
            lambda engine: hasattr(engine.player, 'poison_bullets') and engine.player.poison_bullets, 100
        ),
        "lightning_master": Achievement(
            "lightning_master", "Громовержец", "Взять перк цепной молнии",
            lambda engine: hasattr(engine.player, 'chain_lightning') and engine.player.chain_lightning > 0, 100
        ),
        "orbital_master": Achievement(
            "orbital_master", "Орбитальщик", "Взять орбитальную защиту",
            lambda engine: hasattr(engine.player, 'orbital_bullets') and engine.player.orbital_bullets > 0, 100
        ),
        "freeze_master": Achievement(
            "freeze_master", "Ледяной маг", "Взять перк заморозки",
            lambda engine: hasattr(engine.player, 'freeze_bullets') and engine.player.freeze_bullets, 100
        ),
        "explosion_master": Achievement(
            "explosion_master", "Подрывник", "Взять перк взрывных пуль",
            lambda engine: hasattr(engine.player, 'explosive_bullets') and engine.player.explosive_bullets, 100
        ),
        "reflect_master": Achievement(
            "reflect_master", "Зеркало", "Взять перк отражения",
            lambda engine: hasattr(engine.player, 'reflect_damage') and engine.player.reflect_damage > 0, 100
        ),
        
        # === ОСОБЫЕ ДОСТИЖЕНИЯ ===
        "vampire": Achievement(
            "vampire", "Вампир", "Набрать 50%+ вампиризма",
            lambda engine: engine.player.lifesteal >= 0.5, 200
        ),
        "sniper_ach": Achievement(
            "sniper_ach", "Снайпер", "Иметь 50%+ крит шанс",
            lambda engine: engine.player.crit_chance >= 0.5, 200
        ),
        "games_10": Achievement(
            "games_10", "Ветеран I", "Сыграйте 10 игр",
            lambda engine: engine.save_system.data["stats"]["games_played"] >= 10, 100
        ),
        "games_50": Achievement(
            "games_50", "Ветеран II", "Сыграйте 50 игр",
            lambda engine: engine.save_system.data["stats"]["games_played"] >= 50, 300
        ),
        "games_100": Achievement(
            "games_100", "Ветеран III", "Сыграйте 100 игр",
            lambda engine: engine.save_system.data["stats"]["games_played"] >= 100, 600
        ),
        "score_1000": Achievement(
            "score_1000", "Счётовод I", "Набрать 1000 очков за игру",
            lambda engine: engine.score >= 1000, 75
        ),
        "score_5000": Achievement(
            "score_5000", "Счётовод II", "Набрать 5000 очков за игру",
            lambda engine: engine.score >= 5000, 150
        ),
        "score_20000": Achievement(
            "score_20000", "Счётовод III", "Набрать 20000 очков за игру",
            lambda engine: engine.score >= 20000, 400
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
    
    MAX_PERK_STACKS = {
        "hp": 10, "hp_big": 5, "dmg": 20, "dmg_big": 10,
        "fire_rate": 8, "fire_rate_big": 4,
        "speed": 10, "speed_big": 5,
        "multishot": 4, "multishot_big": 2,
        "lifesteal": 5, "lifesteal_big": 2,
        "shield": 15, "shield_big": 8,
        "regen": 10, "armor": 3,
        "crit": 10, "crit_big": 5, "crit_damage": 3,
        "piercing": 5, "piercing_big": 3,
        "bullet_size": 2, "bullet_speed": 5, "bullet_lifetime": 5,
        "exp_magnet": 5, "exp_boost": 5, "exp_multiplier": 1, "gold_boost": 3,
        "dash_cooldown": 3, "dash_invuln": 3,
        "parallel_shot": 2,
    }
    
    @staticmethod
    def get_available_perks(player: 'Player' = None) -> List[PerkOption]:
        all_perks = [
            # ===== БАЗОВЫЕ ХАРАКТЕРИСТИКИ =====
            PerkOption("hp", "+25 MAX HP", "Увеличивает максимальное здоровье на 25", "[+]", "common"),
            PerkOption("hp_big", "+50 MAX HP", "Значительно увеличивает здоровье на 50", "[++]", "uncommon"),
            PerkOption("dmg", "+5 УРОН", "Каждая пуля наносит на 5 больше урона", "[!]", "common"),
            PerkOption("dmg_big", "+15 УРОН", "Каждая пуля наносит на 15 больше урона", "[!!]", "uncommon"),
            PerkOption("fire_rate", "+15% СКОРОСТРЕЛЬНОСТЬ", "Стреляйте быстрее — пули чаще", "[>>]", "common"),
            PerkOption("fire_rate_big", "+30% СКОРОСТРЕЛЬНОСТЬ", "Сильное ускорение темпа стрельбы", "[>>>]", "rare"),
            PerkOption("speed", "+10% СКОРОСТЬ", "Двигайтесь быстрее, уклоняйтесь легче", "[>]", "common"),
            PerkOption("speed_big", "+25% СКОРОСТЬ", "Значительный прирост скорости движения", "[>>]", "uncommon"),
            
            # ===== КРИТЫ И МНОЖИТЕЛИ =====
            PerkOption("crit", "+5% КРИТ ШАНС", "Критические попадания: +5% вероятность", "[*]", "uncommon"),
            PerkOption("crit_big", "+15% КРИТ ШАНС", "Намного больше критических ударов", "[**]", "rare"),
            PerkOption("crit_damage", "+50% КРИТ УРОН", "Критические удары становятся намного сильнее", "[***]", "epic"),
            
            # ===== ВЫСТРЕЛЫ И ПРОБИТИЕ =====
            PerkOption("multishot", "+1 ВЫСТРЕЛ", "Стреляйте несколькими пулями в разные стороны", "[|||]", "rare"),
            PerkOption("twin_shot", "ДВОЙНОЙ ВЫСТРЕЛ", "Дополнительная пуля летит вслед за основной. Макс 3.", "[=|]", "uncommon"),
            PerkOption("piercing", "+1 ПРОБИТИЕ", "Пули пробивают врагов и летят дальше", "[->]", "uncommon"),
            PerkOption("piercing_big", "+3 ПРОБИТИЕ", "Пули пробивают сразу нескольких врагов", "[->>]", "rare"),
            
            # ===== ЗАЩИТА И ВЫЖИВАНИЕ =====
            PerkOption("shield", "+50 ЩИТ", "Барьер поглощает урон вместо здоровья", "[#]", "common"),
            PerkOption("shield_big", "+100 ЩИТ", "Мощный щит для защиты от атак", "[##]", "uncommon"),
            PerkOption("lifesteal", "+10% ВАМПИРИЗМ", "Восстанавливайте здоровье с каждого попадания", "[<3]", "uncommon"),
            PerkOption("lifesteal_big", "+25% ВАМПИРИЗМ", "Мощный вампиризм — частое восстановление", "[<3<3]", "rare"),
            PerkOption("regen", "РЕГЕНЕРАЦИЯ +1 HP/сек", "Медленно восстанавливает здоровье со временем", "[+~]", "rare"),
            PerkOption("armor", "+20% БРОНЯ", "Уменьшает весь получаемый урон на 20%", "[[]", "epic"),
            
            # ===== МОДИФИКАТОРЫ ПУЛЬ =====
            PerkOption("bullet_size", "+50% РАЗМЕР ПУЛЬ", "Крупнее пуля — проще попасть по врагу", "[O]", "common"),
            PerkOption("bullet_speed", "+30% СКОРОСТЬ ПУЛЬ", "Пули летят быстрее, дальше уходят", "[=>]", "common"),
            PerkOption("bullet_lifetime", "+50% ДАЛЬНОСТЬ", "Пули летят значительно дальше перед исчезновением", "[==>]", "common"),
            
            # ===== ОПЫТ И ПРОГРЕССИЯ =====
            PerkOption("exp_magnet", "МАГНИТ +50%", "Кристаллы опыта притягиваются на большее расстояние", "[<*>]", "uncommon"),
            PerkOption("exp_boost", "БОНУС К ОПЫТУ +25%", "Получайте на 25% больше опыта от кристаллов", "[XP+]", "uncommon"),
            PerkOption("exp_multiplier", "МНОЖИТЕЛЬ ОПЫТА x2", "Удваивает весь получаемый опыт", "[XP*2]", "rare"),
            PerkOption("gold_boost", "+50% ВАЛЮТА", "Получайте больше монет после каждой игры", "[$+]", "uncommon"),
            
            # ===== ОСОБЫЕ СПОСОБНОСТИ =====
            PerkOption("dash_cooldown", "-30% ПЕРЕЗАРЯДКА РЫВКА", "Используйте рывок значительно чаще", "[<-]", "rare"),
            PerkOption("dash_invuln", "+50% НЕУЯЗВИМОСТЬ РЫВКА", "Дольше неуязвимы во время рывка", "[<*-]", "rare"),
            
            # ===== УЛЬТЫ И ЛЕГЕНДАРНЫЕ (ОДНОРАЗОВЫЕ) =====
            PerkOption("heal", "ПОЛНОЕ ВОССТАНОВЛЕНИЕ", "Немедленно восстанавливает всё HP и щит", "[HEAL]", "epic"),
            PerkOption("orbital", "ОРБИТАЛЬНАЯ ЗАЩИТА", "Снаряды вращаются вокруг вас и бьют близких врагов", "[ORB]", "legendary"),
            PerkOption("explosion", "ВЗРЫВНЫЕ ПУЛИ", "Каждое попадание создаёт взрыв вокруг врага", "[BOOM]", "legendary"),
            PerkOption("freeze", "ЗАМОРАЖИВАНИЕ", "Пули замедляют врагов — они двигаются вдвое медленнее", "[ICE]", "legendary"),
            PerkOption("poison", "ЯДОВИТЫЕ ПУЛИ", "Пули оставляют яд: 15 урона в секунду, 3 секунды", "[POISON]", "legendary"),
            PerkOption("chain", "ЦЕПНАЯ МОЛНИЯ", "Урон перескакивает на ближних врагов вокруг цели", "[CHAIN]", "legendary"),
            PerkOption("reflect", "ОТРАЖЕНИЕ", "25% получаемого урона возвращается врагу", "[REFLECT]", "legendary"),
            PerkOption("thorns", "ШИПЫ", "Враги получают 10 урона при каждой атаке на вас", "[THORNS]", "legendary"),
        ]
        
        # Фильтруем одноразовые перки, которые уже взяты
        if player and hasattr(player, 'acquired_perks'):
            all_perks = [p for p in all_perks if p.id not in player.acquired_perks or p.id not in PerkManager.ONE_TIME_PERKS]

        # Балансовые ограничения
        if player:
            up = player.upgrades
            filtered = []
            for p in all_perks:
                # HP: не более 10 стаков (+25 каждый = +250 макс)
                if p.id == "hp" and up.get("max_hp", 0) >= 10: continue
                if p.id == "hp_big" and up.get("max_hp", 0) >= 8: continue
                # Урон: не более 8 стаков
                if p.id == "dmg" and up.get("dmg", 0) >= 8: continue
                if p.id == "dmg_big" and up.get("dmg", 0) >= 6: continue
                # HP: не более +500 доп. хп
                if p.id in ("hp", "hp_big") and player.max_hp >= 600: continue
                # Урон: не более +150
                if p.id in ("dmg", "dmg_big") and player.upgrades.get("dmg", 0) >= 20: continue
                # Скорострельность: нижняя граница 75мс
                if p.id in ("fire_rate", "fire_rate_big") and player.fire_rate <= 75: continue
                # Скорость: не более 5 стаков
                if p.id in ("speed", "speed_big") and up.get("speed", 0) >= 5: continue
                # Вампиризм: max 70%
                if p.id in ("lifesteal", "lifesteal_big") and player.lifesteal >= 0.70: continue
                # Мультишот в стороны: не более 6 пуль
                if p.id == "multishot" and player.multishot >= 6: continue
                if p.id == "multishot_big" and player.multishot >= 4: continue
                # Двойной выстрел: не более 3 стаков
                if p.id == "twin_shot" and getattr(player, 'twin_shot', 0) >= 3: continue
                # Опыт: не более 4x суммарно
                if p.id in ("exp_boost", "exp_multiplier") and getattr(player, 'exp_multiplier', 1.0) >= 4.0: continue
                # Броня: max 60%
                if p.id == "armor" and getattr(player, 'armor', 0) >= 0.60: continue
                filtered.append(p)
            all_perks = filtered

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
            player.multishot = min(6, player.multishot + 1)
            player.upgrades["multishot"] += 1
        elif perk_id == "twin_shot":
            if not hasattr(player, 'twin_shot'):
                player.twin_shot = 0
            player.twin_shot = min(3, player.twin_shot + 1)
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
            player.lifesteal = min(0.75, player.lifesteal + 0.10)
            player.upgrades["lifesteal"] += 1
        elif perk_id == "lifesteal_big":
            player.lifesteal = min(0.75, player.lifesteal + 0.25)
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