from collections import defaultdict


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

        self.points = set()
        self.edges = set()

        self.graph = defaultdict(set)

        self.commands = frozenset({"M", "V", "H", "Z", "L", '"'})

        self.cursor_x = 0
        self.cursor_y = 0

    def _read_source_file(self) -> str:
        with open(self.source_file_path) as f:
            return f.readlines()

    def _read_a_pair(self, i: int):
        buf = [[], []]
        i += 1
        k = 0
        while self.main_string[i] not in self.commands:
            if self.main_string[i] == " ":
                k += 1
            elif k < 2:
                buf[k].append(self.main_string[i])
            i += 1
        return float("".join(buf[0])), float("".join(buf[1])), i - 1

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
                t1, t2, i = self._read_a_pair(i)
                self.cursor_x = t1
                self.cursor_y = t2
                self.points.add((t1, t2))
                if (t1, t2) not in self.graph.keys():
                    self.graph[(t1, t2)] = set()

            elif self.main_string[i] == "V" or self.main_string[i] == "H":
                command = self.main_string[i]
                t, i = self._read_a_point(i)
                new_point = (
                    (self.cursor_x, t)
                    if command == "V"
                    else (t, self.cursor_y)
                )
                if new_point != (self.cursor_x, self.cursor_y):
                    self.graph[new_point].add((self.cursor_x, self.cursor_y))
                    self.graph[(self.cursor_x, self.cursor_y)].add(new_point)
                    self.cursor_x, self.cursor_y = new_point

            elif self.main_string[i] == "L":
                command = self.main_string[i]
                t1,t2, i = self._read_a_pair(i)
                if (t1,t2) != (self.cursor_x, self.cursor_y):
                    self.graph[(t1,t2)].add((self.cursor_x, self.cursor_y))
                    self.graph[(self.cursor_x, self.cursor_y)].add((t1,t2))
                    self.cursor_x, self.cursor_y = t1,t2
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
        self._parse_meaning_string()
        self.is_graph_connected = self._check_conectedness()

'''а что дальше?
- проверить, нормально ли связан граф а не по-дибильному
    1. замкнуть по транзитивности (матрицей и возвести в степень )
    2. убрать все рёбра, которые можно заменить маршрутом большей длины - хотя может наломать мне всё...
    0. а если сначала нарисовать скелет коридора, потом добавить проходы до кабинетов, то норм


'''
def main():
    image_path = "svg_parser\\Vector 639 (1).svg"
    image_path = "svg_parser\\Vector 711 (2).svg"
    gb = GraphBuilderSVG(image_path)
    gb.run()
    if gb.is_graph_connected:
        print("aboba")
    else:
        print("kys")
        print(gb.visited.difference(set(gb.graph.keys())))
        print('525252')
        print(set(gb.graph.keys()).difference(gb.visited))


if __name__ == "__main__":
    main()
