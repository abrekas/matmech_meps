import re
import json
from pathlib import Path
from typing import NamedTuple

# from __future__ import annotations

# import xml.etree.ElementTree as ET
from collections import defaultdict
from math import sqrt, isclose
from dataclasses import dataclass
from typing import Dict, Set, Tuple, List, Optional
import os


FINAL_GRAPH_JSON_PATH = ""


class Node(NamedTuple):
    x: int
    y: int
    neighbours: List[str]
    floor: str
    korpus: str


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
        self.graph: defaultdict[Tuple[float, float], Set[Tuple[float, float]]] = (
            defaultdict(set)
        )

        name_args = Path(self.source_file_path).name[:-4].split()
        self.floor = name_args[1]
        self.korpus = name_args[2]

        # Для хранения информации о кабинетах
        self.rooms: List[RoomInfo] = []
        self.valid_tags = frozenset(["g", "path", "text", "/g", "rect"])

        # Максимальное расстояние для связывания комнаты с вершиной
        self.room_link_threshold = 40.0

        self.staircase_pattern = "staircase"
        self.no_use_pattern = "no_use"
        self.component_pattern = "Component"

        self.global_x_offset = 0.0
        self.global_y_offset = 0.0

        file_path = Path(self.source_file_path)
        self.output_folder_name = file_path.parent.parent / file_path.stem
        os.makedirs(self.output_folder_name, exist_ok=True)

        self.stupid_json_path = os.path.join(
            self.output_folder_name, "navigation_graph_with_rooms.json"
        )
        self.graph_json_path = os.path.join(self.output_folder_name, "graph.json")
        self.names_json_path = os.path.join(self.output_folder_name, "names.json")

        self.coordinate_patterns = [
            re.compile(r"translate\(([\d.]+) ([\d.]+)\)"),
            re.compile(r"matrix\([-\d.]+ [-\d.]+ [-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)\)"),
            re.compile(r'd="M([\d.]+) ([\d.]+)'),
            re.compile(r'x="([\d.]+)" y="([\d.]+)"'),
        ]

        self.names_result = {}
        self.result_dict_coords = {}

    def _process_svg(self):
        """строит граф по файлу"""

        # 1. Парсим файлик и вносим все нужные данные
        self._parse_svg_file()

        # 2. Привязываем кабинеты к ближайшим вершинам
        self._link_rooms_to_graph()

    def _parse_svg_file(self):
        groups_stack = []
        skip_flag: bool = False

        with open(self.source_file_path) as f:
            for s in f:
                tag = re.search(r"(\S+ )|(<\S+>)", s).group()[1:-1]
                if tag not in self.valid_tags:
                    continue
                if tag == "/g":
                    if len(groups_stack) > 0:
                        dropped_group = groups_stack.pop()
                        if self.no_use_pattern in dropped_group:
                            skip_flag = False
                    continue
                if skip_flag:
                    continue
                id_match = re.search(r' id=.+?"', s)
                if not id_match:
                    continue
                id = id_match.group()[5:-1]
                if tag == "g":
                    groups_stack.append(id)
                    if self.no_use_pattern in id:
                        skip_flag = True

                if re.search(self.component_pattern, id):
                    parsed_id = id.split()
                    if len(parsed_id) != 3:
                        raise RuntimeError("invalid component format")
                    self.global_x_offset, self.global_y_offset = float(parsed_id[1]), float(parsed_id[2])

                elif re.search(r"graph", id):
                    self._parse_path_data(s)

                elif (
                    groups_stack[-1] == "rooms_numbers"
                    or groups_stack[-1] == "room_ids"
                ) and tag == "text":
                    self._add_room_by_id(s, id)

                elif (
                    len(groups_stack) > 2
                    and re.search(self.staircase_pattern, groups_stack[-2])
                    and (tag == "path" or tag == "text")
                ):
                    if self.staircase_pattern in id:
                        self._add_room_by_id(s, id)

                # вот и все ифы получается
                # print("aboba")

    def _add_room_by_id(self, s, id):
        for ptrn in self.coordinate_patterns:
            xy_match = re.search(ptrn, s)
            if xy_match:
                x, y = float(xy_match.group(1)), float(xy_match.group(2))
                break
        else:
            RuntimeError("somehow regex didnt work")

        self.rooms.append(RoomInfo(number=id, x=float(x)+self.global_x_offset, y=float(y)+self.global_y_offset))

    def _parse_path_data(self, path_data: str):
        """Парсит данные пути из SVG"""
        path_data = re.search(r' d="(.+?)"', path_data).group(1)
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
                        current_point = (x+self.global_x_offset, y+self.global_y_offset)
                        if start_point is None:
                            start_point = current_point
                        self.points.add(current_point)

            elif command == "L":  # LineTo
                for j in range(0, len(numeric_args), 2):
                    if j + 1 < len(numeric_args):
                        x, y = numeric_args[j], numeric_args[j + 1]
                        new_point = (x+self.global_x_offset, y+self.global_y_offset)
                        self._add_edge(current_point, new_point)
                        current_point = new_point
                        self.points.add(current_point)

            elif command == "H":  # Horizontal Line
                for x in numeric_args:
                    new_point = (x+self.global_x_offset, current_point[1])
                    self._add_edge(current_point, new_point)
                    current_point = new_point
                    self.points.add(current_point)

            elif command == "V":  # Vertical Line
                for y in numeric_args:
                    new_point = (current_point[0], y+self.global_y_offset)
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

    def _is_edge_redundant(
        self, p1: Tuple[float, float], p2: Tuple[float, float]
    ) -> bool:
        # return False
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
                if isinstance(self.graph[closest_node], Dict):
                    print("room double count .__.") #почему случается?????
                    continue
                closest_node_neighbour = self.graph[closest_node].pop()
                del self.graph[closest_node]
                self.graph[closest_node_neighbour].remove(closest_node)
                if (closest_node_neighbour, closest_node) in self.edges:
                    self.edges.remove((closest_node_neighbour, closest_node))
                elif (closest_node, closest_node_neighbour) in self.edges:
                    self.edges.remove((closest_node, closest_node_neighbour))
                else:
                    raise RuntimeError(f"ошибка при обработке комнаты {room.number}")

                room.node_id = closest_node_neighbour
                # Добавляем информацию о комнате в граф
                if "rooms" not in self.graph[room.node_id]:
                    self.graph[room.node_id] = {"neighbors": set(), "rooms": []}
                elif isinstance(self.graph[room.node_id], set):
                    # Конвертируем старую структуру в новую
                    neighbors = self.graph[room.node_id]
                    self.graph[room.node_id] = {"neighbors": neighbors, "rooms": []}
                    raise RuntimeError("две комнаты под одной вершиной графа")

                self.graph[room.node_id]["rooms"].append(room.number)

    def _export_with_rooms(self, output_path: str):
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
        for edge in self.edges:
            p1, p2 = edge
            if p1 in node_ids and p2 in node_ids:
                output_data["edges"].append({"from": node_ids[p1], "to": node_ids[p2]})

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

    def _visualize(self):
        """Визуализирует граф с комнатами (для отладки)"""
        import matplotlib.pyplot as plt
        
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

    def run(self):
        self._process_svg()
        self._visualize()
        self._export_with_rooms(self.stupid_json_path)
        # self._convert_to_sensible_format()

        self._convert_to_correct_format()
        self.dump_correct_json(self.correct_graph, self.correct_names)

    def _convert_to_sensible_format(self):

        dicta = {}

        with open(self.stupid_json_path, "r", encoding="utf-8") as file:
            dicta = json.load(file)

        nodes = dicta["nodes"]
        edges = dicta["edges"]
        names = dicta["rooms"]

        self.names_result = {}

        nodes_dict = {}
        result_dict = {}

        self.result_dict_coords = {}

        for node in nodes:
            result_dict[node["id"]] = []
            nodes_dict[node["id"]] = " ".join(
                (str(int(node["x"])), str(int(node["y"])))
            )
            for edge in edges:
                if edge["from"] == node["id"]:
                    result_dict[node["id"]].append(edge["to"])
                if edge["to"] == node["id"]:
                    result_dict[node["id"]].append(edge["from"])

        for des in result_dict.keys():
            self.result_dict_coords[nodes_dict[des]] = list(
                map(lambda x: nodes_dict[x], result_dict[des])
            )

        for name in names:
            self.names_result[name["number"]] = nodes_dict[name["node_id"]]

        # Точка (563, 132)
        print(self.result_dict_coords)

    def get_new_id(self, id):
        return f"{id} {self.floor} {self.korpus}"

    def get_new_name(self, name):
        return f"{name} {self.korpus}"

    def _convert_to_correct_format(self):
        dicta = {}

        with open(self.stupid_json_path, "r", encoding="utf-8") as file:
            dicta = json.load(file)

        nodes = dicta["nodes"]
        edges = dicta["edges"]
        names = dicta["rooms"]

        self.correct_graph: dict[str, Node] = {}
        self.correct_names: dict[str, str] = {}

        for node in nodes:
            self.correct_graph[self.get_new_id(node["id"])] = Node(
                node["x"], node["y"], list(), self.floor, self.korpus
            )

        for edge in edges:
            v1 = edge["to"]
            v2 = edge["from"]
            self.correct_graph[self.get_new_id(v1)].neighbours.append(
                self.get_new_id(v2)
            )
            self.correct_graph[self.get_new_id(v2)].neighbours.append(
                self.get_new_id(v1)
            )

        for name in names:
            room_name = self.get_new_name(name["number"])
            node_name = self.get_new_id(name["node_id"])
            self.correct_names[room_name] = node_name

    def dump_correct_json(self, result_graph, result_names):
        with open(self.graph_json_path, "w", encoding="utf-8") as f:
            json.dump(result_graph, f, ensure_ascii=False, indent=2)

        with open(self.names_json_path, "w", encoding="utf-8") as f:
            json.dump(result_names, f, ensure_ascii=False, indent=2)


name_change_dict: Dict[str, str] = {
    "dekanat": "деканат",
    "wc_m": "туалет мужской",
    "wc_w": "туалет женский",
    "a": "а",
    "stolovaya": "столовая",
    "library": "библиотека",
}


def merge_correct_jsons(parsers: List[GraphBuilderSVG], result_folder_path: Path):
    ans_dict_graph: Dict[str, Node] = {}
    ans_dict_names: Dict[str, str] = {}
    staircases_patterns = frozenset(["staircase", "lifts"])
    staircases: Dict[str, Dict[int, str]] = defaultdict(
        dict
    )  # [dict[stair_index -> dict[floor -> name]] ]

    for p in parsers:
        ans_dict_graph.update(p.correct_graph)
        ans_dict_names.update(p.correct_names)
        for key in p.correct_names:
            t = key.split()
            if t[0] in staircases_patterns:
                index = "1" if len(t) < 4 else t[2]
                staircases[f"{t[0]}:{index}"][t[1]] = key

    for stair in staircases.keys():
        floors = sorted(staircases[stair].keys())
        for i in range(1, len(floors)):
            ans_dict_graph[
                ans_dict_names[staircases[stair][floors[i - 1]]]
            ].neighbours.append(ans_dict_names[staircases[stair][floors[i]]])
            ans_dict_graph[
                ans_dict_names[staircases[stair][floors[i]]]
            ].neighbours.append(ans_dict_names[staircases[stair][floors[i - 1]]])

    with open(
        parsers[0].output_folder_name.parent / Path("ans_graph.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(ans_dict_graph, f, ensure_ascii=False, indent=2)

    with open(
        parsers[0].output_folder_name.parent / Path("ans_names.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(ans_dict_names, f, ensure_ascii=False, indent=2)

    ans_ans_dict_names = {}
    ans_ans_dict_graph = {}

    for node_id in ans_dict_graph.keys():
        curr_node = ans_dict_graph[node_id]

        node_coordinate = f"{int(curr_node.x)} {int(curr_node.y)} {curr_node.korpus}_{curr_node.floor}"

        ans_ans_dict_graph[node_coordinate] = [
            f"{int(ans_dict_graph[node_name].x)} {int(ans_dict_graph[node_name].y)} {ans_dict_graph[node_name].korpus}_{ans_dict_graph[node_name].floor}"
            for node_name in curr_node.neighbours
        ]

    for name in ans_dict_names.keys():
        if any((p in name) for p in staircases_patterns):
            continue
        curr_node = ans_dict_graph[ans_dict_names[name]]

        node_coordinate = f"{int(curr_node.x)} {int(curr_node.y)} {curr_node.korpus}_{curr_node.floor}"

        name = " ".join(name.split()[:-1])

        for str_to_change in name_change_dict.keys():
            if str_to_change in name:
                name = re.sub(
                    pattern=str_to_change,
                    string=name,
                    repl=name_change_dict[str_to_change],
                    count=1,
                )

        ans_ans_dict_names[name] = node_coordinate

    with open(
        result_folder_path / Path("ans_ans_graph.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(ans_ans_dict_graph, f, ensure_ascii=False, indent=2)

    with open(
        result_folder_path / Path("ans_ans_names.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(ans_ans_dict_names, f, ensure_ascii=False, indent=2)


def main():

    svg_paths = [
        # ".\\GB\\GraphBuilder\\svg_parser\\input_images\\floor 6 matmeh.svg",
        ".\\GB\\GraphBuilder\\svg_parser\\input_images\\floor 5 matmeh.svg",
        # ".\\GB\\GraphBuilder\\svg_parser\\input_images\\floor 3 kuibysheva.svg"
    ]

    parsers = [GraphBuilderSVG(path) for path in svg_paths]

    for p in parsers:
        p.run()
    print('aboba')
    # merge_correct_jsons(parsers, parsers[0].output_folder_name.parent.parent.parent)


if __name__ == "__main__":
    main()


"""

убрать:
-х лестницы, лифты: из ans_ans_names.json
-х matmeh в конце названий кабинетов
-х перевести все кабинеты на русский

-+- убрать туалеты (возможно)

"""
