import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from math import sqrt, isclose
from dataclasses import dataclass
from typing import Dict, Set, Tuple, List, Optional


@dataclass
class RoomInfo:
    number: str
    x: float
    y: float
    node_id: Optional[str] = None


class GraphBuilderSVG:
    def __init__(self, src_file_path: str):
        self.source_file_path = src_file_path
        self.points: Set[Tuple[float, float]] = set()
        self.edges: Set[Tuple[Tuple[float, float], Tuple[float, float]]] = set()
        self.graph: defaultdict[Tuple[float, float], Set[Tuple[float, float]]] = defaultdict(
            set
        )

        self.new_graph: Dict[
            Tuple[float, float], Tuple[Set[Tuple[float, float]], str]
        ] = defaultdict(tuple[set, str])

        # Для хранения информации о кабинетах
        self.rooms: List[RoomInfo] = []
        self.valid_tags = frozenset(["g", "path", "text", "/g"])

        # Параметры для поиска кабинетов
        # self.room_patterns = ['room', 'кабинет', 'office', '№']

        # Максимальное расстояние для связывания комнаты с вершиной
        self.room_link_threshold = 40.0

    def process_svg(self):
        """Парсит SVG файл с использованием ElementTree"""
        # tree = ET.parse(self.source_file_path)
        # root = tree.getroot()

        # Определяем namespace для SVG
        # ns = {'svg': 'http://www.w3.org/2000/svg'}

        self._parse_svg_file()

        # 1. Парсим все path элементы (граф навигации)
        # for path_elem in root.findall('.//svg:path', ns):
        #     path_data = path_elem.get('d', '')
        #     if path_data:
        #         self._parse_path_data(path_data)

        # # 2. Парсим все text элементы (номера кабинетов)
        # for text_elem in root.findall('.//svg:text', ns):
        #     self._parse_text_element(text_elem)

        # 3. Удаляем промежуточные точки на прямых линиях
        # self._simplify_graph()

        # 4. Привязываем кабинеты к ближайшим вершинам
        self._link_rooms_to_graph()

    def _parse_svg_file(self):
        groups_stack = []
        temp_id = ""
        with open(self.source_file_path) as f:
            for s in f:
                tag = re.search(r"(\S+ )|(<\S+>)", s).group()[1:-1]
                if (tag not in self.valid_tags) and (tag[1:] not in self.valid_tags):
                    continue
                if tag == "/g":
                    groups_stack.pop()
                    continue
                id = re.search(r' id=.+?"', s).group()[5:-1]
                if tag == "g":
                    groups_stack.append(id)

                if re.search(r"graph", id):
                    # self.main_string = s
                    # self._parse_meaning_string()
                    self._parse_path_data(s)

                elif groups_stack[-1] == "rooms_numbers" and tag == "text":
                    self._add_room_by_id(s, id)

                elif len(groups_stack) > 2 and groups_stack[-2] == "rooms_numbers":
                    if tag == "g":
                        temp_id = id
                    else:
                        self._add_room_by_id(s, temp_id)

                # вот и все ифы получается
                print("aboba")

    def _add_room_by_id(self, s, id):
        transform_match = re.search(r"transform", s)
        if transform_match:
            pattern1 = re.compile(r"translate\(([\d.]+) ([\d.]+)\)")
            pattern2 = re.compile(
                r"matrix\([-\d.]+ [-\d.]+ [-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)\)"
            )
            # pattern2 = r'matrix\([\d.]+) [\d.]+) [\d.]+) [\d.]+) ([\d.]+) ([\d.]+)\)'
            coord_match1 = re.search(pattern=pattern1, string=s)
            coord_match2 = re.search(pattern=pattern2, string=s)

            if coord_match1:
                x, y = float(coord_match1.group(1)), float(coord_match1.group(2))
            elif coord_match2:
                x, y = float(coord_match2.group(1)), float(coord_match2.group(2))
            else:
                raise RuntimeError("somehow regex didnt work")

        else:
            x = re.search(r' x="([\d.]+)"', s).group(1)
            y = re.search(r' y="([\d.]+)"', s).group(1)


        self.rooms.append(RoomInfo(number=id, x=float(x), y=float(y)))

    def _parse_path_data(self, path_data: str):
        """Парсит данные пути из SVG"""
        path_data = re.search(r' d="(.+)" ', path_data).group(1)
        commands = []
        current_command = None
        current_args = []

        i = 0
        while i < len(path_data):
            char = path_data[i]

            if char.isalpha():
                if current_command is not None:
                    commands.append((current_command, current_args))
                current_command = char
                current_args = []
            elif char in " ,":
                if current_args and current_args[-1] != "":
                    current_args.append("")
            else:
                if not current_args:
                    current_args.append("")
                current_args[-1] += char

            i += 1

        if current_command is not None:
            commands.append((current_command, current_args))

        # Обработка команд
        current_point = (0.0, 0.0)
        start_point = None

        for command, args in commands:
            numeric_args = []
            for arg in args:
                if arg.strip():
                    try:
                        numeric_args.append(float(arg))
                    except ValueError:
                        continue

            if command == "M":  # MoveTo
                for j in range(0, len(numeric_args), 2):
                    if j + 1 < len(numeric_args):
                        x, y = numeric_args[j], numeric_args[j + 1]
                        current_point = (x, y)
                        if start_point is None:
                            start_point = current_point
                        self.points.add(current_point)

            elif command == "L":  # LineTo
                for j in range(0, len(numeric_args), 2):
                    if j + 1 < len(numeric_args):
                        x, y = numeric_args[j], numeric_args[j + 1]
                        new_point = (x, y)
                        self._add_edge(current_point, new_point)
                        current_point = new_point
                        self.points.add(current_point)

            elif command == "H":  # Horizontal Line
                for x in numeric_args:
                    new_point = (x, current_point[1])
                    self._add_edge(current_point, new_point)
                    current_point = new_point
                    self.points.add(current_point)

            elif command == "V":  # Vertical Line
                for y in numeric_args:
                    new_point = (current_point[0], y)
                    self._add_edge(current_point, new_point)
                    current_point = new_point
                    self.points.add(current_point)

            elif command == "Z":  # Close Path
                if start_point is not None:
                    self._add_edge(current_point, start_point)
                    current_point = start_point

    def _add_edge(self, p1: Tuple[float, float], p2: Tuple[float, float]):
        """Добавляет ребро в граф, проверяя коллинеарность"""
        if p1 == p2:
            return

        # Проверяем, нет ли уже более коротких ребер между этими точками
        if not self._is_edge_redundant(p1, p2):
            self.graph[p1].add(p2)
            self.graph[p2].add(p1)
            self.edges.add((p1, p2))

            self.new_graph[p1][0].add(p2)
            self.new_graph[p2][0].add(p1)

    def _is_edge_redundant(
        self, p1: Tuple[float, float], p2: Tuple[float, float]
    ) -> bool:
        """Проверяет, является ли ребро избыточным"""
        # Проверяем, есть ли путь между p1 и p2 через другие точки
        visited = set()
        stack = [p1]

        while stack:
            current = stack.pop()
            if current == p2:
                return True

            visited.add(current)

            for neighbor in self.graph[current]:
                if neighbor not in visited and neighbor != p1 and neighbor != p2:
                    stack.append(neighbor)

        return False

    def _parse_text_element__deprecated(self, text_elem):
        """Парсит текстовый элемент для поиска номеров кабинетов"""
        # Получаем текст
        text = text_elem.text.strip() if text_elem.text else ""

        # Ищем номер кабинета (может быть "101", "Каб. 102", "Room 103" и т.д.)
        room_number = None

        # Простая эвристика для поиска номеров
        words = text.split()
        for word in words:
            # Убираем знаки препинания
            cleaned = "".join(c for c in word if c.isdigit() or c.isalpha())

            # Если строка состоит из цифр и имеет длину 2-4 символа
            if cleaned.isdigit() and 2 <= len(cleaned) <= 4:
                room_number = cleaned
                break

        if room_number:
            # Получаем координаты
            x = float(text_elem.get("x", 0))
            y = float(text_elem.get("y", 0))

            # Проверяем transform атрибут для учета смещений
            transform = text_elem.get("transform", "")
            if "translate" in transform:
                # Простой парсинг трансформации
                import re

                match = re.search(r"translate\(([^,]+),\s*([^)]+)\)", transform)
                if match:
                    dx = float(match.group(1))
                    dy = float(match.group(2))
                    x += dx
                    y += dy

            self.rooms.append(
                RoomInfo(number=room_number, x=x, y=y, node_id=room_number)
            )

    def _simplify_graph(self):
        """Упрощает граф, удаляя промежуточные точки на прямых линиях"""
        points_to_remove = set()

        for point in list(self.graph.keys()):
            neighbors = list(self.graph[point])

            # Если точка имеет только двух соседей и они коллинеарны
            if len(neighbors) == 2:
                p1, p2 = neighbors

                # Проверяем коллинеарность
                if self._are_points_collinear(p1, point, p2):
                    # Добавляем прямое ребро между соседями
                    self._add_edge(p1, p2)

                    # Удаляем промежуточную точку
                    self.graph[p1].remove(point)
                    self.graph[p2].remove(point)
                    if point in self.graph:
                        del self.graph[point]
                    points_to_remove.add(point)

        # Удаляем точки из общего множества
        self.points -= points_to_remove

    def _are_points_collinear(self, p1, p2, p3, tolerance=1e-6):
        """Проверяет, лежат ли три точки на одной прямой"""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3

        # Вычисляем площадь треугольника
        area = abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0)
        return area < tolerance

    def _link_rooms_to_graph(self):
        """Привязывает кабинеты к ближайшим вершинам графа"""
        for room in self.rooms:
            closest_node = None
            min_distance = float("inf")

            for node in self.graph.keys():
                distance = sqrt((room.x - node[0]) ** 2 + (room.y - node[1]) ** 2)

                if distance < min_distance and distance < self.room_link_threshold:
                    min_distance = distance
                    closest_node = node

            if closest_node:
                room.node_id = closest_node
                # Добавляем информацию о комнате в граф
                if "rooms" not in self.graph[closest_node]:
                    self.graph[closest_node] = {"neighbors": set(), "rooms": []}
                elif isinstance(self.graph[closest_node], set):
                    # Конвертируем старую структуру в новую
                    neighbors = self.graph[closest_node]
                    self.graph[closest_node] = {"neighbors": neighbors, "rooms": []}

                self.graph[closest_node]["rooms"].append(room.number)

    def export_with_rooms(self, output_path: str):
        """Экспортирует граф с информацией о комнатах"""
        import json

        output_data = {"nodes": [], "edges": [], "rooms": []}

        # Создаем mapping точек в ID
        node_ids = {}
        for idx, point in enumerate(self.graph.keys()):
            node_id = f"node_{idx}"
            node_ids[point] = node_id

            node_data = {
                "id": node_id,
                "x": point[0],
                "y": point[1],
            }

            # Добавляем информацию о комнатах, если есть
            if isinstance(self.graph[point], dict) and "rooms" in self.graph[point]:
                node_data["rooms"] = self.graph[point]["rooms"]

            output_data["nodes"].append(node_data)

        # Добавляем ребра
        # for edge in self.edges:
        #     p1, p2 = edge
        #     if p1 in node_ids and p2 in node_ids:
        #         output_data["edges"].append({"from": node_ids[p1], "to": node_ids[p2]})

        # Добавляем информацию о комнатах
        for room in self.rooms:
            output_data["rooms"].append(
                {
                    "number": room.number,
                    "x": room.x,
                    "y": room.y,
                    "node_id": node_ids.get(room.node_id) if room.node_id else None,
                }
            )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

    def visualize(self):
        """Визуализирует граф с комнатами (для отладки)"""
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        fig, ax = plt.subplots(figsize=(12, 8))

        # Рисуем ребра
        for edge in self.edges:
            p1, p2 = edge
            x_values = [p1[0], p2[0]]
            y_values = [p1[1], p2[1]]
            ax.plot(x_values, y_values, "b-", alpha=0.7, linewidth=1)

        # Рисуем вершины
        nodes_x = [p[0] for p in self.graph.keys()]
        nodes_y = [p[1] for p in self.graph.keys()]
        ax.scatter(nodes_x, nodes_y, c="red", s=30, zorder=5)

        # Рисуем номера кабинетов
        for room in self.rooms:
            ax.text(
                room.x,
                room.y,
                room.number,
                fontsize=9,
                ha="center",
                va="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
            )

            # Показываем связь с вершиной
            if room.node_id:
                node = room.node_id
                ax.plot(
                    [room.x, node[0]],
                    [room.y, node[1]],
                    "g--",
                    alpha=0.3,
                    linewidth=0.5,
                )

        ax.set_aspect("equal")
        plt.title("Граф навигации с привязанными кабинетами")
        plt.grid(True, alpha=0.3)
        plt.show()


# Пример использования
def main():
    # Путь к вашему SVG файлу
    svg_path = "svg_parser\\floor6 matmeh4.svg"

    # Создаем парсер
    parser = GraphBuilderSVG(svg_path)

    # Парсим SVG
    parser.process_svg()

    # Визуализируем результат (опционально)
    parser.visualize()

    # Экспортируем данные
    parser.export_with_rooms("navigation_graph_with_rooms.json")

    # Статистика
    print(f"Найдено вершин: {len(parser.graph)}")
    print(f"Найдено ребер: {len(parser.edges)}")
    print(f"Найдено кабинетов: {len(parser.rooms)}")

    # Показываем привязанные кабинеты
    for room in parser.rooms:
        if room.node_id:
            print(f"Кабинет {room.number} привязан к вершине {room.node_id}")


if __name__ == "__main__":
    main()
