from PyQt5.QtWidgets import (QDialog, QWidget, QHBoxLayout, QLabel, QSizePolicy,
                            QSpacerItem, QVBoxLayout)
from PyQt5.QtCore import Qt

class CustomTitleBarDialog(QDialog):
    """
    自定义标题栏对话框基类
    使用方法：
    class MyDialog(CustomTitleBarDialog):
        def __init__(self, parent=None):
            super().__init__("窗口标题", parent)
            self.setup_ui()
            
        def setup_ui(self):
            # 添加你的内容布局
            pass
    """
    
    def __init__(self, title="窗口标题", parent=None):
        super().__init__(parent)
        self.title_text = title
        self.drag_pos = None
        
        # 初始化无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setWindowFlags(
        #     Qt.FramelessWindowHint | 
        #     Qt.WindowStaysOnTopHint | 
        #     Qt.Dialog  # 对话框类型，确保依赖父窗口
        # )
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 设置默认样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
        """)
        
        # 初始化标题栏
        self.init_title_bar()
        
        # 内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.main_layout.addWidget(self.content_widget)
        
        # 默认大小
        self.setMinimumSize(300, 200)
    
    def init_title_bar(self):
        """初始化自定义标题栏"""
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("""
            background-color: #3498db;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        """)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 标题
        self.title_label = QLabel(self.title_text)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(self.title_label)
        
        # 弹簧使按钮靠右
        title_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 关闭按钮
        # self.close_btn = QPushButton("×")
        # self.close_btn.setFixedSize(40, 40)
        # self.close_btn.setStyleSheet("""
        #     QPushButton {
        #         color: white;
        #         font-size: 30px;
        #         font-weight: bold;
        #         background: transparent;
        #         border: none;
        #         border-radius: 10px;
        #     }
        #     QPushButton:hover {
        #         background-color: #e74c3c;
        #     }
        # """)
        # self.close_btn.clicked.connect(self.close)
        # title_layout.addWidget(self.close_btn)
        
        self.main_layout.addWidget(self.title_bar)
    
    def set_title(self, title):
        """设置窗口标题"""
        self.title_text = title
        self.title_label.setText(title)
    
    # def mousePressEvent(self, event):
    #     """鼠标按下事件 - 实现窗口拖动"""
    #     if event.button() == Qt.LeftButton and event.y() <= self.title_bar.height():
    #         self.drag_pos = event.globalPos() - self.pos()
    #         event.accept()

    # def mouseMoveEvent(self, event):
    #     """鼠标移动事件 - 实现窗口拖动"""
    #     if event.buttons() == Qt.LeftButton and self.drag_pos:
    #         self.move(event.globalPos() - self.drag_pos)
    #         event.accept()

    # def mouseReleaseEvent(self, event):
    #     """鼠标释放事件"""
    #     self.drag_pos = None