import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import KDTree
from scipy import ndimage
from skimage.morphology import thin, skeletonize
from skimage import measure
from typing import Tuple


class GraphBuilderDream:
    def __init__(self, img_path, plan_path):
        self.image = cv2.imread(img_path)
        self.hsv_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        self.rgba_image = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        self.image_path = img_path
        self.plan_txt_path = plan_path
        self.floor_plan = {}   
        self.floor_plan_points = {} 

    def _process_floor(self):
        k_bottom = 0
        k_up = 0
        green_cnt = 0
        for j in range(self.hsv_image.shape[1]):  # y
            is_down_the_redline = False
            for i in range(self.hsv_image.shape[0]):  # x
                # pixel = self.hsv_image[i, j]  # y, x
                pixel = self.image[i,j]
                # is_down_the_redline = is_down_the_redline or (pixel[0] < 35 or pixel[0] > 330) and (50 <= pixel[1] <= 255) and (50 <= pixel[2] <= 255)
                # is_green = (86 > pixel[0] > 34) and (50 <= pixel[1] <= 255) and (50 <= pixel[2] <= 255)

                is_green = (pixel[0] == 80) and (pixel[1] == 180) and (pixel[2] == 56)
                is_down_the_redline = is_down_the_redline or ((pixel[2] == 255) and (pixel[0] < 150) and (pixel[1] < 150))
                if is_green:
                    green_cnt += 1
                    if is_down_the_redline:
                        self.floor_plan_points[self.floor_plan['bottom'][k_bottom]] = (i,j)
                        k_bottom += 1
                    else:
                        self.floor_plan_points[self.floor_plan['upper'][k_up]] = (i,j)
                        k_up += 1
        



                    


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
        plt.figure(figsize=(1000,1000))
        img_copy = np.copy(self.image)
        for val in self.floor_plan_points.values():
            cv2.circle(img_copy, val[::-1], 3, (255,0,255), -1)
        plt.imshow(img_copy)
        plt.show()

    def run(self):
        self._parse_txt_plan()
        self._process_floor()
        self._visualize_results() #всё норм
        # with open('dream_floor6_result.txt','w') as f:
        #     for k in self.floor_plan_points.keys():
        #         f.write(f'{k}: {self.floor_plan_points[k]}\n')


def main():
    image_path = "input_images\\floor6\\floor6_dream_path.png"
    plan_path = "input_images\\floor6\\floor6_room_plan.txt"
    gbd = GraphBuilderDream(img_path=image_path, plan_path=plan_path)
    gbd.run()


if __name__ == "__main__":
    main()
