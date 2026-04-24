import sys
import cv2
import RPi.GPIO as GPIO
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                            QVBoxLayout, QHBoxLayout, QSlider, QLabel)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

# GPIO设置
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)

class CameraApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 初始化GPIO为高电平
        GPIO.output(17, GPIO.HIGH)
        
        # 窗口设置
        self.setWindowTitle("USB相机控制")
        self.setGeometry(100, 100, 800, 600)
        
        # 主控件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 布局
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        # 相机显示标签
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.camera_label)
        
        # 曝光控制部分
        exposure_layout = QHBoxLayout()
        
        # 曝光标签
        exposure_label = QLabel("曝光时间(3-2047):")
        exposure_layout.addWidget(exposure_label)
        
        # 曝光值显示标签
        self.exposure_value_label = QLabel("100")
        exposure_layout.addWidget(self.exposure_value_label)
        
        # 曝光控制滑块
        self.exposure_slider = QSlider(Qt.Horizontal)
        self.exposure_slider.setMinimum(3)
        self.exposure_slider.setMaximum(2047)
        self.exposure_slider.setValue(100)
        self.exposure_slider.valueChanged.connect(self.update_exposure)
        exposure_layout.addWidget(self.exposure_slider)
        
        self.layout.addLayout(exposure_layout)
        
        # 亮度控制部分
        brightness_layout = QHBoxLayout()
        
        # 亮度标签
        brightness_label = QLabel("亮度(-64~64):")
        brightness_layout.addWidget(brightness_label)
        
        # 亮度值显示标签
        self.brightness_value_label = QLabel("0")
        brightness_layout.addWidget(self.brightness_value_label)
        
        # 亮度控制滑块
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setMinimum(-64)
        self.brightness_slider.setMaximum(64)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.update_brightness)
        brightness_layout.addWidget(self.brightness_slider)
        
        self.layout.addLayout(brightness_layout)
        
        # 初始化相机
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            print("无法打开相机")
            sys.exit(1)
            
        # 设置初始相机参数
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.update_exposure(self.exposure_slider.value())
        self.update_brightness(self.brightness_slider.value())
        
        # 定时器更新画面
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 约30fps
        
    def update_exposure(self, value):
        """更新相机曝光时间"""
        self.cap.set(cv2.CAP_PROP_EXPOSURE, value)
        self.exposure_value_label.setText(str(value))  # 更新显示值
        
    def update_brightness(self, value):
        """更新相机亮度"""
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)
        self.brightness_value_label.setText(str(value))  # 更新显示值
        
    def update_frame(self):
        """更新相机画面"""
        ret, frame = self.cap.read()
        if ret:
            # 转换颜色空间
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 转换为Qt图像
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # 显示图像
            pixmap = QPixmap.fromImage(q_img)
            self.camera_label.setPixmap(pixmap.scaled(
                self.camera_label.width(), 
                self.camera_label.height(),
                Qt.KeepAspectRatio
            ))
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止定时器
        self.timer.stop()
        
        # 释放相机资源
        if self.cap.isOpened():
            self.cap.release()
        
        # GPIO置低位
        GPIO.output(17, GPIO.LOW)
        GPIO.cleanup()
        
        # 调用父类关闭事件
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())