from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QSlider, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

__all__ = ['DoubleSliderWithButtons']

class DoubleSliderWithButtons(QWidget):
    valueChanged = pyqtSignal(float)  # 新增浮点数变化信号
    
    def __init__(self, param_name="参数", min_val=0.0, max_val=1.0, default_val=0.5, decimals=2):
        super().__init__()
        
        # 初始化参数
        self.min_val = min_val
        self.max_val = max_val
        self.decimals = decimals
        self.scale_factor = 10 ** decimals # 用于整数转换的缩放因子
        
        # 转换为整数范围（保持精度）
        self.int_min = int(min_val * self.scale_factor)
        self.int_max = int(max_val * self.scale_factor)
        self.current_val = default_val
        
        # 创建控件
        self.label_param = QLabel(param_name)
        self.btn_decrease = QPushButton("-")
        self.slider = QSlider(Qt.Horizontal)
        self.btn_increase = QPushButton("+")
        self.label_value = QLabel(self._format_value(default_val))
        
        # 设置滑动条范围（使用整数）
        self.slider.setRange(self.int_min, self.int_max)
        self.slider.setValue(int(default_val * self.scale_factor))
        
        # 连接信号槽
        self.btn_decrease.clicked.connect(self.decrease_value)
        self.btn_increase.clicked.connect(self.increase_value)
        self.slider.valueChanged.connect(self._on_slider_changed)
        
        # 设置布局
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        layout.addWidget(self.label_param)
        layout.addWidget(self.btn_decrease)
        layout.addWidget(self.slider)
        layout.addWidget(self.btn_increase)
        layout.addWidget(self.label_value)
        self.setLayout(layout)
        
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
                font-size: 25px;
                min-width: 30px;
                color: #333333;
            }
            
            /* 按钮样式 */
            QPushButton {
                font-size: 70px;
                width: 80px;
                height: 80px;
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
    
    def _format_value(self, value):
        """格式化显示值，保留指定位数小数"""
        return f"{value:.{self.decimals}f}"
    
    def _int_to_float(self, int_value):
        """将整数转换为浮点数"""
        return int_value / self.scale_factor
    
    def _float_to_int(self, float_value):
        """将浮点数转换为整数"""
        return int(float_value * self.scale_factor)
    
    def _on_slider_changed(self, int_value):
        """滑动条值变化时的处理"""
        self.current_val = self._int_to_float(int_value)
        self.label_value.setText(self._format_value(self.current_val))
        self.valueChanged.emit(self.current_val)
    
    def set_value(self, value):
        """设置当前值"""
        value = max(self.min_val, min(self.max_val, value))
        self.current_val = value
        self.slider.setValue(self._float_to_int(value))
        self.label_value.setText(self._format_value(value))
    
    def decrease_value(self):
        """减少值（步长为10^-decimals）"""
        step = 1 / self.scale_factor
        new_val = max(self.min_val, self.current_val - step)
        self.set_value(new_val)
    
    def increase_value(self):
        """增加值（步长为10^-decimals）"""
        step = 1 / self.scale_factor
        new_val = min(self.max_val, self.current_val + step)
        self.set_value(new_val)
    
    def value(self):
        """获取当前值"""
        return self.current_val
    
    def set_range(self, min_val, max_val):
        """设置取值范围"""
        self.min_val = min_val
        self.max_val = max_val
        self.int_min = int(min_val * self.scale_factor)
        self.int_max = int(max_val * self.scale_factor)
        self.slider.setRange(self.int_min, self.int_max)
    
    def set_decimals(self, decimals):
        """设置小数位数"""
        if decimals != self.decimals:
            old_value = self.current_val
            self.decimals = decimals
            self.scale_factor = 10 ** decimals
            self.set_range(self.min_val, self.max_val)
            self.set_value(old_value)

# 示例使用
if __name__ == "__main__":
    app = QApplication([])
    
    window = QWidget()
    window.setWindowTitle("Double Slider Demo")
    layout = QHBoxLayout()
    
    slider2 = DoubleSliderWithButtons("透明度", 0.0, 1.0, 0.75, 2)
    
    # 连接值变化信号
    slider2.valueChanged.connect(lambda v: print(f"透明度改变: {v}"))
    
    layout.addWidget(slider2)
    
    window.setLayout(layout)
    window.show()
    app.exec_()