from __future__ import annotations

import random
import pygame


class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.shake_time = 0.0
        self.shake_strength = 0.0
        self.offset = pygame.Vector2(0, 0)
        self.focus = 1

    def update(self, dt: float):
        self.zoom += (self.target_zoom - self.zoom) * min(1.0, dt * 7.0)
        if self.shake_time > 0:
            self.shake_time -= dt
            self.offset.x = random.uniform(-self.shake_strength, self.shake_strength)
            self.offset.y = random.uniform(-self.shake_strength, self.shake_strength)
        else:
            self.offset.xy = (0, 0)

    def bump(self, amount: float = 0.03):
        self.zoom = min(1.2, self.zoom + amount)

    def shake(self, strength: float, duration: float):
        self.shake_strength = strength
        self.shake_time = duration

    def set_focus(self, who: int):
        self.focus = int(who)
