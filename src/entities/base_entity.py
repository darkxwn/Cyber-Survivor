import pygame
from abc import ABC, abstractmethod

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