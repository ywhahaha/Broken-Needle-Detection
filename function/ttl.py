import time
from PyQt5.QtCore import QMutex
import serial
from typing import Optional, Dict, Tuple
import glob

_global_mutex = QMutex()

class NeedleController:
    """机针管家串口通信控制器（协议V1.1）"""
    
    # 协议常量
    START_CODE = bytes.fromhex('AA55')
    END_CODE = bytes.fromhex('EF')
    
    # 命令码定义
    CMD_GET_HEARTBEAT = 0x01
    CMD_GET_STATUS = 0x02
    CMD_DRIVE_MOTOR = 0x03
    CMD_DRIVE_SOLENOID = 0x04
    CMD_SET_LED = 0x05
    CMD_QUERY_TIMEOUT = 0x06
    CMD_RESET = 0x60


    def __init__(self):
        self.ser = None

    # def connect(self, ports: list = ['/dev/ttyUSB0', '/dev/ttyUSB1','/dev/ttyUSB2'], baudrate: int = 9600) -> bool:
    #     """
    #     尝试连接多个串口（线程安全）
    #     参数:
    #         ports: 按优先级排序的串口列表
    #         baudrate: 波特率
    #     返回:
    #         bool: 是否连接成功
    #     """
    #     _global_mutex.lock()
    #     try:
    #         # 先关闭已有连接
    #         if hasattr(self, 'ser') and self.ser is not None:
    #             self.ser.close()
    #             self.ser = None

    #         # 依次尝试所有端口
    #         for port in ports:
    #             try:
    #                 self.ser = serial.Serial(port, baudrate, timeout=1)
    #                 print(f"成功连接到串口: {port}")
    #                 return True
    #             except (serial.SerialException, OSError) as e:
    #                 print(f"无法连接 {port}: {str(e)}")
    #                 continue

    #         # 所有端口均失败
    #         print("所有串口连接尝试均失败")
    #         return False
    #     finally:
    #         _global_mutex.unlock()

    def connect(self, baudrate: int = 9600) -> bool:
        """
        自动检测并连接USB串口设备（简化版）
        """
        _global_mutex.lock()
        try:
            # 关闭已有连接
            if hasattr(self, 'ser') and self.ser is not None:
                self.ser.close()
                self.ser = None

            # 查找所有USB串口设备
            usb_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
            
            if not usb_ports:
                print("未找到USB串口设备")
                return False

            # print(f"找到USB串口设备: {usb_ports}")

            # 尝试连接每个设备
            for port in usb_ports:
                try:
                    self.ser = serial.Serial(port, baudrate, timeout=1)
                    print(f"成功连接到: {port}")
                    return True
                except (serial.SerialException, OSError) as e:
                    print(f"连接 {port} 失败: {e}")
                    continue

            print("所有USB串口连接尝试均失败")
            return False
            
        finally:
            _global_mutex.unlock()
        
    def close(self):
        """关闭串口连接（线程安全）"""
        _global_mutex.lock()
        try:
            if self.ser is not None and self.ser.is_open:
                self.ser.close()
        finally:
            _global_mutex.unlock()

    def _build_command(self, cmd: int, params: bytes = None) -> bytes:
        """
        构建协议帧
        :param cmd: 命令码
        :param params: 参数字节（可选）
        :return: 完整的协议帧
        """
        if params is None:
            params = bytes()
            
        # 构建数据部分（长度 + 命令码 + 参数）
        length = 1 + 1 + len(params)  # 长度1字节 + 命令码1字节 + 参数长度
        data = bytes([length, cmd]) + params
        
        # 计算校验和（长度+命令码+参数的累加和低8位）
        checksum = sum(data) & 0xFF
        
        # 组合完整帧
        return self.START_CODE + data + bytes([checksum]) + self.END_CODE

    def _parse_response(self, response: bytes) -> Tuple[bool, Optional[Dict]]:
        """
        解析响应数据
        :param response: 原始响应字节
        :return: (是否成功, 参数字典)
        """
        if not response or len(response) < 5:
            return False, None
            
        # 检查起始码和结束码
        if response[:2] != self.START_CODE or response[-1:] != self.END_CODE:
            return False, None
            
        # 提取数据部分（长度+命令码+参数+校验和）
        data = response[2:-1]
        if len(data) != data[0] + 1:  # 长度字段应等于后续数据长度
            return False, None
            
        # 校验和验证
        if sum(data[:-1]) & 0xFF != data[-1]:
            return False, None
            
        # 提取命令码和参数
        cmd = data[1]
        params = data[2:-1]
        
        # 根据命令码解析参数
        result = {'command': cmd}
        if cmd == self.CMD_GET_HEARTBEAT:
            result['heartbeat_count'] = int.from_bytes(params, byteorder='big') if params else None
        elif cmd == self.CMD_GET_STATUS:
            if len(params) >= 1:
                status1 = params[0]
                result.update({
                    'recycle_motor_running': bool(status1 & 0x01),
                    'release_motor_running': bool(status1 & 0x02),
                    'recycle_motor_timeout': bool(status1 & 0x04),
                    'release_motor_timeout': bool(status1 & 0x08),
                    'recycle_home_pos': bool(status1 & 0x10),
                    'release_home_pos': bool(status1 & 0x20),
                    'recycle_door_open': bool(status1 & 0x40),
                    'release_door_open': bool(status1 & 0x80)
                })
        elif cmd == self.CMD_QUERY_TIMEOUT:
            result['timeout_slot'] = params[0] if params else None
            
        return True, result

    def send_command(self, cmd: int, params: bytes = None, timeout: float = 1.0) -> Optional[Dict]:
        """
        发送指令并获取响应（线程安全版本）
        :param cmd: 命令码
        :param params: 参数字节（可选）
        :param timeout: 超时时间（秒）
        :return: 解析后的参数字典（失败返回None）
        """
        current = time.time()
        _global_mutex.lock()  # 加锁
        try:
            if not self.ser or not self.ser.is_open:
                # print("串口未连接")
                return None

            self.ser.reset_input_buffer()

            # 构建和发送命令
            frame = self._build_command(cmd, params)
            # print(f"[发送] {frame.hex(' ')}")
            self.ser.write(frame)
            
            # 等待并读取响应
            start_time = time.time()
            response = bytes()
            while time.time() - start_time < timeout:
                if self.ser.in_waiting:
                    response += self.ser.read(self.ser.in_waiting)
                    # 检查是否收到完整帧
                    if len(response) >= 5 and response[-1:] == self.END_CODE:
                        break
                time.sleep(0.02)

            # print(f"[接收] {response.hex(' ')}")
            success, result = self._parse_response(response)
            return result if success else None

        except Exception as e:
            print(f"命令执行失败: {str(e)}")
            return None
        finally:
            _global_mutex.unlock()  # 解锁

    # ---------- 高层指令封装 ----------
    def get_heartbeat(self) -> Optional[int]:
        """查询心跳计数"""
        res = self.send_command(self.CMD_GET_HEARTBEAT)
        return res['heartbeat_count'] if res else None

    def get_status(self) -> Optional[Dict]:
        """查询控制板状态"""
        return self.send_command(self.CMD_GET_STATUS)

    def drive_motor(self, slot: int, is_recycle: bool = False, 
                   period: int = 100, duty_cycle: int = 6) -> bool:
        """
        驱动电机
        :param slot: 仓位号（1-4）
        :param is_recycle: 是否为回收电机
        :param period: PWM周期（0-255ms）
        :param duty_cycle: 占空比（0-100%）
        :return: 是否成功
        """
        motor_code = 0x30 if is_recycle else slot
        params = bytes([motor_code, period, duty_cycle])
        return self.send_command(self.CMD_DRIVE_MOTOR, params) is not None

    def drive_solenoid(self, is_recycle_bin: bool = True) -> bool:
        """驱动电磁阀"""
        params = bytes([0x01 if is_recycle_bin else 0x02])
        return self.send_command(self.CMD_DRIVE_SOLENOID, params) is not None

    def set_led(self, brightness: int) -> bool:
        """设置LED亮度（0-255）"""
        params = bytes([brightness])
        # print(params)
        return self.send_command(self.CMD_SET_LED, params) is not None

    def query_timeout(self) -> Optional[int]:
        """查询超时仓位号"""
        res = self.send_command(self.CMD_QUERY_TIMEOUT)
        return res['timeout_slot'] if res else None

    def reset(self) -> bool:
        """复位控制板"""
        return self.send_command(self.CMD_RESET) is not None

# 使用示例
if __name__ == "__main__":
    controller = NeedleController()
    controller.connect()
    
    try:
        # 查询心跳时间
        # print(controller.get_heartbeat())

        # 查询状态
        # status = controller.get_status()
        # print(f"当前状态: {status}")

        # # 发放1号仓位机针
        controller.drive_motor(slot=0, is_recycle=True)

        # # 查询状态
        # status = controller.get_status()['recycle_motor_running']
        # if not status:
        #     print("电机")
        # else: 
            # print(f"当前状态: {status}")
        
        # 驱动仓门电磁阀
        # print(controller.drive_solenoid(False))
        
        # 设置LED亮度
        # controller.set_led(255)
        
        # # 查询超时
        # timeout_slot = controller.query_timeout()
        # if timeout_slot:
        #     print(f"超时仓位: {timeout_slot}")

        # 复位
        # controller.reset()

            
    finally:
        controller.close()