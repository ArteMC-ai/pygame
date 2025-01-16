import math
import random
import time

import pygame

# Инициализация pygame
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
UNIT_GROWTH_INTERVAL = 1  # Время в секундах для набора войск (уменьшено с 5 до 1)
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

    def draw(self, screen):
        color = WHITE if self.owner == 0 else (BLUE if self.owner == 1 else RED)
        pygame.draw.circle(screen, color, (self.x, self.y), self.radius)
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

            # Если расстояние больше, чем скорость, двигаем в нужном направлении
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


# Функция для проверки наложения кружочков
def check_collision(new_node, nodes):
    for node in nodes:
        distance = math.sqrt((new_node.x - node.x) ** 2 + (new_node.y - node.y) ** 2)
        if distance < new_node.radius + node.radius:
            return True
    return False


# Функция создания узлов с проверкой на наложение
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
        owner = 0  # Начнем с нейтрального
        troops = random.randint(5, 20)

        # Убираем лишнюю нейтральную территорию
        if len(nodes) < num_allied:
            owner = 1  # Союзная территория
        elif len(nodes) < num_allied + num_enemy:
            owner = 2  # Вражеская территория
        else:
            owner = 0  # Нейтральная территория

        new_node = Node(x, y, owner, troops)

        # Проверяем, что новый узел не перекрывает существующие
        if not check_collision(new_node, nodes):
            nodes.append(new_node)

    return nodes


# Функция для отображения экрана выбора сложности
def show_difficulty_selection():
    font = pygame.font.SysFont(None, 48)
    text = font.render("Select Difficulty", True, BLACK)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3 - text.get_height() // 2))

    button_font = pygame.font.SysFont(None, 36)
    easy_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 30, 200, 60)
    medium_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 60)
    hard_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 110, 200, 60)

    pygame.draw.rect(screen, (200, 200, 200), easy_button)
    pygame.draw.rect(screen, (200, 200, 200), medium_button)
    pygame.draw.rect(screen, (200, 200, 200), hard_button)

    easy_text = button_font.render("Easy", True, BLACK)
    medium_text = button_font.render("Medium", True, BLACK)
    hard_text = button_font.render("Hard", True, BLACK)

    screen.blit(easy_text,
                (easy_button.centerx - easy_text.get_width() // 2, easy_button.centery - easy_text.get_height() // 2))
    screen.blit(medium_text, (
        medium_button.centerx - medium_text.get_width() // 2, medium_button.centery - medium_text.get_height() // 2))
    screen.blit(hard_text,
                (hard_button.centerx - hard_text.get_width() // 2, hard_button.centery - hard_text.get_height() // 2))

    pygame.display.flip()

    selecting = True
    difficulty_level = 1  # По умолчанию выбран лёгкий уровень

    while selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if easy_button.collidepoint(event.pos):
                    difficulty_level = 1
                    selecting = False
                elif medium_button.collidepoint(event.pos):
                    difficulty_level = 2
                    selecting = False
                elif hard_button.collidepoint(event.pos):
                    difficulty_level = 3
                    selecting = False

    return difficulty_level


# Функция для рисования линий между территориями (новая функция)
def draw_lines(nodes):
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            pygame.draw.line(screen, BLACK, (nodes[i].x, nodes[i].y), (nodes[j].x, nodes[j].y), 1)


# Функция для проверки победы
def check_victory(nodes):
    # Проверяем, что все территории принадлежат игроку (owner == 1)
    return all(node.owner == 1 for node in nodes)


def show_victory_message():
    font = pygame.font.SysFont(None, 48)
    text = font.render("Вы победили!", True, (255, 0, 0))  # Красный цвет
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)


def game_loop(difficulty_level):
    # Создание узлов с учетом уровня сложности
    nodes = create_nodes(10, difficulty_level)

    selected_node = None

    running = True
    while running:
        # Заливка фона зелёным цветом
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

                                    if node.owner == 2:  # Вражеская территория
                                        # Уменьшаем количество войск на вражеской территории
                                        node.troops -= troops_to_send

                                        # Если вражеские войска стали меньше или равны нулю, захватываем территорию
                                        if node.troops <= 0:
                                            node.owner = 1  # Переход в руки игрока
                                            node.troops = abs(
                                                node.troops)  # Устанавливаем положительное количество войск

                                    elif node.owner == 0:  # Нейтральная территория
                                        node.troops -= troops_to_send

                                        # Если вражеские войска стали меньше или равны нулю, захватываем территорию
                                        if node.troops <= 0:
                                            node.owner = 1  # Переход в руки игрока
                                            node.troops = abs(
                                                node.troops)  # Устанавливаем положительное количество войск

                                    elif node.owner == 1:  # Союзная территория
                                        node.troops += troops_to_send  # Просто добавляем войска

                                    selected_node = None

        # Проверка на победу
        if check_victory(nodes):
            # Очищаем экран перед выводом сообщения о победе
            screen.fill(GREEN)  # Зеленый фон
            show_victory_message()  # Отображаем сообщение
            pygame.display.update()
            pygame.time.wait(2000)  # Пауза, чтобы сообщение успело отобразиться
            running = False  # Заканчиваем игру

        else:
            # Обновляем и рисуем территорию
            for node in nodes:
                node.update_troops()
                node.draw(screen)

            # Рисуем линии между территориями
            draw_lines(nodes)

        pygame.display.update()
        clock.tick(FPS)


# Начало игры
difficulty_level = show_difficulty_selection()
game_loop(difficulty_level)

pygame.quit()
