import math
import random
import time
import pygame
from pygame.math import Vector2

pygame.init()

# Настройки экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("State.io Clone")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Кадровая частота
clock = pygame.time.Clock()
FPS = 60

# Время для роста войск
UNIT_GROWTH_INTERVAL = 1  # юниты в секунду
MOVEMENT_SPEED = 5  # Скорость перемещения войск


# Классы
class Node:
    def __init__(self, x, y, owner, troops, player_growth_interval, enemy_growth_interval):
        self.x = x
        self.y = y
        self.owner = owner  # 0 - нейтральный, 1 - игрок, 2 - враг
        self.troops = troops
        self.radius = 30
        self.last_growth_time = time.time()
        self.moving = False
        self.target = None
        self.start_pos = None
        self.neighbors = []
        self.player_growth_interval = player_growth_interval
        self.enemy_growth_interval = enemy_growth_interval

        self.sprite_neutral = pygame.transform.scale(
            pygame.image.load("sprites/neutral_castle.png").convert_alpha(), (50, 50)
        )
        self.sprite_player = pygame.transform.scale(
            pygame.image.load("sprites/blue_castle.png").convert_alpha(), (50, 50)
        )
        self.sprite_enemy = pygame.transform.scale(
            pygame.image.load("sprites/red_castle.png").convert_alpha(), (50, 50)
        )

    def update_troops(self):
        if self.owner == 1:
            if time.time() - self.last_growth_time > self.player_growth_interval:
                self.troops += 2
                self.last_growth_time = time.time()
        elif self.owner == 2:
            if time.time() - self.last_growth_time > self.enemy_growth_interval:
                self.troops += 2
                self.last_growth_time = time.time()

    def draw(self, screen):
        # Выбор спрайта в зависимости от владельца
        if self.owner == 0:
            sprite = self.sprite_neutral
        elif self.owner == 1:
            sprite = self.sprite_player
        else:
            sprite = self.sprite_enemy

        # Отрисовка спрайта
        sprite_rect = sprite.get_rect(center=(self.x, self.y))
        screen.blit(sprite, sprite_rect)

        # Отображение количества войск
        font = pygame.font.SysFont(None, 24)
        text = font.render(str(self.troops), True, BLACK)
        screen.blit(text, (self.x - text.get_width() // 2, self.y - text.get_height() // 2))

    def is_clicked(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx ** 2 + dy ** 2 <= self.radius ** 2

    def start_movement(self, target_node):
        if not self.moving:
            self.moving = True
            self.target = target_node
            self.start_pos = (self.x, self.y)

    def move(self):
        if self.moving and self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance > MOVEMENT_SPEED:
                dx /= distance
                dy /= distance
                self.x += dx * MOVEMENT_SPEED
                self.y += dy * MOVEMENT_SPEED
            else:
                self.x, self.y = self.target.x, self.target.y
                self.moving = False
                self.target = None

    def add_neighbor(self, node):
        if node not in self.neighbors:
            self.neighbors.append(node)


class TroopMovement:
    def __init__(self, start_node, target_node):
        self.troops = start_node.troops // 2
        self.color = BLUE if start_node.owner == 1 else RED
        self.pos = Vector2(start_node.x, start_node.y)
        self.target = Vector2(target_node.x, target_node.y)
        self.speed = MOVEMENT_SPEED
        self.direction = (self.target - self.pos).normalize()

    def update(self):
        self.pos += self.direction * self.speed
        if (self.pos - self.target).length() < self.speed:
            return True  # Достигли цели
        return False

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), 8)


# уровни
levels = [
    {
        "name": "Level 1",
        "player_growth_interval": 1,
        "enemy_growth_interval": 1.5,
        "nodes": [
            {"x": 200, "y": 200, "owner": 1, "troops": 20},
            {"x": 600, "y": 200, "owner": 2, "troops": 10},
            {"x": 400, "y": 400, "owner": 0, "troops": 20},
        ]
    },
    {
        "name": "Level 2",
        "player_growth_interval": 1.5,
        "enemy_growth_interval": 2,
        "nodes": [
            {"x": 150, "y": 150, "owner": 1, "troops": 50},
            {"x": 650, "y": 150, "owner": 2, "troops": 25},
            {"x": 400, "y": 300, "owner": 2, "troops": 15},
            {"x": 300, "y": 500, "owner": 0, "troops": 30},
            {"x": 500, "y": 500, "owner": 0, "troops": 40},
        ]
    },
    {
        "name": "Level 3",
        "player_growth_interval": 2,
        "enemy_growth_interval": 1.5,
        "nodes": [
            {"x": 100, "y": 100, "owner": 1, "troops": 70},
            {"x": 700, "y": 100, "owner": 2, "troops": 30},
            {"x": 400, "y": 300, "owner": 2, "troops": 20},
            {"x": 250, "y": 450, "owner": 0, "troops": 40},
            {"x": 550, "y": 450, "owner": 0, "troops": 50},
            {"x": 400, "y": 550, "owner": 0, "troops": 45},
        ]
    }
]


def create_nodes(level):
    nodes = []
    player_growth_interval = level.get("player_growth_interval", 1)
    enemy_growth_interval = level.get("enemy_growth_interval", 1)

    for node_info in level["nodes"]:
        new_node = Node(
            node_info["x"], node_info["y"], node_info["owner"],
            node_info["troops"], player_growth_interval, enemy_growth_interval
        )
        nodes.append(new_node)

    for node in nodes:
        for other_node in nodes:
            if node != other_node:
                node.add_neighbor(other_node)

    return nodes


def ai_turn(nodes, moving_troops):
    for node in nodes:
        if node.owner == 2:
            for neighbor in node.neighbors:
                if neighbor.owner != 2 and neighbor.troops < node.troops:
                    if node.troops > neighbor.troops:
                        troops_to_send = node.troops // 2
                        node.troops -= troops_to_send
                        moving_troops.append(TroopMovement(node, neighbor))


def check_victory(nodes):
    return not any(node.owner == 2 for node in nodes)  # Победа, если у врага нет узлов


def check_defeat(nodes):
    return not any(node.owner == 1 for node in nodes)  # Поражение, если у игрока нет узлов


def level_selection_screen():
    font = pygame.font.SysFont(None, 48)
    title_text = font.render("Выберите уровень", True, BLACK)
    title_rect = title_text.get_rect(center=(WIDTH // 2, 100))

    level_buttons = []
    for i, level in enumerate(levels):
        button_text = font.render(level["name"], True, BLACK)
        button_rect = pygame.Rect(WIDTH // 2 - 100, 200 + i * 80, 200, 50)
        level_buttons.append((button_text, button_rect))

    running = True
    while running:
        screen.fill(WHITE)
        screen.blit(title_text, title_rect)

        for i, (button_text, button_rect) in enumerate(level_buttons):
            pygame.draw.rect(screen, (200, 200, 200), button_rect)
            screen.blit(button_text, button_rect.move(50, 10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for i, (_, button_rect) in enumerate(level_buttons):
                    if button_rect.collidepoint(pos):
                        game_loop(i)

        pygame.display.update()
        clock.tick(FPS)


def show_victory_message():
    font = pygame.font.SysFont(None, 48)
    text = font.render("Вы победили!", True, (255, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)


def show_defeat_message():
    font = pygame.font.SysFont(None, 48)
    text = font.render("Вы проиграли!", True, (255, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)


def game_loop(level_index):
    level = levels[level_index]
    nodes = create_nodes(level)
    moving_troops = []

    selected_node = None
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for node in nodes:
                    if node.is_clicked(pos):
                        if selected_node is None:
                            selected_node = node
                        else:
                            if selected_node != node and selected_node.owner == 1:
                                if selected_node.troops > 1:
                                    moving_troops.append(TroopMovement(selected_node, node))
                                    selected_node.troops = selected_node.troops // 2
                                selected_node = None

        ai_turn(nodes, moving_troops)

        # Обновляем движущиеся войска
        for troop in moving_troops[:]:
            if troop.update():
                moving_troops.remove(troop)
                target_node = next((node for node in nodes if (node.x, node.y) == (troop.target.x, troop.target.y)), None)
                if target_node:
                    if target_node.owner == 1 and troop.color == BLUE:
                        target_node.troops += troop.troops
                    elif target_node.owner == 2 and troop.color == RED:
                        target_node.troops += troop.troops
                    else:
                        target_node.troops -= troop.troops
                        if target_node.troops <= 0:
                            target_node.owner = 1 if troop.color == BLUE else 2
                            target_node.troops = abs(target_node.troops)

        screen.fill(GREEN)
        for node in nodes:
            node.update_troops()
            node.draw(screen)

        for troop in moving_troops:
            troop.draw(screen)

        if check_victory(nodes):
            show_victory_message()
            pygame.display.update()
            pygame.time.wait(2000)
            if level_index + 1 < len(levels):
                game_loop(level_index + 1)
            return

        elif check_defeat(nodes):
            show_defeat_message()
            pygame.display.update()
            pygame.time.wait(2000)
            running = False

        pygame.display.update()
        clock.tick(FPS)


# Начало игры
level_selection_screen()
pygame.quit()