import pygame
from typing import Tuple

class HUD:
    def __init__(self):
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
    def draw(self, surf: pygame.Surface, player, enemies, game_state, score: int, wave: int, dt: float):
        # Рисуем основной интерфейс
        self.draw_player_info(surf, player)
        self.draw_game_info(surf, score, wave)
        
        # В зависимости от состояния игры рисуем соответствующие элементы
        if game_state == "PAUSE":
            self.draw_pause_menu(surf)
        elif game_state == "GAME_OVER":
            self.draw_game_over(surf)
        elif game_state == "LEVEL_UP":
            self.draw_level_up_screen(surf)
    
    def draw_player_info(self, surf: pygame.Surface, player):
        # Полоска здоровья
        hp_bar_width = 200
        hp_bar_height = 20
        hp_ratio = player.hp / player.max_hp
        
        # Фон полоски
        pygame.draw.rect(surf, (60, 60, 60), 
                        (20, 20, hp_bar_width, hp_bar_height))
        # Заполнение полоски
        pygame.draw.rect(surf, (255, 80, 80) if hp_ratio > 0.3 else (255, 200, 0),
                        (20, 20, int(hp_bar_width * hp_ratio), hp_bar_height))
        # Граница
        pygame.draw.rect(surf, (200, 200, 200), 
                        (20, 20, hp_bar_width, hp_bar_height), 2)
        
        # Текст здоровья
        hp_text = self.font_small.render(f"{int(player.hp)}/{player.max_hp}", True, (255, 255, 255))
        surf.blit(hp_text, (25, 25))
        
        # Полоска щита (если есть)
        if player.max_shield > 0:
            shield_ratio = player.shield / player.max_shield
            pygame.draw.rect(surf, (60, 60, 60), 
                            (20, 50, hp_bar_width, hp_bar_height))
            pygame.draw.rect(surf, (100, 200, 255),
                            (20, 50, int(hp_bar_width * shield_ratio), hp_bar_height))
            pygame.draw.rect(surf, (100, 150, 200), 
                            (20, 50, hp_bar_width, hp_bar_height), 2)
            
            shield_text = self.font_small.render(f"{int(player.shield)}/{player.max_shield}", True, (255, 255, 255))
            surf.blit(shield_text, (25, 55))
        
        # Полоска опыта
        exp_bar_width = 200
        exp_bar_height = 10
        exp_ratio = player.exp / player.exp_to_next
        
        pygame.draw.rect(surf, (60, 60, 60), 
                        (20, 80, exp_bar_width, exp_bar_height))
        pygame.draw.rect(surf, (0, 200, 255),
                        (20, 80, int(exp_bar_width * exp_ratio), exp_bar_height))
        pygame.draw.rect(surf, (100, 150, 200), 
                        (20, 80, exp_bar_width, exp_bar_height), 1)
        
        # Текст уровня
        level_text = self.font_small.render(f"Lvl {player.level}", True, (255, 255, 255))
        surf.blit(level_text, (25, 95))
    
    def draw_game_info(self, surf: pygame.Surface, score: int, wave: int):
        # Счет
        score_text = self.font_medium.render(f"Score: {score}", True, (240, 240, 255))
        surf.blit(score_text, (surf.get_width() - score_text.get_width() - 20, 20))
        
        # Волна
        wave_text = self.font_medium.render(f"Wave: {wave}", True, (240, 240, 255))
        surf.blit(wave_text, (surf.get_width() - wave_text.get_width() - 20, 60))
        
        # Количество врагов
        enemy_count_text = self.font_small.render(f"Enemies: {len(enemies)}", True, (240, 240, 255))
        surf.blit(enemy_count_text, (surf.get_width() - enemy_count_text.get_width() - 20, 100))
    
    def draw_pause_menu(self, surf: pygame.Surface):
        overlay = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))
        
        title = self.font_large.render("PAUSED", True, (255, 255, 255))
        resume = self.font_medium.render("Press ESC to Resume", True, (200, 200, 200))
        
        surf.blit(title, (surf.get_width()//2 - title.get_width()//2, surf.get_height()//2 - 50))
        surf.blit(resume, (surf.get_width()//2 - resume.get_width()//2, surf.get_height()//2 + 10))
    
    def draw_game_over(self, surf: pygame.Surface):
        overlay = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surf.blit(overlay, (0, 0))
        
        title = self.font_large.render("GAME OVER", True, (255, 100, 100))
        restart = self.font_medium.render("Press R to Restart", True, (200, 200, 200))
        
        surf.blit(title, (surf.get_width()//2 - title.get_width()//2, surf.get_height()//2 - 50))
        surf.blit(restart, (surf.get_width()//2 - restart.get_width()//2, surf.get_height()//2 + 10))
    
    def draw_level_up_screen(self, surf: pygame.Surface):
        overlay = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
        overlay.fill((10, 20, 40, 220))
        surf.blit(overlay, (0, 0))
        
        title = self.font_large.render("LEVEL UP!", True, (0, 255, 204))
        instruction = self.font_medium.render("Choose an upgrade:", True, (240, 240, 255))
        
        surf.blit(title, (surf.get_width()//2 - title.get_width()//2, 100))
        surf.blit(instruction, (surf.get_width()//2 - instruction.get_width()//2, 160))