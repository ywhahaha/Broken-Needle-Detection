import cv2
import numpy as np
from pathlib import Path
import importlib.util
import sys
import time

sys.path.append(str(Path(__file__).parent.parent / 'function'))

from ttl import NeedleController


def process_complete_img(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    gradient = cv2.morphologyEx(blurred, cv2.MORPH_GRADIENT, kernel)
    _, thresholded = cv2.threshold(gradient, 10, 255, cv2.THRESH_BINARY)

    # 查找轮廓
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 从所有轮廓中选择一个合适的针体轮廓
    selected_contour = None
    area_selected_contour=0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        """
        根据实际需要调整针的面积范围
        """
        if 1000 < area< 35000 :
            if(area>area_selected_contour):
                selected_contour = cnt
                area_selected_contour=cv2.contourArea(cnt)
                # print(area_selected_contour)
                # break

    if selected_contour is None:
        return image, thresholded

    # 绘制最小外接矩形
    cv2.drawContours(image, [selected_contour], -1, (0, 255, 0), 2)

    return image, thresholded

def process_broken_img(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    gradient = cv2.morphologyEx(blurred, cv2.MORPH_GRADIENT, kernel)
    _, thresholded = cv2.threshold(gradient, 5, 255, cv2.THRESH_BINARY)

    kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    eroded = cv2.erode(thresholded, kernel_rect, iterations=1)

    # 查找轮廓
    contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    filtered_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 400 <= area <= 60000:  # 面积在100到100000之间的轮廓
            filtered_contours.append(cnt)
            area_selected_contour=cv2.contourArea(cnt)
            # print(area_selected_contour)
            # 绘制轮廓（绿色，线宽2）
            cv2.drawContours(image, [cnt], -1, (0, 255, 0), 1)

    return image, thresholded


# 初始化摄像头
cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# 创建调试窗口
cv2.namedWindow('Camera Debugger', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Camera Debugger', 1920, 1080)

# 初始化参数
params = {
    'exposure': 53,
    'brightness': -27,  # 中间值为0，范围是-64~64
    'contrast': 1,
    'focus': 321,
    "gray_threshold":161
}

# 设置相机初始参数
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # 1=手动曝光，3=自动曝光
cap.set(cv2.CAP_PROP_EXPOSURE, params['exposure'])
# 映射亮度值到OpenCV范围（0~128）
cap.set(cv2.CAP_PROP_BRIGHTNESS, params['brightness'] + 64)
cap.set(cv2.CAP_PROP_CONTRAST, params['contrast'])

controller = NeedleController()
controller.connect()
controller.set_led(255)
# controller.send_command('light_set', 50)

# 创建滑动条回调函数
def nothing(x):
    pass

# 创建控制滑动条
cv2.createTrackbar('Exposure', 'Camera Debugger', params['exposure'], 1000, nothing)
# 亮度滑动条范围设置为0~128，对应实际值-64~64
cv2.createTrackbar('Brightness', 'Camera Debugger', params['brightness'] + 64, 128, nothing)
cv2.createTrackbar('Contrast', 'Camera Debugger', params['contrast'], 95, nothing)
cv2.createTrackbar('Focus', 'Camera Debugger', params['focus'], 1023, nothing)
cv2.createTrackbar('gray_threshold', 'Camera Debugger', params['gray_threshold'], 255, nothing)

# 添加文字说明
font = cv2.FONT_HERSHEY_SIMPLEX
help_text = [
    "按键说明:",
    "1. 调整滑动条改变参数",
    "2. 按 's' 保存当前帧",
    "3. 按 'q' 退出程序"
]

while True:
    # 获取滑动条当前值
    params['exposure'] = cv2.getTrackbarPos('Exposure', 'Camera Debugger')
    # 转换亮度值：0~128 → -64~64
    brightness_raw = cv2.getTrackbarPos('Brightness', 'Camera Debugger')
    params['brightness'] = brightness_raw - 64
    params['contrast'] = cv2.getTrackbarPos('Contrast', 'Camera Debugger')
    params['focus'] = cv2.getTrackbarPos('Focus', 'Camera Debugger')
    params['gray_threshold'] = cv2.getTrackbarPos('gray_threshold', 'Camera Debugger')

    # 应用参数到摄像头
    cap.set(cv2.CAP_PROP_EXPOSURE, params['exposure'])
    cap.set(cv2.CAP_PROP_BRIGHTNESS, params['brightness'])  # 使用原始值（0~128）设置
    cap.set(cv2.CAP_PROP_CONTRAST, params['contrast'])
    cap.set(cv2.CAP_PROP_FOCUS, params['focus'])

    # 获取并显示帧
    ret, frame = cap.read()
    if not ret:
        print("无法获取帧")
        break

    # x, y, w, h = 1302, 1022, 1689,259
    x, y, w, h=277,472,1270,315
    frame = frame[y:y+h, x:x+w]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # print(np.mean(gray))
    

    cv2.imwrite("frame_whole.jpg",frame)
    processed_img, thresholded = process_broken_img(frame)

    # 显示帮助信息
    # y_pos = 30
    # for line in help_text:
    #     cv2.putText(frame, line, (10, y_pos), font, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
    #     y_pos += 30

    # 显示当前参数值
    # param_text = f"Exposure: {params['exposure']} | Brightness: {params['brightness']} | Contrast: {params['contrast']} | Focus: {params['focus']}"
    # cv2.putText(frame, param_text, (10, y_pos+60), font, 0.6, (0, 255, 255), 1, cv2.LINE_AA)

    result = cv2.vconcat([processed_img, cv2.cvtColor(thresholded, cv2.COLOR_GRAY2BGR)])
    
    cv2.imshow('Camera Debugger', result)

    # 键盘控制
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        filename = f"capture_{time.time()}.jpg"
        cv2.imwrite(filename, frame)
        print(f"已保存: {filename}")

# 释放资源
cap.release()
cv2.destroyAllWindows()    
controller.set_led(0)