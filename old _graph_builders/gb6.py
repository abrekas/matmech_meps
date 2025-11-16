import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import KDTree
from scipy import ndimage
from skimage.morphology import thin
from skimage.morphology import skeletonize
from skimage import measure

def process_floor_plan(image_path):
    # Загружаем изображение
    image = cv2.imread(image_path)
    
    # 1. Выделяем зеленую область (коридор)
    green_mask = extract_green_area(image)
    
    # 2. Выделяем красные области (двери)
    red_mask = extract_red_areas(image)
    
    # 3. Строим упрощённый скелет коридора с помощью thin
    corridor_skeleton = create_skeleton_with_thin(green_mask, skeletonize)
    
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

def create_skeleton_with_thin(green_mask, thin_or_skeletonize):
    """Создаем скелет с помощью thin и упрощаем его"""
    # Убедимся, что маска бинарная
    _, binary = cv2.threshold(green_mask, 1, 255, cv2.THRESH_BINARY)
    
    # Используем thin для получения скелета
    skeleton = thin_or_skeletonize(binary // 255)
    skeleton = (skeleton * 255).astype(np.uint8)
    
    # Упрощаем скелет - находим основные ветви
    simplified_skeleton = simplify_skeleton(skeleton)
    
    return simplified_skeleton

def simplify_skeleton(skeleton):
    """Упрощаем скелет, оставляя только основные ветви"""
    # Находим концевые точки и точки ветвления
    endpoints, branch_points = find_key_points(skeleton)
    
    # Создаем граф скелета
    skeleton_graph = build_skeleton_graph(skeleton)
    
    # Находим основные пути между ключевыми точками
    main_paths = find_main_paths(skeleton_graph, endpoints, branch_points)
    
    # Создаем упрощенный скелет на основе основных путей
    simplified = np.zeros_like(skeleton)
    
    for path in main_paths:
        for i in range(len(path) - 1):
            pt1 = path[i]
            pt2 = path[i + 1]
            cv2.line(simplified, pt1, pt2, 255, 1)
    
    return simplified

def find_key_points(skeleton):
    """Находим концевые точки и точки ветвления скелета"""
    endpoints = []
    branch_points = []
    
    # Ядро для проверки соседей
    kernel = np.ones((3, 3), np.uint8)
    
    for y in range(1, skeleton.shape[0] - 1):
        for x in range(1, skeleton.shape[1] - 1):
            if skeleton[y, x] == 255:
                # Вычисляем количество соседей
                neighborhood = skeleton[y-1:y+2, x-1:x+2]
                neighbors = np.sum(neighborhood == 255) - 1  # исключаем центральный пиксель
                
                if neighbors == 1:
                    endpoints.append((x, y))
                elif neighbors >= 3:
                    branch_points.append((x, y))
    
    return endpoints, branch_points

def build_skeleton_graph(skeleton):
    """Строим граф представления скелета"""
    # Находим все точки скелета
    points = np.column_stack(np.where(skeleton > 0))
    points = [(p[1], p[0]) for p in points]  # преобразуем в (x, y)
    
    # Создаем граф
    G = nx.Graph()
    G.add_nodes_from(points)
    
    # Добавляем ребра между соседними точками
    for point in points:
        x, y = point
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
            neighbor = (x + dx, y + dy)
            if neighbor in G.nodes:
                G.add_edge(point, neighbor)
    
    return G

def find_main_paths(graph, endpoints, branch_points):
    """Находим основные пути в скелете"""
    key_points = endpoints + branch_points
    
    # Если ключевых точек мало, возвращаем все пути между ними
    if len(key_points) <= 1:
        return []
    
    # Находим все пути между ключевыми точками
    main_paths = []
    
    for i, start in enumerate(key_points):
        for j, end in enumerate(key_points):
            if i < j and graph.has_node(start) and graph.has_node(end):
                try:
                    path = nx.shortest_path(graph, start, end)
                    # Фильтруем короткие пути и пути с малым количеством изгибов
                    if len(path) > 10 and is_straight_path(path):
                        main_paths.append(path)
                except nx.NetworkXNoPath:
                    continue
    
    # Если не нашли путей, берем самый длинный путь между конечными точками
    if not main_paths and len(endpoints) >= 2:
        for i, start in enumerate(endpoints):
            for j, end in enumerate(endpoints):
                if i < j and graph.has_node(start) and graph.has_node(end):
                    try:
                        path = nx.shortest_path(graph, start, end)
                        if len(path) > 10:
                            main_paths.append(path)
                    except nx.NetworkXNoPath:
                        continue
    
    return main_paths

def is_straight_path(path, angle_threshold=30):
    """Проверяем, является ли путь достаточно прямым"""
    if len(path) < 3:
        return False
    
    # Вычисляем углы между последовательными сегментами
    angles = []
    for i in range(1, len(path) - 1):
        v1 = (path[i][0] - path[i-1][0], path[i][1] - path[i-1][1])
        v2 = (path[i+1][0] - path[i][0], path[i+1][1] - path[i][1])
        
        # Вычисляем угол между векторами
        dot_product = v1[0]*v2[0] + v1[1]*v2[1]
        mag1 = np.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = np.sqrt(v2[0]**2 + v2[1]**2)
        
        if mag1 > 0 and mag2 > 0:
            cos_angle = dot_product / (mag1 * mag2)
            cos_angle = np.clip(cos_angle, -1, 1)  # избегаем численных ошибок
            angle = np.degrees(np.arccos(cos_angle))
            angles.append(angle)
    
    if not angles:
        return True
    
    # Если средний угол меньше порога, путь считается прямым
    return np.mean(angles) < angle_threshold

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
    skeleton_points = find_skeleton_points(corridor_skeleton)
    if len(skeleton_points) == 0:
        return G
    
    # Создаем KD-дерево для быстрого поиска ближайших точек скелета
    skeleton_kdtree = KDTree(skeleton_points)
    
    # Для каждой двери находим ближайшую точку на скелете
    for i, door in enumerate(door_points):
        door_node = f"door_{i}"
        
        # Находим ближайшую точку скелета
        distance, idx = skeleton_kdtree.query([door])
        nearest_skeleton_point = tuple(skeleton_points[idx[0]])
        
        # Создаем манхэттеновский путь от двери до скелета
        path = create_optimized_manhattan_path(door, nearest_skeleton_point, green_mask)
        
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
    
    # Соединяем точки скелета между собой
    connect_skeleton_points(G, skeleton_points, corridor_skeleton)
    
    return G

def find_skeleton_points(skeleton):
    """Находим ключевые точки скелета"""
    # Находим все точки скелета
    points = np.column_stack(np.where(skeleton > 0))
    if len(points) == 0:
        return []
    
    # Преобразуем в формат (x, y)
    points = points[:, [1, 0]]
    
    # Находим концевые точки и точки ветвления
    key_points = []
    
    for point in points:
        x, y = point
        # Проверяем количество соседей
        neighbors = 0
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < skeleton.shape[1] and 0 <= ny < skeleton.shape[0] and 
                skeleton[ny, nx] > 0):
                neighbors += 1
        
        # Сохраняем концевые точки и точки ветвления
        if neighbors == 1 or neighbors >= 3:
            key_points.append((x, y))
    
    # Если ключевых точек мало, добавляем равномерно распределенные точки
    if len(key_points) < 3:
        step = max(1, len(points) // 10)
        key_points.extend([tuple(points[i]) for i in range(0, len(points), step)])
    
    return key_points

def create_optimized_manhattan_path(start, end, green_mask):
    """Создаем оптимизированный манхэттеновский путь"""
    path = [start]
    
    # Пробуем разные варианты путей в порядке предпочтения
    path_options = [
        # 1. Сначала горизонтально, потом вертикально
        [(end[0], start[1]), end],
        # 2. Сначала вертикально, потом горизонтально
        [(start[0], end[1]), end],
        # 3. Добавляем промежуточную точку для обхода препятствий
        [(start[0] + (end[0]-start[0])//2, start[1]), 
         (start[0] + (end[0]-start[0])//2, end[1]), end],
        # 4. Другой вариант с промежуточной точкой
        [(start[0], start[1] + (end[1]-start[1])//2),
         (end[0], start[1] + (end[1]-start[1])//2), end]
    ]
    
    for option in path_options:
        valid_path = True
        test_path = [start] + option
        
        # Проверяем, что все сегменты пути находятся в коридоре
        for i in range(len(test_path) - 1):
            if not is_path_in_green_area(test_path[i], test_path[i+1], green_mask):
                valid_path = False
                break
        
        if valid_path:
            return test_path
    
    # Если ни один вариант не сработал, возвращаем прямой путь (даже если он не в коридоре)
    return [start, end]

def is_path_in_green_area(point1, point2, green_mask):
    """Проверяем, что путь между двумя точками находится в коридоре"""
    # Создаем временное изображение для проверки пути
    temp_mask = np.zeros_like(green_mask)
    cv2.line(temp_mask, point1, point2, 255, 2)
    
    # Проверяем, что все точки пути находятся в зеленой области
    intersection = cv2.bitwise_and(temp_mask, green_mask)
    
    # Если более 90% пути находится в коридоре, считаем путь валидным
    path_pixels = np.sum(temp_mask > 0)
    valid_pixels = np.sum(intersection > 0)
    
    return path_pixels > 0 and valid_pixels / path_pixels > 0.9

def is_point_in_green_area(point, green_mask):
    """Проверяем, находится ли точка в зеленой области (коридоре)"""
    x, y = int(point[0]), int(point[1])
    if 0 <= x < green_mask.shape[1] and 0 <= y < green_mask.shape[0]:
        return green_mask[y, x] > 0
    return False

def distance_between(point1, point2):
    """Вычисляем манхэттеновское расстояние между точками"""
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

def connect_skeleton_points(G, skeleton_points, skeleton):
    """Соединяем точки скелета между собой"""
    if len(skeleton_points) < 2:
        return
    
    # Создаем KD-дерево для точек скелета
    kdtree = KDTree(skeleton_points)
    
    # Соединяем близлежащие точки скелета
    for i, point1 in enumerate(skeleton_points):
        node1 = f"skeleton_{i}"
        if node1 not in G.nodes:
            G.add_node(node1, pos=point1, type='skeleton_point')
        
        # Находим ближайшие точки
        distances, indices = kdtree.query([point1], k=min(5, len(skeleton_points)))
        
        for j, idx in enumerate(indices[0]):
            if i != idx:  # Не соединяем точку с самой собой
                point2 = skeleton_points[idx]
                distance = distances[0][j]
                
                # Соединяем, если точки близки и соединение имеет смысл
                if distance < 100 and are_points_connected(point1, point2, skeleton):
                    node2 = f"skeleton_{idx}"
                    if node2 not in G.nodes:
                        G.add_node(node2, pos=point2, type='skeleton_point')
                    
                    if not G.has_edge(node1, node2):
                        G.add_edge(node1, node2, weight=distance)

def are_points_connected(point1, point2, skeleton):
    """Проверяем, соединены ли точки через скелет"""
    # Создаем линию между точками
    temp = np.zeros_like(skeleton)
    cv2.line(temp, point1, point2, 255, 2)
    
    # Проверяем пересечение со скелетом
    intersection = cv2.bitwise_and(temp, skeleton)
    
    # Если есть достаточное пересечение, точки соединены
    return np.sum(intersection > 0) > 0.5 * np.sum(temp > 0)

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
    axes[1,0].set_title('Упрощенный скелет коридора')
    
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