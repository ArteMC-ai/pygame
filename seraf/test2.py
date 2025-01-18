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

def create_nodes(num_nodes, difficulty_level):
    nodes = []

    # В зависимости от уровня сложности определяем количество территорий
    if difficulty_level == 1:
        num_enemy = 1
        num_allied = 1
        num_neutral = 1
    elif difficulty_level == 2:
        num_enemy = 2
        num_allied = 2
        num_neutral = 2
    elif difficulty_level == 3:
        num_enemy = 5
        num_allied = 5
        num_neutral = 5

    while len(nodes) < num_enemy + num_allied + num_neutral:
        x = random.randint(100, WIDTH - 100)
        y = random.randint(100, HEIGHT - 100)
        owner = 0
        troops = random.randint(5, 20)

        # Убираем лишнюю нейтральную территорию
        if len(nodes) < num_allied:
            owner = 1  # Союзная территория
        elif len(nodes) < num_allied + num_enemy:
            owner = 2  # Вражеская территория
        else:
            owner = 0  # Нейтральная территория

        new_node = Node(x, y, owner, troops)

        if not check_collision(new_node, nodes):
            nodes.append(new_node)

    # Добавляем соседей для каждой территории
    for node in nodes:
        for other_node in nodes:
            if node != other_node:
                node.add_neighbor(other_node)

    return nodes

#ИИ
"""Он смотри короче если на территории меньше чем у него то он кидает на неё своих моментально"""
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
def game_loop(difficulty_level):
    nodes = create_nodes(10, difficulty_level)

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
                                        node.troops += troops_to_send #просто рождаем челиков

                                    selected_node = None

        ai_turn(nodes)

        # Проверка на победу
        if check_victory(nodes):
            screen.fill(GREEN)
            show_victory_message()
            pygame.display.update()
            pygame.time.wait(2000)
            running = False  # Заканчиваем игру

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
difficulty_level = 1  # Можно настроить на разные уровни сложности
game_loop(difficulty_level)

pygame.quit()
