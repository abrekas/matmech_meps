import cv2
import numpy as np
import matplotlib.pyplot as plt

# 1. Загружаем и обрабатываем изображение
# img = cv2.imread()
# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# gray_float = np.float32(gray)

# # 2. Детектор Харриса
# dst = cv2.cornerHarris(gray_float, 2, 3, 0.04)
# # dst = cv2.dilate(dst, None)
# # img[dst > 0.01 * dst.max()] = [0, 0, 255]  # Отмечаем углы красным

# # 3. Отображение
# plt.figure(figsize=(1000, 1000))
# plt.imshow(cv2.cvtColor(dst, cv2.COLOR_BGR2RGB))
# plt.show()

'''пусть этот класс есть и он работает.
т.е. вместо чисел ставит точки, и создаёт словарь:
номер кабинета -> точка на карте'''

class Cluster:
    def __init__(self):
        self.vector_list = []
        self.center_mass = None
        self.count = 0
    
    def add_point(self, new_point: tuple[int,int]):
        self.vector_list.append(new_point)
        self.center_mass[0] = self.center_mass[0] * (self.count / (float)(self.count+1)) + new_point[0] / (float)(self.count+1)
        self.center_mass[1] = self.center_mass[1] * (self.count / (float)(self.count+1)) + new_point[1] / (float)(self.count+1)
        self.count+=1

        

class RoomsFinder1:
    def __init__(self, unprocessed_image_path):
        self._unprocessed_image = cv2.imread(unprocessed_image_path)
        self._unprocessed_image_path = unprocessed_image_path
        self.cluster_max_radius = 7

    @staticmethod
    def _get_corners(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_float = np.float32(gray)

        # 2. Детектор Харриса
        dst = cv2.cornerHarris(gray_float, 2, 3, 0.04)
        return dst


class RoomsFinder:
    def __init__(self, unprocessed_image_path):
        self._unprocessed_image = cv2.imread(unprocessed_image_path)
        self._unprocessed_image_path = unprocessed_image_path
        self.cluster_max_radius = 7

    @staticmethod
    def _get_corners(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_float = np.float32(gray)

        # 2. Детектор Харриса
        dst = cv2.cornerHarris(gray_float, 2, 3, 0.04)
        return dst
    
    #Вычслить расстояние между точками
    @staticmethod
    def get_distance(p1,p2):
        x1,y1=p1
        x2,y2=p2
        return ((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2))**0.5  # Евклидово расстояние между последней и текущей точкой

    #получить центр масс точек
    @staticmethod
    def get_center(centers, point, max_radius = 5):
        l=len(centers)
        res=-1
        min_r=9999999999999.0
        for i in range(0,l):
            center=centers[i]
            x,y,count=center
            r=RoomsFinder.get_distance(point,(x,y))
            if r>=max_radius:
                continue
            if r<min_r:
                res=i
                min_r=r
        return res

    #Добавить точку в центр масс
    @staticmethod
    def add_to_center(center, point):
        x1,y1,count=center
        count+=1
        x2,y2=point
        x=x1+(x2-x1)/float(count)
        y=y1+(y2-y1)/float(count)
        return x,y,count

    @staticmethod
    def _merge_into_clusters(points):
        points_count=len(points)
        centers=[]
        for i in range(0,points_count):
            point=points[i]
            center_index=RoomsFinder.get_center(centers,point)
            if center_index==-1:
                x,y=point
                centers.append((x,y,1))
            else:
                center = centers[center_index]
                centers[center_index]=RoomsFinder.add_to_center(center,point)
        
        return RoomsFinder._parse_clusters(centers)
    
    @staticmethod
    def _parse_clusters(centers):
        ans_points = []
        for c in centers:
            ans_points.append((int(c[1]),int(c[0])))
        return ans_points

    @staticmethod
    def _put_all_corners_into_list(cornered_image):
        height = cornered_image.shape[0]
        width = cornered_image.shape[1]
        points = []
        for x in range(0,width):
            for y in range(0,height):
                if cornered_image[y,x] > 0:
                    points.append((x,y))
        return points
    
    # def _get_cluster_centers(self, corners: list[tuple[int,int]]):
    #     clusters = [] #c[i] = [<mass_center, <total_vector_sum>, <points_count>]

    #     for p in corners:
    #         if len(clusters) == 0:
    #             clusters.append([p,p,1])
    #         else:

    #             for c in clusters:
    

    @staticmethod
    def _recusion_call(func, initial_v, n):
        it = initial_v
        for _ in range(n):
            it = func(it)
        return it


    def _process_corners(self):
        self.corners = RoomsFinder._put_all_corners_into_list(self._corners_on_image)
        self.ans_corners = RoomsFinder._merge_into_clusters(self.corners)

        self.ans_ans_ans_corners = RoomsFinder._recusion_call(RoomsFinder._merge_into_clusters, self.ans_corners, 3)

    def _graph_points_onto_black(self, points: list):        
        black_img = np.zeros(self._unprocessed_image.shape)
        for p in points:
            black_img[p] = 255
        RoomsFinder._show_picture(black_img)
        
    @staticmethod
    def _show_picture(img):
        plt.figure(figsize=(1000, 1000))
        plt.imshow(img)
        plt.show()

    def _graph_points_onto_initial_image(self, points: list):
        img_copy = np.copy(self._unprocessed_image)
        for p in points:
            cv2.circle(img_copy, p, 3, (0,0,255), -1)
        RoomsFinder._show_picture(img_copy)
        


    
    def check_corners(self):
        '''UPD: всё проверил, сходится 1 в 1 !!!'''
        # self._graph_points_onto_black(self.corners)
        self._graph_points_onto_initial_image(self.corners)
        # self._graph_points_onto_black(self.ans_corners)
        # self._graph_points_onto_initial_image(self.ans_corners)
        # self._graph_points_onto_initial_image(self.ans_ans_ans_corners)
        
        


    def _process_floor(self):
        self._corners_on_image = self._get_corners(self._unprocessed_image)
        self._process_corners()

        

    def _visualize_results(self):
        plt.figure(figsize=(1000, 1000))
        plt.imshow(cv2.cvtColor(self._corners_on_image, cv2.COLOR_BGR2RGB))
        plt.show()

    def run(self):
        self._process_floor()
        # self._visualize_results()

def main():
    image_path = "input_images\\floor5\\floor5_unchanged.png"
    rf = RoomsFinder(image_path)
    rf.run()
    rf.check_corners()

if __name__ == '__main__':
    main()