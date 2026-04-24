import cv2
import numpy as np
from pathlib import Path
import time
import sys

sys.path.append(str(Path(__file__).parent.parent / 'function'))
from ttl import NeedleController

# 初始化摄像头
cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# 设置相机参数
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
cap.set(cv2.CAP_PROP_EXPOSURE, 53)
cap.set(cv2.CAP_PROP_BRIGHTNESS, -27)  # -27 + 64 = 37
cap.set(cv2.CAP_PROP_CONTRAST, 1)
cap.set(cv2.CAP_PROP_FOCUS, 321)

# 初始化LED控制器
try:
    controller = NeedleController()
    controller.connect()
    controller.set_led(255)  # LED亮度设置为255
    print("LED控制器连接成功，亮度设置为255")
except Exception as e:
    print(f"LED控制器连接失败: {e}")
    controller = None

# 创建显示窗口
cv2.namedWindow('Camera View', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Camera View', 1280, 320)

print("程序已启动，按 'c' 拍摄图片，按 'q' 退出")

while True:
    # 获取帧
    ret, frame = cap.read()
    if not ret:
        print("无法获取帧")
        break
    
    x, y, w, h=277,472,1270,315
    frame = frame[y:y+h, x:x+w]
    # 显示原始画面
    cv2.imshow('Camera View', frame)

    # 键盘控制
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        # 拍摄图片
        filename = f"capture_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(filename, frame)
        print(f"图片已保存: {filename}")

# 释放资源
cap.release()
cv2.destroyAllWindows()

# 关闭LED
if controller:
    controller.set_led(0)
    print("LED已关闭")