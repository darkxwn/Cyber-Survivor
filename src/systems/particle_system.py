import pygame
import random
import math
from dataclasses import dataclass
from typing import List, Tuple

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