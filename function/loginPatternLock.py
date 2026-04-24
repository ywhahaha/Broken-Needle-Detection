import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import pyqtSignal
from function.get_resource_path import get_path

class PatternLockWidget(QWidget):
    login_success_signal = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 400)
        self.points = []
        self.selected_points = []
        self.current_pattern = []
        self.data = self.load_pattern()
        self.default_pattern, self.saved_pattern = self.data["login"]["default_pattern"], self.data["login"]["user_pattern"]
        self.mode = "normal"  # normal, setup, reset, change
        self.setup_ui()

        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.status_label = QLabel("绘制解锁图案")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 九宫格区域会通过paintEvent自动绘制
        
        # 按钮区域
        btn_layout = QVBoxLayout()
        
        self.reset_btn = QPushButton("重置手势")
        self.reset_btn.clicked.connect(self.reset_pattern)
        btn_layout.addWidget(self.reset_btn)
        
        self.change_btn = QPushButton("修改手势")
        self.change_btn.clicked.connect(self.change_pattern)
        btn_layout.addWidget(self.change_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # 初始化点位置
        self.init_points()
        
    def init_points(self):
        """初始化九宫格点的位置"""
        size = min(self.width(), self.height()) - 50
        start_x = (self.width() - size) // 2
        start_y = 50
        
        point_size = QSize(30, 30)
        spacing = size // 3
        
        self.points = []
        for row in range(3):
            for col in range(3):
                center = QPoint(
                    start_x + col * spacing + spacing // 2,
                    start_y + row * spacing + spacing // 2
                )
                self.points.append({
                    "center": center,
                    "radius": 15,
                    "selected": False,
                    "index": row * 3 + col
                })
    
    def paintEvent(self, event):
        """绘制九宫格和连线"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制点
        for point in self.points:
            if point["selected"]:
                painter.setPen(QPen(QColor(0, 150, 255), 2))
                painter.setBrush(QColor(200, 230, 255))
            else:
                painter.setPen(QPen(Qt.black, 2))
                painter.setBrush(Qt.white)
            
            painter.drawEllipse(point["center"], point["radius"], point["radius"])
        
        # 绘制连线
        if len(self.selected_points) > 1:
            pen = QPen(QColor(0, 150, 255), 3)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            for i in range(len(self.selected_points) - 1):
                start = self.selected_points[i]["center"]
                end = self.selected_points[i+1]["center"]
                painter.drawLine(start, end)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.check_point_selection(event.pos())
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        self.check_point_selection(event.pos())
        self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.handle_pattern_complete()
            self.clear_selection()
            self.update()
    
    def check_point_selection(self, pos):
        """检查是否选中了点"""
        for point in self.points:
            if (point["center"] - pos).manhattanLength() < point["radius"]:
                if not point["selected"]:
                    point["selected"] = True
                    self.selected_points.append(point)
                    self.current_pattern.append(point["index"])
                break
    
    def clear_selection(self):
        """清除选中状态"""
        for point in self.points:
            point["selected"] = False
        self.selected_points = []
        self.current_pattern = []
    
    def handle_pattern_complete(self):
        """处理图案完成后的逻辑"""
        if len(self.current_pattern) < 4:
            QMessageBox.warning(self, "提示", "至少连接4个点")
            return
            
        if self.mode == "normal":
            self.verify_pattern()
        elif self.mode == "setup":
            self.save_pattern()
        elif self.mode == "change":
            self.verify_for_change()
    
    def verify_pattern(self):
        """验证图案是否正确"""
        if not self.saved_pattern:
            QMessageBox.information(self, "提示", "未设置手势密码，请先设置")
            self.set_mode("setup")
            return
            
        if self.current_pattern == self.saved_pattern:
            QMessageBox.information(self, "成功", "解锁成功！")
            self.status_label.setText("解锁成功")
            self.login_success_signal.emit()
            # 解锁成功后关闭父窗口
            if self.parent() and isinstance(self.parent(), QWidget):
                self.parent().close()
            
        else:
            QMessageBox.warning(self, "失败", "手势密码错误")
            self.status_label.setText("手势密码错误")
    
    def save_pattern(self):
        """保存图案"""
        self.saved_pattern = self.current_pattern.copy()
        self.save_pattern_to_file()
        QMessageBox.information(self, "成功", "手势密码设置成功")
        self.status_label.setText("手势密码设置成功")
        self.set_mode("normal")
    
    def reset_pattern(self):
        """重置手势密码"""
        # self.set_mode("reset")
        self.data["login"]["current_pattern"] = self.default_pattern
        with open(get_path('config.json'), 'w') as f:
            json.dump(self.data, f, indent=4)
        self.status_label.setText("手势密码已恢复出厂设置")
    
    def change_pattern(self):
        """修改手势密码"""
        if not self.saved_pattern:
            QMessageBox.information(self, "提示", "未设置手势密码，请先设置")
            self.set_mode("setup")
            return
            
        self.set_mode("change")
        self.status_label.setText("请先验证原手势密码")
    
    def verify_for_change(self):
        """修改手势前的验证"""
        if self.current_pattern == self.saved_pattern:
            self.status_label.setText("请绘制新手势密码")
            self.mode = "setup"
        else:
            QMessageBox.warning(self, "失败", "原手势密码错误")
            self.status_label.setText("原手势密码错误")
            self.mode = "change"
    
    def set_mode(self, mode):
        """设置当前模式"""
        self.mode = mode
        if mode == "normal":
            self.status_label.setText("绘制解锁图案")
        elif mode == "setup":
            self.status_label.setText("请设置新手势密码")
        elif mode == "change":
            self.status_label.setText("请先验证原手势密码")
    
    def load_pattern(self):
        """从文件加载保存的图案"""
        try:
            with open(get_path('config.json'), 'r') as f:
               return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_pattern_to_file(self):
        """保存图案到文件"""
        self.data["login"]["current_pattern"] = self.saved_pattern
        with open(get_path('config.json'), 'w') as f:
            json.dump(self.data, f, indent=4)



            

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.pattern_lock = PatternLockWidget()
        layout.addWidget(self.pattern_lock)
        self.setLayout(layout)
        self.setWindowTitle("九宫格手势解锁")
        self.setFixedSize(320, 500)
