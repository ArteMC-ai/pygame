import math
import time

import pygame
from pygame.math import Vector2

from levels import levels

pygame.init()
pygame.mixer.init()


# Функция для воспроизведения музыки
def play_music(track):
    pygame.mixer.music.stop()
    pygame.mixer.music.load(track)
    pygame.mixer.music.set_volume(0.05)
    pygame.mixer.music.play(-1)


# Настройки экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("State.io Clone")
clock = pygame.time.Clock()
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

# Цвета фона для магазина и главного меню
SHOP_BG = (220, 220, 255)  # Светло-голубой фон для магазина
MENU_BG = (220, 255, 220)  # Светло-зелёный фон для главного меню

# Базовые настройки
UNIT_GROWTH_INTERVAL = 1  # базовое время роста войск (сек)
MOVEMENT_SPEED = 5  # скорость перемещения войск
ai_last_attack_time = time.time()
ai_attack_cooldown = 3

# Глобальные переменные для магазина и прокачек
monet = 0  # монеты (начинается с 0, начисляются за уровень)
count_upgrade_level = 0  # уровень прокачки количества войск
growth_upgrade_level = 0  # уровень прокачки скорости роста войск
troop_count_increase = 0  # бонус к начальному количеству войск (прокачка количества войск)


# Функция для отображения текста
def draw_text(text, font, color, x, y):
    label = font.render(text, True, color)
    screen.blit(label, (x, y))


# Магазин с кнопками (вызывается как по клавише M, так и из главного меню)
def shop_screen():
    global monet, count_upgrade_level, growth_upgrade_level, troop_count_increase
    # Запускаем музыку магазина
    play_music("sounds/shop_music.mp3")

    running = True
    font_large = pygame.font.SysFont(None, 48)
    font_small = pygame.font.SysFont(None, 36)

    # Определяем кнопки магазина
    button_upgrade_count = pygame.Rect(100, 150, 400, 50)
    button_upgrade_growth = pygame.Rect(100, 220, 400, 50)
    button_exit = pygame.Rect(100, 300, 200, 50)

    while running:
        screen.fill(SHOP_BG)  # Цветной фон магазина
        draw_text("Магазин", font_large, BLACK, 100, 50)
        draw_text(f"Монеты: {monet}", font_small, BLACK, 100, 100)

        cost1 = count_upgrade_level * 10 + 10
        cost2 = growth_upgrade_level * 15 + 15

        pygame.draw.rect(screen, GRAY, button_upgrade_count)
        pygame.draw.rect(screen, GRAY, button_upgrade_growth)
        pygame.draw.rect(screen, BLUE, button_exit)

        draw_text(f"+Войска (+{5 + count_upgrade_level}) за {cost1} монет", font_small, BLACK, 110, 160)
        draw_text(f"Скорость роста за {cost2} монет", font_small, BLACK, 110, 230)
        draw_text("Выйти", font_small, WHITE, 150, 310)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_upgrade_count.collidepoint(event.pos):
                    if monet >= cost1:
                        monet -= cost1
                        count_upgrade_level += 1
                        # При первом уровне бонус +5, затем +6, +7 и т.д.
                        troop_count_increase += (5 + count_upgrade_level - 1)
                elif button_upgrade_growth.collidepoint(event.pos):
                    if monet >= cost2:
                        monet -= cost2
                        growth_upgrade_level += 1
                elif button_exit.collidepoint(event.pos):
                    running = False

        pygame.display.update()
        clock.tick(FPS)


# Класс узлов (баз)
class Node:
    def __init__(self, x, y, owner, troops, player_growth_interval, enemy_growth_interval):
        self.x = x
        self.y = y
        self.owner = owner  # 0 - нейтральный, 1 - игрок, 2 - враг (красный), 3 - враг (зелёный), 4 - враг (желтый)
        self.troops = troops
        self.radius = 30
        self.click_radius = self.radius + 10  # улучшенная зона клика
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
            effective_interval = self.player_growth_interval - 0.1 * growth_upgrade_level
            if effective_interval < 0.1:
                effective_interval = 0.1
            if current_time - self.last_growth_time > effective_interval:
                self.troops += 2  # базовый прирост для игрока (бонус уже применён в начале уровня)
                self.last_growth_time = current_time
        elif self.owner in [2, 3, 4]:
            if current_time - self.last_growth_time > self.enemy_growth_interval:
                self.troops += 2
                self.last_growth_time = current_time

    def draw(self, screen):
        if self.owner == 0:
            sprite = self.sprite_neutral
            circle_color = WHITE
        elif self.owner == 1:
            sprite = self.sprite_player
            circle_color = BLUE
        elif self.owner == 2:
            sprite = self.sprite_enemy
            circle_color = RED
        elif self.owner == 3:
            sprite = self.sprite_enemy_green
            circle_color = GREEN
        elif self.owner == 4:
            sprite = self.sprite_enemy_yellow
            circle_color = YELLOW

        pygame.draw.circle(screen, circle_color, (self.x, self.y), self.radius + 10, 3)
        sprite_rect = sprite.get_rect(center=(self.x, self.y))
        screen.blit(sprite, sprite_rect)
        font = pygame.font.SysFont(None, 24)
        text = font.render(str(self.troops), True, BLACK)
        text_rect = text.get_rect(center=(self.x, self.y - self.radius - 1))
        screen.blit(text, text_rect)

    def is_clicked(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx ** 2 + dy ** 2 <= self.click_radius ** 2

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


# Класс перемещения войск
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
            return True
        return False

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), 8)


# Функция создания узлов уровня. Для узлов игрока бонус troop_count_increase прибавляется один раз в начале уровня.
def create_nodes(level):
    nodes = []
    player_growth_interval = level.get("player_growth_interval", UNIT_GROWTH_INTERVAL)
    enemy_growth_interval = level.get("enemy_growth_interval", UNIT_GROWTH_INTERVAL)
    for node_info in level["nodes"]:
        new_node = Node(node_info["x"], node_info["y"], node_info["owner"],
                        node_info["troops"], player_growth_interval, enemy_growth_interval)
        nodes.append(new_node)
    for node in nodes:
        if node.owner == 1:
            node.troops += troop_count_increase
        for other_node in nodes:
            if node != other_node:
                node.add_neighbor(other_node)
    return nodes


def ai_turn(nodes, moving_troops):
    global ai_last_attack_time
    current_time = time.time()
    if current_time - ai_last_attack_time < ai_attack_cooldown:
        return
    for node in nodes:
        if node.owner in [2, 3, 4] and node.troops > 1:
            target_node = min((neighbor for neighbor in node.neighbors if neighbor.owner != node.owner),
                              key=lambda n: n.troops, default=None)
            if target_node:
                troops_to_send = node.troops // 2
                node.troops -= troops_to_send
                moving_troops.append(TroopMovement(node, target_node))
                ai_last_attack_time = current_time


def check_victory(nodes):
    return not any(node.owner in [2, 3, 4] for node in nodes)


def check_defeat(nodes):
    return not any(node.owner == 1 for node in nodes)


def finish_level(level_index):
    global monet
    monet += (level_index + 1) * 10


# Экран выбора уровня (главное меню) с цветным фоном
def level_selection_screen():
    # Запускаем музыку главного меню
    play_music("sounds/menu_music.mp3")

    font_large = pygame.font.SysFont(None, 48)
    title_text = font_large.render("Выберите уровень", True, BLACK)
    title_rect = title_text.get_rect(center=(WIDTH // 2, 100))

    level_buttons = []
    for i, level in enumerate(levels):
        button_text = pygame.font.SysFont(None, 36).render(level["name"], True, BLACK)
        button_rect = pygame.Rect(WIDTH // 2 - 100, 150 + i * 80, 200, 50)  # Сдвинул на 50 пикселей вверх
        level_buttons.append((button_text, button_rect))

    # Дополнительная кнопка магазина
    shop_button_rect = pygame.Rect(WIDTH // 2 - 100, 150 + len(levels) * 80 + 20, 200,
                                   50)  # Сдвинул на 50 пикселей вверх
    shop_button_text = pygame.font.SysFont(None, 36).render("Магазин", True, BLACK)

    # Кнопка выхода
    exit_button_rect = pygame.Rect(WIDTH // 2 - 100, 150 + (len(levels) + 1) * 80 + 20, 200,
                                   50)  # Сдвинул на 50 пикселей вверх
    exit_button_text = pygame.font.SysFont(None, 36).render("Выход", True, BLACK)

    running = True
    while running:
        screen.fill(MENU_BG)  # Цветной фон главного меню
        screen.blit(title_text, title_rect)
        for i, (button_text, button_rect) in enumerate(level_buttons):
            pygame.draw.rect(screen, (200, 200, 200), button_rect)
            screen.blit(button_text, button_rect.move(50, 10))
        # Отрисовка кнопки магазина
        pygame.draw.rect(screen, (150, 150, 150), shop_button_rect)
        screen.blit(shop_button_text, shop_button_rect.move(50, 10))
        # Отрисовка кнопки выхода
        pygame.draw.rect(screen, RED, exit_button_rect)
        screen.blit(exit_button_text, exit_button_rect.move(50, 10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                # Проверяем нажатия на кнопки уровней
                for i, (_, button_rect) in enumerate(level_buttons):
                    if button_rect.collidepoint(pos):
                        game_loop(i)
                # Проверяем нажатие на кнопку магазина
                if shop_button_rect.collidepoint(pos):
                    shop_screen()
                # Проверяем нажатие на кнопку выхода
                if exit_button_rect.collidepoint(pos):
                    running = False  # Завершаем игру
        pygame.display.update()
        clock.tick(FPS)
    pygame.quit()
    exit()


def show_victory_message():
    victory_sound = pygame.mixer.Sound("sounds/victory_sound.mp3")
    victory_sound.set_volume(0.5)
    victory_sound.play()
    font_msg = pygame.font.SysFont(None, 48)
    text = font_msg.render("Вы победили!", True, (255, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)


def show_defeat_message():
    defeat_sound = pygame.mixer.Sound("sounds/defeat_sound.mp3")
    defeat_sound.set_volume(0.3)
    defeat_sound.play()
    font_msg = pygame.font.SysFont(None, 48)
    text = font_msg.render("Вы проиграли!", True, (255, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)


def game_loop(level_index):
    level = levels[level_index]
    nodes = create_nodes(level)
    moving_troops = []
    background = level["background"]
    # Запускаем музыку уровня: если в уровне задан ключ "music", используем его, иначе стандартный трек.
    if "music" in level:
        play_music(level["music"])
    else:
        play_music("sounds/level_music.mp3")

    if isinstance(background, tuple):
        background_color = background
        background_image = None
    else:
        background_image = pygame.image.load(background).convert()
        background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
        background_color = None
    selected_node = None
    running = True
    while running:
        if background_color:
            screen.fill(background_color)
        else:
            screen.blit(background_image, (0, 0))

        # Отрисовка кнопок в углах:
        # Теперь кнопка меню в левом верхнем углу
        menu_button_game = pygame.Rect(10, 10, 100, 40)
        pygame.draw.rect(screen, GRAY, menu_button_game)
        draw_text("Меню", pygame.font.SysFont(None, 24), BLACK, 15, 20)
        # А кнопка магазина в правом верхнем углу
        shop_button_game = pygame.Rect(WIDTH - 110, 10, 100, 40)
        pygame.draw.rect(screen, GRAY, shop_button_game)
        draw_text("Магазин", pygame.font.SysFont(None, 24), BLACK, WIDTH - 100, 20)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                # Если нажата кнопка меню в левом верхнем углу
                if menu_button_game.collidepoint(pos):
                    level_selection_screen()
                    return
                # Если нажата кнопка магазина в правом верхнем углу
                if shop_button_game.collidepoint(pos):
                    shop_screen()
                    continue
                # Обработка кликов по узлам
                for node in nodes:
                    if node.is_clicked(pos):
                        if selected_node is None:
                            selected_node = node
                        else:
                            if selected_node != node and selected_node.owner == 1:
                                if selected_node.troops > 1:
                                    moving_troops.append(TroopMovement(selected_node, node))
                                    selected_node.troops //= 2
                                selected_node = None
                            else:
                                selected_node = node
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    shop_screen()  # Открытие магазина по клавише M
                elif event.key == pygame.K_b:
                    level_selection_screen()  # Возврат в меню по клавише B
                    return
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
            finish_level(level_index)
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
        info_font = pygame.font.SysFont(None, 24)
        draw_text("Нажмите M для магазина, B для меню", info_font, BLUE, 10, HEIGHT - 30)
        pygame.display.update()
        clock.tick(FPS)


# Запуск игры (начало с экрана выбора уровня)
level_selection_screen()
pygame.quit()
