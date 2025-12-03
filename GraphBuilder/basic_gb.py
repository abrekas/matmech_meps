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

    def run(self):
        self._process_floor_plan()
        self._split_into_polygons()
        # self._visualize_results()
        self._visualize_heatmap()

        with open(f"{self.image_path[:-4]}_contour_out.txt", "w") as f:
            f.write(str(self.contour_all))

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

    def _make_cardinal_axis_line(self, start_x, start_y, finish, is_x_dir: bool):
        # start: [0]x, [1]y
        # polygon_field: [0]y, [1]x

        axis = 0 if is_x_dir else 1
        indices = [start_y, start_x]
        # indices = [start_x, start_y]
        for i in range(start_x if is_x_dir else start_y, finish):
            indices[1 - axis] = i
            if self.polygon_field[tuple(indices)] > 0:
                self.polygon_field[tuple(indices)] += 1
            else:
                break

    def _split_into_polygons(self):
        c_len = len(self.contour_compressed)
        height, width = self.binary_mask.shape
        self.polygon_field = self.binary_mask.copy()
        # self.polygon_field[2,5] = '52' (2 по y, 5 по x)
        for p in range(c_len):
            # line_coeffs: Tuple[int, int] = None
            a, b = (
                self.contour_compressed[p],
                self.contour_compressed[(p + 1) % c_len],
            )  # а здесь [0] - по x, [1] - по y
            difx = a[0] - b[0]
            dify = a[1] - b[1]

            if difx != 0 and dify != 0:
                # raise RuntimeError("Диагональ!!! аааа")
                # print(f"непрямая на {a}, {b}!!!")
                if abs(a[0]-b[0]) > 1 and abs(a[1]-b[1]) > 1:
                    print(f"нетривиальная непрямая на {a},{b}")
                

            if dify != 0:  # прямая по y
                start = a if a[1] < b[1] else b
                self._make_cardinal_axis_line(
                    start_x=start[0], start_y=start[1], finish=height, is_x_dir=False
                )
                self._make_cardinal_axis_line(
                    start_x=start[0], start_y=0, finish=start[1], is_x_dir=False
                )

            elif difx != 0:  # прямая по x
                start = a if a[0] < b[0] else b
                self._make_cardinal_axis_line(
                    start_x=start[0], start_y=start[1], finish=width, is_x_dir=True
                )
                self._make_cardinal_axis_line(
                    start_x=0, start_y=start[1], finish=start[0], is_x_dir=True
                )
            else:
                print(f"poing doubling: {a}")
        # print("aboba")

        """
        (!!!) UPDATE: непрямые линии не сохраняются в виде уравнения, 
        а в виде горизонтальных / вертикальных отрезочков (!!!)

        A(x1, y1) B(x2, y2) : ax + by + c = 0
        1. находим a,b,c
        2. проводим прямую и смотрим для каждой последовательной пары точек, есть ли пересечение с contour
            (!) а если прямая очень неровная, то будем смотреть окрестность?
                наверно нет, стоит просто понять какой конфигурацией алгоритма построения прямой мы это делаем
                и применить именно его. должны очев получить ту же самую прямую
            если нашлось, берём самое ближнее:
                если получились точки с обеих сторон отрезка AB, то берём обе самые ближние точки к A и B соотв.
                    хотя могло получиться что и больше точек нужно...
            иначе ничего
        получили список точек, их добавляем на картинку наравне с corner_points (которые получились из appox_simple)

        """

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
        plt.figure(figsize=(800,800))
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


class ImagePrep(GraphBuilder):
    def __init__(self, img_path):
        self.image = cv2.imread(img_path)
        self.image_path = img_path

    def _make_binary(self, image):
        self.gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, self.binary_image = cv2.threshold(
            self.gray_image, 1, 1, cv2.THRESH_BINARY_INV
        )

    @staticmethod
    def _make_skeleton(binary_mask):
        skeleton = skeletonize(binary_mask, method="lee")
        # skeleton = thin(binary_mask)
        skeleton = skeleton.astype(np.uint8)
        return skeleton

    def _process_floor_plan(self):
        self._make_binary(self.image)
        self.contour_skeleton = GraphBuilder._make_skeleton(self.binary_image)
        self.c_skeleton_contour_all, self.c_skeleton_contour_cmpr = (
            GraphBuilder._get_contour(ImagePrep._make_skeleton(self.binary_image))
        )

    def _visualize_results(self):
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes[0, 0].imshow(self.image)
        axes[0, 0].set_title("Исходное изображение")

        axes[0, 1].imshow(self.contour_skeleton, cmap="hot")
        axes[0, 1].set_title("Скелет контура")

        axes[0, 2].imshow(
            GraphBuilder._draw_skeleton_over_image(self.image, self.contour_skeleton)
        )
        axes[0, 2].set_title("Скелет контура на исходной картинке")

        axes[1, 0].imshow(
            GraphBuilder._draw_contour_points_over_image(
                GraphBuilder._draw_contour_points_over_image(
                    self.image, self.c_skeleton_contour_all, is_all_points=True
                ),
                self.c_skeleton_contour_cmpr,
                is_all_points=False,
            )
        )
        axes[1, 0].set_title("Контур скелета контура на исходной картинке")

        plt.tight_layout()
        plt.show()

    def run(self):
        self._process_floor_plan()
        self._visualize_results()


def run_gb():
    image_path = "basic.png"
    image_path = "greenmask.png"
    image_path = "basic copy.png"
    image_path = "prep_plan6.png"
    gb = GraphBuilder(img_path=image_path)
    gb.run()


def run_imgprep():
    image_path = "plan6.png"
    imgprep = ImagePrep(image_path)
    imgprep.run()


if __name__ == "__main__":
    # run_imgprep()
    run_gb()
