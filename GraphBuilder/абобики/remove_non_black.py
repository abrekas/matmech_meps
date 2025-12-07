import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial import KDTree
from scipy import ndimage
from skimage.morphology import thin, skeletonize
from skimage import measure
from typing import Tuple

def remove_non_black(image_path, n=65):
    image: np.ndarray = cv2.imread(image_path)
    mask = image.max(axis=2) > n  # логический массив формой (H,W), где True будет там,
    # где наибольшая составляющая соответствующего пикселя > 35
    image[mask] = [255,255,255]  # заменяем значения пикселей, помеченных маской, на желаемые.
    cv2.imwrite(f'out_{image_path}', img=image)

def threshold_non_black1(image_path, upper_bound : Tuple[int,int,int] =(60,60,60)):
    image = cv2.imread(image_path)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_black = np.array([0,0,0])
    upper_black = np.array(upper_bound)

    # Create a mask using cv2.inRange()
    mask = cv2.inRange(hsv_image, lower_black, upper_black)

    # Apply the mask to the original image to show only the green regions
    result = cv2.bitwise_and(image, image, mask=mask)

    cv2.imwrite(f'out_{image_path}', img=result)

def threshold_non_black(image_path, upper_bound: Tuple[int, int, int] = (180, 50, 50)):
    image = cv2.imread(image_path)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv_image, np.array([0, 0, 0]), np.array(upper_bound))
    result = np.full_like(image, 255)  # Белое изображение
    result[mask == 255] = image[mask == 255]  # Вставляем черные пиксели

    cv2.imwrite(f'out_{image_path}', result)

def run():
    # remove_non_black('a1.jpg', 255)
    # remove_non_black('a1.jpg', 30)
    # remove_non_black('a3.jpg', 55)

    threshold_non_black('a1.jpg',(180,30,150))
    # threshold_non_black('a1.jpg',(180,60,40))
    # threshold_non_black('a3.jpg',(180,30,40))
    

if __name__ == '__main__':
    run()