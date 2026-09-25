'''
采用http接口的方式控制与访问。总计有4个关节
* 关节1：升降，运动范围[0,300]mm
* 关节2：腰部旋转，运动范围[-140,140]度
* 关节3：头部旋转，运动范围[-180,180]度
* 关节4：头部俯仰，运动范围[-5,35]度
'''
import requests
import json
import time
import socket
import threading
import logging
from datetime import datetime
import os
import numpy as np
import threading
import subprocess
import glob
import random
import time
import sys
from contextlib import redirect_stderr
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # lumi_demo 目录
sys.path.insert(0, parent_dir)
import config
from JAKA_SDK_WINDOWS import jkrc

# 初始化机器人控制对象
robot = jkrc.RC(config.ROBOT_IP)  # 创建机器人控制实例
robot.login()  # 登录机器人控制器
print('robot login')
robot.power_on()
robot.enable_robot()

def ext_moveto(point, v = 100, acc = 100):
    """
    控制外部设备移动到指定位置
    :param point: 目标位置坐标 [x, y, z, r]
    :param v: 速度，默认100
    :param acc: 加速度，默认100
    """
    response = requests.post(
        config.EXT_MOVETO_URL,
        json={"pos": point, "vel": v, "acc": acc},
    )
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
    else:
        print('ex move success!')
    return

def send_command_and_receive_response(command, host, port):
    """
    通过TCP/IP发送命令并接收响应
    :param command: 要发送的命令
    :param host: 目标主机IP
    :param port: 目标主机端口
    :return: JSON格式的响应数据
    """
    try:
        # Create a TCP/IP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Connect to the server
            sock.connect((host, port))
            
            # Send the command
            sock.sendall(command.encode('utf-8'))
            
            # Receive the response
            response = sock.recv(4096).decode('utf-8')
            
            # 解析JSON响应
            response_json = json.loads(response)
            return response_json
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def rob_moveto(jpos, vel = 70):
    """
    控制机器人移动到指定关节角度
    :param jpos: 目标关节角度 [J1, J2, J3, J4, J5, J6]
    :param vel: 关节速度，默认90度/秒
    """
    # 将角度转换为弧度
    joint_pos = [0, 0, 0, 0, 0, 0]
    for i in range(6):
        joint_pos[i] = jpos[i] / 180.0 * 3.1415926
    # 执行关节运动
    robot.joint_move(joint_pos, 0, False, vel / 180 * 3.14)
    
    return


def enable_all_joints():
    # 使能所有关节
    response = requests.post(config.EXT_ENABLE_URL, json={"enable": 1})
    if response.status_code != 200:
        print(f"Enable failed: {response.status_code}")
        return False
    print("All joints enabled.")
    return True

def reset_and_enable_all_joints():
    # 先reset
    response = requests.post(config.EXT_RESET_URL, json={})
    if response.status_code != 200:
        print(f"Reset failed: {response.status_code}")
        return False
    print("All joints reset.")

    # 再enable
    response = requests.post(config.EXT_ENABLE_URL, json={"enable": 1})
    if response.status_code != 200:
        print(f"Enable failed: {response.status_code}")
        return False
    print("All joints enabled.")
    return True

def agvMove(Command,times):
    for temp in range(times):
        response = send_command_and_receive_response(Command, config.AGV_HOST, config.AGV_PORT)
        time.sleep(0.4)

def agvCircle():
    radius = 0.25
    speed = 0.3
    if radius != 0:
        angular_velocity = -1.0 * speed / radius
    else:
        angular_velocity = 0  # 半径为0时，原地旋转
    # 发送控制指令
    cir_command = f"/api/joy_control?angular_velocity={angular_velocity}&linear_velocity={speed}"
    while True:
        agvMove(cir_command,10)

# 用法示例
if __name__ == '__main__':

    agv_thread = threading.Thread(target=agvCircle)
    agv_thread.start()

    while True:
        # if not reset_and_enable_all_joints():
        #     print("退出")
        #     exit(1)  # 失败则退出

        # 第一组：外部轴和机器人同时运动
        rob_thread1 = threading.Thread(target=rob_moveto, args=([0,0,0,0,0,0], 40))
        ext_thread1 = threading.Thread(target=ext_moveto, args=([10.0, 0.0, 0.0, 0.0], 100, 100))
        rob_thread2 = threading.Thread(target=rob_moveto, args=([-3, 54, 48, 130, -63, 2], 40))
        rob_thread3 = threading.Thread(target=rob_moveto, args=([-80, -4, -77, 45, 55, 50], 40))

        rob_thread1.start()
        rob_thread2.start()
        rob_thread3.start()
        ext_thread1.start()

        rob_thread1.join()  
        rob_thread2.join()
        rob_thread3.join()
        ext_thread1.join()

        # 第二组：外部轴和机器人同时运动
        rob_thread2 = threading.Thread(target=rob_moveto, args=([-3, 54, 48, 130, -63, 2], 40))
        ext_thread2 = threading.Thread(target=ext_moveto, args=([200.0, -100.0, -90.0, -5.0], 100, 100))

        rob_thread2.start()
        ext_thread2.start()
        rob_thread2.join()
        ext_thread2.join()

        # 第三组：外部轴和机器人同时运动
        ext_thread3 = threading.Thread(target=ext_moveto, args=([10.0, 100.0, 90.0, 30.0], 100, 100))
        rob_thread3 = threading.Thread(target=rob_moveto, args=([-80, -4, -77, 45, 55, 50], 40))
        
        rob_thread3.start()
        ext_thread3.start()
        rob_thread3.join()
        ext_thread3.join()

        print('外部轴和机器人同时移动到目标位置！')

