#!/usr/bin/env python3
"""Neon Dodge: a small offline arcade game for Raspberry Pi 3.

Controls:
  Arrow keys / WASD  Move
  P              Pause
  R              Restart after game over
  Esc            Quit
"""
import random
import sys
from dataclasses import dataclass

import pygame

WIDTH, HEIGHT = 800, 480
FPS = 60
BG = (8, 12, 28)
GRID = (18, 28, 55)
WHITE = (235, 245, 255)
CYAN = (45, 225, 255)
PINK = (255, 65, 155)
YELLOW = (255, 220, 80)
RED = (255, 75, 80)


@dataclass
class Star:
    x: int
    y: int
    speed: float
    size: int


@dataclass
class Block:
    rect: pygame.Rect
    speed: float
    color: tuple


class NeonDodge:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Neon Dodge - Raspberry Pi 3")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.big_font = pygame.font.Font(None, 76)
        self.small_font = pygame.font.Font(None, 23)
        self.stars = [Star(random.randrange(WIDTH), random.randrange(HEIGHT), random.uniform(20, 70), random.choice((1, 1, 2))) for _ in range(70)]
        self.best = 0
        self.reset()

    def reset(self):
        self.player = pygame.Rect(WIDTH // 2 - 18, HEIGHT - 64, 36, 28)
        self.blocks = []
        self.spawn_timer = 0.0
        self.elapsed = 0.0
        self.score = 0
        self.lives = 3
        self.invulnerable = 0.0
        self.paused = False
        self.game_over = False

    def spawn_block(self):
        size = random.randint(18, 42)
        x = random.randint(20, WIDTH - size - 20)
        speed = random.uniform(145, 235) + min(self.elapsed * 3.0, 120)
        color = random.choice((PINK, YELLOW, RED))
        self.blocks.append(Block(pygame.Rect(x, -size, size, size), speed, color))

    def update_stars(self, dt):
        for star in self.stars:
            star.y += star.speed * dt
            if star.y >= HEIGHT:
                star.y = -star.size
                star.x = random.randrange(WIDTH)

    def update(self, dt):
        self.update_stars(dt)
        if self.paused or self.game_over:
            return
        self.elapsed += dt
        self.score = int(self.elapsed * 10)
        self.invulnerable = max(0.0, self.invulnerable - dt)

        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        self.player.x += int(dx * 280 * dt)
        self.player.y += int(dy * 280 * dt)
        self.player.clamp_ip(pygame.Rect(8, 42, WIDTH - 16, HEIGHT - 50))

        self.spawn_timer -= dt
        interval = max(0.22, 0.70 - self.elapsed * 0.006)
        if self.spawn_timer <= 0:
            self.spawn_block()
            self.spawn_timer = interval

        for block in self.blocks:
            block.rect.y += int(block.speed * dt)
        self.blocks = [b for b in self.blocks if b.rect.top < HEIGHT + 10]

        if self.invulnerable <= 0:
            for block in self.blocks[:]:
                if self.player.colliderect(block.rect):
                    self.blocks.remove(block)
                    self.lives -= 1
                    self.invulnerable = 1.3
                    if self.lives <= 0:
                        self.game_over = True
                        self.best = max(self.best, self.score)
                    break

    def draw_text(self, text, font, color, pos, center=False):
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        self.screen.blit(surface, rect)

    def draw(self):
        self.screen.fill(BG)
        for y in range(45, HEIGHT, 32):
            pygame.draw.line(self.screen, GRID, (0, y), (WIDTH, y), 1)
        for x in range(0, WIDTH, 40):
            pygame.draw.line(self.screen, GRID, (x, 45), (x, HEIGHT), 1)
        for star in self.stars:
            pygame.draw.rect(self.screen, (45, 70, 115), (star.x, int(star.y), star.size, star.size))

        pygame.draw.rect(self.screen, (12, 18, 42), (0, 0, WIDTH, 42))
        pygame.draw.line(self.screen, CYAN, (0, 41), (WIDTH, 41), 2)
        self.draw_text("NEON DODGE", self.font, CYAN, (16, 9))
        self.draw_text(f"SCORE {self.score:05d}", self.font, WHITE, (270, 9))
        self.draw_text(f"BEST {self.best:05d}", self.font, YELLOW, (470, 9))
        self.draw_text("LIVES " + "♥" * self.lives, self.font, PINK, (650, 9))

        for block in self.blocks:
            pygame.draw.rect(self.screen, block.color, block.rect, border_radius=5)
            pygame.draw.rect(self.screen, WHITE, block.rect, 2, border_radius=5)

        visible = self.invulnerable <= 0 or int(self.invulnerable * 12) % 2 == 0
        if visible:
            pygame.draw.polygon(self.screen, CYAN, [(self.player.centerx, self.player.top - 10), (self.player.right, self.player.bottom), (self.player.left, self.player.bottom)])
            pygame.draw.polygon(self.screen, WHITE, [(self.player.centerx, self.player.top - 10), (self.player.right, self.player.bottom), (self.player.left, self.player.bottom)], 2)

        if self.paused:
            self.draw_text("PAUSED", self.big_font, WHITE, (WIDTH // 2, HEIGHT // 2 - 20), True)
            self.draw_text("Press P to continue", self.font, CYAN, (WIDTH // 2, HEIGHT // 2 + 38), True)
        elif self.game_over:
            pygame.draw.rect(self.screen, (5, 8, 20), (175, 125, 450, 220), border_radius=14)
            pygame.draw.rect(self.screen, PINK, (175, 125, 450, 220), 2, border_radius=14)
            self.draw_text("GAME OVER", self.big_font, PINK, (WIDTH // 2, 178), True)
            self.draw_text(f"Final score: {self.score}", self.font, WHITE, (WIDTH // 2, 238), True)
            self.draw_text("Press R to play again  •  Esc to quit", self.small_font, CYAN, (WIDTH // 2, 285), True)

        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_p and not self.game_over:
                        self.paused = not self.paused
                    if event.key == pygame.K_r and self.game_over:
                        self.reset()
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    pygame.init()
    NeonDodge().run()
