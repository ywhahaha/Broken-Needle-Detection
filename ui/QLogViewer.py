from datetime import datetime
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QTextCharFormat, QColor
from PyQt5.QtWidgets import (QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout,
                            QDialog, QLabel, QCalendarWidget)

class LogViewer(QDialog):
    """日志查看器（带退出按钮，在父窗口内显示）"""
    def __init__(self, log_stream, parent=None):
        super().__init__(parent)
        self.log_stream = log_stream
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无标题栏
            Qt.WindowStaysOnTopHint |  # 保持在顶层
            Qt.WindowFullscreenButtonHint  # 支持全屏
        )
        
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setGeometry(self.parent().geometry())

        # 创建界面组件
        self.create_ui()
        
        # 自动保存当前日志
        self.log_stream.conditional_flush()

        self.last_refresh_time = None
        
        # 初始加载当天日志
        self.refresh_log()
    
    def create_ui(self):
        """创建界面布局，补充背景样式解决透明问题"""
        # -------------------------- 新增：全局样式表（关键解决透明问题） --------------------------
        self.setStyleSheet("""
            /* 1. 主窗口背景：避免底层透明穿透 */
            QDialog {
                background-color: #f8f8f8; /* 与界面主色调匹配，覆盖透明 */
            }
            
            /* 2. 标签控件：解决日期标签底部透明 */
            QLabel {
                background-color: #f8f8f8; /* 与主窗口背景一致 */
                border: none; /* 清除默认边框（若有） */
                padding: 5px 0; /* 可选：增加内边距，避免文字贴边 */
                font-size: 25px;
                min-height: 100px;
            }
            
            /* 3. 按钮控件：解决日历/刷新/退出按钮底部透明 */
            QPushButton {
                background-color: #e0e0e0; /* 按钮背景色（可自定义） */
                border: 1px solid #cccccc; /* 按钮边框（增强视觉层次） */
                border-radius: 4px; /* 可选：圆角优化 */
                padding: 5px 10px; /* 内边距，避免文字贴边 */
                min-width: 200px;
                min-height: 100px;
                font-size: 25px;
            }
            /* 按钮 hover 状态（可选，增强交互） */
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            
            /* 4. 日历控件（弹出窗口）：避免弹出时透明 */
            QCalendarWidget {
                background-color: white; /* 日历背景色 */
                border: 1px solid #cccccc;
            }
            /* 日历头部（月份/年份区域）背景 */
            QCalendarWidget QWidget {
                background-color: white;
            }
            /* 日历日期单元格背景 */
            QCalendarWidget QAbstractItemView {
                background-color: white;
            }
            
            /* 5. 文本编辑框（日志区域）：确保背景不透明 */
            QTextEdit {
                background-color: white; /* 日志区域背景（与之前样式合并） */
                border: 1px solid #cccccc;
                font-size: 20px;       
            }
                           
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 60px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 50px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f1f1f1;
                height: 60px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #c1c1c1;
                min-width: 50px;
            }
        """)

        # -------------------------- 原有界面布局代码（保持不变） --------------------------
        # 顶部控制栏
        control_layout = QHBoxLayout()
        
        # 日期标签
        self.date_label = QLabel("当前日志日期:")
        self.current_date_label = QLabel(datetime.now().strftime("%Y-%m-%d"))
        
        # 日历控件
        self.calendar = QCalendarWidget()
        self.calendar.setWindowFlags(Qt.Popup)
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_calendar_clicked)
        self.update_calendar_dates()
        
        # 日历按钮
        self.calendar_btn = QPushButton("选择日期")
        self.calendar_btn.clicked.connect(self.show_calendar)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_log)
        
        # 退出按钮
        self.exit_btn = QPushButton("退出")
        self.exit_btn.clicked.connect(self.close)
        
        # 添加到控制栏
        control_layout.addWidget(self.date_label)
        control_layout.addWidget(self.current_date_label)
        control_layout.addStretch()
        control_layout.addWidget(self.calendar_btn)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.exit_btn)
        
        # 日志显示区域（原有样式可保留，已在全局QSS中补充背景）
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.NoWrap)
        self.text_edit.setFontFamily("Courier New")
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.text_edit)
        
        # 设置布局边距和间距
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        self.setLayout(main_layout)
        
        # 设置大小策略
        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def update_calendar_dates(self):
        """更新日历中的可用日期"""
        # 获取日期范围
        today = QDate.currentDate()
        min_date = today.addDays(-self.log_stream.max_log_days)
        
        # 设置日历控件的日期范围
        minimumdate = QDate(min_date.year(), min_date.month(), 1)
        maximumdate = QDate(today.year(), today.month(), today.daysInMonth())
    
        self.calendar.setMinimumDate(minimumdate)
        self.calendar.setMaximumDate(maximumdate)

        available_dates = self.log_stream.get_available_dates()
        available_qdates = [QDate.fromString(date, "yyyy-MM-dd") for date in available_dates]

        # 创建禁用日期的格式
        disabled_format = QTextCharFormat()
        disabled_format.setForeground(QColor(200, 200, 200))  # 灰色

        date = self.calendar.minimumDate()
       
        while date <= self.calendar.maximumDate():
            if date not in available_qdates:
                self.calendar.setDateTextFormat(date, disabled_format)
            date = date.addDays(1)
    
    def show_calendar(self):
        """显示日历选择"""
        # 在按钮下方显示日历
        # global_pos = self.calendar_btn.mapToGlobal(self.calendar_btn.rect().bottomLeft())
        # self.calendar.move(global_pos)
        # self.calendar.show()

        window_center = self.mapToGlobal(self.rect().center())
    
        # 调整日历位置，使其中心与窗口中心对齐
        calendar_width = self.calendar.width()
        calendar_height = self.calendar.height()
        
        self.calendar.move(
            window_center.x() - calendar_width // 2,
            window_center.y() - calendar_height // 2
        )
        self.calendar.show()
    
    def on_calendar_clicked(self, date):
        """日历选择日期"""
        date_str = date.toString("yyyy-MM-dd")
        available_dates = self.log_stream.get_available_dates()
        
        if date_str in available_dates:
            self.current_date_label.setText(date_str)
            self.refresh_log()
        self.calendar.hide()
    
    def refresh_log(self):
        """刷新日志内容（自动获取最新记录）"""
        date_str = self.current_date_label.text()
        
        # 如果是当天日志，先强制保存缓冲区
        if date_str == datetime.now().strftime("%Y-%m-%d"):
            self.log_stream.conditional_flush()
        
        # 获取日志内容
        log_content = self.log_stream.get_log_content(date_str)
        
        # 如果是当天日志且不是第一次刷新，只追加新内容
        if (date_str == datetime.now().strftime("%Y-%m-%d") 
                and self.last_refresh_time is not None):
            # 提取上次刷新后的新内容
            new_content = self.extract_new_content(log_content)
            if new_content:
                self.text_edit.append(new_content)
        else:
            # 首次加载或非当天日志，全量刷新
            self.text_edit.setPlainText(log_content)
        
        # 滚动到底部并更新时间戳
        self.text_edit.moveCursor(self.text_edit.textCursor().End)
        self.last_refresh_time = datetime.now()

    def extract_new_content(self, full_content):
        """
        提取上次刷新后新增的日志内容
        :return: 新增内容字符串
        """
        # 获取当前文本的最后一行
        current_text = self.text_edit.toPlainText()
        if not current_text:
            return full_content
        
        # 找到最后一行在完整日志中的位置
        last_line = current_text.strip().split('\n')[-1]
        pos = full_content.rfind(last_line)
        
        # 返回位置之后的所有内容
        if pos >= 0:
            return full_content[pos + len(last_line):].lstrip('\n')
        return full_content  # 如果找不到匹配，返回全部内容
