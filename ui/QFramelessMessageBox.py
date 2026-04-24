from PyQt5.QtWidgets import (QDialog, QLabel, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt

class FramelessMessageBox(QDialog):
    """树莓派专用无标题框消息框（完全自定义，无任何标题残留）"""
    Yes = 1
    No = 0
    Ok = 1

    def __init__(self, text="", icon=None, buttons=Ok, parent=None):
        super().__init__(parent)
        self.result = None  # 存储用户选择结果
        
        # 核心：无边框 + 无任务栏条目（避免被窗口管理器识别为普通窗口）
        self.setWindowFlags(
            Qt.FramelessWindowHint 
            | Qt.WindowStaysOnTopHint 
            | Qt.SubWindow  # 关键：标记为子窗口，避免窗口管理器添加装饰
        )
        
        # 固定样式（确保无默认边框）
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QLabel {
                color: #333;
                font-size: 14px;
                padding: 15px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                margin: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # 初始化UI
        self.init_ui(text, icon, buttons)
        
        # 窗口拖动功能
        self.drag_pos = None
        self.setFixedWidth(300)  # 固定宽度，适应树莓派屏幕

    def init_ui(self, text, icon, buttons):
        main_layout = QVBoxLayout(self)
        
        # 1. 内容区域（文本+图标）
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        
        # 图标（可选）
        if icon:
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(48, 48))
            content_layout.addWidget(icon_label, alignment=Qt.AlignTop)
        
        # 文本内容
        text_label = QLabel(text)
        text_label.setWordWrap(True)  # 自动换行
        content_layout.addWidget(text_label)
        
        main_layout.addWidget(content_widget)
        
        # 2. 按钮区域
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setSpacing(10)
        
        # 根据按钮类型添加按钮
        if buttons & FramelessMessageBox.Ok:
            ok_btn = QPushButton("确定")
            ok_btn.clicked.connect(lambda: self.set_result(FramelessMessageBox.Ok))
            btn_layout.addWidget(ok_btn)
        
        if buttons & FramelessMessageBox.Yes:
            yes_btn = QPushButton("是")
            yes_btn.clicked.connect(lambda: self.set_result(FramelessMessageBox.Yes))
            btn_layout.addWidget(yes_btn)
        
        if buttons & FramelessMessageBox.No:
            no_btn = QPushButton("否")
            no_btn.clicked.connect(lambda: self.set_result(FramelessMessageBox.No))
            btn_layout.addWidget(no_btn)
        
        main_layout.addWidget(btn_widget, alignment=Qt.AlignCenter)

    def set_result(self, result):
        self.result = result
        self.accept()

    # 拖动实现
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    # 静态方法：模拟QMessageBox使用方式
    @staticmethod
    def information(parent, text):
        msg = FramelessMessageBox(text=text, parent=parent)
        msg.exec_()
        return msg.result

    @staticmethod
    def question(parent, text):
        msg = FramelessMessageBox(
            text=text, 
            buttons=FramelessMessageBox.Yes | FramelessMessageBox.No,
            parent=parent
        )
        msg.exec_()
        return msg.result

    @staticmethod
    def warning(parent, text):
        # 可添加警告图标
        msg = FramelessMessageBox(text=text, parent=parent)
        msg.exec_()
        return msg.result