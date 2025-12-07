import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.morphology import thin
from scipy.spatial import KDTree
from scipy import ndimage


def find_skeleton_corners(image_path):
    """
    Находит углы в скелете коридора и визуализирует их
    """
    # Загружаем изображение
    image = cv2.imread(image_path)

    # 1. Выделяем зеленую область (коридор)
    green_mask = extract_green_area(image)

    # 2. Строим скелет коридора
    skeleton = create_skeleton_with_thin(green_mask)

    # 3. Находим углы в скелете
    corner_points = find_corners_in_skeleton(skeleton)

    # 4. Визуализируем результат
    visualize_skeleton_corners(image, skeleton, corner_points, green_mask)

    return corner_points, skeleton, green_mask


def extract_green_area(image):
    """Выделяем зеленую область (коридор)"""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Диапазон зеленого цвета в HSV
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])

    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    # Морфологические операции для очистки маски
    kernel = np.ones((3, 3), np.uint8)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)

    return green_mask


def create_skeleton_with_thin(green_mask):
    """Создаем скелет коридора с помощью thin"""
    # Убедимся, что маска бинарная
    _, binary = cv2.threshold(green_mask, 1, 255, cv2.THRESH_BINARY)

    # Используем thin для получения скелета
    skeleton = thin(binary // 255)
    skeleton = (skeleton * 255).astype(np.uint8)

    return skeleton


def find_corners_in_skeleton(skeleton, min_angle_change=30, window_size=5):
    """
    Находит углы в скелете, анализируя изменения направления

    Args:
        skeleton: бинарное изображение скелета
        min_angle_change: минимальное изменение угла для определения угла (градусы)
        window_size: размер окна для анализа направления
    """
    # Находим все точки скелета
    points = np.column_stack(np.where(skeleton > 0))
    if len(points) == 0:
        return []

    # Преобразуем в формат (x, y)
    points = [(p[1], p[0]) for p in points]

    # Строим граф скелета для анализа связности
    skeleton_graph = build_skeleton_graph(skeleton)

    # Находим ключевые точки (концевые и точки ветвления)
    endpoints, branch_points = find_key_skeleton_points(skeleton)

    # Анализируем изменение направления в каждой точке
    corner_points = []

    for point in points:
        x, y = point

        # Пропускаем концевые точки
        if (x, y) in endpoints:
            continue

        # Анализируем изменение направления в точке
        if is_corner_point(skeleton_graph, (x, y), min_angle_change, window_size):
            corner_points.append((x, y))

    # Добавляем точки ветвления как углы
    corner_points.extend(branch_points)

    # Фильтруем близко расположенные точки
    corner_points = filter_close_points(corner_points, min_distance=10)

    return corner_points


def build_skeleton_graph(skeleton):
    """Строит граф представления скелета"""
    # Находим все точки скелета
    points = np.column_stack(np.where(skeleton > 0))
    points = [(p[1], p[0]) for p in points]  # преобразуем в (x, y)

    # Создаем граф
    G = {}

    # Для каждой точки находим соседей
    for point in points:
        x, y = point
        neighbors = []

        # Проверяем 8-связных соседей
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                neighbor = (x + dx, y + dy)
                if neighbor in points:
                    neighbors.append(neighbor)

        G[point] = neighbors

    return G


def find_key_skeleton_points(skeleton):
    """Находит концевые точки и точки ветвления скелета"""
    endpoints = []
    branch_points = []

    # Находим все точки скелета
    points = np.column_stack(np.where(skeleton > 0))
    points = [(p[1], p[0]) for p in points]

    for point in points:
        x, y = point

        # Считаем количество соседей
        neighbors = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                if (x + dx, y + dy) in points:
                    neighbors += 1

        # Концевые точки имеют 1 соседа
        if neighbors == 1:
            endpoints.append((x, y))
        # Точки ветвления имеют 3+ соседей
        elif neighbors >= 3:
            branch_points.append((x, y))

    return endpoints, branch_points


def is_corner_point(graph, point, min_angle_change, window_size):
    """
    Определяет, является ли точка углом, анализируя изменение направления
    """
    if point not in graph or len(graph[point]) < 2:
        return False

    # Получаем направления ветвей, исходящих из точки
    directions = []

    for neighbor in graph[point]:
        # Вычисляем направление от точки к соседу
        dx = neighbor[0] - point[0]
        dy = neighbor[1] - point[1]

        # Вычисляем угол направления
        angle = np.degrees(np.arctan2(dy, dx)) % 180
        directions.append(angle)

    # Если есть только два направления, проверяем угол между ними
    if len(directions) == 2:
        angle_diff = min(
            abs(directions[0] - directions[1]), 180 - abs(directions[0] - directions[1])
        )

        # Если угол между направлениями достаточно большой, это угол
        if angle_diff >= min_angle_change:
            return True

    # Для точек с более чем двумя соседями всегда считаем углом
    elif len(directions) > 2:
        return True

    return False


# def find_corners_using_harris(skeleton):
#     """Находит углы в скелете с помощью детектора Харриса"""
#     # Преобразуем скелет в градации серого для детектора Харриса
#     skeleton_gray = skeleton.astype(np.float32)

#     # Применяем детектор углов Харриса
#     harris_response = cv2.cornerHarris(skeleton_gray, blockSize=2, ksize=3, k=0.04)

#     # Нормализуем и применяем порог
#     harris_response = cv2.dilate(harris_response, None)
#     threshold = 0.01 * harris_response.max()

#     # Находим координаты углов
#     corner_coords = np.where(harris_response > threshold)
#     corners = list(zip(corner_coords[1], corner_coords[0]))  # (x, y)

#     return corners


def find_corners_using_shi_tomasi(skeleton, max_corners=50):
    """Находит углы в скелете с помощью Shi-Tomasi"""
    # Применяем детектор углов Shi-Tomasi
    corners = cv2.goodFeaturesToTrack(
        skeleton.astype(np.uint8),
        maxCorners=max_corners,
        qualityLevel=0.05,
        minDistance=15,
    )

    if corners is None:
        return []

    # Преобразуем в формат (x, y)
    corners = [tuple(map(int, corner[0])) for corner in corners]

    return corners


def filter_close_points(points, min_distance=10):
    """Фильтрует близко расположенные точки"""
    if len(points) <= 1:
        return points

    points_array = np.array(points)
    kdtree = KDTree(points_array)

    # Находим пары точек, которые слишком близко
    pairs = kdtree.query_pairs(min_distance)

    # Собираем точки для удаления
    to_remove = set()
    for i, j in pairs:
        # Оставляем точку с меньшим индексом, удаляем другую
        to_remove.add(max(i, j))

    # Фильтруем точки
    filtered_points = [points[i] for i in range(len(points)) if i not in to_remove]

    return filtered_points


def visualize_skeleton_corners(image, skeleton, corner_points, green_mask):
    """Визуализирует скелет и найденные углы"""
    # Создаем цветное изображение для визуализации
    skeleton_color = cv2.cvtColor(skeleton, cv2.COLOR_GRAY2BGR)
    result_img = image.copy()

    # Создаем фигуру для отображения
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # 1. Исходное изображение
    axes[0, 0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    axes[0, 0].set_title("Исходное изображение")
    axes[0, 0].axis("off")

    # 2. Маска коридора
    axes[0, 1].imshow(green_mask, cmap="Greens")
    axes[0, 1].set_title("Маска коридора")
    axes[0, 1].axis("off")

    # 3. Скелет коридора
    axes[0, 2].imshow(skeleton, cmap="gray")
    axes[0, 2].set_title("Скелет коридора")
    axes[0, 2].axis("off")

    # 4. Скелет с углами (простой вариант)
    skeleton_with_corners = skeleton_color.copy()
    for x, y in corner_points:
        cv2.circle(skeleton_with_corners, (x, y), 5, (0, 0, 255), -1)  # Красные точки

    axes[1, 0].imshow(cv2.cvtColor(skeleton_with_corners, cv2.COLOR_BGR2RGB))
    axes[1, 0].set_title(f"Скелет с углами ({len(corner_points)} точек)")
    axes[1, 0].axis("off")

    # 5. Исходное изображение со скелетом и углами
    result_with_skeleton = image.copy()

    # Рисуем скелет поверх изображения (зеленым)
    skeleton_points = np.where(skeleton > 0)
    for y, x in zip(skeleton_points[0], skeleton_points[1]):
        cv2.circle(result_with_skeleton, (x, y), 1, (0, 255, 255), -1)

    # Рисуем углы (красным)
    for x, y in corner_points:
        cv2.circle(result_with_skeleton, (x, y), 6, (0, 0, 255), -1)
        cv2.circle(result_with_skeleton, (x, y), 8, (255, 255, 255), 2)  # Белая обводка

    axes[1, 1].imshow(cv2.cvtColor(result_with_skeleton, cv2.COLOR_BGR2RGB))
    axes[1, 1].set_title("Исходное + скелет + углы")
    axes[1, 1].axis("off")

    # 6. Детальная визуализация углов
    detailed_img = image.copy()

    # Рисуем скелет тонкими линиями
    skeleton_points = np.where(skeleton > 0)
    for y, x in zip(skeleton_points[0], skeleton_points[1]):
        cv2.circle(detailed_img, (x, y), 1, (0, 255, 0), -1)

    # Рисуем углы с номерами
    for i, (x, y) in enumerate(corner_points):
        cv2.circle(detailed_img, (x, y), 8, (0, 0, 255), -1)
        cv2.circle(detailed_img, (x, y), 10, (255, 255, 255), 2)
        cv2.putText(
            detailed_img,
            str(i),
            (x + 12, y + 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            2,
        )

    axes[1, 2].imshow(cv2.cvtColor(detailed_img, cv2.COLOR_BGR2RGB))
    axes[1, 2].set_title("Детальная визуализация углов")
    axes[1, 2].axis("off")

    plt.tight_layout()
    plt.show()

    return result_with_skeleton


def compare_corner_detection_methods(skeleton):
    """Сравнивает разные методы обнаружения углов в скелете"""
    # Метод 1: Анализ изменения направления
    method1_corners = find_corners_in_skeleton(skeleton)

    # Метод 2: Детектор Харриса
    # method2_corners = find_corners_using_harris(skeleton)
    method2_corners = None

    # # Метод 3: Shi-Tomasi
    method3_corners = find_corners_using_shi_tomasi(skeleton)
    # method3_corners = None

    print("=== СРАВНЕНИЕ МЕТОДОВ ОБНАРУЖЕНИЯ УГЛОВ ===")
    print(f"Метод 1 (анализ направления): {len(method1_corners)} углов")
    print(f"Метод 2 (Харрис): {method2_corners} углов")
    print(f"Метод 3 (Shi-Tomasi): {method3_corners} углов")

    # Объединяем все углы (убирая дубликаты)
    all_corners = method1_corners + method3_corners
    unique_corners = filter_close_points(all_corners, min_distance=5)

    print(f"Объединенный результат: {len(unique_corners)} уникальных углов")

    return unique_corners


# Основная функция для использования
def analyze_skeleton_corners(image_path, use_combined_method=True):
    """
    Анализирует углы в скелете коридора

    Args:
        image_path: путь к изображению
        use_combined_method: использовать комбинированный метод
    """
    print("=== АНАЛИЗ УГЛОВ В СКЕЛЕТЕ КОРИДОРА ===")

    # Загружаем изображение и строим скелет
    image = cv2.imread(image_path)
    green_mask = extract_green_area(image)
    skeleton = create_skeleton_with_thin(green_mask)

    # Находим углы
    if use_combined_method:
        corner_points = compare_corner_detection_methods(skeleton)
    else:
        corner_points = find_corners_in_skeleton(skeleton)

    # Визуализируем результат
    result_img = visualize_skeleton_corners(image, skeleton, corner_points, green_mask)

    # Выводим информацию об углах
    print(f"\nНайдено углов в скелете: {len(corner_points)}")
    print("\nКоординаты угловых точек:")
    for i, (x, y) in enumerate(corner_points):
        print(f"  Угол {i}: ({x}, {y})")

    # Анализируем распределение углов
    if corner_points:
        points_array = np.array(corner_points)
        print(f"\nСтатистика углов:")
        print(
            f"  Область: X [{np.min(points_array[:, 0])}-{np.max(points_array[:, 0])}], "
            f"Y [{np.min(points_array[:, 1])}-{np.max(points_array[:, 1])}]"
        )
        print(
            f"  Центр масс: ({np.mean(points_array[:, 0]):.1f}, {np.mean(points_array[:, 1]):.1f})"
        )

    return {
        "corner_points": corner_points,
        "skeleton": skeleton,
        "green_mask": green_mask,
        "visualization": result_img,
    }


# Пример использования
if __name__ == "__main__":
    image_path = "preprocessed_plan5.png"

    try:
        # Анализируем углы в скелете
        results = analyze_skeleton_corners(image_path, use_combined_method=True)

        # Сохраняем результаты
        np.save("skeleton_corners.npy", np.array(results["corner_points"]))
        cv2.imwrite("skeleton_with_corners.png", results["visualization"])

        print("\nРезультаты сохранены в файлы:")
        print("  - skeleton_corners.npy (координаты углов)")
        print("  - skeleton_with_corners.png (визуализация)")

    except Exception as e:
        print(f"Ошибка при обработке изображения: {e}")
