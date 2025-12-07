import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import KDTree
from scipy import ndimage
from skimage.morphology import thin, skeletonize
from skimage import measure
from typing import Tuple

from basic_gb import GraphBuilder

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

def run_imgprep():
    image_path = "plan6.png"
    imgprep = ImagePrep(image_path)
    imgprep.run()