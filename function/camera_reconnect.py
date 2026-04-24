from PyQt5.QtCore import (pyqtSignal, Qt, QTimer)
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton)

class CameraReconnectManager():
    # close_app_requested = pyqtSignal()

    """重连管理器，处理所有重连逻辑"""
    def __init__(self, camera_thread, parent_window):
        # super().__init__()

        self.camera_thread = camera_thread
        self.parent_window = parent_window
        self.reconnect_dialog = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.attempt_reconnect)
        self.auto_reconnect_enabled = True

    def show_reconnect_dialog(self):
        """显示重连对话框"""
        if self.reconnect_dialog is None or not self.reconnect_dialog.isVisible():
            self.reconnect_dialog = ReconnectDialog(self.parent_window, self.max_reconnect_attempts)
            self.reconnect_dialog.reconnect_requested.connect(self.manual_reconnect)
            # self.reconnect_dialog.close_app_requested.connect(self.on_close_app_requested)
            self.reconnect_dialog.show()
        
        self.auto_reconnect_enabled = True
        self.update_reconnect_status("相机正在尝试重新连接...", 0)
        self.reconnect_attempts = 0
        self.reconnect_timer.start(2000)

    def update_reconnect_status(self, message, attempt=None):
        """更新重连状态"""
        if attempt is not None:
            self.reconnect_attempts = attempt
        
        if self.reconnect_dialog and self.reconnect_dialog.isVisible():
            self.reconnect_dialog.update_status(message, self.reconnect_attempts)

    def dismiss_reconnect_dialog(self):
        """关闭重连对话框"""
        if self.reconnect_dialog and self.reconnect_dialog.isVisible():
            self.reconnect_dialog.close()
        self.reconnect_timer.stop()

    def attempt_reconnect(self):
        """尝试重连"""
        if not self.auto_reconnect_enabled:
            return
            
        self.reconnect_attempts += 1
        self.update_reconnect_status(f"相机正在尝试第 {self.reconnect_attempts} 次重连", self.reconnect_attempts)
        
        if self.camera_thread.camera_connect():
            self.reconnect_success()
        elif self.reconnect_attempts >= self.max_reconnect_attempts:
            self.reconnect_failed()
        
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.reconnect_timer.stop()

    def reconnect_success(self):
        """重连成功处理"""
        self.dismiss_reconnect_dialog()
        self.parent_window._start_camera_thread()

    def reconnect_failed(self):
        """重连失败处理"""
        self.update_reconnect_status("相机自动重连失败，请手动重连")

    def manual_reconnect(self):
        """手动重连"""
        self.update_reconnect_status("相机正在执行手动重连...")
        
        if self.camera_thread.camera_connect():
            self.reconnect_success()
        else:
            self.update_reconnect_status("相机手动重连失败")

    # def on_close_app_requested(self):
    #     """处理关闭软件请求，转发信号"""
    #     self.close_app_requested.emit()
    
class ReconnectDialog(QDialog):
    """重连对话框"""
    reconnect_requested = pyqtSignal()
    close_app_requested = pyqtSignal()

    def __init__(self, parent=None, max_reconnect_attempts=10):
        super().__init__(parent)
        self.setWindowTitle("连接状态")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.max_reconnect_attempts = max_reconnect_attempts
        
        layout = QVBoxLayout()
        self.status_label = QLabel("相机正在尝试重新连接...")
        self.attempt_label = QLabel(f"尝试次数: 0/{self.max_reconnect_attempts}")
        self.reconnect_button = QPushButton("手动重连")
        # self.close_app_button = QPushButton("关闭软件") 

        layout.addWidget(self.status_label)
        layout.addWidget(self.attempt_label)
        layout.addWidget(self.reconnect_button)
        # layout.addWidget(self.close_app_button)
        self.setLayout(layout)
        
        self.reconnect_button.clicked.connect(self.on_reconnect_clicked)
        # self.close_app_button.clicked.connect(self.on_close_app_clicked)
        
        self.setStyleSheet("""
            QDialog {
                background: white;
                border: 2px solid #3498db;
                padding: 10px;
                min-width: 300px;
            }
            QLabel {
                font-size: 14px;
                padding: 5px;
            }
            QPushButton {
                min-width: 80px;
                padding: 5px;
                margin: 5px;
            }
        """)
    
    def on_reconnect_clicked(self):
        """手动重连按钮点击处理"""
        self.reconnect_requested.emit()
    
    def on_close_app_clicked(self):
        self.close_app_requested.emit()

    def update_status(self, message, attempt):
        """更新对话框状态"""
        self.status_label.setText(message)
        self.attempt_label.setText(f"尝试次数: {attempt}/{self.max_reconnect_attempts}")