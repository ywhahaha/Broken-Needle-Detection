import os
from PyQt5.QtCore import QTimer, QPoint, Qt, QEvent
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QWidget


class ScreenSaver(QWidget):
    def __init__(self, parent=None, image_folder="figs/屏保", inactive_timeout=300, switch_interval=20):
        """
        改进版屏保窗口，解决多窗口环境下的置顶问题
        
        参数:
            parent: 父窗口
            image_folder: 屏保图片文件夹路径
            inactive_timeout: 无操作超时时间(秒)
            switch_interval: 图片切换间隔(秒)
        """
        super().__init__(parent)
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.Window | 
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        
        # 初始化配置
        self.image_folder = image_folder
        self.inactive_timeout = inactive_timeout
        self.switch_interval = switch_interval
        
        # 状态变量
        self.inactive_time = 0
        self.last_mouse_pos = QPoint()
        self.images = []
        self.current_image_index = -1
        
        # 初始化UI
        self._init_ui()
        self._load_images()
        self._init_timers()
        
        # 安装事件过滤器
        if parent:
            parent.installEventFilter(self)
    
    def _init_ui(self):
        """初始化UI组件"""
        self.setStyleSheet("background-color: black;")
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.hide()
    
    def _load_images(self):
        """加载屏保图片"""
        if os.path.exists(self.image_folder) and os.path.isdir(self.image_folder):
            for file in os.listdir(self.image_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    self.images.append(os.path.join(self.image_folder, file))
        
        if not self.images:
            print(f"警告: 未在 {self.image_folder} 中找到屏保图片")
    
    def _init_timers(self):
        """初始化定时器"""
        self.activity_timer = QTimer(self)
        self.activity_timer.timeout.connect(self._check_activity)
        self.activity_timer.start(1000)  # 每秒检查一次
        
        self.switch_timer = QTimer(self)
        self.switch_timer.timeout.connect(self._show_next_image)
    
    def _check_activity(self):
        """检查用户活动"""
        current_pos = self.cursor().pos()
        if current_pos != self.last_mouse_pos:
            self._reset_screensaver()
            self.last_mouse_pos = current_pos
        else:
            self.inactive_time += 1
            if self.inactive_time >= self.inactive_timeout and not self.isVisible():
                self._activate_screensaver()
    
    def _activate_screensaver(self):
        """激活屏保"""
        if not self.images:
            return
            
        # 确保屏保覆盖整个屏幕并置顶
        if self.parent():
            self.setGeometry(self.parent().geometry())
        else:
            self.showFullScreen()
        
        self._show_next_image()
        self.switch_timer.start(self.switch_interval * 1000)
        self.raise_()
        self.show()
    
    def _show_next_image(self):
        """显示下一张屏保图片"""
        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        pixmap = QPixmap(self.images[self.current_image_index])
        
        scaled_pixmap = pixmap.scaled(
            self.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.label.setPixmap(scaled_pixmap)
        self.label.resize(scaled_pixmap.size())
        self.label.move(
            (self.width() - scaled_pixmap.width()) // 2,
            (self.height() - scaled_pixmap.height()) // 2
        )
    
    def _reset_screensaver(self):
        """重置屏保状态"""
        self.inactive_time = 0
        self.switch_timer.stop()
        self.hide()
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于捕获父窗口及其子窗口的事件"""
        if event.type() in (QEvent.MouseMove, QEvent.KeyPress):
            self._reset_screensaver()
        return super().eventFilter(obj, event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        self._reset_screensaver()
        super().mouseMoveEvent(event)
    
    def keyPressEvent(self, event):
        """按键事件"""
        self._reset_screensaver()
        super().keyPressEvent(event)