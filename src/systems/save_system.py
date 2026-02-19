import json
import os
from typing import Dict, Any

class SaveSystem:
    def __init__(self):
        # Сохранение в папку data/
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "..", "data")
        
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
                "up": 119,  # pygame.K_w
                "down": 115,  # pygame.K_s
                "left": 97,  # pygame.K_a
                "right": 100,  # pygame.K_d
                "dash": 32,  # pygame.K_SPACE
                "auto_fire_toggle": 9
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