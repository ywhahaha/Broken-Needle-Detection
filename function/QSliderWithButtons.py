from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSlider, QPushButton, QLabel
from PyQt5.QtCore import Qt

__all__ = ['SliderWithButtons', 'value']

class SliderWithButtons(QWidget):
    def __init__(self, param_name="参数", min_val=0, max_val=100, default_val=50):
        super().__init__()
        
        # 初始化参数
        self.min_val = min_val
        self.max_val = max_val
        self.current_val = default_val
        
        # 创建控件
        self.label_param = QLabel(param_name)  # 参数名称（左侧）
        self.btn_decrease = QPushButton("-")   # 减号按钮
        self.slider = QSlider(Qt.Horizontal)   # 水平滑动条
        self.btn_increase = QPushButton("+")   # 加号按钮
        self.label_value = QLabel(str(default_val))  # 当前值（右侧）
        
        # 设置滑动条范围
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default_val)
        
        # 连接信号槽
        self.btn_decrease.clicked.connect(self.decrease_value)
        self.btn_increase.clicked.connect(self.increase_value)
        self.slider.valueChanged.connect(self.update_value)
        
        # 设置布局
        layout = QHBoxLayout()
        layout.addWidget(self.label_param)
        layout.addWidget(self.btn_decrease)
        layout.addWidget(self.slider)
        layout.addWidget(self.btn_increase)
        layout.addWidget(self.label_value)
        self.setLayout(layout)
        
        # 样式设置（可选）
        # 样式设置（可自定义）
        self.setStyleSheet("""
            /* 滑动条样式 */
            QSlider {
                min-width: 120px;
                height: 60px;
            }
                           
            QSlider::groove:horizontal {
                height: 20px;
                background: #e0e0e0;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
                background: #4285F4;
                border: 1px solid #3367D6;
            }
            
            QSlider::handle:horizontal:hover {
                background: #3367D6;
            }
            
            QSlider::sub-page:horizontal {
                background: #4285F4;
                border-radius: 3px;
            }
            
            /* 标签样式 */
            QLabel {
                font-size: 50px;
                min-width: 60px;
                color: #333333;
            }
            
            /* 按钮样式 */
            QPushButton {
                font-size: 50px;
                width: 60px;
                height: 60px;
                border-radius: 3px;
                background: #f1f1f1;
                border: 1px solid #ddd;
            }
            
            QPushButton:hover {
                background: #e7e7e7;
            }
            
            QPushButton:pressed {
                background: #ddd;
            }
        """)
        
    # 减少值
    def decrease_value(self):
        new_val = max(self.min_val, self.current_val - 1)
        self.slider.setValue(new_val)
    
    # 增加值
    def increase_value(self):
        new_val = min(self.max_val, self.current_val + 1)
        self.slider.setValue(new_val)
    
    # 更新值显示
    def update_value(self, val):
        self.current_val = val
        self.label_value.setText(str(val))

    def value(self):
        return self.current_val
