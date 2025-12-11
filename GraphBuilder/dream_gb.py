import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import KDTree
from scipy import ndimage
from skimage.morphology import thin, skeletonize
from skimage import measure
from typing import Tuple
from skimage.morphology import thin, skeletonize



class GraphBuilderDream:
    def __init__(self, img_path, plan_path):
        self.image = cv2.imread(img_path)
        self.rgba_image = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        self.image_path = img_path
        self.plan_txt_path = plan_path
        self.floor_plan = {}
        self.floor_plan_points = {}

    def _process_floor(self):
        self._parse_txt_plan()
        self._find_rooms_enters()

    def _find_rooms_enters(self):
        k_bottom = 0
        k_up = 0
        green_cnt = 0
        for j in range(self.hsv_image.shape[1]):  # y
            is_down_the_redline = False
            for i in range(self.hsv_image.shape[0]):  # x
                pixel = self.image[i, j]
                is_green = (pixel[0] == 80) and (pixel[1] == 180) and (pixel[2] == 56)
                is_down_the_redline = is_down_the_redline or (
                    (pixel[2] == 255) and (pixel[0] < 150) and (pixel[1] < 150)
                )
                if is_green:
                    green_cnt += 1
                    if is_down_the_redline:
                        self.floor_plan_points[self.floor_plan["bottom"][k_bottom]] = (
                            i,
                            j,
                        )
                        k_bottom += 1
                    else:
                        self.floor_plan_points[self.floor_plan["upper"][k_up]] = (i, j)
                        k_up += 1

    def _leave_out_non_red(self):
        lower_red = np.array([0, 0, 255])
        upper_red = np.array([130, 130, 255])

        lower_red = np.array([0, 0, 255][::-1])
        upper_red = np.array([130, 130, 255][::-1])

        red_mask = cv2.inRange(self.image, lower_red, upper_red)

        # Очищаем маску
        kernel = np.ones((3, 3), np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)

        # Создаем изображение только с красными областями (в цвете)
        red_only = cv2.bitwise_and(self.image, self.image, mask=red_mask)

        plt.figure(figsize=(1000, 1000))
        plt.imshow(red_only)
        plt.show()

    def _parse_txt_plan(self):
        with open(self.plan_txt_path) as f:
            curr_section_name = ""
            is_in_section = False
            for s in f:
                if s == "\n":
                    continue
                if not is_in_section:
                    if s == "{\n":
                        is_in_section = True
                        continue
                    curr_section_name = s[:-1]
                    self.floor_plan[curr_section_name] = []
                else:
                    if s == "}\n":
                        is_in_section = False
                        continue
                    self.floor_plan[curr_section_name].append(s.strip())

    def _visualize_results(self):
        plt.figure(figsize=(1000, 1000))
        img_copy = np.copy(self.image)
        for val in self.floor_plan_points.values():
            cv2.circle(img_copy, val[::-1], 3, (255, 0, 255), -1)
        plt.imshow(img_copy)
        plt.show()

    def _dp_non_red(self):

        # Конвертируем в HSV цветовое пространство
        image_bgr = self.image
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

        # Диапазоны красного цвета в HSV
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([18, 255, 255])

        # Создаем маски для каждого диапазона
        red_mask = cv2.inRange(hsv, lower_red1, upper_red1)

        # # Очищаем маску
        # kernel = np.ones((3, 3), np.uint8)
        # red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        # red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)

        thinnized = thin(red_mask)

        # corners = cv2.cornerHarris(red_mask, 5,3,0.04)
        # corners = cv2.goodFeaturesToTrack(red_mask)

        # Визуализация
        plt.figure(figsize=(12, 6))

        # Исходное изображение
        plt.subplot(1, 2, 1)
        plt.imshow(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
        plt.title("Исходное изображение")
        plt.axis("off")

        # Только красные области (в цвете)
        plt.subplot(1, 2, 2)
        plt.imshow(cv2.cvtColor(red_only, cv2.COLOR_BGR2RGB))
        plt.title("Только красные области")
        plt.axis("off")

        plt.tight_layout()
        plt.show()

        # Также покажем бинарную маску
        plt.figure(figsize=(6, 6))
        plt.imshow(red_mask, cmap="gray")
        plt.title("Бинарная маска красных областей")
        plt.axis("off")
        plt.show()

        print(f"Количество красных пикселей: {np.sum(red_mask > 0)}")

    def run(self):
        # self._process_floor()
        # self._leave_out_non_red()
        self._dp_non_red()
        # self._leave_out_non_red()


def main():
    image_path = "input_images\\floor6\\floor6_dream_path.png"
    plan_path = "input_images\\floor6\\floor6_room_plan.txt"
    gbd = GraphBuilderDream(img_path=image_path, plan_path=plan_path)
    gbd.run()


if __name__ == "__main__":
    main()
