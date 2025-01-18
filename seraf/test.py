import math
import random
import time
import pygame

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
GREEN = (0, 255, 0)  # Зеленый цвет фона

# Кадровая частота
clock = pygame.time.Clock()
FPS = 60

# Время для роста войск
UNIT_GROWTH_INTERVAL = 1  # Время в секундах для набора войск
MOVEMENT_SPEED = 5  # Скорость перемещения войск

# Классы
class Node:
    def __init__(self, x, y, owner, troops):
        self.x = x
        self.y = y
        self.owner = owner  # 0 - нейтральный, 1 - игрок, 2 - враг
        self.troops = troops
        self.radius = 30
        self.last_growth_time = time.time()  # Время последнего роста войск
        self.moving = False  # Флаг для отслеживания перемещения
        self.target = None  # Целевая точка для перемещения
        self.start_pos = None  # Начальная позиция
        self.neighbors = []  # Соседи для захвата

    def draw(self, screen):
        # Определяем основной цвет в зависимости от владельца
        if self.owner == 0:
            color = WHITE
            border_color = (220, 220, 220)  # Светло-серый для нейтральных территорий
        elif self.owner == 1:
            color = BLUE
            border_color = (100, 100, 255)  # Бледно-синий для союзных территорий
        else:  # Вражеская территория
            color = RED
            border_color = (255, 150, 150)  # Бледно-красный для вражеских территорий

        # Рисуем обводку (более бледный цвет)
        pygame.draw.circle(screen, border_color, (self.x, self.y), self.radius + 5)  # Обводка

        # Рисуем саму базу
        pygame.draw.circle(screen, color, (self.x, self.y), self.radius)

        # Отображаем количество войск в центре базы
        font = pygame.font.SysFont(None, 24)
        text = font.render(str(self.troops), True, BLACK)
        screen.blit(text, (self.x - text.get_width() // 2, self.y - text.get_height() // 2))

    def is_clicked(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx ** 2 + dy ** 2 <= self.radius ** 2

    def update_troops(self):
        # Обновление войск для территорий игрока (owner == 1) и врага (owner == 2)
        if self.owner == 1:  # Обновляем для территории игрока
            if time.time() - self.last_growth_time > UNIT_GROWTH_INTERVAL:
                self.troops += 2  # Увеличиваем войска на 2
                self.last_growth_time = time.time()
        elif self.owner == 2:  # Для врага тоже обновляем войска
            if time.time() - self.last_growth_time > UNIT_GROWTH_INTERVAL:
                self.troops += 2  # Враги тоже увеличивают количество войск
                self.last_growth_time = time.time()

    def start_movement(self, target_node):
        if not self.moving:
            self.moving = True
            self.target = target_node
            self.start_pos = (self.x, self.y)

    def move(self):
        if self.moving and self.target:
            # Рассчитываем направление
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance > MOVEMENT_SPEED:
                dx /= distance
                dy /= distance
                self.x += dx * MOVEMENT_SPEED
                self.y += dy * MOVEMENT_SPEED
            else:
                # Если войска достигли цели, обновляем территорию
                self.x, self.y = self.target.x, self.target.y
                self.moving = False
                self.target = None  # Сброс цели
                # Проверяем захват территории
                if self.target and self.target.owner != 1:
                    if self.troops > self.target.troops:
                        self.target.owner = 1  # Захватить территорию
                        self.target.troops = self.troops
                    else:
                        self.target.troops += self.troops

    def add_neighbor(self, node):
        if node not in self.neighbors:
            self.neighbors.append(node)

# Функция для проверки наложения кружочков
def check_collision(new_node, nodes):
    for node in nodes:
        distance = math.sqrt((new_node.x - node.x) ** 2 + (new_node.y - node.y) ** 2)
        if distance < new_node.radius + node.radius:
            return True
    return False

# Список уровней
levels = [
    {
        "name": "Level 1",
        "nodes": [
            {"x": 200, "y": 200, "owner": 1, "troops": 20},
            {"x": 600, "y": 200, "owner": 2, "troops": 20},
            {"x": 400, "y": 400, "owner": 0, "troops": 40},
        ]
    },
    {
        "name": "Level 2",
        "nodes": [
            {"x": 150, "y": 150, "owner": 1, "troops": 40},
            {"x": 650, "y": 150, "owner": 2, "troops": 30},
            {"x": 400, "y": 300, "owner": 2, "troops": 25},
            {"x": 300, "y": 500, "owner": 0, "troops": 40},
            {"x": 500, "y": 500, "owner": 0, "troops": 30},
        ]
    },
    {
        "name": "Level 3",
        "nodes": [
            {"x": 100, "y": 100, "owner": 1, "troops": 30},
            {"x": 700, "y": 100, "owner": 2, "troops": 30},
            {"x": 400, "y": 300, "owner": 2, "troops": 45},
            {"x": 250, "y": 450, "owner": 0, "troops": 50},
            {"x": 550, "y": 450, "owner": 0, "troops": 45},
            {"x": 400, "y": 550, "owner": 0, "troops": 35},
        ]
    }
]

# Функция для создания узлов для текущего уровня
def create_nodes(level):
    nodes = []
    for node_info in level["nodes"]:
        new_node = Node(node_info["x"], node_info["y"], node_info["owner"], node_info["troops"])
        nodes.append(new_node)

    # Добавляем соседей для каждой территории
    for node in nodes:
        for other_node in nodes:
            if node != other_node:
                node.add_neighbor(other_node)

    return nodes

# ИИ
def ai_turn(nodes):
    for node in nodes:
        if node.owner == 2:
            for neighbor in node.neighbors:
                if neighbor.owner != 2 and neighbor.troops < node.troops:
                    if node.troops > neighbor.troops:
                        troops_to_send = node.troops // 2
                        node.troops -= troops_to_send
                        neighbor.troops -= troops_to_send
                        if neighbor.troops <= 0:
                            neighbor.owner = 2
                            neighbor.troops = abs(neighbor.troops)

# Функция для проверки победы
def check_victory(nodes):
    return all(node.owner == 1 for node in nodes)

# Функция для проверки поражения
def check_defeat(nodes):
    return all(node.owner == 2 for node in nodes)

# Экран выбора уровня
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
                        game_loop(i)  # Переход на выбранный уровень

        pygame.display.update()
        clock.tick(FPS)

#вывод победы
def show_victory_message():
    font = pygame.font.SysFont(None, 48)
    text = font.render("Вы победили!", True, (255, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)

#вывод поражения
def show_defeat_message():
    font = pygame.font.SysFont(None, 48)
    text = font.render("Вы проиграли!", True, (255, 0, 0))  # Красный цвет
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)

# Главный игровой цикл
def game_loop(level_index):
    level = levels[level_index]
    nodes = create_nodes(level)

    selected_node = None
    running = True
    while running:
        screen.fill(GREEN)

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
                            if selected_node != node:
                                # Проверяем захват территории
                                if selected_node.owner == 1 and selected_node.troops > 1:
                                    troops_to_send = selected_node.troops // 2
                                    selected_node.troops -= troops_to_send

                                    if node.owner == 2:
                                        node.troops -= troops_to_send

                                        if node.troops <= 0:
                                            node.owner = 1
                                            node.troops = abs(node.troops)

                                    elif node.owner == 0:
                                        node.troops -= troops_to_send

                                        if node.troops <= 0:
                                            node.owner = 1
                                            node.troops = abs(node.troops)

                                    elif node.owner == 1:
                                        node.troops += troops_to_send  # Просто увеличиваем войска

                                    selected_node = None

        ai_turn(nodes)

        # Проверка на победу
        if check_victory(nodes):
            screen.fill(GREEN)
            show_victory_message()
            pygame.display.update()
            pygame.time.wait(2000)
            if level_index + 1 < len(levels):
                game_loop(level_index + 1)  # Переход к следующему уровню
                return  # Завершаем текущий цикл

        # Проверка на поражение
        elif check_defeat(nodes):
            screen.fill(GREEN)
            show_defeat_message()
            pygame.display.update()
            pygame.time.wait(2000)
            running = False  # Заканчиваем игру

        else:
            # Обновляем и рисуем территорию
            for node in nodes:
                node.update_troops()
                node.draw(screen)

        pygame.display.update()
        clock.tick(FPS)

# Начало игры
level_selection_screen()  # Экран выбора уровня

pygame.quit()
