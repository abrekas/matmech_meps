import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import KDTree
from scipy import ndimage
from skimage.morphology import thin, skeletonize
from skimage import measure

def process_floor_plan(image_path):
    # Загружаем изображение
    image = cv2.imread(image_path)
    
    # 1. Выделяем зеленую область (коридор)
    green_mask = extract_green_area(image)
    
    # 2. Выделяем красные области (двери)
    red_mask = extract_red_areas(image)
    
    # 3. Строим упрощённый скелет коридора с помощью thin
    corridor_skeleton = create_skeleton(green_mask)
    # with open('reco1_out.txt', 'w') as f:
    #     f.write(str(corridor_skeleton))
    
    # 4. Находим центры красных линий (двери)
    door_points = find_door_centers(red_mask)
    
    # 5. Строим граф с чисто манхэттеновскими путями
    G = build_manhattan_graph_strict(door_points, corridor_skeleton, green_mask)
    
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

def create_skeleton(green_mask):
    """Создаем скелет с помощью thin и упрощаем его"""
    # Убедимся, что маска бинарная
    _, binary = cv2.threshold(green_mask, 1, 255, cv2.THRESH_BINARY)
    
    # Используем thin для получения скелета
    # skeleton = thin(binary // 255)
    skeleton = skeletonize(binary // 255)
    skeleton = (skeleton * 255).astype(np.uint8)
    
    return skeleton

def find_angles(skeleton):
    cv2.findContours()
    angles = cv2.cornerHarris(skeleton, )

def find_angles_contour(skeleton):
    # Находим контуры и аппроксимируем
    approx_list = []
    contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        approx_list.append(approx)
        # Углы - это вершины аппроксимированного контура
    return approx_list

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

def build_manhattan_graph_strict(door_points, corridor_skeleton, green_mask):
    """Строим граф со строго манхэттеновскими путями (только горизонтальные/вертикальные)"""
    G = nx.Graph()
    
    # Добавляем узлы для дверей
    for i, door in enumerate(door_points):
        G.add_node(f"door_{i}", pos=door, type='door')
    
    # Находим точки скелета для соединения
    skeleton_points = find_skeleton_points_straight(corridor_skeleton)
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
        
        # Создаем строго манхэттеновский путь от двери до скелета
        path = create_strict_manhattan_path(door, nearest_skeleton_point, green_mask)
        
        # Добавляем путь в граф
        if path and len(path) > 1:
            add_path_to_graph(G, path, door_node, i)
    
    # Соединяем точки скелета между собой строго ортогональными путями
    connect_skeleton_points_strict(G, skeleton_points, green_mask)
    
    return G

def find_skeleton_points_straight(skeleton):
    """Находим ключевые точки скелета, предпочитая прямые участки"""
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
        # Проверяем количество соседей (только ортогональные)
        neighbors = 0
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < skeleton.shape[1] and 0 <= ny < skeleton.shape[0] and 
                skeleton[ny, nx] > 0):
                neighbors += 1
        
        # Сохраняем концевые точки и точки ветвления
        if neighbors == 1 or neighbors >= 3:
            key_points.append((x, y))
    
    # Если ключевых точек мало, добавляем точки с максимальным количеством ортогональных соседей
    if len(key_points) < 3:
        # Сортируем по количеству соседей и берем топ-10
        neighbor_counts = []
        for point in points:
            x, y = point
            neighbors = 0
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < skeleton.shape[1] and 0 <= ny < skeleton.shape[0] and 
                    skeleton[ny, nx] > 0):
                    neighbors += 1
            neighbor_counts.append((point, neighbors))
        
        neighbor_counts.sort(key=lambda x: x[1], reverse=True)
        additional_points = [p[0] for p in neighbor_counts[:min(10, len(neighbor_counts))]]
        key_points.extend(additional_points)
    
    return list(set(key_points))  # Убираем дубликаты

def create_strict_manhattan_path(start, end, green_mask):
    """Создаем строго манхэттеновский путь (только горизонтальные/вертикальные отрезки)"""
    path = [start]
    
    # Всегда сначала горизонтальное движение, потом вертикальное
    intermediate = (end[0], start[1])
    
    # Проверяем, что оба отрезка находятся в коридоре
    if (is_path_in_green_area(start, intermediate, green_mask) and 
        is_path_in_green_area(intermediate, end, green_mask)):
        path.append(intermediate)
        path.append(end)
    else:
        # Пробуем вертикальное движение первым
        intermediate = (start[0], end[1])
        if (is_path_in_green_area(start, intermediate, green_mask) and 
            is_path_in_green_area(intermediate, end, green_mask)):
            path.append(intermediate)
            path.append(end)
        else:
            # Если прямой путь не работает, находим альтернативный манхэттеновский путь
            path = find_alternative_manhattan_path_strict(start, end, green_mask)
    
    return path

def find_alternative_manhattan_path_strict(start, end, green_mask):
    """Находим альтернативный строго манхэттеновский путь"""
    path = [start]
    
    # Пробуем разные комбинации горизонтального/вертикального движения
    options = [
        # Вариант 1: Горизонтально -> Вертикально
        [(end[0], start[1]), end],
        # Вариант 2: Вертикально -> Горизонтально  
        [(start[0], end[1]), end],
        # Вариант 3: С промежуточной точкой посередине
        [(start[0] + (end[0]-start[0])//2, start[1]),
         (start[0] + (end[0]-start[0])//2, end[1]), end],
        # Вариант 4: Другой вариант с промежуточной точкой
        [(start[0], start[1] + (end[1]-start[1])//2),
         (end[0], start[1] + (end[1]-start[1])//2), end]
    ]
    
    for option in options:
        valid_path = True
        test_path = [start] + option
        
        # Проверяем, что все сегменты пути находятся в коридоре
        for i in range(len(test_path) - 1):
            if not is_path_in_green_area(test_path[i], test_path[i+1], green_mask):
                valid_path = False
                break
        
        if valid_path:
            return test_path
    
    # Если ни один вариант не сработал, возвращаем минимальный манхэттеновский путь
    return [start, (end[0], start[1]), end] if abs(end[0]-start[0]) > abs(end[1]-start[1]) else [start, (start[0], end[1]), end]

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

def connect_skeleton_points_strict(G, skeleton_points, green_mask):
    """Соединяем точки скелета между собой строго ортогональными путями"""
    if len(skeleton_points) < 2:
        return
    
    # Создаем KD-дерево для точек скелета
    kdtree = KDTree(skeleton_points)
    
    # Соединяем близлежащие точки скелета строго манхэттеновскими путями
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
                
                # Соединяем, если точки близки
                if distance < 100:
                    # Создаем строго манхэттеновский путь между точками скелета
                    path = create_strict_manhattan_path(point1, point2, green_mask)
                    
                    if len(path) > 1:
                        node2 = f"skeleton_{idx}"
                        if node2 not in G.nodes:
                            G.add_node(node2, pos=point2, type='skeleton_point')
                        
                        # Добавляем путь между точками скелета
                        add_path_to_graph(G, path, node1, f"sk_{i}_{idx}")

def distance_manhattan(point1, point2):
    """Вычисляем манхэттеновское расстояние между точками"""
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

def visualize_results(image, G, door_points, corridor_skeleton, green_mask, red_mask, angles_points):
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
    axes[1,0].set_title('Скелет коридора')
    
    # Все обнаруженные точки
    result_img = image.copy()
    for door in door_points:
        cv2.circle(result_img, door, 6, (0, 0, 255), -1)  # Красные - двери
    
    # Рисуем скелет поверх изображения
    skeleton_points = np.where(corridor_skeleton > 0)
    for y, x in zip(skeleton_points[0], skeleton_points[1]):
        cv2.circle(result_img, (x, y), 2, (255, 0, 0), -1)  # Синие - точки скелета

    angles_points = np.where(angles_points > 0)
    for y,x in zip(angles_points[0], angles_points[1]):
        cv2.circle(result_img, (y,x), 10, (0, 0, 255), -1)
    
    axes[1,1].imshow(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
    axes[1,1].set_title('Двери и скелет')
    
    # # Финальный граф
    # final_img = image.copy()
    
    # # Рисуем ребра графа
    # for edge in G.edges():
    #     node1_pos = G.nodes[edge[0]]['pos']
    #     node2_pos = G.nodes[edge[1]]['pos']
    #     cv2.line(final_img, node1_pos, node2_pos, (0, 255, 0), 2)
    
    # # Рисуем узлы графа
    # for node, data in G.nodes(data=True):
    #     pos = data['pos']
    #     if data['type'] == 'door':
    #         cv2.circle(final_img, pos, 6, (0, 0, 255), -1)  # Красные - двери
    #     elif data['type'] == 'path_point':
    #         cv2.circle(final_img, pos, 3, (255, 255, 0), -1)  # Голубые - точки пути
    #     elif data['type'] == 'skeleton_point':
    #         cv2.circle(final_img, pos, 4, (255, 0, 0), -1)  # Синие - точки скелета
    
    # axes[1,2].imshow(cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB))
    # axes[1,2].set_title('Строго манхэттеновский граф')
    
    plt.tight_layout()
    plt.show()

# Использование
if __name__ == "__main__":
    image_path = "preprocessed_plan5.png"
    G, doors, skeleton, green_mask, red_mask = process_floor_plan(image_path)

    angles = find_angles_contour(skeleton=skeleton)
    # with open('result_angles.txt', 'w') as f:
    #     f.write(str(list(map(str,angles))))
    
    # Загружаем изображение для визуализации
    image = cv2.imread(image_path)
    visualize_results(image, G, doors, skeleton, green_mask, red_mask, angles[0])
    cv2.imwrite('greenmask_result.png', green_mask)
    
    # Выводим информацию о графе
    print(f"Всего дверей: {len(doors)}")
    print(f"Всего вершин в графе: {G.number_of_nodes()}")
    print(f"Всего ребер в графе: {G.number_of_edges()}")
    
    # Сохраняем граф для дальнейшего использования
    # nx.write_gml(G, "floor_plan_graph.gml")