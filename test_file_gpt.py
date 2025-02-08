import pygame
import random

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

# Кадровая частота
clock = pygame.time.Clock()
FPS = 60


# Классы
class Node:
    def __init__(self, x, y, owner, troops):
        self.x = x
        self.y = y
        self.owner = owner  # 0 - нейтральный, 1 - игрок, 2 - враг
        self.troops = troops
        self.radius = 30

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

# Функции

def draw_lines(nodes):
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            pygame.draw.line(screen, BLACK, (nodes[i].x, nodes[i].y), (nodes[j].x, nodes[j].y), 1)

# Создание узлов
nodes = [
    Node(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100), random.choice([0, 1, 2]), random.randint(5, 20))
    for _ in range(5)
]

selected_node = None

# Игровой цикл
running = True
while running:
    screen.fill(WHITE)

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
                            # Отправить войска
                            if selected_node.owner == 1 and selected_node.troops > 1:
                                troops_to_send = selected_node.troops // 2
                                selected_node.troops -= troops_to_send
                                if node.owner != 1:
                                    node.troops -= troops_to_send
                                    if node.troops <= 0:
                                        node.owner = 1
                                        node.troops = abs(node.troops)
                                else:
                                    node.troops += troops_to_send
                        selected_node = None

    # Отрисовка линий
    draw_lines(nodes)

    # Отрисовка узлов
    for node in nodes:
        node.draw(screen)

    # Обновление экрана
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
