"""
集成控制系统：同时控制AGV底盘、机械臂和外部轴系统
使用配置文件分离配置参数
"""

import threading
import time
import json
import socket
from typing import List, Optional, Dict, Any
import requests
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # lumi_demo 目录
sys.path.insert(0, parent_dir)
import config
from JAKA_SDK_WINDOWS import jkrc


DEG_TO_RAD = 3.1415926 / 180.0
RAD_TO_DEG = 180.0 / 3.1415926


class RobotController:
    """机械臂控制器类"""
    
    def __init__(self, ip_address: str = config.ROBOT_IP):
        """
        初始化机械臂控制器
        
        Args:
            ip_address: 机械臂IP地址，默认为配置中的值
        """
        self.robot = jkrc.RC(ip_address)
        self._initialize_robot()
    
    def _initialize_robot(self) -> None:
        """初始化机器人连接并上电"""
        # 登录机器人控制器 1.7版本登录方式
        login_result = self.robot.login()
        if login_result[0] != 0:
            # 尝试备用登录方式 3.2版本登录方式
            login_result = self.robot.login(1)
                
        # 机器人上电
        power_on_result = self.robot.power_on()
        if power_on_result[0] != 0:
            raise RuntimeError("机器人上电失败")
        
        # 使能机器人
        self.robot.enable_robot()
    
    def move_to_joint_position(self, 
                               joint_angles_deg: List[float], 
                               flag: bool = True,
                               velocity_deg_per_sec: float = 90) -> None:
        """
        控制机器人移动到指定关节角度
        
        Args:
            joint_angles_deg: 目标关节角度 [J1, J2, J3, J4, J5, J6] (单位: 度)
            velocity_deg_per_sec: 关节速度 (单位: 度/秒)
        """
        # 角度转弧度
        joint_positions_rad = [angle * DEG_TO_RAD for angle in joint_angles_deg]
        
        # 速度转换
        velocity_rad_per_sec = velocity_deg_per_sec * DEG_TO_RAD
        
        # 执行关节运动
        self.robot.joint_move(joint_positions_rad, 0, flag, velocity_rad_per_sec)

class ExternalAxisController:
    """外部轴控制器类"""
    
    @staticmethod
    def reset_and_enable_all_joints() -> bool:
        """
        重置并使能所有外部轴关节
        
        Returns:
            bool: 操作是否成功
        """
        try:
            # 重置所有关节
            reset_response = requests.post(
                config.EXT_RESET_URL, 
                json={}
            )
            if reset_response.status_code != 200:
                print(f"重置失败: {reset_response.status_code}")
                return False
            print("所有外部轴关节已重置")
            
            # 使能所有关节
            enable_response = requests.post(
                config.EXT_ENABLE_URL, 
                json={"enable": 1}
            )
            if enable_response.status_code != 200:
                print(f"使能失败: {enable_response.status_code}")
                return False
            print("所有外部轴关节已使能")
            
            return True
            
        except requests.RequestException as e:
            print(f"网络请求错误: {e}")
            return False
    
    @staticmethod
    def move_to_position(position: List[float], 
                         velocity: float = 200, 
                         acceleration: float = 200) -> bool:
        """
        控制外部设备移动到指定位置
        
        Args:
            position: 目标位置坐标 [x, y, z, r]
            velocity: 移动速度
            acceleration: 加速度
            
        Returns:
            bool: 移动是否成功
        """
        # 确保关节已使能
        if not ExternalAxisController.reset_and_enable_all_joints():
            return False
        
        try:
            response = requests.post(
                config.EXT_MOVETO_URL,
                json={"pos": position, "vel": velocity, "acc": acceleration}
            )
            
            if response.status_code == 200:
                print('外部轴移动成功!')
                return True
            else:
                print(f"移动失败: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"移动请求错误: {e}")
            return False


class AGVController:
    """AGV底盘控制器类"""
    
    @staticmethod
    def send_command(command: str, 
                     host: str = config.AGV_HOST, 
                     port: int = config.AGV_PORT) -> Optional[Dict[str, Any]]:
        """
        通过TCP/IP发送命令并接收响应
        
        Args:
            command: 要发送的命令字符串
            host: 目标主机IP地址
            port: 目标主机端口
            
        Returns:
            Optional[Dict]: JSON格式的响应数据，失败时返回None
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # 设置超时时间
                sock.settimeout(5)
                
                # 连接到服务器
                sock.connect((host, port))
                
                # 发送命令
                sock.sendall(command.encode('utf-8'))
                
                # 接收响应
                response_data = sock.recv(4096).decode('utf-8')
                
                # 解析JSON响应
                return json.loads(response_data)
                
        except socket.timeout:
            print("AGV通信超时")
            return None
        except (socket.error, json.JSONDecodeError) as e:
            print(f"AGV通信错误: {e}")
            return None
    
    @staticmethod
    def execute_movement_sequence(command: str, 
                                  repetitions: int, 
                                  interval: float = 0.4) -> None:
        """
        执行AGV移动序列
        
        Args:
            command: 移动命令
            repetitions: 重复次数
            interval: 命令间隔时间(秒)
        """
        for i in range(repetitions):
            response = AGVController.send_command(command)
            if response:
                print(f"AGV移动 {i+1}/{repetitions} - 响应: {response}")
            time.sleep(interval)


def main() -> None:
    """主函数：执行完整的协同控制流程"""
    print("========== 开始系统初始化 ==========")
    
    # 1. 初始化机械臂
    print("初始化机械臂...")
    robot_controller = RobotController()
    
    # 2. 初始化外部轴
    print("初始化外部轴...")
    if not ExternalAxisController.reset_and_enable_all_joints():
        print("警告: 外部轴初始化不完整，继续执行...")
    
    print("========== 执行位置初始化 ==========")
    
    # 3. 外部轴位置初始化
    home_pos = [300, 135, -75, 0]
    print(f"外部轴移动到初始位置: {home_pos}")
    ExternalAxisController.move_to_position(
        home_pos, 
        200, 
        200
    )
    
    # 4. 机械臂位置初始化
    home_j = [51.864, -28.716, -105.127, 172.459, 25.24, 104.609]
    print(f"机械臂移动到初始位置: {home_j}")
    robot_controller.move_to_joint_position(home_j)
    
    print("========== 开始协同运动 ==========")
    
    # 5. 创建并启动线程
    threads = []
    
    # 外部轴姿态
    ext_pos = [50, -135, 75, -5]
    # 机械臂姿态
    arm_joint = [-25.58,33.628,54.273,10.118,41.249,32.812]
    # 底盘移动命令
    AGV_FORWARD_CMD = f"/api/joy_control?angular_velocity=0&linear_velocity=0.2"

    # 线程1: 外部轴移动到目标位置
    thread_ext = threading.Thread(
        target=ExternalAxisController.move_to_position,
        args=(ext_pos, 200, 200),
        name="ExternalAxisMovement"
    )
    
    # 线程2: AGV前进
    thread_agv = threading.Thread(
        target=AGVController.execute_movement_sequence,
        args=(AGV_FORWARD_CMD, 20),
        name="AGVMovement"
    )
    # 线程3: ARM移动
    thread_arm = threading.Thread(
        target=robot_controller.move_to_joint_position,
        args=(arm_joint,False,90),
        name="ARMMovement"
    )
    
    threads = [thread_agv,thread_ext,thread_arm]
    
    # 启动所有线程
    for thread in threads:
        thread.start()
        print(f"启动线程: {thread.name}")
        time.sleep(0.1)  # 短暂延时避免冲突
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
        print(f"线程完成: {thread.name}")
    
    print("========== 协同运动完成 ==========")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()