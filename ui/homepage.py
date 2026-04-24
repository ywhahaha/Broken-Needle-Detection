from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import json
import os

class Ui_WarehouseInterface(object):
    def setupUi(self, MainWindow):
        MainWindow.setWindowTitle("仓库管理系统")
        
        # 创建中心部件和主布局
        self.central_widget = QWidget(MainWindow)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # 添加仓库卡片区域
        self.add_warehouse_cards()
        
        # 添加图像显示区域
        self.add_image_area()
        
        # 添加底部按钮区域
        self.add_bottom_buttons()
        
        MainWindow.setCentralWidget(self.central_widget)
        
        # 应用样式
        self.apply_styles(MainWindow)
    
    def apply_styles(self, widget):
        """应用样式表"""
        widget.setStyleSheet("""
            /* 仓库卡片样式 */
            QWidget#warehouse_1, QWidget#warehouse_2, 
            QWidget#warehouse_3, QWidget#warehouse_4 {
                background-color: #64B4FF;
                border-radius: 10px;
            }
            
            /* 仓库标题样式 */
            QLabel#warehouse_1_title, QLabel#warehouse_2_title,
            QLabel#warehouse_3_title, QLabel#warehouse_4_title {
                font-family: "SimHei";
                font-size: 40px;
                font-weight: bold;
                color: #000000;
            }
            
            /* 表格标签样式 */
            QLabel#warehouse_1_model_label, QLabel#warehouse_2_model_label,
            QLabel#warehouse_3_model_label, QLabel#warehouse_4_model_label,
            QLabel#warehouse_1_quantity_label, QLabel#warehouse_2_quantity_label,
            QLabel#warehouse_3_quantity_label, QLabel#warehouse_4_quantity_label {
                font-family: "SimHei";
                font-size: 25px;
                color: #FFFFFF;
            }
            
            QLabel#warehouse_1_model_value, QLabel#warehouse_2_model_value,
            QLabel#warehouse_3_model_value, QLabel#warehouse_4_model_value,
            QLabel#warehouse_1_quantity_value, QLabel#warehouse_2_quantity_value,
            QLabel#warehouse_3_quantity_value, QLabel#warehouse_4_quantity_value {
                font-family: "SimHei";
                font-size: 25px;
                color: #FFFFFF;
                font-weight: bold;
            }
            
            /* 仓库按钮样式 */
            QPushButton#warehouse_1_btn, QPushButton#warehouse_2_btn,
            QPushButton#warehouse_3_btn, QPushButton#warehouse_4_btn {
                background-color: #FFFFFF;
                border-radius: 15px;
                width: 30px;
                height: 50px;
                font-size: 40px;
                margin-left: auto;
                margin-right: auto;
            }
            
            QPushButton#warehouse_1_btn:hover, QPushButton#warehouse_2_btn:hover,
            QPushButton#warehouse_3_btn:hover, QPushButton#warehouse_4_btn:hover {
                background-color: #EEEEEE;
            }
            
            /* 图像区域样式 */
            QFrame#image_frame {
                background-color: #000000;
                border-radius: 5px;
            }
            
            /* 底部按钮样式 */
            QPushButton#bottom_btn_设置, QPushButton#bottom_btn_检测断针,
            QPushButton#bottom_btn_退出软件, QPushButton#bottom_btn_显示日志 {
                font-family: "SimHei";
                font-size: 25px;
                color: #FFFFFF;
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 #64B4FF, stop:1 #3296E6);
                border-radius: 5px;
                padding-left: 20px;
                padding-right: 20px;
            }
            
            QPushButton#bottom_btn_设置:hover, QPushButton#bottom_btn_检测断针:hover,
            QPushButton#bottom_btn_退出软件:hover, QPushButton#bottom_btn_显示日志:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 #74BBFF, stop:1 #42A6F6);
            }
        """)
    
    def load_config(self):
        """从 config.json 加载仓库数据"""
        try:
            config_path = os.path.abspath("config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("repertory", [])  # 返回仓库数据
            return []
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return []
        
    def update_warehouse_cards(self):
        """更新仓库卡片数据（不重新创建，直接更新现有控件）"""
        # 从config.json重新加载数据
        warehouse_data = self.load_config()
        
        # 构建按仓号索引的数据字典
        warehouse_dict = {item["bin_num"]: item for item in warehouse_data}
        
        # 更新每个仓库卡片
        for i in range(1, 5):
            bin_num = f"{i}"
            card = self.cards_layout.itemAt(i-1).widget()
            
            # 查找该仓的数据（没有则使用默认值）
            data = warehouse_dict.get(bin_num, {
                "model": "未录入",
                "quantity": 0
            })

            data["button"] = "+" if bin_num not in warehouse_dict else "⚙"       
            # 更新卡片内容
            title_label = card.findChild(QLabel, f"warehouse_{i}_title")
            model_value = card.findChild(QLabel, f"warehouse_{i}_model_value")
            quantity_value = card.findChild(QLabel, f"warehouse_{i}_quantity_value")
            button = card.findChild(QPushButton, f"warehouse_{i}_btn")
            
            if title_label:
                title_label.setText(bin_num)
            if model_value:
                model_value.setText(data["model"])
            if quantity_value:
                quantity_value.setText(str(data["quantity"]))
            if button:
                button.setText(data["button"])
    
    def add_warehouse_cards(self):
        """修改后的添加仓库卡片方法"""
        # 仓库卡片布局
        if not hasattr(self, 'cards_layout'):
            self.cards_layout = QHBoxLayout()
            self.cards_layout.setSpacing(20)
            self.main_layout.insertLayout(0, self.cards_layout)  # 插入到主布局中
        
        self.needle_Management_buttons = {}  # 清空按钮字典
        
        # 从 config.json 加载仓库数据
        warehouse_data = self.load_config()
        
        # 默认数据（如果 config.json 中没有对应仓库）
        default_data = [
            {"bin_num": "1", "model": "未录入", "quantity": 0, "button": "+"},
            {"bin_num": "2", "model": "未录入", "quantity": 0, "button": "+"},
            {"bin_num": "3", "model": "未录入", "quantity": 0, "button": "+"},
            {"bin_num": "4", "model": "未录入", "quantity": 0, "button": "+"}
        ]
        
        # 更新默认数据（如果 config.json 中有对应仓库）
        for warehouse in warehouse_data:
            bin_num = warehouse["bin_num"]
            if bin_num == "1":
                default_data[0] = {
                    "bin_num": bin_num,
                    "model": warehouse["model"],
                    "quantity": warehouse["quantity"],
                    "button": "⚙"
                }
            elif bin_num == "2":
                default_data[1] = {
                    "bin_num": bin_num,
                    "model": warehouse["model"],
                    "quantity": warehouse["quantity"],
                    "button": "⚙"
                }
            elif bin_num == "3":
                default_data[2] = {
                    "bin_num": bin_num,
                    "model": warehouse["model"],
                    "quantity": warehouse["quantity"],
                    "button": "⚙"
                }
            elif bin_num == "4":
                default_data[3] = {
                    "bin_num": bin_num,
                    "model": warehouse["model"],
                    "quantity": warehouse["quantity"],
                    "button": "⚙"
                }
        
        # 创建四个仓库卡片
        for i, data in enumerate(default_data):
            card = self.create_warehouse_card(
                f"warehouse_{i+1}", 
                data["bin_num"], 
                data["model"],
                data["quantity"],
                data["button"]
            )
            self.cards_layout.addWidget(card)
        
    
    def create_warehouse_card(self, obj_name, title, model, quantity, button_text):
        # 创建仓库卡片控件
        card = QWidget()
        card.setObjectName(obj_name)
        card.setMinimumWidth(180)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 15, 0, 15)
        layout.setSpacing(10)
        
        # 标题标签
        title_label = QLabel(title)
        title_label.setObjectName(f"{obj_name}_title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建表格布局
        table_layout = QGridLayout()
        table_layout.setHorizontalSpacing(10)
        table_layout.setVerticalSpacing(0)
        table_layout.setContentsMargins(0, 0, 0, 20)
        
        # 第一行：型号信息
        model_label = QLabel("型号：")
        model_label.setObjectName(f"{obj_name}_model_label")
        model_label.setMaximumHeight(30)
        model_value = QLabel(model)
        model_value.setObjectName(f"{obj_name}_model_value")
        
        # 第二行：数量信息
        quantity_label = QLabel("剩余：")
        quantity_label.setObjectName(f"{obj_name}_quantity_label")
        quantity_label.setMaximumHeight(30)
        quantity_value = QLabel(str(quantity))
        quantity_value.setObjectName(f"{obj_name}_quantity_value")

        # 添加到表格布局
        table_layout.addWidget(model_label, 0, 0)
        table_layout.addWidget(model_value, 0, 1)
        table_layout.addWidget(quantity_label, 1, 0)
        table_layout.addWidget(quantity_value, 1, 1)
        
        # 设置对齐方式
        for i in range(table_layout.count()):
            widget = table_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                if widget.objectName().endswith("_label"):
                    widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    widget.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        layout.addLayout(table_layout)
        
        # 操作按钮
        btn = QPushButton(button_text)
        btn.setObjectName(f"{obj_name}_btn")
        btn.setMinimumHeight(60)
        layout.addWidget(btn)
        self.needle_Management_buttons[obj_name] = btn  # 存储到字典
        
        return card
    
    def add_image_area(self):
        # 图像显示区域
        self.image_frame = QFrame()
        self.image_frame.setObjectName("image_frame")
        self.image_frame.setMaximumHeight(150)
        
        frame_layout = QVBoxLayout(self.image_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self.image_label)
        
        self.main_layout.addWidget(self.image_frame)
    
    def add_bottom_buttons(self):
        # 底部按钮布局
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(20)

        self.bottom_buttons = {}
        
        button_texts = ["设置", "检测断针", "退出软件", "显示日志"]
        
        for text in button_texts:
            btn = QPushButton(text)
            btn.setObjectName(f"bottom_btn_{text}")
            btn.setMinimumHeight(120)
            self.buttons_layout.addWidget(btn)
            self.bottom_buttons[text] = btn  # 存储到字典
    
        self.main_layout.addLayout(self.buttons_layout)
