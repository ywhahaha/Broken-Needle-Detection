#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派WiFi连接程序 - 修复版
需要安装: sudo apt install network-manager
"""

import sys
import subprocess
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

# 环境变量设置
os.environ["QT_IM_MODULE"] = "qtvirtualkeyboard"
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = "/usr/lib/aarch64-linux-gnu/qt5/plugins/platforms/"

class SimpleWifiConnect(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_wifi = None
        self.init_ui()
        self.scan_wifi()
        
    def init_ui(self):
        self.setWindowTitle('树莓派WiFi连接')
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("WiFi连接器")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # WiFi列表
        layout.addWidget(QLabel("可用的WiFi网络:"))
        self.wifi_list = QListWidget()
        self.wifi_list.setStyleSheet("""
            QListWidget {
                font-size: 20px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QScrollBar:vertical {
                width: 40px;  /* 垂直滚动条宽度 */
            }
            QScrollBar:horizontal {
                height: 40px;  /* 水平滚动条高度 */
            }
        """)
        self.wifi_list.itemClicked.connect(self.select_wifi)
        layout.addWidget(self.wifi_list)
        
        # 密码输入
        layout.addWidget(QLabel("密码:"))
        self.password_input = QLineEdit()
        # self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        # 连接按钮
        self.connect_btn = QPushButton("连接")
        self.connect_btn.clicked.connect(self.connect_wifi)
        layout.addWidget(self.connect_btn)
        
        # 状态显示
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.clicked.connect(self.scan_wifi)
        layout.addWidget(refresh_btn)
        
        # 断开连接按钮
        disconnect_btn = QPushButton("断开连接")
        disconnect_btn.clicked.connect(self.disconnect_wifi)
        layout.addWidget(disconnect_btn)
        
        self.setLayout(layout)
        
    def scan_wifi(self):
        """扫描WiFi网络"""
        self.wifi_list.clear()
        self.status_label.setText("正在扫描WiFi...")
        QApplication.processEvents()  # 更新UI
        
        try:
            # 使用nmcli扫描WiFi，获取更多信息
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'SSID,SECURITY,SIGNAL', 'dev', 'wifi'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                networks = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 1 and parts[0]:  # 确保有SSID
                            ssid = parts[0]
                            if ssid and ssid not in networks:
                                # 显示带安全类型和信号强度的网络
                                security = parts[1] if len(parts) > 1 else ""
                                signal = parts[2] if len(parts) > 2 else ""
                                display_text = f"{ssid} {'🔒' if security else '🌐'} {signal}%"
                                self.wifi_list.addItem(display_text)
                                networks.append(ssid)
                
                self.status_label.setText(f"找到 {len(networks)} 个网络")
            else:
                # 尝试使用iwlist扫描
                self.scan_with_iwlist()
                
        except Exception as e:
            self.status_label.setText(f"错误: {str(e)}")
            
    def scan_with_iwlist(self):
        """使用iwlist扫描WiFi（备用方法）"""
        try:
            result = subprocess.run(
                ['sudo', 'iwlist', 'wlan0', 'scan'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                ssids = []
                for line in result.stdout.split('\n'):
                    if 'ESSID:' in line:
                        ssid = line.split('ESSID:"')[1].split('"')[0]
                        if ssid and ssid not in ssids:
                            ssids.append(ssid)
                            self.wifi_list.addItem(ssid)
                self.status_label.setText(f"找到 {len(ssids)} 个网络")
            else:
                self.status_label.setText("扫描失败，请检查无线网卡")
                
        except Exception as e:
            self.status_label.setText(f"iwlist错误: {str(e)}")
            
    def select_wifi(self, item):
        """选择WiFi"""
        item_text = item.text()
        # 提取纯SSID（去掉emoji和信号强度）
        ssid = item_text.split(' ')[0]
        self.selected_wifi = ssid
        self.status_label.setText(f"已选择: {ssid}")
        
    def connect_wifi(self):
        """连接WiFi"""
        if not self.selected_wifi:
            self.status_label.setText("请先选择一个WiFi网络")
            return
            
        password = self.password_input.text()
        if not password:
            # 尝试连接开放网络
            self.connect_open_wifi()
            return
            
        self.status_label.setText(f"正在连接 {self.selected_wifi}...")
        QApplication.processEvents()  # 更新UI
        
        try:
            # 方法1: 使用nmcli连接（修复版）
            if self.connect_with_nmcli(password):
                return
                
            # 方法2: 如果nmcli失败，尝试wpa_supplicant
            if self.connect_with_wpa_supplicant(password):
                return
                
            self.status_label.setText("所有连接方法都失败")
                
        except Exception as e:
            self.status_label.setText(f"连接错误: {str(e)}")
            
    def connect_open_wifi(self):
        """连接开放网络（无密码）"""
        try:
            cmd = ['sudo', 'nmcli', 'dev', 'wifi', 'connect', self.selected_wifi]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.status_label.setText(f"✓ 已连接到开放网络 {self.selected_wifi}")
            else:
                self.status_label.setText(f"连接失败: {result.stderr}")
                
        except Exception as e:
            self.status_label.setText(f"错误: {str(e)}")
    
    def connect_with_nmcli(self, password):
        """使用nmcli连接WiFi"""
        try:
            # 先删除已存在的连接配置
            subprocess.run(
                ['sudo', 'nmcli', 'connection', 'delete', self.selected_wifi],
                capture_output=True,
                text=True
            )
            
            # 创建新的WiFi连接配置
            cmd = [
                'sudo', 'nmcli', 'device', 'wifi', 'connect',
                self.selected_wifi, 'password', password
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.status_label.setText(f"✓ 已连接到 {self.selected_wifi}")
                return True
            else:
                # 尝试另一种语法
                cmd = [
                    'sudo', 'nmcli', 'connection', 'add',
                    'type', 'wifi',
                    'con-name', self.selected_wifi,
                    'ifname', 'wlan0',
                    'ssid', self.selected_wifi
                ]
                
                subprocess.run(cmd, capture_output=True, text=True)
                
                # 设置WiFi安全
                cmd = [
                    'sudo', 'nmcli', 'connection', 'modify', self.selected_wifi,
                    'wifi-sec.key-mgmt', 'wpa-psk',
                    'wifi-sec.psk', password
                ]
                
                subprocess.run(cmd, capture_output=True, text=True)
                
                # 启用连接
                cmd = ['sudo', 'nmcli', 'connection', 'up', self.selected_wifi]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.status_label.setText(f"✓ 已连接到 {self.selected_wifi}")
                    return True
                    
            return False
            
        except Exception as e:
            self.status_label.setText(f"nmcli错误: {str(e)}")
            return False
    
    def connect_with_wpa_supplicant(self, password):
        """使用wpa_supplicant连接WiFi"""
        try:
            # 生成wpa_passphrase配置
            cmd = ['wpa_passphrase', self.selected_wifi, password]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # 备份原配置
                subprocess.run(['sudo', 'cp', '/etc/wpa_supplicant/wpa_supplicant.conf',
                              '/etc/wpa_supplicant/wpa_supplicant.conf.bak'])
                
                # 追加新配置
                with open('/tmp/wpa_temp.conf', 'w') as f:
                    f.write(result.stdout)
                
                subprocess.run(['sudo', 'cp', '/tmp/wpa_temp.conf', 
                              '/etc/wpa_supplicant/wpa_supplicant.conf'])
                
                # 重启wpa_supplicant
                subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'])
                subprocess.run(['sudo', 'dhclient', 'wlan0'])
                
                self.status_label.setText(f"✓ 正在连接 {self.selected_wifi} (wpa_supplicant)")
                return True
                
        except Exception as e:
            self.status_label.setText(f"wpa_supplicant错误: {str(e)}")
            return False
    
    def disconnect_wifi(self):
        """断开当前WiFi连接"""
        try:
            cmd = ['sudo', 'nmcli', 'radio', 'wifi', 'off']
            subprocess.run(cmd, capture_output=True, text=True)
            
            # 等待一下再打开
            subprocess.run(['sleep', '2'])
            
            cmd = ['sudo', 'nmcli', 'radio', 'wifi', 'on']
            subprocess.run(cmd, capture_output=True, text=True)
            
            self.status_label.setText("已断开WiFi连接")
            self.selected_wifi = None
            self.password_input.clear()
            
        except Exception as e:
            self.status_label.setText(f"断开错误: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimpleWifiConnect()
    window.show()
    sys.exit(app.exec_())
