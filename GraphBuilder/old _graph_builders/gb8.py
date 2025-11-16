import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import KDTree
from skimage.morphology import thin
import math

def process_floor_plan(image_path):
    # Загружаем изображение
    image = cv2.imread(image_path)
    
    # 1. Выделяем зеленую область (коридор)
    green_mask = extract_green_area(image)
    
    # 2. Выделяем красные области (двери)
    red_mask = extract_red_areas(image)
    
    # 3. Разделяем коридор на большие и маленькие прямоугольники
    main_corridor_rects, extension_rects = segment_corridor_rectangles(green_mask)
    
    # 4. Строим центральные линии для каждого прямоугольника
    corridor_skeleton = create_corridor_skeleton_from_rectangles(main_corridor_rects, extension_rects, green_mask.shape)
    
    # 5. Находим центры красных линий (двери)
    door_points = find_door_centers(red_mask)
    
    # 6. Строим граф
    G = build_corridor_graph(door_points, corridor_skeleton, green_mask, main_corridor_rects, extension_rects)
    
    return G, door_points, corridor_skeleton, green_mask, red_mask, main_corridor_rects, extension_rects

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

def segment_corridor_rectangles(green_mask):
    """Разделяем коридор на большие прямоугольники (основной коридор) и маленькие (расширения)"""
    # Находим контуры коридора
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return [], []
    
    # Берем самый большой контур (весь коридор)
    main_contour = max(contours, key=cv2.contourArea)
    
    # Аппроксимируем контур до упрощенной формы
    epsilon = 0.01 * cv2.arcLength(main_contour, True)
    approx = cv2.approxPolyDP(main_contour, epsilon, True)
    
    # Получаем ограничивающий прямоугольник всего коридора
    x, y, w, h = cv2.boundingRect(main_contour)
    
    # Анализируем геометрию коридора для разделения
    main_rects, extension_rects = analyze_corridor_geometry(green_mask, approx)
    
    return main_rects, extension_rects

def analyze_corridor_geometry(mask, contour):
    """Анализируем геометрию коридора и разделяем на прямоугольники"""
    # Получаем bounding rect всего контура
    x, y, w, h = cv2.boundingRect(contour)
    
    # Создаем маску для анализа
    analysis_mask = np.zeros_like(mask)
    cv2.drawContours(analysis_mask, [contour], 0, 255, -1)
    
    # Используем алгоритм разделения на прямоугольники
    return recursive_rectangle_split(analysis_mask, x, y, w, h)

def recursive_rectangle_split(mask, x, y, w, h, min_area_ratio=0.1, max_aspect_ratio=4):
    """Рекурсивно разделяем область на прямоугольники"""
    rect_area = w * h
    if rect_area < 500:  # Минимальная площадь
        return [], []
    
    # Проверяем, насколько прямоугольник заполнен коридором
    roi = mask[y:y+h, x:x+w]
    filled_ratio = np.sum(roi > 0) / rect_area
    
    # Если заполненность хорошая, это основной прямоугольник
    if filled_ratio > 0.8:
        return [(x, y, w, h)], []
    
    # Если заполненность средняя, проверяем аспектное соотношение
    aspect_ratio = max(w, h) / min(w, h)
    if filled_ratio > 0.3 and aspect_ratio < max_aspect_ratio:
        # Это расширение коридора
        return [], [(x, y, w, h)]
    
    # Если заполненность плохая, рекурсивно разделяем
    main_rects = []
    extension_rects = []
    
    if w > h:
        # Разделяем по ширине
        w1 = w // 2
        w2 = w - w1
        m1, e1 = recursive_rectangle_split(mask, x, y, w1, h, min_area_ratio, max_aspect_ratio)
        m2, e2 = recursive_rectangle_split(mask, x + w1, y, w2, h, min_area_ratio, max_aspect_ratio)
        main_rects.extend(m1 + m2)
        extension_rects.extend(e1 + e2)
    else:
        # Разделяем по высоте
        h1 = h // 2
        h2 = h - h1
        m1, e1 = recursive_rectangle_split(mask, x, y, w, h1, min_area_ratio, max_aspect_ratio)
        m2, e2 = recursive_rectangle_split(mask, x, y + h1, w, h2, min_area_ratio, max_aspect_ratio)
        main_rects.extend(m1 + m2)
        extension_rects.extend(e1 + e2)
    
    return main_rects, extension_rects

def create_corridor_skeleton_from_rectangles(main_rects, extension_rects, shape):
    """Создаем скелет коридора на основе прямоугольников"""
    skeleton = np.zeros(shape, dtype=np.uint8)
    
    # Для каждого основного прямоугольника рисуем центральную линию
    for rect in main_rects:
        x, y, w, h = rect
        
        if w > h:
            # Горизонтальный прямоугольник - вертикальная центральная линия
            center_x = x + w // 2
            cv2.line(skeleton, (center_x, y), (center_x, y + h), 255, 2)
        else:
            # Вертикальный прямоугольник - горизонтальная центральная линия
            center_y = y + h // 2
            cv2.line(skeleton, (x, center_y), (x + w, center_y), 255, 2)
    
    # Для расширений тоже рисуем центральные линии, но тоньше
    for rect in extension_rects:
        x, y, w, h = rect
        
        if w > h:
            center_x = x + w // 2
            cv2.line(skeleton, (center_x, y), (center_x, y + h), 255, 1)
        else:
            center_y = y + h // 2
            cv2.line(skeleton, (x, center_y), (x + w, center_y), 255, 1)
    
    # Соединяем центральные линии между соседними прямоугольниками
    skeleton = connect_rectangle_centers(skeleton, main_rects, extension_rects)
    
    return skeleton

def connect_rectangle_centers(skeleton, main_rects, extension_rects):
    """Соединяем центральные линии между прямоугольниками"""
    all_rects = main_rects + extension_rects
    
    for i, rect1 in enumerate(all_rects):
        for j, rect2 in enumerate(all_rects):
            if i >= j:
                continue
            
            x1, y1, w1, h1 = rect1
            x2, y2, w2, h2 = rect2
            
            # Центры прямоугольников
            center1 = (x1 + w1 // 2, y1 + h1 // 2)
            center2 = (x2 + w2 // 2, y2 + h2 // 2)
            
            # Проверяем, соседствуют ли прямоугольники
            if are_rectangles_adjacent(rect1, rect2):
                # Соединяем центры
                cv2.line(skeleton, center1, center2, 255, 2)
    
    return skeleton

def are_rectangles_adjacent(rect1, rect2, max_gap=20):
    """Проверяем, соседствуют ли два прямоугольника"""
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    
    # Расширяем прямоугольники для учета зазора
    rect1_expanded = (x1 - max_gap, y1 - max_gap, w1 + 2 * max_gap, h1 + 2 * max_gap)
    rect2_expanded = (x2 - max_gap, y2 - max_gap, w2 + 2 * max_gap, h2 + 2 * max_gap)
    
    # Проверяем пересечение расширенных прямоугольников
    return do_rectangles_intersect(rect1_expanded, rect2_expanded)

def do_rectangles_intersect(rect1, rect2):
    """Проверяем пересечение двух прямоугольников"""
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    
    return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

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

def build_corridor_graph(door_points, corridor_skeleton, green_mask, main_rects, extension_rects):
    """Строим граф коридора с учетом разделения на прямоугольники"""
    G = nx.Graph()
    
    # Добавляем узлы для дверей
    for i, door in enumerate(door_points):
        G.add_node(f"door_{i}", pos=door, type='door')
    
    # Добавляем узлы для центров прямоугольников
    rect_centers = []
    for i, rect in enumerate(main_rects):
        x, y, w, h = rect
        center = (x + w // 2, y + h // 2)
        rect_centers.append(center)
        G.add_node(f"main_rect_{i}", pos=center, type='main_corridor')
    
    for i, rect in enumerate(extension_rects):
        x, y, w, h = rect
        center = (x + w // 2, y + h // 2)
        rect_centers.append(center)
        G.add_node(f"ext_rect_{i}", pos=center, type='corridor_extension')
    
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
        path = create_strict_manhattan_path(door, nearest_skeleton_point, green_mask)
        
        # Добавляем путь в граф
        if path and len(path) > 1:
            add_path_to_graph(G, path, door_node, i)
    
    # Соединяем центры прямоугольников между собой
    connect_rectangle_centers_in_graph(G, main_rects, extension_rects, green_mask)
    
    return G

def find_skeleton_points(skeleton):
    """Находим ключевые точки скелета"""
    points = np.column_stack(np.where(skeleton > 0))
    if len(points) == 0:
        return []
    
    # Преобразуем в формат (x, y)
    points = points[:, [1, 0]]
    
    # Находим концевые точки и точки ветвления
    key_points = []
    
    for point in points:
        x, y = point
        neighbors = 0
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < skeleton.shape[1] and 0 <= ny < skeleton.shape[0] and 
                skeleton[ny, nx] > 0):
                neighbors += 1
        
        if neighbors == 1 or neighbors >= 3:
            key_points.append((x, y))
    
    return key_points

def create_strict_manhattan_path(start, end, green_mask):
    """Создаем строго манхэттеновский путь"""
    path = [start]
    
    # Всегда сначала горизонтальное движение, потом вертикальное
    intermediate = (end[0], start[1])
    
    if is_path_in_green_area(start, intermediate, green_mask) and is_path_in_green_area(intermediate, end, green_mask):
        path.append(intermediate)
        path.append(end)
    else:
        # Пробуем вертикальное движение первым
        intermediate = (start[0], end[1])
        if is_path_in_green_area(start, intermediate, green_mask) and is_path_in_green_area(intermediate, end, green_mask):
            path.append(intermediate)
            path.append(end)
    
    return path

def is_path_in_green_area(point1, point2, green_mask):
    """Проверяем, что путь между двумя точками находится в коридоре"""
    temp_mask = np.zeros_like(green_mask)
    cv2.line(temp_mask, point1, point2, 255, 2)
    
    intersection = cv2.bitwise_and(temp_mask, green_mask)
    path_pixels = np.sum(temp_mask > 0)
    valid_pixels = np.sum(intersection > 0)
    
    return path_pixels > 0 and valid_pixels / path_pixels > 0.9

def add_path_to_graph(G, path, start_node, path_id):
    """Добавляем путь в граф"""
    prev_point = path[0]
    prev_node = start_node
    
    for j, point in enumerate(path[1:], 1):
        point_node = f"path_{path_id}_{j}"
        G.add_node(point_node, pos=point, type='path_point')
        G.add_edge(prev_node, point_node, weight=distance_manhattan(prev_point, point))
        prev_node = point_node
        prev_point = point

def connect_rectangle_centers_in_graph(G, main_rects, extension_rects, green_mask):
    """Соединяем центры прямоугольников в графе"""
    all_rects = []
    
    # Добавляем основные прямоугольники
    for i, rect in enumerate(main_rects):
        x, y, w, h = rect
        center = (x + w // 2, y + h // 2)
        all_rects.append((center, f"main_rect_{i}"))
    
    # Добавляем расширения
    for i, rect in enumerate(extension_rects):
        x, y, w, h = rect
        center = (x + w // 2, y + h // 2)
        all_rects.append((center, f"ext_rect_{i}"))
    
    # Соединяем соседние прямоугольники
    for i, (center1, node1) in enumerate(all_rects):
        for j, (center2, node2) in enumerate(all_rects):
            if i >= j:
                continue
            
            # Проверяем расстояние между центрами
            dist = distance_euclidean(center1, center2)
            if dist < 200:  # Максимальное расстояние для соединения
                # Создаем манхэттеновский путь между центрами
                path = create_strict_manhattan_path(center1, center2, green_mask)
                if len(path) > 1:
                    # Добавляем путь в граф
                    add_path_to_graph(G, path, node1, f"rect_{i}_{j}")

def distance_manhattan(point1, point2):
    """Манхэттенское расстояние"""
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

def distance_euclidean(point1, point2):
    """Евклидово расстояние"""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def visualize_detailed_results(image, G, door_points, corridor_skeleton, green_mask, red_mask, main_rects, extension_rects):
    """Визуализация результатов с разделением на прямоугольники"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Исходное изображение
    axes[0,0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    axes[0,0].set_title('Исходное изображение')
    
    # Зеленая маска (коридор) с прямоугольниками
    result_img = image.copy()
    
    # Рисуем основные прямоугольники (синие)
    for rect in main_rects:
        x, y, w, h = rect
        cv2.rectangle(result_img, (x, y), (x + w, y + h), (255, 0, 0), 2)
    
    # Рисуем расширения (желтые)
    for rect in extension_rects:
        x, y, w, h = rect
        cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 255), 2)
    
    axes[0,1].imshow(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
    axes[0,1].set_title('Разделение на прямоугольники')
    
    # Красная маска (двери)
    axes[0,2].imshow(red_mask, cmap='Reds')
    axes[0,2].set_title('Двери (красные области)')
    
    # Скелет коридора
    axes[1,0].imshow(corridor_skeleton, cmap='gray')
    axes[1,0].set_title('Скелет коридора')
    
    # Все обнаруженные точки
    points_img = image.copy()
    for door in door_points:
        cv2.circle(points_img, door, 6, (0, 0, 255), -1)  # Красные - двери
    
    # Рисуем центры прямоугольников
    for rect in main_rects:
        x, y, w, h = rect
        center = (x + w // 2, y + h // 2)
        cv2.circle(points_img, center, 4, (255, 0, 0), -1)  # Синие - основные прямоугольники
    
    for rect in extension_rects:
        x, y, w, h = rect
        center = (x + w // 2, y + h // 2)
        cv2.circle(points_img, center, 4, (0, 255, 255), -1)  # Желтые - расширения
    
    axes[1,1].imshow(cv2.cvtColor(points_img, cv2.COLOR_BGR2RGB))
    axes[1,1].set_title('Двери и центры прямоугольников')
    
    # Финальный граф
    final_img = image.copy()
    
    # Рисуем прямоугольники
    for rect in main_rects:
        x, y, w, h = rect
        cv2.rectangle(final_img, (x, y), (x + w, y + h), (255, 0, 0), 1)
    
    for rect in extension_rects:
        x, y, w, h = rect
        cv2.rectangle(final_img, (x, y), (x + w, y + h), (0, 255, 255), 1)
    
    # Рисуем ребра графа
    for edge in G.edges():
        node1_pos = G.nodes[edge[0]]['pos']
        node2_pos = G.nodes[edge[1]]['pos']
        cv2.line(final_img, node1_pos, node2_pos, (0, 255, 0), 2)
    
    # Рисуем узлы графа
    for node, data in G.nodes(data=True):
        pos = data['pos']
        if data['type'] == 'door':
            cv2.circle(final_img, pos, 6, (0, 0, 255), -1)
        elif data['type'] == 'main_corridor':
            cv2.circle(final_img, pos, 5, (255, 0, 0), -1)
        elif data['type'] == 'corridor_extension':
            cv2.circle(final_img, pos, 5, (0, 255, 255), -1)
        elif data['type'] == 'path_point':
            cv2.circle(final_img, pos, 3, (255, 255, 0), -1)
    
    axes[1,2].imshow(cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB))
    axes[1,2].set_title('Финальный граф с прямоугольниками')
    
    plt.tight_layout()
    plt.show()

# Использование
if __name__ == "__main__":
    image_path = "preprocessed_plan5.png"
    G, doors, skeleton, green_mask, red_mask, main_rects, extension_rects = process_floor_plan(image_path)
    
    # Загружаем изображение для визуализации
    image = cv2.imread(image_path)
    visualize_detailed_results(image, G, doors, skeleton, green_mask, red_mask, main_rects, extension_rects)
    
    # Выводим информацию
    print(f"Всего дверей: {len(doors)}")
    print(f"Основных прямоугольников коридора: {len(main_rects)}")
    print(f"Расширений коридора: {len(extension_rects)}")
    print(f"Всего вершин в графе: {G.number_of_nodes()}")
    print(f"Всего ребер в графе: {G.number_of_edges()}")
    
    # Сохраняем граф
    nx.write_gml(G, "floor_plan_graph.gml")