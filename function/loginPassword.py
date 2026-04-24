import json
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.QCustomTitleBarDialog import CustomTitleBarDialog
from function.get_resource_path import get_path
from function.show_info_message import show_info_message

class LoginWindow(CustomTitleBarDialog):
    login_success_signal = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.change_password_window = None
        self.config_file = get_path('config.json')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.initUI()
        self.load_remembered_credentials()
        self.setGeometry(parent.geometry().x(), parent.geometry().y(), parent.size().width(), parent.size().height())

    def initUI(self):
        # 用户名输入框
        username_layout = QHBoxLayout()
        username_label = QLabel('用户名:')
        username_label.setStyleSheet("""
            QLabel {
                font-size: 25px;  /* 文字大小 */
                min-height: 60;
            }
        """)
        self.username_edit = QLineEdit()
        self.username_edit.setStyleSheet("""
            QLineEdit {
                font-size: 25px;  /* 文字大小 */
                min-height: 60;
            }
        """)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_edit)

        # 密码输入框
        password_layout = QHBoxLayout()
        password_label = QLabel('密码:')
        password_label.setStyleSheet("""
            QLabel {
                font-size: 25px;  /* 文字大小 */
                min-height: 60;
            }
        """)
        self.password_edit = QLineEdit()
        self.password_edit.setStyleSheet("""
            QLineEdit {
                font-size: 25px;  /* 文字大小 */
                min-height: 60;
            }
        """)
        self.password_edit.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_edit)

        # 记住密码复选框
        self.remember_checkbox = QCheckBox('记住密码')
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 25px;  /* 文字大小 */
                min-width: 120;
                min-height: 100;
            }
            QCheckBox::indicator {
                width: 40px;      /* 复选框指示器宽度 */
                height: 40px;     /* 复选框指示器高度 */
            }
        """)
        self.remember_checkbox.stateChanged.connect(self.remember_credentials)

        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 登录按钮
        login_button = QPushButton('登录')
        login_button.setStyleSheet("""
            QPushButton {
                font-size: 25px;  /* 文字大小 */
                min-height: 100;
            }
        """)
        login_button.clicked.connect(self.check_login)
        
        # 修改密码按钮
        change_password_button = QPushButton('修改密码')
        change_password_button.setStyleSheet("""
            QPushButton {
                font-size: 25px;  /* 文字大小 */
                min-height: 100;
            }
        """)
        change_password_button.clicked.connect(self.show_change_password_window)
        
        # 退出按钮
        exit_button = QPushButton('退出')
        exit_button.setStyleSheet("""
            QPushButton {
                font-size: 25px;  /* 文字大小 */
                min-height: 100;
            }
        """)
        exit_button.clicked.connect(self.close)
        
        # 添加按钮到布局
        button_layout.addWidget(login_button)
        button_layout.addWidget(change_password_button)
        button_layout.addWidget(exit_button)

        self.content_layout.addLayout(username_layout)
        self.content_layout.addLayout(password_layout)
        self.content_layout.addWidget(self.remember_checkbox)
        self.content_layout.addLayout(button_layout)

        self.set_title('用户登录')


    def load_remembered_credentials(self):
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            users = config["login"]
                
        if users["remember_me"]:
            username = users["remember_username"]
            password = users["remember_password"]
            self.username_edit.setText(username)
            self.password_edit.setText(password)
        
        self.remember_checkbox.setChecked(users["remember_me"])

    def remember_credentials(self):
        remember = self.remember_checkbox.isChecked()
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                users = config["login"]
        except FileNotFoundError:
            users = {}
        if remember:
            users["remember_username"] = self.username_edit.text()
            users["remember_password"] = self.password_edit.text()
            users["remember_me"] = True
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config["login"] = users
                json.dump(config, f, indent=4, ensure_ascii=False)
        else:
            users["remember_me"] = False
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config["login"] = users
                json.dump(config, f, indent=4, ensure_ascii=False)


    def check_login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                users = config["login"]
        except FileNotFoundError:
            users = {}

        if users["username"] == username and users["password"] == password:
            # QMessageBox.information(self, '登录成功', '欢迎登录！')
            if self.remember_checkbox.isChecked():
                users["remember_username"] = self.username_edit.text()
                users["remember_password"] = self.password_edit.text()
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    config["login"] = users
                    json.dump(config, f, indent=4, ensure_ascii=False)

            self.login_success_signal.emit()
            self.close()
        else:
            show_info_message(self, '登录失败', '用户名或密码错误，请重新输入。')

    def show_change_password_window(self):
        self.change_password_window = ChangePasswordWindow(self.username_edit.text(), parent=self)
        self.change_password_window.move(
            self.geometry().center() - self.change_password_window.rect().center()
        )
        self.change_password_window.show()

    def closeEvent(self, event):
        if self.change_password_window is not None:
            self.change_password_window.close()
        event.accept()

class ChangePasswordWindow(CustomTitleBarDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.initUI()
        self.config_file = get_path('config.json')
        # self.setWindowFlags(Qt.Window)  # 设为独立窗口
        self.set_title("修改密码 - " + username)
        self.setGeometry(parent.geometry().x(), parent.geometry().y(), parent.size().width(), parent.size().height())

    def initUI(self):
        # 旧密码输入框
        old_password_layout = QHBoxLayout()
        old_password_label = QLabel('旧密码:')
        old_password_label.setStyleSheet("""
            QLabel {
                font-size: 25px;  /* 文字大小 */
                min-height: 60;
            }
        """)
        self.old_password_edit = QLineEdit()
        self.old_password_edit.setStyleSheet("""
            QLineEdit {
                font-size: 25px;  /* 文字大小 */
                min-height: 60;
            }
        """)
        self.old_password_edit.setEchoMode(QLineEdit.Password)
        old_password_layout.addWidget(old_password_label)
        old_password_layout.addWidget(self.old_password_edit)

        # 新密码输入框
        new_password_layout = QHBoxLayout()
        new_password_label = QLabel('新密码:')
        new_password_label.setStyleSheet("""
            QLabel {
                font-size: 25px;  /* 文字大小 */
                min-height: 60;
            }
        """)
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setStyleSheet("""
            QLineEdit {
                font-size: 25px;  /* 文字大小 */
                min-height: 60;
            }
        """)
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        new_password_layout.addWidget(new_password_label)
        new_password_layout.addWidget(self.new_password_edit)

        # 确认新密码输入框
        confirm_password_layout = QHBoxLayout()
        confirm_password_label = QLabel('确认新密码:')
        confirm_password_label.setStyleSheet("""
            QLabel {
                font-size: 25px;  /* 文字大小 */
                min-height: 60;
            }
        """)
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setStyleSheet("""
            QLineEdit {
                font-size: 25px;  /* 文字大小 */
                min-height: 60;
            }
        """)
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        confirm_password_layout.addWidget(confirm_password_label)
        confirm_password_layout.addWidget(self.confirm_password_edit)

        blank_widget = QWidget()
        blank_widget.setFixedHeight(150)

        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 修改按钮
        change_button = QPushButton('修改')
        change_button.setStyleSheet("""
            QPushButton {
                font-size: 25px;  /* 文字大小 */
                min-height: 100;
            }
        """)
        change_button.clicked.connect(self.change_password)
        
        # 退出按钮
        exit_button = QPushButton('退出')
        exit_button.setStyleSheet("""
            QPushButton {
                font-size: 25px;  /* 文字大小 */
                min-height: 100;
            }
        """)
        exit_button.clicked.connect(self.close)
        
        button_layout.addWidget(change_button)
        button_layout.addWidget(exit_button)

        self.content_layout.addLayout(old_password_layout)
        self.content_layout.addLayout(new_password_layout)
        self.content_layout.addLayout(confirm_password_layout)
        self.content_layout.addWidget(blank_widget)
        self.content_layout.addLayout(button_layout)

    def change_password(self):
        old_password = self.old_password_edit.text()
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                users = config["login"]
        except FileNotFoundError:
            users = {}

        if users["username"] == self.username and users["password"] == old_password:
            if new_password == confirm_password:
                users["password"] = new_password
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    config["login"] = users
                    json.dump(config, f, indent=4, ensure_ascii=False)
                show_info_message(self, '修改成功', '密码修改成功，请使用新密码登录。')
                self.close()
            else:
                show_info_message(self, '修改失败', '新密码和确认密码不一致，请重新输入。')
        else:
            show_info_message(self, '修改失败', '旧密码错误，请重新输入。')
    