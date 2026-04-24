import sys
import os

from PyQt5.QtWidgets import (QApplication, QMainWindow, QDialog, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QMutexLocker

from ui.QScreensaver import ScreenSaver
from ui.QLogViewer import LogViewer
from ui.homepage import Ui_WarehouseInterface
from function.loginPassword import LoginWindow
from function.camera import CameraThread, NeedleSelectionDialog
from function.needleInventoryManagement import InventoryDialog
from function.setting import ConfigSettingUI
from function.EmittingStream import EmittingStream
from function.read_config import ConfigReader
from function.ttl import NeedleController
from function.HeartbeatThread import HeartbeatThread, ReconnectManager
from function.camera_reconnect import CameraReconnectManager
import traceback
import signal


# 环境变量设置应放在最前
os.environ["QT_IM_MODULE"] = "qtvirtualkeyboard"
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = "/usr/lib/aarch64-linux-gnu/qt5/plugins/platforms/"

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)  # 更简洁的父类调用
        self._init_read_config()
        self.redirect_output()
        self.setup_exit_monitor()
        self._init_ui()
        self._init_signals()
        self._init_variables()
        self._init_screensaver()
        self.setup_controller()
        self.setup_reconnect_manager()
        self.start_heartbeat_thread()
        self._start_camera_thread()
        self.setup_camera_reconnect_manager()
        print("系统初始化完成\n准备就绪...")

    def _init_ui(self):
        """初始化UI界面"""
        self.ui = Ui_WarehouseInterface()
        self.ui.setupUi(self)
        self.showFullScreen()
        self.setGeometry(100, 100, 1024, 600)
        

    def _init_signals(self):
        """初始化信号连接"""
        self.ui.needle_Management_buttons["warehouse_1"].clicked.connect(self._handle_needle_action)
        self.ui.needle_Management_buttons["warehouse_2"].clicked.connect(self._handle_needle_action)
        self.ui.needle_Management_buttons["warehouse_3"].clicked.connect(self._handle_needle_action)
        self.ui.needle_Management_buttons["warehouse_4"].clicked.connect(self._handle_needle_action)

        self.ui.bottom_buttons["设置"].clicked.connect(self._handle_setting_action)
        self.ui.bottom_buttons["检测断针"].clicked.connect(self.manual_detect_needle)
        self.ui.bottom_buttons["退出软件"].clicked.connect(self.exit_system)
        self.ui.bottom_buttons["显示日志"].clicked.connect(self.show_log_viewer)

    def _init_variables(self):
        """初始化类变量"""
        self.is_login = False  # PEP8命名：使用下划线
        self.triggered_action = None
        self.management = self.setting = self.login = self.log_viewer = self.warning_dialog= None  # 合并声明
    
    def _init_screensaver(self):
        """初始化屏保"""
        self.screensaver = ScreenSaver(self, inactive_timeout=self.config.inactive_timeout, switch_interval=self.config.switch_interval)  # 传入主窗口作为父部件

        # 设置屏保覆盖所有子窗口
        self.screensaver.setWindowFlags(
            self.screensaver.windowFlags() | 
            Qt.WindowStaysOnTopHint
        )
    
    def _init_read_config(self):
        self.config = ConfigReader('default.yaml')

    def mouseMoveEvent(self, event):
        """重写鼠标移动事件"""
        super().mouseMoveEvent(event)
    
    def keyPressEvent(self, event):
        """重写按键事件"""
        super().keyPressEvent(event)

    def _start_camera_thread(self):
        """启动相机线程"""
        self.camera_thread = None
        self.camera_thread = CameraThread(parent=self)
        self.camera_thread.frame_signal.connect(self.update_display)
        self.camera_thread.selection_needed.connect(self.show_needle_selection_dialog)
        self.camera_thread.inventory_warning.connect(self.show_warning)
        self.camera_thread.connection_lost.connect(self.on_camera_connection_lost)
        self.camera_thread.update_warehouse_cards.connect(self.ui.update_warehouse_cards)
        self.camera_thread.show_message_signal.connect(self.show_warning)
        self.camera_thread.start()
    
    def setup_camera_reconnect_manager(self):
        """初始化重连管理器"""
        self.camera_reconnect_manager = CameraReconnectManager(self.camera_thread, self)
        # self.camera_reconnect_manager.close_app_requested.connect(self.exit_system)

    def on_camera_connection_lost(self):
        """连接丢失处理"""
        self.camera_thread.stop()
        self.camera_reconnect_manager.show_reconnect_dialog()

    def setup_controller(self):
        """初始化控制器"""
        self.controller = NeedleController()
        self.controller.connect()

    def setup_reconnect_manager(self):
        """初始化重连管理器"""
        self.reconnect_manager = ReconnectManager(self.controller, self)
        # self.reconnect_manager.close_app_requested.connect(self.exit_system)

    def start_heartbeat_thread(self):
        """启动心跳线程"""
        self.heartbeat_thread = None
        self.heartbeat_thread = HeartbeatThread(self.controller)
        self.heartbeat_thread.connection_lost.connect(self.on_connection_lost)
        self.heartbeat_thread.start()
    
    def restart_camera(self):
        self.camera_thread._init_device()

    def on_connection_lost(self):
        """连接丢失处理"""
        self.heartbeat_thread.stop()
        self.reconnect_manager.show_reconnect_dialog()
        self.camera_thread.stop()

    # def center(self):
    #     """居中显示窗口"""
    #     screen = QDesktopWidget().screenGeometry()
    #     size = self.geometry()
    #     self.move(
    #         (screen.width() - size.width()) // 2,
    #         (screen.height() - size.height()) // 2
    #     )

    def update_display(self, original_frame):
        """更新显示的图像"""
        # if original_frame is None:
        #     original_frame = cv2.imread("figs/cframe.jpg")
        self._display_image(original_frame, self.ui.image_label)
        
    def _display_image(self, image, label):
        """内部图像显示方法"""
        height, width, _ = image.shape
        bytes_per_line = 3 * width
        q_img = QImage(image.data, width, height, bytes_per_line, 
                      QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        label.setAlignment(Qt.AlignCenter)
        label.setPixmap(pixmap.scaled(
            label.width(), 
            label.height(), 
            Qt.KeepAspectRatio, 
            Qt.FastTransformation
        ))

    def show_login_window(self):
        """显示登录窗口（单例模式）"""
        if self.login is None:
            self.login = LoginWindow(parent=self)
            self.login.login_success_signal.connect(self._handle_login_success)
            self._center_child_window(self.login)
            self.login.destroyed.connect(lambda: setattr(self, 'login', None))
            self.login.show()
        else:
            self._activate_window(self.login)

    def _handle_setting_action(self):
        """处理设置菜单动作"""
        self.triggered_action = self.sender()
        self.show_login_window()

    def _handle_needle_action(self):
        """处理针具管理菜单动作"""
        self.triggered_action = self.sender()
        self.show_login_window()

    def _handle_login_success(self):
        """登录成功后的处理"""
        if self.triggered_action == self.ui.bottom_buttons["设置"]:
            self.show_setting_window()
        else:
            self.show_needle_inventory_management(self.triggered_action)

    def show_needle_inventory_management(self, button):
        # """显示针具管理窗口"""
        if self.management is None:
            if button.text() == "⚙":
                self.management = InventoryDialog('change', button.objectName()[-5], parent=self)
            else:
                self.management = InventoryDialog('create', button.objectName()[-5], parent=self)
                self.camera_thread.tempstop = True
            self._connect_management_signals()
            # self._center_child_window(self.management)
            self.management.destroyed.connect(lambda: setattr(self, 'management', None))
            self.management.destroyed.connect(lambda: setattr(self.camera_thread, 'tempstop', False))
            self.management.show()
        else:
            self._activate_window(self.management)

    def _connect_management_signals(self):
        """连接针具管理信号"""
        self.management.get_needle_size_signal.connect(
            self.camera_thread.handle_measurement_request
        )
        self.camera_thread.measurement_complete.connect(
            self.management.receive_size_result
        )
        self.management.update_warehouse_signal.connect(
            self.ui.update_warehouse_cards
        )

    def show_setting_window(self):
        """显示设置窗口"""
        if self.setting is None:
            self.setting = ConfigSettingUI(parent=self)
            # self._center_child_window(self.setting)
            self.setting.destroyed.connect(lambda: setattr(self, 'setting', None))
            self.setting.show()
        else:
            self._activate_window(self.setting)

    def show_log_viewer(self):
        """显示日志查看器"""
        if self.log_viewer is None:
            self.log_viewer = LogViewer(self.log_stream, parent=self)
            # self._center_child_window(self.log_viewer)
            self.log_viewer.destroyed.connect(lambda: setattr(self, 'log_viewer', None))
            self.log_viewer.show()
        else:
            self._activate_window(self.log_viewer)

    def _center_child_window(self, window):
        """居中显示子窗口"""
        window.move(
            self.geometry().center() - window.rect().center()
        )

    def _activate_window(self, window):
        """激活并置顶窗口"""
        window.activateWindow()
        window.raise_()

    def manual_detect_needle(self):
        """手动检测针具"""
        self.camera_thread.setting_manual_detect_bool

    def exit_system(self):
        """退出系统"""
        self.camera_thread.stop()
        QApplication.quit()

    def show_needle_selection_dialog(self, matches):
        """显示针具选择对话框"""
        dialog = NeedleSelectionDialog(matches, self)
        if dialog.exec_() == QDialog.Accepted:
            self.camera_thread.user_selection = str(dialog.selected_id)
        
        # 使用上下文管理器简化锁操作
        locker = QMutexLocker(self.camera_thread.mutex)
        self.camera_thread.wait_condition.wakeAll()

    def show_warning(self, message):
        """显示警告对话框"""
        if self.warning_dialog is None:
            # 创建警告对话框
            self.warning_dialog = QMessageBox(self)
            self.warning_dialog.setWindowTitle("警告")
            self.warning_dialog.setText(message)
            self.warning_dialog.setIcon(QMessageBox.Warning)
            
            # 设置标准按钮
            self.warning_dialog.setStandardButtons(QMessageBox.Ok)
            
            # 设置样式表 - 调整文字和按钮大小
            self.warning_dialog.setStyleSheet("""
                QMessageBox QLabel {
                    font-size: 25px;  /* 设置消息文本字体大小 */
                }
            """)
            
            # 单独设置按钮大小
            ok_button = self.warning_dialog.button(QMessageBox.Ok)
            if ok_button:
                ok_button.setText("确定")  # 设置按钮文本
                ok_button.setFixedSize(150, 80)  # 固定按钮大小
            
            # 对话框关闭时自动设置为None
            self.warning_dialog.destroyed.connect(lambda: setattr(self, 'warning_dialog', None))
        else:
            self.warning_dialog.setText(message)
            self.warning_dialog.setWindowTitle("警告")
        
        self.warning_dialog.show()
        self.warning_dialog.raise_()  # 提升到最前面
        self.warning_dialog.activateWindow()  # 激活窗口


    def redirect_output(self):
        self.log_stream = EmittingStream(
            max_buffered_lines=self.config.max_buffered_lines, #条
            flush_interval= self.config.flush_interval, #秒
            log_dir="logs",
            max_log_days=self.config.max_log_days
        )
        sys.stdout = self.log_stream

    def closeEvent(self, event):
        """窗口关闭事件"""
        sys.stdout = sys.__stdout__
        super().closeEvent(event)
        self.camera_thread.stop()

    def setup_exit_monitor(self):
        """设置退出监控"""  
        # 异常信号捕获
        signal.signal(signal.SIGTERM, self.on_forced_exit)
        signal.signal(signal.SIGINT, self.on_forced_exit)
        # 捕获异常
        sys.excepthook = self.exception_hook

    def on_forced_exit(self, signum=None, frame=None):
        """强制退出处理"""
        self.camera_thread.stop()
        print(f"应用程序被强制终止 (信号: {signum})")
        # 紧急保存操作...
        QApplication.quit()

    def exception_hook(self, exc_type, exc_value, exc_traceback):
        """
        全局异常处理函数
        """
        # 格式化异常信息
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log_entry = f"程序崩溃:\n{error_msg}\n{'='*50}\n"
        print(log_entry)
        self.camera_thread.stop()
        # 调用默认的异常处理（退出程序）
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()  # PEP8命名
    main_window.show()
    sys.exit(app.exec_())