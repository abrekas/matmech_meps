# Python программа для иллюстрации
# обнаружение угла с
# Метод определения угла Харриса

import cv2
import numpy as np
import math
import time

#Вычслить расстояние между точками
def get_distance(p1,p2):
    x1,y1=p1
    x2,y2=p2
    return ((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2))**0.5  # Евклидово расстояние между последней и текущей точкой

#получить центр масс точек
def get_center(centers, point):
    l=len(centers)
    res=-1
    min_r=9999999999999.0
    for i in range(0,l):
        center=centers[i]
        x,y,count=center
        r=get_distance(point,(x,y))
        if r>=10:
            continue
        if r<min_r:
            res=i
            min_r=r
    return res

#Добавить точку в центр масс
def add_to_center(center, point):
    x1,y1,count=center
    count+=1
    x2,y2=point
    x=x1+(x2-x1)/float(count)
    y=y1+(y2-y1)/float(count)
    return x,y,count

#Теперь будем обрабатывать этот список
points_count=len(points)
print("Количество обрабатываемых точек: ",points_count)
beg_time=time.perf_counter()
centers=[]

for i in range(0,points_count):
    point=points[i]
    center_index=get_center(centers,point)
    if center_index==-1:
        x,y=point
        centers.append((x,y,1))
    else:
        center = centers[center_index]
        centers[center_index]=add_to_center(center,point)
end_time=time.perf_counter()

print("Осталось точек ",len(centers))

img_blank1 = np.zeros(image.shape)
for center in centers:
    x,y,count=center
    img_blank1[int(y),int(x),2]=255
