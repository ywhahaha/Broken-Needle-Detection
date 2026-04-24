import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
                            QLineEdit, QPushButton, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.QSliderWithButtons import SliderWithButtons
from function.get_resource_path import get_path
from function.show_info_message import show_info_message


class InventoryDialog(QDialog):
    get_needle_size_signal = pyqtSignal()
    update_warehouse_signal = pyqtSignal()

    def __init__(self, dialog_type, bin_num, parent=None):
        """
        机针库存操作对话框
        
        参数:
            dialog_type: 界面类型 ('create'或'change')
            bin_num: 机针仓号码
            parent: 父窗口
        """
        super().__init__(parent)
        self.dialog_type = dialog_type
        self.bin_num = bin_num
        self.delete_flag = False
        self.config_file = get_path('config.json')
        
        # 加载配置数据
        self.config = self.load_config()
        self.current_needle = self.find_current_needle()
        
        # 初始化UI
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无标题栏
            Qt.WindowStaysOnTopHint |  # 保持在顶层
            Qt.WindowFullscreenButtonHint  # 支持全屏
        )
        
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.init_ui()
        self.apply_styles()

        self.setGeometry(self.parent().geometry())


    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"repertory": []}  # 默认空配置
        except Exception as e:
            show_info_message(self, '错误', f'加载配置文件失败: {e}')
            return {"repertory": []}

    def find_current_needle(self):
        """查找当前仓位的机针数据"""
        if self.dialog_type == 'change':
            for needle in self.config.get('repertory', []):
                if needle.get('bin_num') == self.bin_num:
                    return needle
        return None

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.update_warehouse_signal.emit()
            return True
        except Exception as e:
            show_info_message(self, '错误', f'保存配置文件失败: {e}')
            return False

    def init_ui(self):
        """初始化无标题栏界面"""

        # self.setStyleSheet("""
        #     /* 1. 主窗口背景：避免底层透明穿透 */
        #     QDialog {
        #         background-color: #f8f8f8; /* 与界面主色调匹配，覆盖透明 */
        #     }
        # """)
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # 1. 补针仓信息显示
        bin_layout = QHBoxLayout()
        bin_label = QLabel('补针仓:')
        bin_layout.addWidget(bin_label)

        self.bin_label = QLabel(self.bin_num)
        bin_layout.addWidget(self.bin_label)

        self.main_layout.addLayout(bin_layout)

        # 根据类型加载不同界面
        if self.dialog_type == 'create':
            self.init_create_ui()
        else:
            if not self.current_needle:
                show_info_message(self, '错误', f'{self.bin_num}没有机针数据！')
                self.close()
                return
            self.init_change_ui()

        # 添加操作按钮
        self.init_action_buttons()

    def init_create_ui(self):
        """创建界面UI"""
        # 机针型号输入
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel('机针型号:'))
        self.model_input = QLineEdit()
        model_layout.addWidget(self.model_input)
        self.main_layout.addLayout(model_layout)

        # 录入数量输入
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel('录入数量:'))
        self.quantity_input = QLineEdit()
        self.quantity_input.setInputMethodHints(Qt.ImhDigitsOnly)
        quantity_layout.addWidget(self.quantity_input)
        self.main_layout.addLayout(quantity_layout)

        blank_widget = QWidget()
        blank_widget.setFixedHeight(150)
        self.main_layout.addWidget(blank_widget)

    def init_change_ui(self):
        """修改界面UI"""
        # 显示当前型号
        model_label = QLabel(f'机针型号: {self.current_needle["model"]}')
        self.main_layout.addWidget(model_label)

        # 显示尺寸参数
        size_labels = [
            QLabel(f'总长度: {self.current_needle["needle_total_length"]:.2f}mm'),
            QLabel(f'针柄长度: {self.current_needle["needle_handle_length"]:.2f}mm'),
            QLabel(f'针柄直径: {self.current_needle["needle_handle_diameter"]:.2f}mm'),
            QLabel(f'针杆直径: {self.current_needle["needle_middle_diameter"]:.2f}mm')
        ]
        for label in size_labels:
            self.main_layout.addWidget(label)

        # 库存数量调整
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel('库存数量:'))
        self.quantity_slider = SliderWithButtons("", 0, 100, self.current_needle["quantity"])
        quantity_layout.addWidget(self.quantity_slider)
        self.main_layout.addLayout(quantity_layout)

    def init_action_buttons(self):
        """初始化操作按钮"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 退出按钮
        exit_btn = QPushButton('退出')
        exit_btn.clicked.connect(self.close)
        
        # 根据类型添加不同按钮
        if self.dialog_type == 'create':
            save_btn = QPushButton('录入机针')
            save_btn.clicked.connect(self.add_new_needle)
            button_layout.addWidget(save_btn)
        else:
            save_btn = QPushButton('保存')
            save_btn.clicked.connect(self.save_changes)
            del_btn = QPushButton('删除')
            del_btn.clicked.connect(self.confirm_delete)
            button_layout.addWidget(save_btn)
            button_layout.addWidget(del_btn)
        
        button_layout.addWidget(exit_btn)
        self.main_layout.addLayout(button_layout)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f8f8; /* 与界面主色调匹配，覆盖透明 */
            }
                           
            InventoryDialog > QPushButton {
                font-size: 25px;
                min-width: 240px;
                min-height: 100px;
            }
                           
            QLineEdit {
                min-height: 60px;
            }
                                       
            QLabel {
                min-height: 40px;
                font-size: 25px;           
            }
        """
        )

    def add_new_needle(self):
        """添加新机针"""
        model = self.model_input.text().strip()
        quantity = self.quantity_input.text()
        
        if not model:
            show_info_message(self, '错误', '机针型号不能为空！')
            return
            
        if not quantity:
            show_info_message(self, '错误', '请输入录入数量！')
            return
            
        try:
            quantity = int(quantity)
        except ValueError:
            show_info_message(self, '错误', '录入数量必须为整数！')
            return
            
        # 触发尺寸测量
        self.get_needle_size_signal.emit()

    def receive_size_result(self, size_data):
        """接收尺寸测量结果并保存"""
        model = self.model_input.text().strip()
        quantity = int(self.quantity_input.text())
        
        # 创建新机针记录
        new_needle = {
            "model": model,
            "quantity": quantity,
            "bin_num": self.bin_num,
            "needle_total_length": size_data["total_length"],
            "needle_handle_length": size_data["shank_length"],
            "needle_handle_diameter": size_data["shank_diameter"],
            "needle_middle_diameter": size_data["shaft_diameter"]
        }
        
        # 检查是否已存在相同型号
        existing_index = next((i for i, item in enumerate(self.config["repertory"]) 
                              if item["model"] == model and item["bin_num"] == self.bin_num), None)
        
        if existing_index is not None:
            # 更新现有记录
            self.config["repertory"][existing_index]["quantity"] += quantity
        else:
            # 添加新记录
            self.config["repertory"].append(new_needle)
        
        # 保存配置
        if self.save_config():
            show_info_message(self, '成功', '机针数据已保存！')
            # self.update_warehouse_signal.emit()
            self.close()
        else:
            show_info_message(self, '错误', '保存机针数据失败！')

    def save_changes(self):
        """保存修改"""
        new_quantity = self.quantity_slider.value()
        
        # 更新当前机针数量
        for needle in self.config["repertory"]:
            if needle["model"] == self.current_needle["model"] and needle["bin_num"] == self.bin_num:
                needle["quantity"] = new_quantity
                break
        
        # 保存配置
        if self.save_config():
            show_info_message(self, '成功', '库存数量已更新！')
            self.deleteLater()
            self.close()
        else:
            show_info_message(self, '错误', '更新库存数量失败！')

    def confirm_delete(self):
        """确认删除型号"""
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Question)
        dialog.setWindowTitle('确认删除')
        dialog.setText(f'确定要删除型号 {self.current_needle["model"]} 吗？')
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        
        # 设置按钮大小
        yes_button = dialog.button(QMessageBox.Yes)
        no_button = dialog.button(QMessageBox.No)
        
        if yes_button:
            yes_button.setFixedSize(150, 80)
            yes_button.setStyleSheet("""
                QPushButton {
                    font-size: 25px;
                }
            """)
        
        if no_button:
            no_button.setFixedSize(150, 80)
            no_button.setStyleSheet("""
                QPushButton {
                    font-size: 25px;
                }
            """)
        
        reply = dialog.exec_()
        if reply == QMessageBox.Yes:
            self.delete_model()


    def delete_model(self):
        """删除机针型号"""
        # 从配置中移除
        self.config["repertory"] = [
            item for item in self.config["repertory"] 
            if not (item["model"] == self.current_needle["model"] and item["bin_num"] == self.bin_num)
        ]
        
        # 保存配置
        if self.save_config():
            self.delete_flag = True
            show_info_message(self, '成功', '机针型号已删除！')
            self.close()
        else:
            show_info_message(self, '错误', '删除机针型号失败！')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 确保有测试用的config.json文件
    
    # 测试create对话框
    create_dialog = InventoryDialog('create', '2')
    if create_dialog.exec_():
        print("创建操作完成")
    
    # 测试change对话框
    # change_dialog = InventoryDialog('change', '1')
    # if change_dialog.exec_():
    #     if change_dialog.delete_flag:
    #         print("删除操作完成")
    #     else:
    #         print("修改操作完成")
    
    # sys.exit(app.exec_())