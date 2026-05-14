from __future__ import annotations

import pygame


def draw_text(screen, font, text, pos, color=(255, 255, 255), anchor="topleft"):
    surf = font.render(str(text), True, color)
    rect = surf.get_rect()
    setattr(rect, anchor, pos)
    screen.blit(surf, rect)
    return rect


def draw_panel(screen, rect, fill=(20, 20, 28, 220), border=(255, 255, 255)):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill(fill)
    screen.blit(panel, rect.topleft)
    pygame.draw.rect(screen, border, rect, 2, border_radius=10)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Toast:
    def __init__(self):
        self.items: list[tuple[str, float]] = []

    def push(self, text: str, ttl: float = 2.0):
        self.items.append((text, ttl))

    def update(self, dt: float):
        self.items = [(t, ttl - dt) for t, ttl in self.items if ttl - dt > 0]

    def draw(self, screen, font):
        y = 18
        for text, ttl in self.items[-5:]:
            surf = font.render(text, True, (255, 240, 160))
            rect = surf.get_rect(topright=(screen.get_width() - 18, y))
            bg = rect.inflate(20, 12)
            pygame.draw.rect(screen, (0, 0, 0, 160), bg, border_radius=8)
            screen.blit(surf, rect)
            y += bg.height + 6
