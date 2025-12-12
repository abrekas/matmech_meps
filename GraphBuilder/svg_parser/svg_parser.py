from collections import defaultdict
import re


class queue:
    def __init__(self, max_size):
        self._size = 0
        self._head = 0
        self._max_size = max_size
        self._list = [0] * self._max_size

    @property
    def size(self):
        return self._size

    def enqueue(self, x):
        self._list[(self._head + self._size) % self._max_size] = x
        self._size += 1

    def dequeue(self) -> any:
        t = self._list[self._head]
        self._head = (self._head + 1) % self._max_size
        self._size -= 1
        return t


class GraphBuilderSVG:
    def __init__(self, src_file_path):
        self.source_file_path = src_file_path
        self.data = self._read_source_file()
        self.main_string = self.data[1]

        self.valid_tags = frozenset(["g", "path", "text"])

        self.points = set()
        self.edges = set()

        self.graph = defaultdict(set)

        self.commands = frozenset({"M", "V", "H", "Z", "L", '"'})

        self.cursor_x = 0
        self.cursor_y = 0

    def _read_source_file(self) -> str:
        with open(self.source_file_path) as f:
            return f.readlines()

    def _parse_svg_file(self):
        groups_stack = []
        rooms_dict = {}
        temp_id = ''
        with open(self.source_file_path) as f:
            for s in f:
                tag = re.search(r"\S* ", s).group()[1:-1]
                if tag not in self.valid_tags:
                    continue
                id = re.search(r' id=[\S]*[" ]', s).group()[5:-1]
                if tag == "g":
                    groups_stack.append(id)
                elif tag == "/g":
                    groups_stack.pop()

                if re.search(r"graph", id):
                    self.main_string = s
                    self._parse_meaning_string()
                
                elif groups_stack[-1] == 'rooms_numbers' and tag == 'text':
                    x = re.search(r'x="\S+"', s).group()[3:-1]
                    y = re.search(r'y="\S+"', s).group()[3:-1]
                    rooms_dict[id] = (x,y)
                
                elif len(groups_stack) > 2 and groups_stack[-2] == 'rooms_numbers':
                    if tag == 'g':
                        temp_id = id
                    else:
                        x = re.search(r'x="\S+"', s).group()[3:-1]
                        y = re.search(r'y="\S+"', s).group()[3:-1]
                        rooms_dict[temp_id] = (x,y)
                #вот и все ифы получается
                print('aboba')

    def _read_a_pair(self, i: int) -> tuple[tuple[float, float], int]:
        buf = [[], []]
        i += 1
        k = 0
        while self.main_string[i] not in self.commands:
            if self.main_string[i] == " ":
                k += 1
            elif k < 2:
                buf[k].append(self.main_string[i])
            i += 1
        return (float("".join(buf[0])), float("".join(buf[1]))), i - 1

    def _read_a_point(self, i):
        buf = []
        i += 1
        while self.main_string[i] not in self.commands and self.main_string[i] != " ":
            buf.append(self.main_string[i])
            i += 1
        return float("".join(buf)), i - 1

    def _parse_meaning_string(self):
        i = 0
        n = len(self.main_string)
        while i < n and self.main_string[i] != '"':
            i += 1
        i += 1
        while self.main_string[i] != '"':
            if self.main_string[i] == "M":
                new_point, i = self._read_a_pair(i)
                self.cursor_x, self.cursor_y = new_point
                self.points.add(new_point)
                if new_point not in self.graph.keys():
                    self.graph[new_point] = set()

            elif self.main_string[i] == "L":
                new_point, i = self._read_a_pair(i)
                if new_point != (self.cursor_x, self.cursor_y):
                    self.graph[new_point].add((self.cursor_x, self.cursor_y))
                    self.graph[(self.cursor_x, self.cursor_y)].add(new_point)
                    self.cursor_x, self.cursor_y = new_point

            elif self.main_string[i] == "V" or self.main_string[i] == "H":
                command = self.main_string[i]
                t, i = self._read_a_point(i)
                new_point = (self.cursor_x, t) if command == "V" else (t, self.cursor_y)
                if new_point != (self.cursor_x, self.cursor_y):
                    self.graph[new_point].add((self.cursor_x, self.cursor_y))
                    self.graph[(self.cursor_x, self.cursor_y)].add(new_point)
                    self.cursor_x, self.cursor_y = new_point
            i += 1

    def _bfs(self) -> set:
        q = queue(len(self.graph.keys()))
        visited = set()
        current_node = (self.cursor_x, self.cursor_y)
        q.enqueue(current_node)
        while q.size > 0:
            current_node = q.dequeue()
            visited.add(current_node)
            for neighbour in self.graph[current_node]:
                if neighbour not in visited:
                    q.enqueue(neighbour)

        return visited

    def _check_conectedness(self):
        self.visited = self._bfs()
        return self.visited == self.graph.keys()

    def run(self):
        self._parse_svg_file()
        self._parse_meaning_string()
        self.is_graph_connected = self._check_conectedness()


def main():
    image_path = "svg_parser\\input_images\\Vector 639 (1).svg"
    image_path = "svg_parser\\floor6 matmeh.svg"
    gb = GraphBuilderSVG(image_path)
    gb.run()
    if gb.is_graph_connected:
        print("aboba")
    else:
        print("kys")
        print(gb.visited.difference(set(gb.graph.keys())))
        print("525252")
        print(set(gb.graph.keys()).difference(gb.visited))


if __name__ == "__main__":
    main()
