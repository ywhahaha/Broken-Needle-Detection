import os
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap

class SlideshowWidget(QWidget):
    def __init__(self, image_folder="figs", parent=None):
        super().__init__(parent)
        self.image_folder = image_folder
        self.image_paths = []
        self.current_index = 0
        
        # 获取文件夹中的所有图片文件
        self.load_images()
        
        # 设置布局
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        
        # 创建图片显示标签
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        self.layout.addWidget(self.image_label)
        
        # 设置计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_image)
        
        # 显示第一张图片
        if self.image_paths:
            self.show_current_image()
        else:
            self.image_label.setText("未找到图片文件")
    
    def load_images(self):
        """加载指定文件夹中的图片"""
        if os.path.exists(self.image_folder) and os.path.isdir(self.image_folder):
            for file in os.listdir(self.image_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    self.image_paths.append(os.path.join(self.image_folder, file))
    
    def start(self, interval=3000):
        """开始轮播"""
        if self.image_paths:
            self.timer.start(interval)
    
    def stop(self):
        """停止轮播"""
        self.timer.stop()
    
    def next_image(self):
        """切换到下一张图片"""
        if self.image_paths:
            self.current_index = (self.current_index + 1) % len(self.image_paths)
            self.show_current_image()
    
    def show_current_image(self):
        """显示当前图片"""
        if self.image_paths and 0 <= self.current_index < len(self.image_paths):
            pixmap = QPixmap(self.image_paths[self.current_index])
            if not pixmap.isNull():
                # 保持图片原始比例，但不缩放窗口
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event):
        """窗口大小改变时重新缩放图片"""
        self.show_current_image()
        super().resizeEvent(event)