from __future__ import annotations

import pygame


class State:
    def __init__(self, app):
        self.app = app

    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def handle_event(self, event: pygame.event.Event):
        pass

    def update(self, dt: float):
        pass

    def draw(self, screen: pygame.Surface):
        pass


class StateMachine:
    def __init__(self, app):
        self.app = app
        self.current: State | None = None

    def change(self, state_cls, **kwargs):
        if self.current:
            self.current.exit()
        self.current = state_cls(self.app)
        self.current.enter(**kwargs)

    def handle_event(self, event):
        if self.current:
            self.current.handle_event(event)

    def update(self, dt):
        if self.current:
            self.current.update(dt)

    def draw(self, screen):
        if self.current:
            self.current.draw(screen)
