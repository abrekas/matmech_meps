import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import KDTree
from scipy import ndimage
from skimage.morphology import thin, skeletonize
from skimage import measure
from typing import Tuple

class GraphBuilder:
    def __init__(self, img_path):
        self.image = cv2.imread(img_path)
        self.image_path = img_path
        self.max_trivial_distance = 5.5

    def _process_floor_plan(self):
        self.green_mask = GraphBuilder._extract_green_area(self.image)
        self.binary_mask = GraphBuilder._get_binary_image(self.green_mask)
        self.corridor_skeleton = GraphBuilder._make_skeleton(self.binary_mask)
        self.contour_all, self.contour_compressed = GraphBuilder._get_contour(
            self.binary_mask
        )

    @staticmethod
    def _extract_green_area(image):
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

    @staticmethod
    def _get_binary_image(image):
        _, binary = cv2.threshold(image, 1, 255, cv2.THRESH_BINARY)
        return binary // 255

    @staticmethod
    def _make_skeleton(binary_mask):
        skeleton = skeletonize(binary_mask, method="lee")
        # skeleton = thin(binary_mask)
        skeleton = (skeleton * 255).astype(np.uint8)
        return skeleton

    @staticmethod
    def _draw_skeleton_over_image(image, binary_skeleton_image):
        result_img = image.copy()
        skeleton_points = np.where(binary_skeleton_image > 0)
        for y, x in zip(skeleton_points[0], skeleton_points[1]):
            cv2.circle(result_img, (x, y), 0, (0, 0, 255), 0)  # Синие - точки скелета
        return result_img

    @staticmethod
    def _get_contour(corridor_binary) -> Tuple[list, list]:
        cnt, _ = cv2.findContours(
            corridor_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        cnt_cmpr, _ = cv2.findContours(
            corridor_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        return [x[0] for x in cnt[0].tolist()], [x[0] for x in cnt_cmpr[0].tolist()]

    @staticmethod
    def _draw_contour_points_over_image(image, contour, is_all_points):
        result_img = image.copy()
        color = (128, 0, 128) if is_all_points else (255, 0, 255)
        for point in contour:
            cv2.circle(result_img, point, 0, color, 0)
        return result_img

    def _make_cardinal_axis_line(
        self, start_x, start_y, finish, is_x_dir: bool, reverse: bool = False
    ):
        axis = 0 if is_x_dir else 1
        indices = [start_y, start_x]
        start = (start_x if is_x_dir else start_y) if not reverse else finish - 1
        end = finish if not reverse else (start_x if is_x_dir else start_y)
        direction = -1 if reverse else 1
        for i in range(start, end, direction):
            indices[1 - axis] = i
            if self.polygon_field[tuple(indices)] > 0:
                self.polygon_field[tuple(indices)] += 1
            else:
                break

    def p2p_distance(self, p1: list, p2: list) -> float:
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    def _split_into_polygons1(self):
        c_len = len(self.contour_compressed)
        height, width = self.binary_mask.shape
        self.polygon_field = self.binary_mask.copy()
        # self.polygon_field[2,5] = '52' (2 по y, 5 по x)
        p = -1
        while p < c_len-1:
            p += 1
            # line_coeffs: Tuple[int, int] = None
            a, b = (
                self.contour_compressed[p],
                self.contour_compressed[(p + 1) % c_len],
            )  # а здесь [0] - по x, [1] - по y
            difx = a[0] - b[0]
            dify = a[1] - b[1]
            dist = self.p2p_distance(a, b)
            if dist < 3:
                print(f"вырожденная пара точек на {a}, {b}")

                continue
            if difx != 0 and dify != 0:
                if dist > self.max_trivial_distance:
                    print(f"нетривиальная диагональ на {a},{b}")
                continue

            if difx != 0 or dify != 0:
                # Определяем ось и параметры
                is_x_axis = difx != 0
                axis_index = 0 if is_x_axis else 1
                bound = width if is_x_axis else height

                # Определяем начальную точку (с меньшей координатой по оси)
                start = a if a[axis_index] < b[axis_index] else b

                # Первая линия: от start до границы
                self._make_cardinal_axis_line(
                    start_x=start[0], start_y=start[1], finish=bound, is_x_dir=is_x_axis
                )

                # Вторая линия: от 0 до start
                # UPD: НЕТ!!!  нужно делать от start до 0 в обратном направлении
                # UPD: готово, сделано! :)
                self._make_cardinal_axis_line(
                    start_x=0 if is_x_axis else start[0],
                    start_y=start[1] if is_x_axis else 0,
                    finish=start[axis_index],
                    is_x_dir=is_x_axis,
                    reverse=True,
                )

    def run(self):
        self._process_floor_plan()
        self._split_into_polygons1()
        self._visualize_results()
        self._visualize_heatmap()

        # with open(f"{self.image_path[:-4]}_contour_out.txt", "w") as f:
        #     f.write(str(self.contour_all))

    def _visualize_results(self):

        fig, axes = plt.subplots(2, 3, figsize=(36, 24))
        axes[0, 0].imshow(self.image)
        axes[0, 0].set_title("Исходное изображение")

        axes[0, 1].imshow(self.corridor_skeleton, cmap="hot")
        axes[0, 1].set_title("Скелет коридора")

        axes[0, 2].imshow(
            GraphBuilder._draw_skeleton_over_image(self.image, self.corridor_skeleton)
        )
        axes[0, 2].set_title("Скелет поверх карты")

        axes[1, 0].imshow(
            GraphBuilder._draw_contour_points_over_image(
                GraphBuilder._draw_contour_points_over_image(
                    self.image, self.contour_all, True
                ),
                self.contour_compressed,
                False,
            )
        )
        axes[1, 0].set_title("Контур коридора")

        # 'hot', 'coolwarm', 'plasma', 'inferno'
        axes[1, 1].imshow(self.polygon_field, cmap="viridis")
        # axes[1, 1].set_colorbar(label="Значения")
        axes[1, 1].set_title("Heatmap")

        plt.tight_layout()
        plt.show()

    def _visualize_heatmap(self):
        plt.figure(figsize=(800, 800))
        plt.imshow(
            GraphBuilder._draw_contour_points_over_image(
                GraphBuilder._draw_contour_points_over_image(
                    self.image, self.contour_all, True
                ),
                self.contour_compressed,
                False,
            )
        )

        # 'hot', 'coolwarm', 'plasma', 'inferno'
        plt.imshow(self.polygon_field, cmap="viridis")
        # plt.set_colorbar(label="Значения")
        plt.title("Heatmap")
        plt.show()


def run_gb():
    image_path = "input_images\\basic\\basic copy.png"
    image_path = "input_images\\basic\\basic.png"
    image_path = "input_images\\floor5\\greenmask.png"
    image_path = "input_images\\floor6\\prep_plan6.png"

    section = 'floor6'
    name = 'prep_plan6.png'
    
    image_path = f'input_images\\{section}\\{name}'

    gb = GraphBuilder(img_path=image_path)
    gb.run()


if __name__ == "__main__":
    # run_imgprep()
    run_gb()
