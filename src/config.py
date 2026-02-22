import pygame
from enum import Enum

FPS = 60
pygame.init()

try:
    info = pygame.display.Info()
    WIDTH, HEIGHT = info.current_w, info.current_h 
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
except:
    WIDTH, HEIGHT = 1280, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

COLORS = {
    "bg": (8, 10, 20),
    "bg_alt": (12, 15, 28),
    "grid": (25, 30, 50),
    "player": (0, 255, 204),
    "player_glow": (0, 200, 160),
    "enemy": (255, 46, 99),
    "enemy_glow": (200, 30, 80),
    "elite_enemy": (255, 140, 0),
    "boss": (150, 0, 255),
    "exp": (0, 200, 255),
    "exp_glow": (0, 150, 200),
    "ui": (240, 240, 255),
    "card": (30, 35, 55),
    "card_border": (60, 70, 100),
    "health": (255, 80, 80),
    "shield": (100, 200, 255),
    "warning": (255, 200, 0),
    "bullet": (255, 255, 200)
}

# Цвета редкости перков
RARITY_COLORS = {
    "common": (200, 200, 200),      # Серый
    "uncommon": (100, 255, 100),    # Зеленый
    "rare": (100, 150, 255),        # Синий
    "epic": (200, 100, 255),        # Фиолетовый
    "legendary": (255, 200, 0)      # Золотой
}

PLAYER_SKINS = {
    "default": {
        "name": "Стандартный", 
        "color": (0, 255, 204), 
        "glow": (0, 200, 160),
        "condition": "Доступен с начала",
        "effect": "Сбалансированные характеристики"
    },
    "red": {
        "name": "Красный охотник", 
        "color": (255, 80, 80), 
        "glow": (200, 60, 60),
        "condition": "500 убийств (суммарно)",
        "effect": "+10% к урону"
    },
    "purple": {
        "name": "Фиолетовый призрак", 
        "color": (180, 100, 255), 
        "glow": (140, 80, 200),
        "condition": "Достичь 15 уровня",
        "effect": "+15% к скорости"
    },
    "gold": {
        "name": "Золотой страж", 
        "color": (255, 215, 0), 
        "glow": (200, 170, 0),
        "condition": "Набрать счёт 10000 за игру",
        "effect": "+20% к здоровью"
    },
    "green": {
        "name": "Зеленый сталкер", 
        "color": (50, 255, 100), 
        "glow": (40, 200, 80),
        "condition": "Выжить 10 минут за игру",
        "effect": "+10% к скорострельности"
    },
    "cyan": {
        "name": "Киберхакер", 
        "color": (0, 220, 255), 
        "glow": (0, 180, 220),
        "condition": "Получить 30 достижений",
        "effect": "+10% к опыту"
    },
    "orange": {
        "name": "Огненный танк", 
        "color": (255, 140, 0), 
        "glow": (220, 110, 0),
        "condition": "2000 убийств (суммарно)",
        "effect": "+8% к броне"
    },
    "white": {
        "name": "Призрак войны", 
        "color": (240, 240, 255), 
        "glow": (200, 200, 220),
        "condition": "Достичь 25 уровня",
        "effect": "+5% ко всем характеристикам"
    },
    "pink": {
        "name": "Розовый ниндзя",
        "color": (255, 120, 200),
        "glow": (220, 90, 170),
        "condition": "Использовать рывок 100 раз",
        "effect": "+20% к скорости рывка"
    },
    "dark": {
        "name": "Тёмный воин",
        "color": (80, 80, 120),
        "glow": (60, 60, 100),
        "condition": "5000 убийств (суммарно)",
        "effect": "+15% к урону, -5% к скорости"
    },
}

class GameState(Enum):
    MENU = "MENU"
    PLAY = "PLAY"
    LEVEL_UP = "LEVEL_UP"
    PAUSE = "PAUSE"
    GAME_OVER = "GAME_OVER"
    WAVE_COMPLETE = "WAVE_COMPLETE"
    MODE_SELECT = "MODE_SELECT"

class GameMode(Enum):
    WAVES = "WAVES"
    ENDLESS = "ENDLESS"