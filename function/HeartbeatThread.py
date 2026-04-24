from PyQt5.QtCore import QObject, QThread, pyqtSignal, QMutex, Qt, QTimer
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton
import time
# import debugpy

class HeartbeatThread(QThread):
    """心跳监测线程"""
    heartbeat_updated = pyqtSignal(int)
    connection_lost = pyqtSignal()

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = True
        self.mutex = QMutex()
        self.last_heartbeat = 0
        self.last_valid_time = 0
        self.timeout_sec = 3

    def run(self):
        # if debugpy.is_client_connected():
        #     debugpy.debug_this_thread()
        while self.running:
            self.mutex.lock()
            current_time = time.time()
            try:
                if self.controller.ser is None:
                    if not self._reconnect():
                        if current_time - self.last_valid_time > self.timeout_sec:
                            self.connection_lost.emit()
                            break

                hb = self.controller.get_heartbeat()
            
                if hb is not None:
                    self.last_heartbeat = hb
                    self.last_valid_time = current_time
                    self.heartbeat_updated.emit(hb)
                else:
                    self.controller.ser = None

                if current_time - self.last_valid_time > self.timeout_sec:
                    self.connection_lost.emit()
                    break

            finally:
                self.mutex.unlock()
                self.msleep(500)

    def _reconnect(self):
        self.controller.close()
        time.sleep(1)
        return self.controller.connect()

    def stop(self):
        self.mutex.lock()
        self.running = False
        self.mutex.unlock()
        self.wait()


class ReconnectManager():
    # close_app_requested = pyqtSignal()

    """重连管理器，处理所有重连逻辑"""
    def __init__(self, controller, parent_window):
        super().__init__()
        
        self.controller = controller
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
        self.update_reconnect_status("单片机正在尝试重新连接...", 0)
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
        self.update_reconnect_status(f"单片机正在尝试第 {self.reconnect_attempts} 次重连", self.reconnect_attempts)
        
        if self.controller.connect():
            self.reconnect_success()
        elif self.reconnect_attempts >= self.max_reconnect_attempts:
            self.reconnect_failed()
        
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.reconnect_timer.stop()

    def reconnect_success(self):
        """重连成功处理"""
        self.dismiss_reconnect_dialog()
        self.parent_window.start_heartbeat_thread()
        self.parent_window.restart_camera()

    def reconnect_failed(self):
        """重连失败处理"""
        self.update_reconnect_status("单片机自动重连失败，请手动重连")

    def manual_reconnect(self):
        """手动重连"""
        self.update_reconnect_status("单片机正在执行手动重连...")
        
        if self.controller.connect():
            self.reconnect_success()
        else:
            self.update_reconnect_status("单片机手动重连失败")

    # def on_close_app_requested(self):
    #     """处理关闭软件请求，转发信号"""
    #     self.close_app_requested.emit()

class ReconnectDialog(QDialog):
    """重连对话框"""
    reconnect_requested = pyqtSignal()
    close_app_requested = pyqtSignal()

    def __init__(self, parent=None, max_reconnect_attempts=10):
        super().__init__(parent)
        self.setWindowTitle("单片机连接状态")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.max_reconnect_attempts = max_reconnect_attempts
        
        layout = QVBoxLayout()
        self.status_label = QLabel("单片机正在尝试重新连接...")
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