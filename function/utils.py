import cv2
import numpy as np
import math
def draw_min_rect_and_label_1(needle_shank_points, color,out_img):
    """
        绘制外接矩阵和标签
    """
    rect = cv2.minAreaRect(needle_shank_points)  # 获取最小外接矩形
    box = cv2.boxPoints(rect)  # 获取矩形四个点
    box = np.int32(box)  # 将点转换为整数
    (width, height) = rect[1]  # 获取矩形的长宽
    # 标注矩形的长和宽
    cv2.polylines(out_img, [box], True, color, 2)  # 绘制矩形
    cv2.putText(out_img, f"Width: {width:.2f}", (int(rect[0][0]), int(rect[0][1] + 40)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    cv2.putText(out_img, f"Height: {height:.2f}", (int(rect[0][0]), int(rect[0][1] + 60)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return min([width, height]), max([width, height])

def draw_min_rect_and_label_2(needle_shank_points, color,out_img):
    # for contour in needle_shank_points:
    rect = cv2.minAreaRect(needle_shank_points)  # 获取最小外接矩形
    box = cv2.boxPoints(rect)  # 获取矩形四个点
    box = np.int32(box)  # 将点转换为整数
    # cv2.polylines(out_img, [box], True, color, 2)  # 绘制矩形
    (width, height) = rect[1]  # 获取矩形的长宽
    # 标注矩形的长和宽
    cv2.putText(out_img, f"Width: {width:.2f}", (int(rect[0][0]-40), int(rect[0][1] + 40)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    cv2.putText(out_img, f"Height: {height:.2f}", (int(rect[0][0]-40), int(rect[0][1] + 60)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return min([width,height]),max([width,height])
def draw_min_rect_and_label_3(needle_shank_points, color,out_img):
    # for contour in needle_shank_points:
    rect = cv2.minAreaRect(needle_shank_points)  # 获取最小外接矩形
    box = cv2.boxPoints(rect)  # 获取矩形四个点
    box = np.int32(box)  # 将点转换为整数
    cv2.polylines(out_img, [box], True, color, 2)  # 绘制矩形
    (width, height) = rect[1]  # 获取矩形的长宽
    # 标注矩形的长和宽
    cv2.putText(out_img, f"Width: {width:.2f}", (int(rect[0][0]), int(rect[0][1] - 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    cv2.putText(out_img, f"Height: {height:.2f}", (int(rect[0][0]), int(rect[0][1] + 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
def measure_diameter_using_min_rect(contour):
    """
    使用最小外接矩形来估算轮廓对应的“直径”或“宽度”。
    返回该矩形最短边(像素单位)。
    """
    rect = cv2.minAreaRect(contour)  # ((cx, cy), (w, h), angle)
    (width, height) = rect[1]
    # 由于矩形有旋转，宽和高并不保证谁是最短边，因此要取 min(w, h)
    diameter_in_pixels = min(width, height)
    length=max(width,height)
    return diameter_in_pixels, rect,length
def get_longest_edges(rect):
    """获取矩形的两条最长边"""
    box_points = cv2.boxPoints(rect)
    # box_points = np.int32(box_points)

    edges = [
        (box_points[0], box_points[1]),
        (box_points[1], box_points[2]),
        (box_points[2], box_points[3]),
        (box_points[3], box_points[0])
    ]

    # 计算每条边的长度
    edge_lengths = [np.linalg.norm(edge[0] - edge[1]) for edge in edges]

    # 获取两条最长的边的索引
    longest_edges_indices = sorted(range(len(edge_lengths)), key=lambda i: edge_lengths[i], reverse=True)[:2]

    # 返回两条最长边
    longest_edge1 = edges[longest_edges_indices[0]]
    longest_edge2 = edges[longest_edges_indices[1]]

    return longest_edge1, longest_edge2


def get_equidistant_points(longest_edge, num_points=20, middle_ratio=0.7):
    """
    在一条边的中间指定比例部分等距取多个点（不包括端点）

    参数:
    - longest_edge: 线段的两个端点，格式为 ((x1, y1), (x2, y2))
    - num_points: 在中间部分等距取的点的数量，默认为20
    - middle_ratio: 中间部分的比例，默认为0.7（即中间70%）
    """
    p1, p2 = longest_edge  # 提取线段的两个端点

    # 计算中间部分的起始点和结束点的比例
    start_ratio = (1 - middle_ratio) / 2  # 起始点距离起点的比例
    end_ratio = 1 - start_ratio  # 结束点距离起点的比例

    # 计算起始点和结束点的坐标
    start_x = p1[0] + start_ratio * (p2[0] - p1[0])
    start_y = p1[1] + start_ratio * (p2[1] - p1[1])
    end_x = p1[0] + end_ratio * (p2[0] - p1[0])
    end_y = p1[1] + end_ratio * (p2[1] - p1[1])

    # 初始化一个空列表用于存储等距点
    points = []

    # 在中间部分等距取点
    for i in range(1, num_points + 1):
        # 计算等距点的坐标
        x = int(start_x + i * (end_x - start_x) / (num_points + 1))
        y = int(start_y + i * (end_y - start_y) / (num_points + 1))
        points.append((x, y))

    return points
def point_to_line_distance(point, line_start, line_end):
    """计算点到线段的最短距离"""
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end

    # 计算线段的长度
    line_length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    if line_length == 0:
        return np.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)  # 防止除以零

    # 计算投影系数
    t = ((x0 - x1) * (x2 - x1) + (y0 - y1) * (y2 - y1)) / line_length ** 2
    t = max(0, min(1, t))  # 限制 t 在 [0, 1] 之间

    # 计算垂足
    closest_point = (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    # 返回点到线段的距离
    return np.sqrt((x0 - closest_point[0]) ** 2 + (y0 - closest_point[1]) ** 2)


def line_intersection(p1, p2, q1, q2):
    """计算两条线段(p1, p2)和(q1, q2)的交点"""
    denom = (p2[0] - p1[0]) * (q2[1] - q1[1]) - (p2[1] - p1[1]) * (q2[0] - q1[0])
    if denom == 0:
        return None  # 平行线无交点

    intersect_x = ((p2[0] * p1[1] - p2[1] * p1[0]) * (q2[0] - q1[0]) - (p2[0] - p1[0]) * (
                q2[0] * q1[1] - q2[1] * q1[0])) / denom
    intersect_y = ((p2[0] * p1[1] - p2[1] * p1[0]) * (q2[1] - q1[1]) - (p2[1] - p1[1]) * (
                q2[0] * q1[1] - q2[1] * q1[0])) / denom
    return (intersect_x, intersect_y)


def is_point_on_segment(point, seg_start, seg_end):
    """判断交点是否在轮廓线段内"""
    x0, y0 = point
    x1, y1 = seg_start
    x2, y2 = seg_end

    # 检查交点是否在两个端点之间的范围内
    return min(x1, x2) <= x0 <= max(x1, x2) and min(y1, y2) <= y0 <= max(y1, y2)


def get_perpendicular_line(point, edge):
    """计算从点到另一条边的垂线"""
    x0, y0 = point
    x1, y1 = edge[0]
    x2, y2 = edge[1]

    # 计算边的方向向量
    dx, dy = x2 - x1, y2 - y1

    # 计算垂直方向向量
    perp_dx, perp_dy = -dy, dx

    # 计算垂足
    t = ((x0 - x1) * perp_dx + (y0 - y1) * perp_dy) / (perp_dx ** 2 + perp_dy ** 2)
    px, py = x0 - t * perp_dx, y0 - t * perp_dy
    # print(px)
    # print(py)
    return (px, py)

# def get_perpendicular_intersections(image, equidistant_points, longest_edge2, contour):
#     """计算从等距点到另一条最长边的垂线与轮廓的交点"""
#     intersection_points = []
#     for point in equidistant_points:
#         # 计算垂线的垂足
#         perpendicular_point = get_perpendicular_line(point, longest_edge2)
#         if math.isnan(perpendicular_point[0]) or math.isnan(perpendicular_point[1]):
#             continue  # 如果px或py为NaN，跳过当前迭代
#         num_inter=[]

#         # cv2.line(image, point, perpendicular_point, (255, 255, 0), 1)  # 绘制垂线（黄色）

#         # 计算垂线与轮廓的交点
#         for i in range(len(contour) - 1):
#             segment_start = tuple(contour[i][0])
#             segment_end = tuple(contour[i + 1][0])

#             intersection = line_intersection(point, perpendicular_point, segment_start, segment_end)
#             if intersection is not None:
#                 # 判断交点是否在该线段上
#                 if is_point_on_segment(intersection, segment_start, segment_end):

#                     num_inter.append(intersection)

#         if len(num_inter)==2:
#             intersection_points.append(num_inter[0])
#             intersection_points.append(num_inter[1])
#             # 绘制交点
#             cv2.circle(image, (int(num_inter[0][0]), int(num_inter[0][1])), 3, (0, 0, 255), -1)  # 绘制交点（红色）
#             cv2.circle(image, (int(num_inter[1][0]), int(num_inter[1][1])), 3, (0, 0, 255), -1)  # 绘制交点（红色）

#     return intersection_points, image



import numpy as np
from collections import defaultdict
import random
def get_perpendicular_intersections(image, equidistant_points, longest_edge2, contour, draw=True):
    """
    优化版垂线与轮廓交点计算（基于空间哈希和射线法）
    参数:
        image: 输入图像 (BGR格式)
        equidistant_points: 等距点列表 [(x1,y1), (x2,y2), ...]
        longest_edge2: 第二条最长边 (array([x1,y1]), array([x2,y2]))
        contour: 轮廓点集 [Nx1x2数组]
        draw: 是否绘制可视化结果
    返回:
        intersection_points: 交点列表 [(x1,y1), (x2,y2), ...]
        marked_image: 标记后的图像
    """
    marked_image = image.copy()
    a = image.copy()
    intersection_points = []
    
    # 1. 预处理：构建轮廓线段的空间哈希表
    grid_size = 30  # 网格大小（根据图像尺寸调整）
    spatial_grid = defaultdict(list)
    
    for i in range(len(contour)-1):
        seg_start = contour[i][0]
        seg_end = contour[i+1][0]
        
        # 计算线段包围盒
        min_x = min(seg_start[0], seg_end[0])
        max_x = max(seg_start[0], seg_end[0])
        min_y = min(seg_start[1], seg_end[1])
        max_y = max(seg_start[1], seg_end[1])
        
        # 将线段添加到覆盖的所有网格
        for x in range(int(min_x//grid_size), int(max_x//grid_size)+1):
            for y in range(int(min_y//grid_size), int(max_y//grid_size)+1):
                spatial_grid[(x,y)].append((seg_start, seg_end))
    
    # 2. 转换坐标格式
    pt1 = tuple(map(int, longest_edge2[0]))
    pt2 = tuple(map(int, longest_edge2[1]))
    
    for point in equidistant_points:
        point = tuple(map(int, point))
        
        # 3. 计算垂足（浮点精度）
        perpendicular_point = get_perpendicular_line(point, (pt1, pt2))
        if perpendicular_point is None or any(math.isnan(c) for c in perpendicular_point):
            continue
            
        pp_int = tuple(map(int, perpendicular_point))
        
        # if draw:
            # cv2.circle(marked_image, point, 2, (0, 255, 0), -1)
            # cv2.circle(marked_image, pp_int, 2, (255, 255, 0), -1)
            # cv2.line(marked_image, point, pp_int, (0, 255, 255), 1)

        # 4. 基于网格的快速交点检测
        ray_start = np.array(point)
        ray_end = np.array(perpendicular_point)
        ray_dir = ray_end - ray_start
        
        # 获取射线经过的网格
        visited_grids = set()
        intersections = []
        
        # 使用Bresenham算法遍历射线经过的网格
        x0, y0 = point
        x1, y1 = pp_int
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1
        
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                grid_key = (x//grid_size, y//grid_size)
                if grid_key not in visited_grids:
                    visited_grids.add(grid_key)
                    # 检查当前网格内的线段
                    for seg_start, seg_end in spatial_grid.get(grid_key, []):
                        seg_start = tuple(seg_start)
                        seg_end = tuple(seg_end)
                        intersection = line_intersection(point, pp_int, seg_start, seg_end)
                        if intersection and is_point_on_segment(intersection, seg_start, seg_end):
                            if len(intersections) == 1 and intersection == intersections[0]:
                                continue
                            intersections.append(tuple(map(int, intersection)))
                            if len(intersections) >= 2:
                                break
                    if len(intersections) >= 2:
                        break
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                grid_key = (x//grid_size, y//grid_size)
                if grid_key not in visited_grids:
                    visited_grids.add(grid_key)
                    for seg_start, seg_end in spatial_grid.get(grid_key, []):
                        seg_start = tuple(seg_start)
                        seg_end = tuple(seg_end)
                        intersection = line_intersection(point, pp_int, seg_start, seg_end)
                        if intersection and is_point_on_segment(intersection, seg_start, seg_end):
                            if len(intersections) == 1 and intersection == intersections[0]:
                                continue
                            intersections.append(tuple(map(int, intersection)))
                            if len(intersections) >= 2:
                                break
                    # print(len(intersections))
                    if len(intersections) >= 2:
                        break
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

        # for cnt in spatial_grid.get(grid_key, []):
        #     pt1,pt2 = cnt
        #     cv2.line(a, pt1, pt2, (0, 255, 0), 2)
        
        # cv2.imwrite("a.jpg", a)

        # 5. 结果处理
        if len(intersections) >= 2:
            # 按距离垂足排序，取最近的两个交点
            intersections.sort(key=lambda p: (p[0]-pp_int[0])**2 + (p[1]-pp_int[1])**2)
            valid_intersections = intersections[:2]
            intersection_points.extend(valid_intersections)
            
            if draw:
                for p in valid_intersections:
                    cv2.circle(marked_image, p, 2, (0, 0, 255), -1)
        # break,

    return intersection_points, marked_image


def get_perpendicular_intersections2(image, equidistant_points, longest_edge2, contour, 
                                  range_start=0.4, range_end=0.6, 
                                  inner_color=(255, 0, 0), outer_color=(0, 0, 255)):
    """
    计算垂线与轮廓的交点，可调范围内绘制指定颜色
    
    参数:
        image: 绘制画布 (OpenCV格式)
        equidistant_points: 等距点列表 
        longest_edge2: 另一条长边坐标
        contour: 目标轮廓
        range_start: 范围起始比例 (默认0.4)
        range_end: 范围结束比例 (默认0.6)
        inner_color: 范围内交点颜色 (默认蓝色)
        outer_color: 范围外交点颜色 (默认红色)
    """
    intersection_points = []
    total_points = len(equidistant_points)
    start_idx = int(range_start * total_points)
    end_idx = int(range_end * total_points)

    for idx, point in enumerate(equidistant_points):
        # 计算垂足
        perpendicular_point = get_perpendicular_line(point, longest_edge2)
        if any(math.isnan(coord) for coord in perpendicular_point):
            continue

        # 查找有效交点
        num_inter = []
        for i in range(len(contour) - 1):
            seg_start, seg_end = tuple(contour[i][0]), tuple(contour[i+1][0])
            intersection = line_intersection(point, perpendicular_point, seg_start, seg_end)
            if intersection and is_point_on_segment(intersection, seg_start, seg_end):
                num_inter.append(intersection)

        # 处理找到的交点
        if len(num_inter) == 2:
            intersection_points.extend(num_inter)
            current_color = inner_color if start_idx <= idx < end_idx else outer_color
            for pt in num_inter:
                cv2.circle(image, tuple(map(int, pt)), 3, current_color, -1)
    
    return intersection_points, image

def get_average_of_smallest_x_percent(values, x):
    """
    计算列表中前 x% 最小值的平均值

    参数:
    - values: 一个数值列表
    - x: 百分比，表示选取前 x% 的最小值
    """
    if not values or x <= 0 or x > 100:
        raise ValueError("列表不能为空，且 x 必须在 (0, 100] 范围内")

    # 对列表进行排序
    sorted_values = sorted(values)

    # 计算前 x% 的元素数量
    num_elements = int(len(sorted_values) * (x / 100.0))

    # 如果 num_elements 为 0，说明 x% 太小，无法选取任何元素
    if num_elements == 0:
        raise ValueError("x% 太小，无法选取任何元素")

    # 选取前 x% 的元素
    smallest_x_percent = sorted_values[:num_elements]

    # 计算这些元素的平均值
    average_value = sum(smallest_x_percent) / len(smallest_x_percent)

    return average_value
def get_average_of_x_to_y_percent(values, x, y):
    """
    计算列表中第 x% 到 y% 区间内数值的平均值

    参数:
    - values: 一个数值列表
    - x: 百分比，表示区间起始点（包含）
    - y: 百分比，表示区间结束点（包含）
    """
    if not values or x <= 0 or y <= 0 or x >= 100 or y > 100 or x >= y:
        raise ValueError("列表不能为空，且 x 和 y 必须满足 0 < x < y <= 100")

    # 对列表进行排序
    sorted_values = sorted(values)

    # 计算 x% 和 y% 对应的索引范围
    start_index = int(len(sorted_values) * (x / 100.0))
    end_index = int(len(sorted_values) * (y / 100.0))

    # 如果 start_index 等于 end_index，说明区间太小，无法选取任何元素
    if start_index == end_index:
        raise ValueError("x% 和 y% 的区间太小，无法选取任何元素")

    # 提取 x% 到 y% 区间内的数值
    values_in_range = sorted_values[start_index:end_index]

    # 计算这些数值的平均值
    average_value = sum(values_in_range) / len(values_in_range)

    return average_value.item()


def needle_shank_detect(largest_contour, img):
    """
    探测针的针柄部分，并计算其长度。

    参数:
        largest_contour (ndarray): 图像中检测到的最大轮廓
        img (ndarray): 原始图像

    返回:
        Length_needle_shank (float): 针柄的长度
    """
    # 计算最小外接矩形，并获取其四个角点
    _, min_rect, _ = measure_diameter_using_min_rect(largest_contour)
    box_points = cv2.boxPoints(min_rect)

    # 获取矩形的四条边及其长度
    edges = []
    for i in range(4):
        pt1 = box_points[i]
        pt2 = box_points[(i + 1) % 4]
        length = np.linalg.norm(np.array(pt1) - np.array(pt2))
        edges.append((pt1, pt2, length))

    # 将边按长度排序，取出两条最长边和两条最短边
    edges.sort(key=lambda x: x[2], reverse=True)
    longest_edges = edges[:2]
    shortest_edges = edges[2:]

    # 计算轮廓上每个点到最长边的最小距离，并记录所属边
    distances = []
    for point in largest_contour:
        pt = list(point[0])
        min_dist = float('inf')
        nearest_edge = None
        for edge in longest_edges:
            start, end, _ = edge
            dist = point_to_line_distance(pt, start, end)
            if dist < min_dist:
                min_dist = dist
                nearest_edge = (start, end)
        distances.append((pt, min_dist, nearest_edge))

    # 初步根据距离分类为针尖或针柄（阈值2.0像素）
    needle_shank = []
    needle_tip = []
    for pt, dist, _ in distances:
        if dist > 1.5:
            needle_tip.append(pt)
        else:
            needle_shank.append(pt)

    # 判断哪一条短边更接近针柄区域
    best_shank_edge = None
    min_total_dist = float('inf')
    for edge in shortest_edges:
        start, end, _ = edge
        total_dist = sum(point_to_line_distance(p, start, end) for p in needle_shank)
        if total_dist < min_total_dist:
            min_total_dist = total_dist
            best_shank_edge = edge

    # 再次筛选部分误分类点（在阈值20像素内的也视为针柄）
    refined_tip = []
    start, end, _ = best_shank_edge
    for pt in needle_tip:
        dist = point_to_line_distance(pt, start, end)
        if 0 < dist < 20.0:
            needle_shank.append(pt)
        else:
            refined_tip.append(pt)

    # 画出针柄部分的最小外接矩形并标注
    D_needle_shank, Length_needle_shank = draw_min_rect_and_label_2(
        np.array(needle_shank), (0, 125, 255), img
    )

    return Length_needle_shank