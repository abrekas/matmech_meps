import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize
import networkx as nx
from scipy import ndimage

def process_floor_plan(image_path):
    # Загружаем изображение
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Бинаризация - настраиваем под ваш план
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
    
    # Инвертируем, чтобы стены были белыми на черном фоне
    binary = 255 - binary
    
    # Находим контуры (включая разорванные)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    # Фильтруем контуры по площади для нахождения комнат
    min_room_area = 1000
    rooms = []
    room_contours = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_room_area:
            # Аппроксимируем контур до прямоугольника
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            
            if len(approx) == 4:  # Прямоугольные комнаты
                rooms.append(approx)
                room_contours.append(cnt)
    
    # Находим центры комнат
    room_centers = []
    for room in rooms:
        M = cv2.moments(room)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            room_centers.append((cx, cy))
    
    # Создаем маску коридоров (убираем комнаты)
    corridor_mask = binary.copy()
    cv2.drawContours(corridor_mask, room_contours, -1, 0, -1)
    
    # Убираем номера аудиторий (маленькие изолированные области)
    kernel = np.ones((3,3), np.uint8)
    corridor_clean = cv2.morphologyEx(corridor_mask, cv2.MORPH_OPEN, kernel)
    
    # Скелетонизация коридоров
    skeleton = skeletonize(corridor_clean // 255)
    skeleton = (skeleton * 255).astype(np.uint8)
    
    # Находим узлы скелета (перекрестки и концевые точки)
    skeleton_nodes = find_skeleton_nodes(skeleton)
    
    # Находим точки дверей (разрывы в контурах комнат)
    door_points = find_door_points(binary, room_contours, door_length=19)
    
    # Строим граф
    G = build_graph(room_centers, skeleton_nodes, door_points, skeleton)
    
    return G, room_centers, skeleton_nodes, door_points, binary, skeleton

def find_skeleton_nodes(skeleton):
    """Находит узлы скелета (концевые точки и точки ветвления)"""
    nodes = []
    
    # Структурные элементы для анализа соседей
    endpoints_kernel = np.array([[1, 1, 1],
                                 [1, 10, 1],
                                 [1, 1, 1]])
    
    # Находим концевые точки и точки ветвления
    for y in range(1, skeleton.shape[0]-1):
        for x in range(1, skeleton.shape[1]-1):
            if skeleton[y, x] == 255:
                # Количество соседей
                neighborhood = skeleton[y-1:y+2, x-1:x+2]
                neighbors = np.sum(neighborhood == 255) - 1
                
                # Концевые точки (1 сосед)
                if neighbors == 1:
                    nodes.append((x, y))
                # Точки ветвления (3+ соседей)
                elif neighbors >= 3:
                    nodes.append((x, y))
    
    return nodes

def find_door_points(binary, room_contours, door_length=19):
    """Находит точки дверей (разрывы в контурах комнат)"""
    door_points = []
    
    for contour in room_contours:
        # Создаем маску для текущей комнаты
        room_mask = np.zeros_like(binary)
        cv2.drawContours(room_mask, [contour], 0, 255, -1)
        
        # Находим границы комнаты
        room_boundary = cv2.Canny(room_mask, 50, 150)
        
        # Находим разрывы в границе
        lines = cv2.HoughLinesP(room_boundary, 1, np.pi/180, 
                               threshold=door_length-5, 
                               minLineLength=door_length-3, 
                               maxLineGap=door_length+3)
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                # Проверяем длину разрыва
                if abs(length - door_length) < 5:
                    # Средняя точка разрыва
                    door_x = (x1 + x2) // 2
                    door_y = (y1 + y2) // 2
                    door_points.append((door_x, door_y))
    
    return door_points

def build_graph(room_centers, skeleton_nodes, door_points, skeleton):
    """Строит граф связей"""
    G = nx.Graph()
    
    # Добавляем вершины
    for i, center in enumerate(room_centers):
        G.add_node(f"room_{i}", pos=center, type='room')
    
    for i, node in enumerate(skeleton_nodes):
        G.add_node(f"corner_{i}", pos=node, type='corner')
    
    for i, door in enumerate(door_points):
        G.add_node(f"door_{i}", pos=door, type='door')
    
    # Соединяем комнаты с дверями
    for i, room_center in enumerate(room_centers):
        room_node = f"room_{i}"
        
        # Находим ближайшую дверь к комнате
        if door_points:
            min_dist = float('inf')
            nearest_door = None
            
            for j, door_point in enumerate(door_points):
                dist = np.sqrt((room_center[0]-door_point[0])**2 + 
                              (room_center[1]-door_point[1])**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest_door = f"door_{j}"
            
            if nearest_door and min_dist < 200:  # Максимальное расстояние
                G.add_edge(room_node, nearest_door, weight=min_dist)
    
    # Соединяем двери с узлами коридора
    for i, door_point in enumerate(door_points):
        door_node = f"door_{i}"
        
        # Находим ближайший узел скелета
        min_dist = float('inf')
        nearest_corner = None
        
        for j, corner_point in enumerate(skeleton_nodes):
            dist = np.sqrt((door_point[0]-corner_point[0])**2 + 
                          (door_point[1]-corner_point[1])**2)
            if dist < min_dist:
                min_dist = dist
                nearest_corner = f"corner_{j}"
        
        if nearest_corner and min_dist < 100:  # Максимальное расстояние
            G.add_edge(door_node, nearest_corner, weight=min_dist)
    
    # Соединяем узлы коридора между собой на основе скелета
    for i in range(len(skeleton_nodes)):
        for j in range(i+1, len(skeleton_nodes)):
            node1 = skeleton_nodes[i]
            node2 = skeleton_nodes[j]
            
            # Проверяем, связаны ли точки через скелет
            if are_connected_in_skeleton(node1, node2, skeleton, max_distance=50):
                dist = np.sqrt((node1[0]-node2[0])**2 + (node1[1]-node2[1])**2)
                G.add_edge(f"corner_{i}", f"corner_{j}", weight=dist)
    
    return G

def are_connected_in_skeleton(point1, point2, skeleton, max_distance=50):
    """Проверяет, связаны ли две точки через скелет"""
    x1, y1 = point1
    x2, y2 = point2
    
    # Проверяем расстояние
    distance = np.sqrt((x2-x1)**2 + (y2-y1)**2)
    if distance > max_distance:
        return False
    
    # Создаем линию между точками
    line_mask = np.zeros_like(skeleton)
    cv2.line(line_mask, (x1, y1), (x2, y2), 255, 1)
    
    # Проверяем пересечение со скелетом
    intersection = cv2.bitwise_and(line_mask, skeleton)
    
    return np.sum(intersection) > 0

def visualize_results(image, G, room_centers, skeleton_nodes, door_points, binary, skeleton):
    """Визуализация результатов"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Исходное изображение с графом
    axes[0,0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    axes[0,0].set_title('Граф на исходном плане')
    
    # Бинаризованное изображение
    axes[0,1].imshow(binary, cmap='gray')
    axes[0,1].set_title('Бинаризованное изображение')
    
    # Скелет коридоров
    axes[1,0].imshow(skeleton, cmap='gray')
    axes[1,0].set_title('Скелет коридоров')
    
    # Визуализация графа
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    
    # Рисуем граф на отдельном изображении
    result_img = image.copy()
    for edge in G.edges():
        node1_pos = G.nodes[edge[0]]['pos']
        node2_pos = G.nodes[edge[1]]['pos']
        cv2.line(result_img, node1_pos, node2_pos, (0, 255, 0), 2)
    
    # Рисуем узлы
    for node, data in G.nodes(data=True):
        pos = data['pos']
        color = (255, 0, 0) if data['type'] == 'room' else (0, 0, 255) if data['type'] == 'door' else (255, 255, 0)
        cv2.circle(result_img, pos, 5, color, -1)
    
    axes[1,1].imshow(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
    axes[1,1].set_title('Финальный граф')
    
    plt.tight_layout()
    plt.show()

# Использование
if __name__ == "__main__":
    image_path = "plan5.bmp"  # или floor_plan.bmp
    G, rooms, corners, doors, binary, skeleton = process_floor_plan(image_path)
    
    # Загружаем изображение для визуализации
    image = cv2.imread(image_path)
    visualize_results(image, G, rooms, corners, doors, binary, skeleton)
    
    # Выводим информацию о графе
    print(f"Всего комнат: {len(rooms)}")
    print(f"Всего узлов коридора: {len(corners)}")
    print(f"Всего дверей: {len(doors)}")
    print(f"Всего вершин в графе: {G.number_of_nodes()}")
    print(f"Всего ребер в графе: {G.number_of_edges()}")