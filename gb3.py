import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize, medial_axis
import networkx as nx
from scipy import ndimage

def process_floor_plan(image_path):
    # Загружаем изображение
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 1. Сначала находим и маскируем номера аудиторий
    # Номера обычно имеют специфический размер и форму
    binary_without_text = remove_text_regions(gray)
    
    # 2. Теперь работаем с очищенным изображением
    _, binary = cv2.threshold(binary_without_text, 128, 255, cv2.THRESH_BINARY_INV)
    
    # 3. Находим комнаты (прямоугольные контуры)
    rooms, room_centers = find_rooms(binary)
    
    # 4. Создаем маску коридоров (убираем комнаты)
    corridor_mask = create_corridor_mask(binary, rooms)
    
    # 5. Скелетонизация коридоров
    skeleton = skeletonize_corridors(corridor_mask)
    
    # 6. Находим точки дверей
    door_points = find_door_points(binary, rooms, door_length=19)
    
    # 7. Находим узлы скелета
    skeleton_nodes = find_skeleton_nodes(skeleton)
    
    # 8. Строим граф
    G = build_graph(room_centers, skeleton_nodes, door_points, skeleton)
    
    return G, room_centers, skeleton_nodes, door_points, binary, skeleton, corridor_mask

def remove_text_regions(gray):
    """Удаляем области с текстом (номерами аудиторий)"""
    # Бинаризуем для поиска темных областей (текст)
    _, binary_dark = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    
    # Морфологические операции для объединения текста
    kernel = np.ones((2,2), np.uint8)
    text_mask = cv2.morphologyEx(binary_dark, cv2.MORPH_CLOSE, kernel)
    
    # Находим контуры текста
    contours, _ = cv2.findContours(text_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Создаем маску для закрашивания текста
    result = gray.copy()
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Фильтруем по размеру (номера аудиторий обычно небольшие)
        if 20 < w < 100 and 10 < h < 50:
            # Закрашиваем текст фоном
            cv2.rectangle(result, (x, y), (x+w, y+h), 255, -1)
    
    return result

def find_rooms(binary):
    """Находим комнаты как прямоугольные контуры"""
    # Морфологические операции для закрытия дверей
    kernel = np.ones((5,5), np.uint8)
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # Находим контуры
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    rooms = []
    room_centers = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # Фильтруем по площади
        if area > 1000:
            # Аппроксимируем контур
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            
            # Проверяем, что это прямоугольник (4 угла)
            if len(approx) >= 4:
                rooms.append(approx)
                
                # Находим центр комнаты
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    room_centers.append((cx, cy))
    
    return rooms, room_centers

def create_corridor_mask(binary, rooms):
    """Создаем маску коридоров (убираем комнаты)"""
    # Создаем маску, где закрашены все комнаты
    room_mask = np.zeros_like(binary)
    cv2.drawContours(room_mask, rooms, -1, 255, -1)
    
    # Коридоры = все изображение минус комнаты
    corridor_mask = binary.copy()
    corridor_mask[room_mask == 255] = 0
    
    # Очищаем маску от мелких объектов
    kernel = np.ones((3,3), np.uint8)
    corridor_mask = cv2.morphologyEx(corridor_mask, cv2.MORPH_OPEN, kernel)
    
    return corridor_mask

def skeletonize_corridors(corridor_mask):
    """Скелетонизация коридоров"""
    # Убедимся, что изображение бинарное
    _, binary_corridor = cv2.threshold(corridor_mask, 1, 255, cv2.THRESH_BINARY)
    
    # Используем медиальную ось для лучшей скелетонизации
    skeleton, distance = medial_axis(binary_corridor // 255, return_distance=True)
    skeleton = (skeleton * 255).astype(np.uint8)
    
    return skeleton

def find_door_points(binary, rooms, door_length=19):
    """Находим точки дверей (разрывы в контурах комнат)"""
    door_points = []
    
    for room in rooms:
        # Создаем маску для текущей комнаты
        room_mask = np.zeros_like(binary)
        cv2.drawContours(room_mask, [room], 0, 255, -1)
        
        # Находим границы комнаты
        room_boundary = cv2.Canny(room_mask, 50, 150)
        
        # Используем преобразование Хафа для поиска линий
        lines = cv2.HoughLinesP(room_boundary, 1, np.pi/180, 
                               threshold=20, 
                               minLineLength=door_length-2, 
                               maxLineGap=door_length+2)
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                # Проверяем длину разрыва (двери)
                if door_length-5 <= length <= door_length+5:
                    # Средняя точка разрыва
                    door_x = (x1 + x2) // 2
                    door_y = (y1 + y2) // 2
                    door_points.append((door_x, door_y))
    
    return door_points

def find_skeleton_nodes(skeleton):
    """Находит узлы скелета (концевые точки и точки ветвления)"""
    nodes = []
    
    # Используем более точный метод для поиска узлов
    for y in range(1, skeleton.shape[0]-1):
        for x in range(1, skeleton.shape[1]-1):
            if skeleton[y, x] > 0:
                # Анализируем 8-связное окружение
                neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        if skeleton[y+dy, x+dx] > 0:
                            neighbors += 1
                
                # Концевые точки (1 сосед)
                if neighbors == 1:
                    nodes.append((x, y))
                # Точки ветвления (3+ соседей)
                elif neighbors >= 3:
                    nodes.append((x, y))
    
    return nodes

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
    
    # Соединяем комнаты с ближайшими дверями
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
            
            if nearest_door and min_dist < 200:
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
        
        if nearest_corner and min_dist < 100:
            G.add_edge(door_node, nearest_corner, weight=min_dist)
    
    # Соединяем узлы коридора между собой на основе скелета
    skeleton_points = np.column_stack(np.where(skeleton > 0))
    for i, node1 in enumerate(skeleton_nodes):
        for j, node2 in enumerate(skeleton_nodes):
            if i != j:
                # Проверяем расстояние
                dist = np.sqrt((node1[0]-node2[0])**2 + (node1[1]-node2[1])**2)
                if dist < 50:  # Максимальное расстояние для соединения
                    # Проверяем, есть ли путь по скелету
                    if is_connected_through_skeleton(node1, node2, skeleton_points, max_gap=10):
                        G.add_edge(f"corner_{i}", f"corner_{j}", weight=dist)
    
    return G

def is_connected_through_skeleton(point1, point2, skeleton_points, max_gap=10):
    """Проверяет, связаны ли две точки через скелет"""
    x1, y1 = point1
    x2, y2 = point2
    
    # Создаем линию между точками
    line_points = []
    steps = max(abs(x2-x1), abs(y2-y1))
    if steps > 0:
        for t in np.linspace(0, 1, steps):
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))
            line_points.append((x, y))
    
    # Проверяем, есть ли точки скелета рядом с линией
    connected = False
    for line_point in line_points:
        for skeleton_point in skeleton_points:
            sx, sy = skeleton_point[1], skeleton_point[0]  # меняем местами, т.к. np.where возвращает (y,x)
            dist = np.sqrt((line_point[0]-sx)**2 + (line_point[1]-sy)**2)
            if dist <= max_gap:
                connected = True
                break
        if connected:
            break
    
    return connected

def visualize_results(image, G, room_centers, skeleton_nodes, door_points, binary, skeleton, corridor_mask):
    """Визуализация результатов"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Исходное изображение
    axes[0,0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    axes[0,0].set_title('Исходное изображение')
    
    # Бинаризованное изображение
    axes[0,1].imshow(binary, cmap='gray')
    axes[0,1].set_title('Бинаризованное изображение')
    
    # Маска коридоров
    axes[0,2].imshow(corridor_mask, cmap='gray')
    axes[0,2].set_title('Маска коридоров')
    
    # Скелет коридоров
    axes[1,0].imshow(skeleton, cmap='gray')
    axes[1,0].set_title('Скелет коридоров')
    
    # Визуализация всех точек
    result_img = image.copy()
    
    # Рисуем центры комнат
    for center in room_centers:
        cv2.circle(result_img, center, 8, (0, 0, 255), -1)  # Красные - комнаты
    
    # Рисуем узлы скелета
    for node in skeleton_nodes:
        cv2.circle(result_img, node, 5, (255, 0, 0), -1)  # Синие - углы коридоров
    
    # Рисуем двери
    for door in door_points:
        cv2.circle(result_img, door, 5, (0, 255, 0), -1)  # Зеленые - двери
    
    axes[1,1].imshow(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
    axes[1,1].set_title('Все обнаруженные точки')
    
    # Финальный граф
    final_img = image.copy()
    
    # Рисуем ребра
    for edge in G.edges():
        node1_pos = G.nodes[edge[0]]['pos']
        node2_pos = G.nodes[edge[1]]['pos']
        cv2.line(final_img, node1_pos, node2_pos, (0, 255, 0), 2)
    
    # Рисуем узлы
    for node, data in G.nodes(data=True):
        pos = data['pos']
        color = (0, 0, 255) if data['type'] == 'room' else (0, 255, 0) if data['type'] == 'door' else (255, 0, 0)
        cv2.circle(final_img, pos, 6, color, -1)
    
    axes[1,2].imshow(cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB))
    axes[1,2].set_title('Финальный граф')
    
    plt.tight_layout()
    plt.show()

# Использование
if __name__ == "__main__":
    image_path = "plan5.png"
    G, rooms, corners, doors, binary, skeleton, corridor_mask = process_floor_plan(image_path)
    
    # Загружаем изображение для визуализации
    image = cv2.imread(image_path)
    visualize_results(image, G, rooms, corners, doors, binary, skeleton, corridor_mask)
    
    # Выводим информацию о графе
    print(f"Всего комнат: {len(rooms)}")
    print(f"Всего узлов коридора: {len(corners)}")
    print(f"Всего дверей: {len(doors)}")
    print(f"Всего вершин в графе: {G.number_of_nodes()}")
    print(f"Всего ребер в графе: {G.number_of_edges()}")
    
    # Сохраняем граф для дальнейшего использования
    nx.write_gml(G, "floor_plan_graph.gml")