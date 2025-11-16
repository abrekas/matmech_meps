import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize
from skimage.morphology import thin
import networkx as nx
from scipy.spatial import KDTree

def process_floor_plan(image_path):
    # Загружаем изображение
    image = cv2.imread(image_path)
    
    # 1. Выделяем зеленую область (коридор)
    green_mask = extract_green_area(image)
    
    # 2. Выделяем красные области (двери)
    red_mask = extract_red_areas(image)
    
    # 3. Строим скелет коридора (центральную артерию)
    corridor_skeleton = create_corridor_skeleton(green_mask)
    
    # 4. Находим центры красных линий (двери)
    door_points = find_door_centers(red_mask)
    
    # 5. Строим граф
    G = build_manhattan_graph(door_points, corridor_skeleton, green_mask)
    
    return G, door_points, corridor_skeleton, green_mask, red_mask

def extract_green_area(image):
    """Выделяем зеленую область (коридор)"""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Диапазон зеленого цвета в HSV
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Морфологические операции для очистки маски
    kernel = np.ones((3,3), np.uint8)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
    
    return green_mask

def extract_red_areas(image):
    """Выделяем красные области (двери)"""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Два диапазона для красного цвета (т.к. красный на границе HSV)
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    
    red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)
    
    return red_mask

def create_corridor_skeleton(green_mask):
    """Создаем скелет коридора (центральную артерию)"""
    # Убедимся, что маска бинарная
    _, binary = cv2.threshold(green_mask, 1, 255, cv2.THRESH_BINARY)
    
    # Скелетонизация
    skeleton = thin(binary // 255)
    skeleton = (skeleton * 255).astype(np.uint8)
    
    
    # Очищаем скелет от мелких ответвлений
    skeleton = clean_skeleton(skeleton)
    
    return skeleton

def clean_skeleton(skeleton):
    """Очищаем скелет от мелких ответвлений"""
    # Находим концевые точки
    endpoints = find_endpoints(skeleton)
    
    # Удаляем короткие ответвления
    for y, x in endpoints:
        # Прослеживаем ответвление от концевой точки
        branch_length = trace_branch_length(skeleton, (x, y))
        if branch_length < 20:  # Удаляем короткие ответвления
            remove_branch(skeleton, (x, y))
    
    return skeleton

def find_endpoints(skeleton):
    """Находим концевые точки скелета"""
    endpoints = []
    for y in range(1, skeleton.shape[0]-1):
        for x in range(1, skeleton.shape[1]-1):
            if skeleton[y, x] == 255:
                # Считаем количество соседей
                neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        if skeleton[y+dy, x+dx] == 255:
                            neighbors += 1
                if neighbors == 1:  # Концевая точка
                    endpoints.append((y, x))
    return endpoints

def trace_branch_length(skeleton, start_point):
    """Определяем длину ответвления"""
    x, y = start_point
    length = 0
    visited = set()
    queue = [(x, y)]
    
    while queue:
        x, y = queue.pop(0)
        if (x, y) in visited:
            continue
        visited.add((x, y))
        length += 1
        
        # Ищем следующий пиксель
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < skeleton.shape[1] and 0 <= ny < skeleton.shape[0] and 
                skeleton[ny, nx] == 255 and (nx, ny) not in visited):
                queue.append((nx, ny))
                break
    
    return length

def remove_branch(skeleton, start_point):
    """Удаляем ответвление из скелета"""
    x, y = start_point
    visited = set()
    queue = [(x, y)]
    
    while queue:
        x, y = queue.pop(0)
        if (x, y) in visited:
            continue
        visited.add((x, y))
        skeleton[y, x] = 0
        
        # Ищем следующий пиксель
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < skeleton.shape[1] and 0 <= ny < skeleton.shape[0] and 
                skeleton[ny, nx] == 255 and (nx, ny) not in visited):
                # Проверяем, не является ли это точкой ветвления
                neighbors = 0
                for ddx, ddy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nnx, nny = nx + ddx, ny + ddy
                    if (0 <= nnx < skeleton.shape[1] and 0 <= nny < skeleton.shape[0] and 
                        skeleton[nny, nnx] == 255):
                        neighbors += 1
                if neighbors <= 2:  # Продолжаем только если не точка ветвления
                    queue.append((nx, ny))

def find_door_centers(red_mask):
    """Находим центры красных линий (двери)"""
    # Находим контуры красных областей
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    door_points = []
    for contour in contours:
        # Аппроксимируем контур до линии
        if len(contour) >= 2:
            # Находим ориентированную bounding box
            rect = cv2.minAreaRect(contour)
            center, size, angle = rect
            door_points.append((int(center[0]), int(center[1])))
    
    return door_points

def build_manhattan_graph(door_points, corridor_skeleton, green_mask):
    """Строим граф с манхэттеновскими путями"""
    G = nx.Graph()
    
    # Добавляем узлы для дверей
    for i, door in enumerate(door_points):
        G.add_node(f"door_{i}", pos=door, type='door')
    
    # Находим точки скелета для соединения
    skeleton_points = np.column_stack(np.where(corridor_skeleton > 0))
    if len(skeleton_points) == 0:
        return G
    
    # Создаем KD-дерево для быстрого поиска ближайших точек скелета
    skeleton_kdtree = KDTree(skeleton_points[:, [1, 0]])  # меняем порядок (x,y)
    
    # Для каждой двери находим ближайшую точку на скелете
    for i, door in enumerate(door_points):
        door_node = f"door_{i}"
        
        # Находим ближайшую точку скелета
        distance, idx = skeleton_kdtree.query([door])
        nearest_skeleton_point = (skeleton_points[idx[0], 1], skeleton_points[idx[0], 0])
        
        # Создаем манхэттеновский путь от двери до скелета
        path = create_manhattan_path(door, nearest_skeleton_point, green_mask)
        
        # Добавляем путь в граф
        if path and len(path) > 1:
            # Добавляем промежуточные точки пути
            prev_point = door
            prev_node = door_node
            
            for j, point in enumerate(path[1:], 1):  # начинаем с 1, т.к. 0 - это дверь
                point_node = f"path_{i}_{j}"
                G.add_node(point_node, pos=point, type='path_point')
                G.add_edge(prev_node, point_node, weight=distance_between(prev_point, point))
                prev_node = point_node
                prev_point = point
            
            # Соединяем последнюю точку пути с точкой скелета
            skeleton_node = f"skeleton_{i}"
            G.add_node(skeleton_node, pos=nearest_skeleton_point, type='skeleton_point')
            G.add_edge(prev_node, skeleton_node, 
                      weight=distance_between(prev_point, nearest_skeleton_point))
    
    return G

def create_manhattan_path(start, end, green_mask):
    """Создаем манхэттеновский путь (только горизонтальные/вертикальные отрезки)"""
    path = [start]
    
    # Первый отрезок: горизонтальное движение
    intermediate1 = (end[0], start[1])
    
    # Проверяем, что промежуточные точки находятся в коридоре
    if is_point_in_green_area(intermediate1, green_mask):
        path.append(intermediate1)
        path.append(end)
    else:
        # Пробуем вертикальное движение первым
        intermediate1 = (start[0], end[1])
        if is_point_in_green_area(intermediate1, green_mask):
            path.append(intermediate1)
            path.append(end)
        else:
            # Если прямой путь не работает, ищем альтернативный маршрут
            path = find_alternative_manhattan_path(start, end, green_mask)
    
    return path

def is_point_in_green_area(point, green_mask):
    """Проверяем, находится ли точка в зеленой области (коридоре)"""
    x, y = int(point[0]), int(point[1])
    if 0 <= x < green_mask.shape[1] and 0 <= y < green_mask.shape[0]:
        return green_mask[y, x] > 0
    return False

def find_alternative_manhattan_path(start, end, green_mask):
    """Находим альтернативный манхэттеновский путь"""
    path = [start]
    
    # Пробуем разные комбинации горизонтального/вертикального движения
    options = [
        [(end[0], start[1]), end],  # Сначала горизонтально, потом вертикально
        [(start[0], end[1]), end],  # Сначала вертикально, потом горизонтально
    ]
    
    for option in options:
        valid = True
        for point in option:
            if not is_point_in_green_area(point, green_mask):
                valid = False
                break
        if valid:
            path.extend(option)
            return path
    
    # Если ни один вариант не сработал, возвращаем только начальную точку
    return [start]

def distance_between(point1, point2):
    """Вычисляем манхэттеновское расстояние между точками"""
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

def visualize_results(image, G, door_points, corridor_skeleton, green_mask, red_mask):
    """Визуализация результатов"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Исходное изображение
    axes[0,0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    axes[0,0].set_title('Исходное изображение')
    
    # Зеленая маска (коридор)
    axes[0,1].imshow(green_mask, cmap='Greens')
    axes[0,1].set_title('Коридор (зеленая область)')
    
    # Красная маска (двери)
    axes[0,2].imshow(red_mask, cmap='Reds')
    axes[0,2].set_title('Двери (красные области)')
    
    # Скелет коридора
    axes[1,0].imshow(corridor_skeleton, cmap='gray')
    axes[1,0].set_title('Центральная артерия коридора')
    
    # Все обнаруженные точки
    result_img = image.copy()
    for door in door_points:
        cv2.circle(result_img, door, 6, (0, 0, 255), -1)  # Красные - двери
    
    # Рисуем скелет поверх изображения
    skeleton_points = np.where(corridor_skeleton > 0)
    for y, x in zip(skeleton_points[0], skeleton_points[1]):
        cv2.circle(result_img, (x, y), 2, (255, 0, 0), -1)  # Синие - точки скелета
    
    axes[1,1].imshow(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
    axes[1,1].set_title('Двери и центральная артерия')
    
    # Финальный граф
    final_img = image.copy()
    
    # Рисуем ребра графа
    for edge in G.edges():
        node1_pos = G.nodes[edge[0]]['pos']
        node2_pos = G.nodes[edge[1]]['pos']
        cv2.line(final_img, node1_pos, node2_pos, (0, 255, 0), 2)
    
    # Рисуем узлы графа
    for node, data in G.nodes(data=True):
        pos = data['pos']
        if data['type'] == 'door':
            cv2.circle(final_img, pos, 6, (0, 0, 255), -1)  # Красные - двери
        elif data['type'] == 'path_point':
            cv2.circle(final_img, pos, 3, (255, 255, 0), -1)  # Голубые - точки пути
        elif data['type'] == 'skeleton_point':
            cv2.circle(final_img, pos, 4, (255, 0, 0), -1)  # Синие - точки скелета
    
    axes[1,2].imshow(cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB))
    axes[1,2].set_title('Финальный граф с манхэттеновскими путями')
    
    plt.tight_layout()
    plt.show()

# Использование
if __name__ == "__main__":
    image_path = "preprocessed_plan5.png"
    G, doors, skeleton, green_mask, red_mask = process_floor_plan(image_path)
    
    # Загружаем изображение для визуализации
    image = cv2.imread(image_path)
    visualize_results(image, G, doors, skeleton, green_mask, red_mask)
    
    # Выводим информацию о графе
    print(f"Всего дверей: {len(doors)}")
    print(f"Всего вершин в графе: {G.number_of_nodes()}")
    print(f"Всего ребер в графе: {G.number_of_edges()}")
    
    # Сохраняем граф для дальнейшего использования
    nx.write_gml(G, "floor_plan_graph.gml")