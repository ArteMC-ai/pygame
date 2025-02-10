import math
import time

import pygame
from pygame.math import Vector2

from levels import levels

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
YELLOW = (255, 255, 0)

# Кадровая частота
clock = pygame.time.Clock()
FPS = 60

# Время для роста войск
UNIT_GROWTH_INTERVAL = 1  # юниты в секунду
MOVEMENT_SPEED = 5  # Скорость перемещения войск

# Скорость атаки ИИ
ai_last_attack_time = time.time()
ai_attack_cooldown = 3


# Классы
class Node:
    def __init__(self, x, y, owner, troops, player_growth_interval, enemy_growth_interval):
        self.x = x
        self.y = y
        self.owner = owner  # 0 - нейтральный, 1 - игрок, 2 - враг (красный), 3 - враг (зелёный), 4 - враг (желтый)
        self.troops = troops
        self.radius = 30
        self.click_radius = self.radius + 10  # добавим отступ к радиусу для улучшенной зоны клика
        self.last_growth_time = time.time()
        self.moving = False
        self.target = None
        self.start_pos = None
        self.neighbors = []
        self.player_growth_interval = player_growth_interval
        self.enemy_growth_interval = enemy_growth_interval

        self.sprite_neutral = pygame.transform.scale(
            pygame.image.load("sprites/neutral_castle.png").convert_alpha(), (55, 55)
        )
        self.sprite_player = pygame.transform.scale(
            pygame.image.load("sprites/blue_castle.png").convert_alpha(), (60, 60)
        )
        self.sprite_enemy = pygame.transform.scale(
            pygame.image.load("sprites/red_castle.png").convert_alpha(), (60, 60)
        )
        self.sprite_enemy_green = pygame.transform.scale(
            pygame.image.load("sprites/green-castle.png").convert_alpha(), (50, 60)
        )
        self.sprite_enemy_yellow = pygame.transform.scale(
            pygame.image.load("sprites/yellow_castle.png").convert_alpha(), (60, 60)
        )

    def update_troops(self):
        current_time = time.time()
        if self.owner == 1:
            if current_time - self.last_growth_time > self.player_growth_interval:
                self.troops += 2
                self.last_growth_time = current_time
        elif self.owner in [2, 3, 4]:
            if current_time - self.last_growth_time > self.enemy_growth_interval:
                self.troops += 2
                self.last_growth_time = current_time

    def draw(self, screen):
        # Выбор спрайта в зависимости от владельца
        if self.owner == 0:
            sprite = self.sprite_neutral
            circle_color = WHITE  # Белый цвет для нейтральных баз
        elif self.owner == 1:
            sprite = self.sprite_player
            circle_color = BLUE  # Синий для игрока
        elif self.owner == 2:
            sprite = self.sprite_enemy
            circle_color = RED  # Красный для врага
        elif self.owner == 3:
            sprite = self.sprite_enemy_green
            circle_color = GREEN  # Зеленый для врага
        elif self.owner == 4:
            sprite = self.sprite_enemy_yellow
            circle_color = YELLOW  # Желтый для врага

        # Отрисовка круга вокруг базы
        pygame.draw.circle(screen, circle_color, (self.x, self.y), self.radius + 10, 3)  # Круг с отступом

        # Отрисовка спрайта базы
        sprite_rect = sprite.get_rect(center=(self.x, self.y))
        screen.blit(sprite, sprite_rect)

        # Отображение количества войск
        font = pygame.font.SysFont(None, 24)
        text = font.render(str(self.troops), True, BLACK)
        screen.blit(text, (self.x - text.get_width() // 2, self.y - text.get_height() // 2))

    def is_clicked(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx ** 2 + dy ** 2 <= self.click_radius ** 2  # Используем новый радиус с отступом

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
        self.color = BLUE if start_node.owner == 1 else RED if start_node.owner == 2 else GREEN if start_node.owner == 3 else YELLOW
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
    global ai_last_attack_time

    current_time = time.time()
    if current_time - ai_last_attack_time < ai_attack_cooldown:
        return  # Skip AI turn if cooldown period hasn't passed

    for node in nodes:
        if node.owner in [2, 3, 4] and node.troops > 1:
            target_node = min(
                (neighbor for neighbor in node.neighbors if neighbor.owner != node.owner),
                key=lambda n: n.troops,
                default=None
            )
            if target_node:
                troops_to_send = node.troops // 2
                node.troops -= troops_to_send
                moving_troops.append(TroopMovement(node, target_node))
                ai_last_attack_time = current_time


def check_victory(nodes):
    return not any(node.owner in [2, 3, 4] for node in nodes)  # Победа, если у врага нет узлов


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
    background = level["background"]
    selected_node = None
    running = True
    while running:
        screen.fill(background)
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
                            else:
                                selected_node = node

        ai_turn(nodes, moving_troops)

        for troop in moving_troops[:]:
            if troop.update():
                moving_troops.remove(troop)
                target_node = next((node for node in nodes if (node.x, node.y) == (troop.target.x, troop.target.y)),
                                   None)
                if target_node:
                    if target_node.owner == 1 and troop.color == BLUE:
                        target_node.troops += troop.troops
                    elif target_node.owner == 2 and troop.color == RED:
                        target_node.troops += troop.troops
                    elif target_node.owner == 3 and troop.color == GREEN:
                        target_node.troops += troop.troops
                    elif target_node.owner == 4 and troop.color == YELLOW:
                        target_node.troops += troop.troops
                    else:
                        target_node.troops -= troop.troops
                        if target_node.troops <= 0:
                            target_node.owner = 1 if troop.color == BLUE else 2 if troop.color == RED else 3 if troop.color == GREEN else 4
                            target_node.troops = abs(target_node.troops)

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
