import cv2
import numpy as np

# 读取图像，使用你的图像路径替换下面的路径
image_path = "capture_exp48_bright37.jpg"  # 替换为你的图像路径
image = cv2.imread(image_path)

if image is None:
    print(f"无法读取图像: {image_path}")
    exit()

# 转换为灰度图
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 创建窗口
cv2.namedWindow('Canny Edge Detector', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Canny Edge Detector', 1200, 800)

# 初始化参数
params = {
    'blur_size': 3,       # 高斯模糊核大小（必须为奇数）
    'threshold1': 50,     # 第一个阈值
    'threshold2': 150,    # 第二个阈值
    'aperture_size': 3,   # Sobel算子孔径大小（3, 5, 7）
    'L2gradient': False   # 是否使用更精确的L2范数计算梯度
}

# 计算最大滑动条值
MAX_BLUR_SIZE = 15  # 必须为奇数
MAX_THRESHOLD = 300
MAX_APERTURE_SIZE = 7  # 必须为3, 5, 7
APERTURE_VALUES = [3, 5, 7]

# 创建滑动条
def on_blur_size_change(value):
    # 确保值为奇数
    params['blur_size'] = max(1, value // 2 * 2 + 1)
    update_canny()

def on_threshold1_change(value):
    params['threshold1'] = value
    update_canny()

def on_threshold2_change(value):
    params['threshold2'] = value
    update_canny()

def on_aperture_size_change(value):
    # 映射到有效的孔径值
    if value < 0 or value >= len(APERTURE_VALUES):
        params['aperture_size'] = 3
    else:
        params['aperture_size'] = APERTURE_VALUES[value]
    update_canny()

def on_l2gradient_change(value):
    params['L2gradient'] = value != 0
    update_canny()

cv2.createTrackbar('Blur Size', 'Canny Edge Detector', params['blur_size'], MAX_BLUR_SIZE, on_blur_size_change)
cv2.createTrackbar('Threshold1', 'Canny Edge Detector', params['threshold1'], MAX_THRESHOLD, on_threshold1_change)
cv2.createTrackbar('Threshold2', 'Canny Edge Detector', params['threshold2'], MAX_THRESHOLD, on_threshold2_change)
cv2.createTrackbar('Aperture Size', 'Canny Edge Detector', APERTURE_VALUES.index(params['aperture_size']), len(APERTURE_VALUES) - 1, on_aperture_size_change)
cv2.createTrackbar('L2 Gradient', 'Canny Edge Detector', int(params['L2gradient']), 1, on_l2gradient_change)

# 添加帮助文本
help_text = [
    "Canny边缘检测参数调节:",
    "1. Blur Size: 高斯模糊核大小 (必须为奇数)",
    "2. Threshold1: 低阈值，控制边缘连接",
    "3. Threshold2: 高阈值，控制边缘检测",
    "4. Aperture Size: Sobel算子孔径大小 (3, 5, 7)",
    "5. L2 Gradient: 是否使用L2范数计算梯度",
    "",
    "操作说明:",
    "- 调整滑动条实时查看效果",
    "- 按 's' 保存当前边缘图像",
    "- 按 'q' 退出程序"
]

# 初始化结果图像
result = np.zeros_like(gray)

def update_canny():
    global result
    # 应用高斯模糊
    blurred = cv2.GaussianBlur(gray, (params['blur_size'], params['blur_size']), 0)
    
    # 应用Canny边缘检测
    edges = cv2.Canny(blurred, params['threshold1'], params['threshold2'], 
                     apertureSize=params['aperture_size'], 
                     L2gradient=params['L2gradient'])
    
    # 为了显示效果，将边缘转换为彩色
    result = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    # 添加原始图像作为参考
    h, w = image.shape[:2]
    if w > 800:
        # 如果图像太宽，缩小显示
        scale = 800 / w
        small_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
        small_edges = cv2.resize(result, (0, 0), fx=scale, fy=scale)
        # 创建对比显示
        combined = np.hstack([small_image, small_edges])
    else:
        combined = np.hstack([image, result])
    
    # 添加参数信息
    param_text = f"Blur: {params['blur_size']}x{params['blur_size']}, Thresholds: {params['threshold1']}-{params['threshold2']}, Aperture: {params['aperture_size']}, L2: {params['L2gradient']}"
    cv2.putText(combined, param_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # 添加帮助信息
    y_pos = 60
    for line in help_text:
        cv2.putText(combined, line, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        y_pos += 30
    
    cv2.imshow('Canny Edge Detector', combined)

# 显示初始结果
update_canny()

# 键盘控制
while True:
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        # 保存边缘图像
        filename = f"canny_edges_blur{params['blur_size']}_thresh{params['threshold1']}_{params['threshold2']}.jpg"
        cv2.imwrite(filename, result)
        print(f"已保存边缘图像: {filename}")

cv2.destroyAllWindows()    