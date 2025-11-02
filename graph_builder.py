import cv2
import numpy as np
from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
import networkx as nx


# Загружаем изображение
image = cv2.imread('plan5.bmp')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Бинаризация
_, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)

# Морфологические операции для выделения комнат
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

# Находим контуры комнат
contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Фильтруем маленькие контуры (шум)
min_area = 1000
rooms = []
for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > min_area:
        rooms.append(cnt)

# Создаем маску коридоров
corridors_mask = binary.copy()
cv2.drawContours(corridors_mask, rooms, -1, 0, -1)  # Убираем комнаты

# Скелетонизация
skeleton = skeletonize(corridors_mask // 255)
skeleton = (skeleton * 255).astype(np.uint8)

# Находим узлы скелета (перекрестки и конечные точки)
kernel = np.ones((3,3), np.uint8)
skeleton_clean = skeleton.copy()

# Узлы скелета
nodes = []
for y in range(1, skeleton_clean.shape[0]-1):
    for x in range(1, skeleton_clean.shape[1]-1):
        if skeleton_clean[y,x] == 255:
            neighborhood = skeleton_clean[y-1:y+2, x-1:x+2]
            if np.sum(neighborhood) > 510:  # Точки ветвления
                nodes.append((x,y))
            elif np.sum(neighborhood) == 510:  # Конечные точки
                nodes.append((x,y))

# Добавляем центры комнат как узлы
room_nodes = []
for room in rooms:
    M = cv2.moments(room)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        room_nodes.append((cx, cy))

# Создаем граф
G = nx.Graph()
all_nodes = nodes + room_nodes
G.add_nodes_from(all_nodes)

# Добавляем ребра на основе скелета
# (здесь нужно реализовать поиск путей между узлами)

# Рисуем граф поверх изображения
plt.figure(figsize=(9, 6))
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
pos = {node: (node[0], node[1]) for node in all_nodes}
nx.draw(G, pos, node_size=20, node_color='red', edge_color='blue')
plt.show()


