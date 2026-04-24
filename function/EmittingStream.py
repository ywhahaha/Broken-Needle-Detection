import sys
import time
import os
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QMutex
from function.get_resource_path import get_path

class EmittingStream(QObject):
    """日志流处理类（支持多条件保存和按日期分割日志）"""
    text_written = pyqtSignal(str)
    
    def __init__(self, parent=None, max_buffered_lines=10, flush_interval=60, 
                 log_dir="logs", max_log_days=30):
        super().__init__(parent)
        self.buffer = []
        self.mutex = QMutex()
        self.max_buffered_lines = max_buffered_lines
        self.flush_interval = flush_interval * 1000  # 转换为毫秒
        self.log_dir = get_path(log_dir)
        self.max_log_days = max_log_days
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 初始化定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.conditional_flush)
        self.timer.start(self.flush_interval)
        
        # 程序退出时保存日志
        import atexit
        atexit.register(self.force_flush)

    def get_current_logfile(self):
        """根据当前日期生成日志文件名"""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"app_{today}.log")

    def write(self, text):
        """重写write方法"""
        text = text.strip()
        if text:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] {text}"
            
            # 线程安全操作缓冲区
            self.mutex.lock()
            self.buffer.append(log_entry)
            self.mutex.unlock()
            
            # 实时发射信号
            self.text_written.emit(text)
            
            # 检查是否达到缓冲上限
            if len(self.buffer) >= self.max_buffered_lines:
                self.conditional_flush()
            
            # 保持原始输出
            sys.__stdout__.write(text + '\n')

    def flush(self):
        pass

    def conditional_flush(self):
        """条件触发保存日志（缓冲区非空时）"""
        if not self.buffer:
            return
            
        self.mutex.lock()
        try:
            log_file = self.get_current_logfile()
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write('\n'.join(self.buffer) + '\n')
            self.buffer.clear()
            
            # 清理过期日志
            self.cleanup_old_logs()
        except Exception as e:
            sys.__stdout__.write(f"日志写入失败: {str(e)}\n")
        finally:
            self.mutex.unlock()

    def cleanup_old_logs(self):
        """清理超过保留天数的日志"""
        now = datetime.now()
        for filename in os.listdir(self.log_dir):
            if filename.startswith("app_") and filename.endswith(".log"):
                try:
                    date_str = filename[4:-4]
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if (now - file_date).days > self.max_log_days:
                        os.remove(os.path.join(self.log_dir, filename))
                except ValueError:
                    continue

    def force_flush(self):
        """强制保存剩余日志"""
        if self.buffer:
            self.conditional_flush()
        self.timer.stop()

    def get_log_content(self, date_str=None):
        """
        读取日志内容
        :param date_str: 日期字符串(格式YYYY-MM-DD)，None表示当天
        :return: 日志内容字符串
        """
        try:
            if date_str is None:
                log_file = self.get_current_logfile()
            else:
                log_file = os.path.join(self.log_dir, f"app_{date_str}.log")
                
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"未找到{date_str}的日志文件"
        except Exception as e:
            return f"读取日志失败: {str(e)}"

    def get_available_dates(self):
        """获取所有可用的日志日期"""
        dates = []
        for filename in os.listdir(self.log_dir):
            if filename.startswith("app_") and filename.endswith(".log"):
                try:
                    date_str = filename[4:-4]
                    datetime.strptime(date_str, "%Y-%m-%d")  # 验证日期格式
                    dates.append(date_str)
                except ValueError:
                    continue
        return sorted(dates, reverse=True)