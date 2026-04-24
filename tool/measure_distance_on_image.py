import cv2
import numpy as np
import math

# 全局变量存储点击的点和图像
points = []
img = None
img_copy = None

def mouse_callback(event, x, y, flags, param):
    global points, img, img_copy
    
    if event == cv2.EVENT_LBUTTONDOWN:
        # 记录点击的点
        points.append((x, y))
        print(f"点击坐标: ({x}, {y})")
        
        # 在图像上绘制点
        cv2.circle(img_copy, (x, y), 1, (0, 0, 255), -1)
        
        # 如果已经有两个点，计算并显示距离
        if len(points) == 2:
            # 计算两点之间的欧氏距离
            distance = math.sqrt((points[1][0] - points[0][0])**2 + (points[1][1] - points[0][1])**2)# * 57.9/1276
            
            # 在两点之间画线
            cv2.line(img_copy, points[0], points[1], (255, 0, 0), 2)
            
            # 显示距离文本（中点位置）
            mid_x = (points[0][0] + points[1][0]) // 2
            mid_y = (points[0][1] + points[1][1]) // 2
            cv2.putText(img_copy, f"{distance:.2f} pixels", (mid_x, mid_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
            
            print(f"两点距离: {distance:.2f} 像素")
            
            # 重置点列表以便下次测量
            points = []
        
        # 显示更新后的图像
        cv2.imshow("Image", img_copy)

def measure_distance_on_image(image_path):
    global img, img_copy
    
    # 读取图像
    img = cv2.imread(image_path)
    if img is None:
        print("无法加载图像，请检查路径")
        return
    
    # x, y, w, h = 449, 552, 1094, 187
    # img = img[y:y+h, x:x+w]
    # img=cv2.resize(img, (1920, 1080))
    img_copy = img.copy()
    
    # 创建窗口并设置鼠标回调
    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", mouse_callback)
    
    # 显示图像
    cv2.imshow("Image", img_copy)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# 使用示例
measure_distance_on_image("runs/segment/predict5/16_2.jpg")  # 替换为你的图片路径