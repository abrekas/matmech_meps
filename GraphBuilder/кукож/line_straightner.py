import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import KDTree
from scipy import ndimage
from skimage.morphology import thin, skeletonize
from skimage import measure
from typing import NamedTuple, Tuple


type Vector2D = np.ndarray[Tuple[int, int], np.dtype[np.int_]]


class pos_tuple(NamedTuple):
    """удобный способ представлять координаты"""

    x: int
    y: int


class line_coefficients(NamedTuple):
    """ax+by+c = 0"""

    a: int
    b: int
    c: int


class Window:
    def __init__(
        self, image: np.ndarray, start: Vector2D, direction: Vector2D, size: int = 3
    ):
        self._image = image
        self._pos = start
        self._direction = direction
        self._size = size

    @property
    def pos(self):
        return pos_tuple(self._pos[0], self._pos[1])

    def std_move(self):
        self._pos += self._direction


class LineStraighnter:
    def __init__(
        self, image, start: pos_tuple, direction: Vector2D, line: line_coefficients
    ):
        self.image = image
        self.pos = start
        self.direction = direction
        self.line_coeffs = line_coefficients
        self.window_size = 3

        self.previous_line_point = start

    def _straighten(self):
        pass
