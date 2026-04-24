import sys
import json
from PyQt5.QtWidgets import (QApplication, QVBoxLayout, 
                            QPushButton, QMessageBox, QHBoxLayout, QGroupBox, QDialog)
from PyQt5.QtCore import Qt
from ui.QDoubleSliderWithButtons import DoubleSliderWithButtons
from function.ttl import NeedleController
from function.get_resource_path import get_path
from function.show_info_message import show_info_message


class ConfigSettingUI(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置窗口属性 - 无标题栏且始终在最前
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无标题栏
            Qt.WindowStaysOnTopHint |  # 保持在顶层
            Qt.WindowFullscreenButtonHint  # 支持全屏
        )
        
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setGeometry(self.parent().geometry())
        self.config_file = get_path('config.json')

        self.initUI()
        self.load_config()
        self.apply_styles()  # 应用统一样式
        self.controller = NeedleController()
        self.controller.connect()

    def initUI(self):
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # 1. 完整度阈值设置区域
        threshold_group = QGroupBox("检测设置")
        threshold_group.setMaximumHeight(150)
        threshold_layout = QVBoxLayout()
        self.slider_control = DoubleSliderWithButtons("完整度报警阈值", 0.0, 1.0, 0.95, 2)
        threshold_layout.addWidget(self.slider_control)
        threshold_group.setLayout(threshold_layout)
        self.main_layout.addWidget(threshold_group)

        # 2. 仓体控制区域
        warehouse_group = QGroupBox("仓体控制")
        warehouse_layout = QVBoxLayout()
        
        # 第一行：主要仓体操作
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(10)

        self.open_recycle_bin_btn = QPushButton('打开断针回收仓门')
        self.open_recycle_bin_btn.clicked.connect(self.open_recycle_bin)
        row1_layout.addWidget(self.open_recycle_bin_btn)

        self.open_refill_bin_btn = QPushButton('打开补针仓门')
        self.open_refill_bin_btn.clicked.connect(self.open_refill_bin)
        row1_layout.addWidget(self.open_refill_bin_btn)

        self.rotateRecyclingWheel_btn = QPushButton('转动回收轮')
        self.rotateRecyclingWheel_btn.clicked.connect(self.rotateRecyclingWheel)
        row1_layout.addWidget(self.rotateRecyclingWheel_btn)

        # 新增重置系统按钮
        self.reset_system_btn = QPushButton('重置系统')
        self.reset_system_btn.clicked.connect(self.resetSystem)
        row1_layout.addWidget(self.reset_system_btn)

        warehouse_layout.addLayout(row1_layout)
        
        # 第二行：补针仓释放操作（按编号分组）
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(10)
        
        self.releaseNeedleRefillBin1_btn = QPushButton('释放补针仓#1')
        self.releaseNeedleRefillBin1_btn.clicked.connect(self.releaseNeedleRefillBin1)
        row2_layout.addWidget(self.releaseNeedleRefillBin1_btn)
        
        self.releaseNeedleRefillBin2_btn = QPushButton('释放补针仓#2')
        self.releaseNeedleRefillBin2_btn.clicked.connect(self.releaseNeedleRefillBin2)
        row2_layout.addWidget(self.releaseNeedleRefillBin2_btn)
        
        self.releaseNeedleRefillBin3_btn = QPushButton('释放补针仓#3')
        self.releaseNeedleRefillBin3_btn.clicked.connect(self.releaseNeedleRefillBin3)
        row2_layout.addWidget(self.releaseNeedleRefillBin3_btn)
        
        self.releaseNeedleRefillBin4_btn = QPushButton('释放补针仓#4')
        self.releaseNeedleRefillBin4_btn.clicked.connect(self.releaseNeedleRefillBin4)
        row2_layout.addWidget(self.releaseNeedleRefillBin4_btn)
        
        warehouse_layout.addLayout(row2_layout)
        
        warehouse_group.setLayout(warehouse_layout)
        self.main_layout.addWidget(warehouse_group)

        # 3. 底部按钮区域（保存+退出）
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        # 退出按钮
        exit_button = QPushButton('退出')
        exit_button.clicked.connect(self.close)
        
        # 保存按钮
        save_button = QPushButton('保存设置')
        save_button.clicked.connect(self.save_config)
        
        bottom_layout.addWidget(exit_button)
        bottom_layout.addWidget(save_button)
        self.main_layout.addLayout(bottom_layout)

    def apply_styles(self):
        """仅修改ConfigSettingUI中的按钮样式"""
        self.setStyleSheet("""
            /* 主窗口背景 */
            QDialog {
                background-color: #f0f0f0;
            }
                           
            QGroupBox {
                font-family: "SimHei";
                font-size: 30px;  /* 设置字体大小 */
                font-weight: bold;
                color: #333333;
                border: 1px solid #64B4FF;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            
            
            /* 仅匹配直接子按钮（不包含DoubleSliderWithButtons内部的按钮） */
            QGroupBox > QPushButton {
                font-family: "SimHei";
                font-size: 25px;
                color: #FFFFFF;
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #64B4FF, stop:1 #3296E6);
                border-radius: 5px;
                padding: 5px 10px;
                min-height: 80px;
            }
            
            QGroupBox > QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #74BBFF, stop:1 #42A6F6);
            }
            
            /* 底部按钮特殊样式 */
            QDialog > QPushButton {
                font-size: 25px;
                min-width: 200px;
                min-height: 100px;
            }
                        
        """)

    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            threshold = config['setting']['completeness_threshold']
            self.slider_control.set_value(threshold)
        except FileNotFoundError:
            show_info_message(self, '错误', '未找到 config.json 文件。')
        except json.JSONDecodeError:
            show_info_message(self, '错误', '无法解析 config.json 文件，请检查文件格式。')
        except KeyError:
            show_info_message(self, '错误', 'config.json 文件中缺少必要的键。')

    def save_config(self):
        try:
            new_threshold = float(self.slider_control.value())
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['setting']['completeness_threshold'] = new_threshold
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            show_info_message(self, '成功', '设置已保存。')
        except ValueError:
            show_info_message(self, '错误', '请输入有效的数字。')
        except FileNotFoundError:
            show_info_message(self, '错误', '未找到 config.json 文件。')
        except json.JSONDecodeError:
            show_info_message(self, '错误', '无法解析 config.json 文件，请检查文件格式。')
        except KeyError:
            show_info_message(self, '错误', 'config.json 文件中缺少必要的键。')
    
    # 断针回收仓打开功能
    def open_recycle_bin(self):
        self.controller.drive_solenoid(True)
    
    # 补针仓打开功能
    def open_refill_bin(self):
        self.controller.drive_solenoid(False)

    # 转动回收轮
    def rotateRecyclingWheel(self):
        self.controller.drive_motor(slot=0, is_recycle=True)

    # 释放补针仓#1
    def releaseNeedleRefillBin1(self):
        self.controller.drive_motor(slot=1)

    # 释放补针仓#2
    def releaseNeedleRefillBin2(self):
        self.controller.drive_motor(slot=2)

    # 释放补针仓#3
    def releaseNeedleRefillBin3(self):
        self.controller.drive_motor(slot=3)

    # 释放补针仓#4
    def releaseNeedleRefillBin4(self):
        self.controller.drive_motor(slot=4)
    
    def resetSystem(self):
        self.controller.reset()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ConfigSettingUI()
    window.show()
    sys.exit(app.exec_())