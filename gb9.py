import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import KDTree
from skimage.morphology import thin

def find_corner_points(image_path):
    """
    Находит угловые точки коридорной области
    Возвращает список точек в формате [(x1,y1), (x2,y2), ...]
    """
    # Загружаем изображение
    image = cv2.imread(image_path)
    
    # 1. Выделяем зеленую область (коридор)
    green_mask = extract_green_area(image)
    
    # 2. Находим контур коридора
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return []
    
    # Берем самый большой контур
    main_contour = max(contours, key=cv2.contourArea)
    
    # 3. Находим угловые точки несколькими методами
    corner_points = []
    
    # # Метод 1: Аппроксимация контура
    # approx_corners = find_contour_corners(main_contour)
    # corner_points.extend(approx_corners)
    
    # Метод 2: Детектор углов Harris
    harris_corners = find_harris_corners(green_mask)
    corner_points.extend(harris_corners)
    
    # Метод 3: Углы минимального ограничивающего прямоугольника
    bounding_corners = find_bounding_rect_corners(main_contour)
    corner_points.extend(bounding_corners)
    
    # 4. Фильтруем и объединяем близкие точки
    filtered_corners = filter_close_points(corner_points, min_distance=5)
    
    return filtered_corners, green_mask, main_contour

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

def find_contour_corners(contour, epsilon_factor=0.02):
    """Находит углы контура с помощью аппроксимации"""
    # Аппроксимируем контур
    epsilon = epsilon_factor * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    
    # Преобразуем в список точек
    corners = [tuple(point[0]) for point in approx]
    
    return corners

def find_harris_corners(mask, quality_level=0.01, min_distance=10):
    """Находит углы с помощью детектора Харриса"""
    # Преобразуем маску в градации серого
    gray = mask.astype(np.float32)
    
    # Применяем детектор углов Harris
    corners = cv2.cornerHarris(gray, blockSize=2, ksize=3, k=0.04)
    
    # Нормализуем и threshold
    corners = cv2.dilate(corners, None)
    threshold = quality_level * corners.max()
    corner_positions = np.where(corners > threshold)
    
    # Собираем точки
    harris_points = []
    for y, x in zip(corner_positions[0], corner_positions[1]):
        harris_points.append((x, y))
    
    return harris_points

def find_bounding_rect_corners(contour):
    """Находит углы ограничивающих прямоугольников"""
    corners = []
    
    # Минимальный ограничивающий прямоугольник
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    corners.extend([tuple(map(int, point)) for point in box])
    
    # Ограничивающий прямоугольник (axis-aligned)
    x, y, w, h = cv2.boundingRect(contour)
    bbox_corners = [
        (x, y), (x + w, y), 
        (x + w, y + h), (x, y + h)
    ]
    corners.extend(bbox_corners)
    
    return corners

def find_convex_hull_corners(contour):
    """Находит углы выпуклой оболочки"""
    hull = cv2.convexHull(contour)
    corners = [tuple(point[0]) for point in hull]
    return corners

def filter_close_points(points, min_distance=10):
    """Фильтрует близко расположенные точки"""
    if not points:
        return []
    
    # Создаем KD-дерево для быстрого поиска соседей
    points_array = np.array(points)
    kdtree = KDTree(points_array)
    
    # Находим пары точек, которые слишком близко
    pairs = kdtree.query_pairs(min_distance)
    
    # Собираем точки для удаления
    to_remove = set()
    for i, j in pairs:
        # Оставляем точку с меньшим индексом, удаляем другую
        to_remove.add(j)
    
    # Фильтруем точки
    filtered_points = [points[i] for i in range(len(points)) if i not in to_remove]
    
    return filtered_points

def find_corridor_junctions(green_mask):
    """Находит точки пересечения/разветвления в коридоре"""
    # Скелетонизируем коридор
    _, binary = cv2.threshold(green_mask, 1, 255, cv2.THRESH_BINARY)
    skeleton = thin(binary // 255)
    skeleton = (skeleton * 255).astype(np.uint8)
    
    # Находим точки разветвления скелета
    junction_points = []
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
                
                # Точки разветвления имеют 3+ соседей
                if neighbors >= 3:
                    junction_points.append((x, y))
    
    return junction_points

def visualize_corner_points(image, corner_points, green_mask, contour, junction_points=None):
    """Визуализирует найденные угловые точки"""
    # Создаем изображение для визуализации
    result_img = image.copy()
    
    # Рисуем контур коридора
    cv2.drawContours(result_img, [contour], -1, (0, 255, 255), 2)
    
    # Рисуем угловые точки
    for i, (x, y) in enumerate(corner_points):
        cv2.circle(result_img, (x, y), 2, (0, 0, 255), -1)  # Красные точки
        cv2.putText(result_img, str(i), (x+10, y+10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Рисуем точки разветвления (если есть)
    if junction_points:
        for x, y in junction_points:
            cv2.circle(result_img, (x, y), 6, (128, 0, 128), -1)  # Синие точки
    
    # Создаем фигуру для отображения
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Исходное изображение с разметкой
    axes[0].imshow(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
    axes[0].set_title(f'Угловые точки коридора (найдено: {len(corner_points)})')
    axes[0].axis('off')
    
    # Маска коридора
    axes[1].imshow(green_mask, cmap='Greens')
    axes[1].set_title('Маска коридора')
    axes[1].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    return result_img

def get_corridor_geometry_analysis(corner_points, green_mask):
    """Анализирует геометрию коридора на основе угловых точек"""
    if len(corner_points) < 3:
        return {"error": "Недостаточно угловых точек для анализа"}
    
    # Преобразуем точки в массив NumPy
    points = np.array(corner_points)
    
    # Вычисляем основные геометрические характеристики
    analysis = {
        "total_corners": len(corner_points),
        "bounding_box": {
            "min_x": np.min(points[:, 0]),
            "max_x": np.max(points[:, 0]),
            "min_y": np.min(points[:, 1]),
            "max_y": np.max(points[:, 1]),
            "width": np.max(points[:, 0]) - np.min(points[:, 0]),
            "height": np.max(points[:, 1]) - np.min(points[:, 1])
        },
        "area": cv2.contourArea(np.array(corner_points).reshape(-1, 1, 2).astype(np.int32)),
        "center_of_mass": (np.mean(points[:, 0]), np.mean(points[:, 1]))
    }
    
    return analysis

# Основная функция для использования
def analyze_corridor_corners(image_path):
    """
    Основная функция для анализа угловых точек коридора
    """
    # Находим угловые точки
    corner_points, green_mask, contour = find_corner_points(image_path)
    
    # Находим точки разветвления
    junction_points = find_corridor_junctions(green_mask)
    
    # Загружаем исходное изображение
    image = cv2.imread(image_path)
    
    # Визуализируем результаты
    result_img = visualize_corner_points(image, corner_points, green_mask, contour, junction_points)
    
    # Анализируем геометрию
    geometry_analysis = get_corridor_geometry_analysis(corner_points, green_mask)
    
    # Выводим информацию
    print("=== АНАЛИЗ УГЛОВЫХ ТОЧЕК КОРИДОРА ===")
    print(f"Найдено угловых точек: {len(corner_points)}")
    print(f"Найдено точек разветвления: {len(junction_points)}")
    
    if "error" not in geometry_analysis:
        print(f"Геометрический анализ:")
        print(f"  - Ограничивающая рамка: {geometry_analysis['bounding_box']['width']} x {geometry_analysis['bounding_box']['height']}")
        print(f"  - Площадь: {geometry_analysis['area']:.2f}")
        print(f"  - Центр масс: ({geometry_analysis['center_of_mass'][0]:.1f}, {geometry_analysis['center_of_mass'][1]:.1f})")
    
    print("\nКоординаты угловых точек:")
    for i, (x, y) in enumerate(corner_points):
        print(f"  {i}: ({x}, {y})")
    
    return {
        "corner_points": corner_points,
        "junction_points": junction_points,
        "geometry_analysis": geometry_analysis,
        "visualization_image": result_img
    }

# Пример использования
if __name__ == "__main__":
    image_path = "preprocessed_plan5.png"
    
    try:
        results = analyze_corridor_corners(image_path)
        
        # Сохраняем угловые точки в файл
        np.save("corridor_corners.npy", np.array(results["corner_points"]))
        print(f"\nУгловые точки сохранены в файл 'corridor_corners.npy'")
        
    except Exception as e:
        print(f"Ошибка при обработке изображения: {e}")