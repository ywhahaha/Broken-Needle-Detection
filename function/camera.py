import json
import time
import cv2
import numpy as np
from typing import Dict, Optional

from PyQt5.QtCore import (QThread, pyqtSignal, Qt, 
                         QWaitCondition, QMutex)
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QRadioButton, QButtonGroup, QHBoxLayout,
                            QPushButton, QMessageBox)
from function.ncnn_detect import NeedleDetection
from function.ttl import NeedleController
from ultralytics import YOLO
from function.get_resource_path import get_path
from function.read_config import ConfigReader
from function.show_info_message import show_info_message
import subprocess
# import debugpy
# import RPi.GPIO as GPIO

class NeedleSelectionDialog(QDialog):
    """机针型号选择对话框"""
    def __init__(self, matches: Dict[str, Dict], parent=None):
        super().__init__(parent)
        self.setParent(parent)
        self.matches = matches
        self.selected_id = None
        self.id_mapping = {}  # 映射按钮ID到原始ID
        
        self._init_ui()
        self._setup_layout()

        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无标题栏
            Qt.WindowStaysOnTopHint |  # 保持在顶层
            Qt.WindowFullscreenButtonHint  # 支持全屏
        )
        self.setGeometry(self.parent().geometry())
        
    def _init_ui(self):
        # self.setWindowTitle("机针型号选择")
        self.setStyleSheet("""
            /* 1. 主窗口背景：避免底层透明穿透 */
            QDialog {
                background-color: #f8f8f8; /* 与界面主色调匹配，覆盖透明 */
            }
        """)
        
    def _setup_layout(self):
        layout = QVBoxLayout()
        
        # 单选按钮组
        self.button_group = QButtonGroup(self)
        for needle_id, needle_data in self.matches.items():
            self._add_needle_option(layout, needle_id, needle_data)
        
        # 按钮行（确认 + 取消）
        button_layout = QHBoxLayout()
        
        confirm_btn = QPushButton("确认选择")
        confirm_btn.setStyleSheet("""
            QPushButton {
                min-height: 100px;
                font-size: 25px;  /* 设置字体大小 */
                font-weight: bold;  /* 可选：设置字体粗细 */
            }
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        button_layout.addWidget(confirm_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                min-height: 100px;
                font-size: 25px;  /* 设置字体大小 */
                font-weight: bold;  /* 可选：设置字体粗细 */
            }
        """)
        cancel_btn.clicked.connect(self.reject)  # 触发 rejected() 信号
        button_layout.addWidget(cancel_btn)
    
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _add_needle_option(self, layout: QVBoxLayout, 
                         needle_id: str, needle_data: Dict):
        size = needle_data['size']
        text = (
            f"型号ID: {needle_id} "
        )
        radio = QRadioButton(text)
        radio.setStyleSheet("""
            QRadioButton {
                min-height: 50px;  /* 最小高度 */
                font-size: 25px;   /* 字体大小 */
            }
            QRadioButton::indicator {
                width: 40px;       /* 单选按钮指示器大小 */
                height: 40px;
            }
        """)
        btn_id = len(self.button_group.buttons()) + 1
        self.button_group.addButton(radio, btn_id)
        self.id_mapping[btn_id] = needle_id  # 保存原始ID
        layout.addWidget(radio)
    
    def _on_confirm(self):
        btn_id = self.button_group.checkedId()
        if btn_id == -1:
            show_info_message(self, "警告", "请选择一种型号")
        else:
            self.selected_id = self.id_mapping[btn_id]
            self.accept()



class CameraThread(QThread):
    """相机处理线程"""
    frame_signal = pyqtSignal(object)
    selection_needed = pyqtSignal(dict)
    inventory_warning = pyqtSignal(str)  # 新增库存警告信号
    measurement_complete = pyqtSignal(dict)
    connection_lost = pyqtSignal()
    update_warehouse_cards = pyqtSignal()
    show_message_signal = pyqtSignal(str)

    # 配置常量
    PROCESS_INTERVAL = 1  # 帧处理间隔
    STABLE_THRESHOLD = 10  # 光流稳定阈值
    COOLDOWN_TIME = 4  # 检测冷却时间(秒)
    RECONNECT_MAX_ATTEMPTS = 10
    RECONNECT_INTERVAL = 2

    # # 外部传入变量
    # isManualDetect = False
    
    def __init__(self, parent=None):
        super().__init__()
        self.time = time.time()
        self.handle_new_needle = False
        self.needle_size = None
        self.isManualDetect = False
        self.running = True
        self.tempstop = False #当进入录入机针面板时，则临时停止检测断针
        self.parent = parent

        self._init_camera()
        self._init_sync_primitives()
        self._init_read_config()
        self._init_state_variables()
        self._init_device()
        self._load_config()
        self._load_model()

        
    def _init_camera(self):
        # 配置相机常量
        self.light_on_exposure_value = 53#48
        self.light_off_exposure_value = 500
        self.light_on_brightness_value = -27
        self.light_off_brightness_value = 64
        self.light_on_frame_width = 3840
        self.light_off_frame_width = 1920
        self.light_on_frame_height = 2160
        self.light_off_frame_height = 1080
        self.light_on_Contrast = 1
        self.light_off_Contrast = 1
        self.focus_value = 321

        self.camera_connect()
    
    def camera_connect(self):  
        cameraisOpened = False
        global GLOBAL_VAR
        self.cap = cv2.VideoCapture(self.get_pc_camera_devices(), cv2.CAP_V4L2)
        if self.cap.isOpened() and self.running:
            cameraisOpened = True
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # 关闭自动对焦
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # 关闭自动曝光
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)  # 关闭自动曝光
            self.cap.set(cv2.CAP_PROP_FOCUS, self.focus_value)
            self.cap.set(cv2.CAP_PROP_EXPOSURE, self.light_off_exposure_value)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.light_off_frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.light_off_frame_height)
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.light_off_brightness_value)
            self.cap.set(cv2.CAP_PROP_CONTRAST, self.light_on_Contrast)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

            #使设置稳定
            for _ in range(1):
                self.cap.read()

            return cameraisOpened
        
        elif self.cap.isOpened() and not self.running:
            cameraisOpened = True
            self.isRunning = True
            self.cap.release()

            return cameraisOpened

        return cameraisOpened

    def get_pc_camera_devices(self):
        """获取PC Camera的所有设备接口"""
        try:
            result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                                capture_output=True, text=True, check=True)
            
            lines = result.stdout.split('\n')
            
            for i, line in enumerate(lines):
                if 'PC Camera' in line:  # 匹配你的相机名称
                    # 找到相机名称，获取下面的设备接口
                    devices = []
                    j = i + 1
                    while j < len(lines) and lines[j].strip().startswith('/dev/'):
                        devices.append(lines[j].strip())
                        j += 1
                    return devices[0]
                    
        except Exception as e:
            print(f"获取相机信息失败: {e}")
        
        return "/dev/video0"
        
    def _init_sync_primitives(self):
        """初始化线程同步原语"""
        self.wait_condition = QWaitCondition()
        self.mutex = QMutex()
        self.user_selection = None
        
    def _init_state_variables(self):
        """初始化状态变量"""
        self.prev_frame = None
        self.moving = False
        self.frame_count = 0
        self.stable_frame_count = 0
        self.last_detection_time = 0
        self.processed_frame_count = 0

        self.high_light = self.config.high_light
        self.low_light = self.config.low_light
        self.conf = self.config.conf
        self.iou = self.config.iou
        self.save_results = self.config.save_results
        self.show_boxes = self.config.show_boxes
        self.save_postprocess_image = self.config.save_postprocess_image
        self.ROI = self.config.roi
        self.show_details = self.config.show_details

    def _init_read_config(self):
        self.config = ConfigReader('default.yaml')

    def _init_device(self):
        """初始化GPIO变量"""
        # GPIO.setmode(GPIO.BCM)

        # # 光源GPIO口设置
        # self.gpio_light_pin = 17
        # self.gpio_light_state_on = GPIO.HIGH
        # self.gpio_light_state_off = GPIO.LOW
        # GPIO.setup(self.gpio_light_pin, GPIO.OUT)
        # GPIO.output(self.gpio_light_pin, self.gpio_light_state_off)

        self.controller = NeedleController()
        res = self.controller.connect()
        self.controller.set_led(self.low_light)

        if res:
            self.SCM_Connection = True
        
    def _load_config(self):
        """加载配置文件"""
        self.inventory_info = {}
        self.camera_info = {}
        self.setting_info = {}
        try:
            with open(get_path('config.json'), 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            for item in config.get('repertory', []):
                model = item['model']
                self.inventory_info[model] = {
                    "bin_num": item['bin_num'],
                    'quantity': item['quantity'],
                    'size': {
                        'total_length': item['needle_total_length'],
                        'shank_length': item['needle_handle_length'],
                        'shank_diameter': item['needle_handle_diameter'],
                        'shaft_diameter': item['needle_middle_diameter']
                    }
                }
                
            self.camera_info = config.get('camera', [])
            self.setting_info = config.get('setting', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载配置文件错误: {str(e)}")

    def _load_model(self):
        model = YOLO(get_path("weight/best-seg_ncnn_model"))

        self.detector = NeedleDetection(
            model=model,
            conf_threshold=self.conf,
            iou_threshold=self.iou
        )

    def _update_inventory(self, needle_id: str) -> bool:
        """更新库存数量，成功返回True，库存不足返回False"""
        try:
            with open(get_path("config.json"), 'r+', encoding='utf-8') as f:
                config = json.load(f)
                
                # 查找并更新对应型号的库存
                for item in config['repertory']:
                    if item['model'] == needle_id:
                        if item['quantity'] <= 0:
                            return False
                        item['quantity'] -= 1
                        break
                else:
                    return False
                    
                # 写回文件
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()
                
            # 更新内存中的库存信息
            self._load_config()
            return True
        
        except Exception as e:
            print(f"更新库存失败: {str(e)}")
            return False

    def run(self):
        # if debugpy.is_client_connected():
        #     debugpy.debug_this_thread()
        # debugpy.debug_this_thread()
        """主线程循环"""
        while self.running:
            if not self.handle_new_needle:
                current = time.time()
                ret, frame = self.cap.read()
                if not ret:
                    self.connection_lost.emit()
                    print("相机断开连接，尝试重新连接...")
                    self.running = False
                    if self.cap is None:
                        print("无法初始化相机")
                    continue
                
                if self.tempstop:
                    time.sleep(0.1)
                    continue

                roi_frame = frame[
                    self.ROI[1]:self.ROI[1] + self.ROI[3],
                    self.ROI[0]:self.ROI[0] + self.ROI[2]
                ].copy()
                    
                self.frame_count += 1
                # if not self.handle_new_needle:
                self._process_frame(roi_frame)
                self.frame_signal.emit(roi_frame)
                time.sleep(0.1)

                # if self.show_details: print(time.time() - current)

        self._release_camera()
                
    
    def _process_frame(self, frame):
        """处理每一帧图像"""
        if self.frame_count % self.PROCESS_INTERVAL != 0:
            return
            
        current_time = time.time()
        if (current_time - self.last_detection_time) < self.COOLDOWN_TIME or self.is_recycle_motor_running(self.controller):
            self.prev_frame = None
            self.processed_frame_count = 0
            return
        
        # 只有处理到第四帧及以后才执行运动检测
        if self.processed_frame_count < 3:
            self.processed_frame_count += 1
            self.prev_frame = frame
            return
            
        self._handle_motion_detection(frame)
        # self.detect_object_by_gray_diff(frame)
        self.prev_frame = frame
    
    def _handle_motion_detection(self, frame):
        """处理运动检测逻辑"""
        if self.isManualDetect:
            self._handle_stable_state(frame)
        elif not self.moving:
            if self._detect_motion_by_gray_diff(self.prev_frame, frame):
                self.moving = True         
        else:
            if not self._detect_motion_by_gray_diff(self.prev_frame, frame):
                if self.stable_frame_count >= self.STABLE_THRESHOLD:
                    # print("光流已稳定，执行后续步骤")
                    self._handle_stable_state(frame)
                else:
                    self.stable_frame_count += 1
    
    def detect_motion_by_optical_flow(self, prev_frame, curr_frame) -> bool:
        """使用光流法检测运动"""
        # 缩放图像提高处理速度
        scale_factor = 0.2
        prev_frame = cv2.resize(prev_frame, None, fx=scale_factor, fy=scale_factor)
        curr_frame = cv2.resize(curr_frame, None, fx=scale_factor, fy=scale_factor)
        
        # 转换为灰度图
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        # 计算光流
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        
        # 计算运动幅度
        magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        is_moving = np.mean(magnitude) > 0.1  # 运动阈值
        # print(np.mean(magnitude))
        if is_moving:
            self.stable_frame_count = 0
        else:
            self.stable_frame_count += 1
            
        return is_moving

    def _detect_motion_by_gray_diff(self, prev_frame, curr_frame, threshold=5) -> bool:
        """使用平均灰度检测运动"""
        # 缩放图像提高处理速度
        scale_factor = 0.2
        prev_frame = cv2.resize(prev_frame, None, fx=scale_factor, fy=scale_factor)
        curr_frame = cv2.resize(curr_frame, None, fx=scale_factor, fy=scale_factor)
        
        # 转换为灰度图
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        # 计算两帧灰度的绝对差值
        gray_diff = cv2.absdiff(prev_gray, curr_gray)
        
        # 计算平均差值（所有像素的平均差异）
        avg_diff = np.mean(gray_diff)
        
        # 判断平均差值是否超过阈值
        is_moving = avg_diff > threshold # 运动阈值
        # print(avg_diff)

        if is_moving:
            self.stable_frame_count = 0
        else:
            self.stable_frame_count += 1

        return is_moving
    
    def _handle_stable_state(self, frame):
        print("开始检测断针")
        """处理稳定状态下的逻辑"""
        self._load_config() # 重新载入
        
        # if not self.detect_object_by_gray_diff(frame):
        #     return
            
        self._process_needle_detection(frame)

        self.moving = False
        self.isManualDetect = False
    
    def _check_roi_illumination(self, frame) -> bool:
        """检查ROI区域照明是否充足"""
        # roi_frame = frame[
        #     self.ROI[1]:self.ROI[1] + self.ROI[3],
        #     self.ROI[0]:self.ROI[0] + self.ROI[2]
        # ]
        # gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        # print(np.mean(gray))
        # return np.mean(gray) > 50  # 灰度阈值
        return True

    def detect_object_by_gray_diff(self, frame, block_size=32, threshold=20):
        """
        通过图像不同区域的灰度差异检测是否存在物体
        
        参数:
            block_size: 图像分块大小，用于计算区域间灰度差
            threshold: 灰度差异阈值，超过此值判定为存在物体
            
        返回:
            bool: 是否检测到物体
            float: 最大灰度差异值
            numpy.ndarray: 标记差异区域的图像（便于可视化）
        """

        roi_frame = frame[
            self.ROI[1]:self.ROI[1] + self.ROI[3],
            self.ROI[0]:self.ROI[0] + self.ROI[2]
        ]

        # 缩放图像提高处理速度
        scale_factor = 0.4
        roi_frame = cv2.resize(roi_frame, None, fx=scale_factor, fy=scale_factor)

        # 读取图像并转换为灰度图
        gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        # cv2.imwrite("gray.png",gray)
        h, w = gray.shape
        
        # 对图像进行分块
        max_diff = 0
        diff_map = np.zeros_like(gray, dtype=np.uint8)
        
        # 遍历图像块
        for i in range(0, h, block_size):
            for j in range(0, w, block_size):
                # 计算当前块的边界
                i2 = min(i + block_size, h)
                j2 = min(j + block_size, w)
                block = gray[i:i2, j:j2]
                block_mean = np.mean(block)
                
                # 计算与相邻块的灰度差（右侧和下方）
                if j2 < w:  # 右侧有相邻块
                    right_block = gray[i:i2, j2:min(j2 + block_size, w)]
                    right_mean = np.mean(right_block)
                    diff = abs(block_mean - right_mean)
                    if diff > max_diff:
                        max_diff = diff
                    if diff > threshold:
                        diff_map[i:i2, j:j2] = 255
                        diff_map[i:i2, j2:min(j2 + block_size, w)] = 255
                
                if i2 < h:  # 下方有相邻块
                    bottom_block = gray[i2:min(i2 + block_size, h), j:j2]
                    bottom_mean = np.mean(bottom_block)
                    diff = abs(block_mean - bottom_mean)
                    if diff > max_diff:
                        max_diff = diff
                    if diff > threshold:
                        diff_map[i:i2, j:j2] = 255
                        diff_map[i2:min(i2 + block_size, h), j:j2] = 255
        
        # 标记差异区域到原图
        # result_img = frame.copy()
        # result_img[diff_map > 0] = [0, 0, 255]  # 差异区域标记为红色
        # print(max_diff)
        
        return max_diff > threshold#, max_diff, result_img
    
    def _process_needle_detection(self, frame):
        """处理机针检测逻辑"""
        # 设置低曝光获取清晰图像
        # GPIO.output(self.gpio_light_pin, self.gpio_light_state_on)
        self.controller.set_led(self.high_light)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, self.light_on_exposure_value)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.light_on_brightness_value)
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.light_on_frame_width)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.light_on_frame_height)

        for _ in range(2):  # 跳过几帧让设置生效
            self.cap.read()
        # time.sleep(1)
        ret, low_exposure_frame = self.cap.read()
        # low_exposure_frame = cv2.imread("low_exposure_frame_1764229485.7222114.png")
        if not ret:
            return
        low_exposure_frame = low_exposure_frame[self.ROI[1]:self.ROI[1]+self.ROI[3], self.ROI[0]:self.ROI[0]+self.ROI[2]]
        
        # 恢复设置
        # GPIO.output(self.gpio_light_pin, self.gpio_light_state_off)
        self.controller.set_led(self.low_light)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, self.light_off_exposure_value)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.light_off_brightness_value)
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.light_off_frame_width)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.light_off_frame_height)
        self.last_detection_time = time.time()

        for _ in range(2):  # 跳过几帧让设置生效
            self.cap.read()
        # 检测机针
        # cv2.imwrite(f"low_exposure_frame_{time.time()}.png",low_exposure_frame)
        # image_path = "low_exposure_frame_1764229485.7222114.png"  # 替换成你自己的图像路径
        # low_exposure_frame = cv2.imread(image_path)

        if not self.handle_new_needle:
            try:
                results = self.detector.predict(low_exposure_frame.copy(), save_results=self.save_results, show_boxes=self.show_boxes)
                needle_info = self.detector.analyze_results(results)
                self.detector.visualize_results(results, save_postprocess_image=self.save_postprocess_image)
                if self.show_details: print(needle_info)
                # needle_info = 2,1,1,1,1
                # if needle_info[0] == 0:
                #     print("未检测到机针")
                #     return
                # elif needle_info[0] == 1:
                #     results = self.detector.predict(low_exposure_frame)
                #     needle_info = self.detector.analyze_results(results)
                # print(needle_info)
                selected_id = self._handle_needle_selection(needle_info[1:])
        
                if selected_id:
                    if self._update_inventory(selected_id):
                        needle_data = self.inventory_info.get(selected_id, {})
                        print(f"成功选择型号 {selected_id}，{needle_data['bin_num']}当前库存: {needle_data.get('quantity', 'N/A')}")
                        
                        self.controller.drive_motor(slot=0, is_recycle=True)
                        self.controller.drive_motor(slot=int(needle_data['bin_num']))
                        self.update_warehouse_cards.emit()
                        print(f"已经释放机针，已经回收机针")
                    else:
                        self.inventory_warning.emit(f"型号 {selected_id} 库存不足或更新失败！")
                # else:
                #     self.show_message_signal.emit("未找到匹配型号")
                #     print("未找到匹配型号")
            
            except Exception as e:
                print("error" + str(e))
        else:
            try:
                results = self.detector.predict(low_exposure_frame)
                _, total_length, shank_length, shank_diameter, shaft_diameter = self.detector.analyze_results(results)
                self.detector.visualize_results(results, save_postprocess_image=self.save_postprocess_image)
                if self.show_details: print(self.needle_size)

                self.needle_size = {
                    'total_length': total_length,
                    'shank_length': shank_length,
                    'shank_diameter': shank_diameter,
                    'shaft_diameter': shaft_diameter
                }
        
            except Exception as e:
                print(str(e))
                self.needle_size = {
                    'total_length': 0,
                    'shank_length': 0,
                    'shank_diameter': 0,
                    'shaft_diameter': 0
                }
            
    
    def _handle_needle_selection(self, needle_info) -> Optional[str]:
        """处理机针选择流程"""
        matches = self._find_matching_needles(needle_info)
        
        if not matches:
            return None
        elif len(matches) == 1:
            return next(iter(matches.keys()))
        else:
            return self._wait_for_user_selection(matches)
    
    def _find_matching_needles(self, needle_info) -> Dict[str, Dict]:
        """查找匹配的机针型号"""
        broken_total, shank_len, shank_dia, shaft_dia = needle_info
        matches = {}
        
        for needle_id, needle_data in self.inventory_info.items():
            size = needle_data['size']
            
            # 尺寸匹配条件
            length_ok = abs(size['shank_length'] - shank_len) <= 1
            diameter_ok = abs(size['shank_diameter'] - shank_dia) <= 0.1
            shaft_ok = abs(size['shaft_diameter'] - shaft_dia) <= 0.07
            size_ok = broken_total >= (self.setting_info["completeness_threshold"] * size['total_length'])
            
            if length_ok and diameter_ok and shaft_ok and size_ok:
                matches[needle_id] = needle_data
            elif length_ok and diameter_ok and shaft_ok and not size_ok:
                self.show_message_signal.emit(f"断针不完整")
                print("断针不完整")

                return matches
        
        if len(matches) == 0:
            self.show_message_signal.emit("未找到匹配型号")
            print("未找到匹配型号")

        return matches
        
    
    def _wait_for_user_selection(self, matches) -> Optional[str]:
        """等待用户选择型号"""
        self.mutex.lock()
        try:
            self.user_selection = None
            self.selection_needed.emit(matches)
            self.wait_condition.wait(self.mutex)
            return self.user_selection
        finally:
            self.mutex.unlock()

    
    def handle_measurement_request(self):
        """处理新机针请求"""
        while True:
            if not self.moving:
                self.handle_new_needle = True
                self._handle_stable_state(self.prev_frame)
                self.handle_new_needle = False
                self.measurement_complete.emit(self.needle_size)
                break
            
            time.sleep(0.05)
    
    @property
    def setting_manual_detect_bool(self):
        self.isManualDetect = True

    def is_recycle_motor_running(self, controller):
        # status = controller.get_status()
        status = False
        return status.get('recycle_motor_running') if status else False

    
    def stop(self):
        self.running = False
        self.controller.set_led(0)
        self.wait()
        
    def _release_camera(self):
        """释放相机资源"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
                

                