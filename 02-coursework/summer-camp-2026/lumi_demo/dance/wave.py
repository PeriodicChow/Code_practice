# -*- coding: utf-8 -*-  
import time       
import json
import requests
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # lumi_demo 目录
sys.path.insert(0, parent_dir)
import config
from JAKA_SDK_WINDOWS import jkrc


# 基础姿态

BASE_URL =config.EXT_AXIS_API_URL

def api_post(endpoint, data,req_type=0):
    """发送POST请求到API"""
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        if(req_type == 0):
            response = requests.post(url, json=data, timeout=5)
        else:
            response = requests.get(url,json=data,timeout=5)
        if response.status_code == 200:
            print(f"{endpoint} ok")
            return response.json() if response.content else True
        else:
            print(f"Error [{endpoint}]: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed [{endpoint}]: {e}")
        return None

ABS = 0  
INCR= 1  

joint_pos1=[
    -25.581*3.14/180,35.010*3.14/180,71.403*3.14/180,10.117*3.14/180,41.249*3.14/180,32.812*3.14/180
]
joint_pos2=[
    -25.58*3.14/180,33.628*3.14/180,54.273*3.14/180,10.118*3.14/180,41.249*3.14/180,32.812*3.14/180
]

print("命令输入成功——当前为挥手姿态：")
# 机械臂移动到初始姿态
robot = jkrc.RC(config.ROBOT_IP)#返回机器人对象  
ret = robot.login(1)#登录  
if ret[0] != 0:
    robot.login()

print("正在给机械臂上电/使能")
robot.power_on() #上电  
robot.enable_robot()  

print("正在给外部轴上使能")
# 外部轴上使能、移动的初始姿态
api_post("enable", {"enable": 1})

print("正在移动外部轴到挥手姿态位置")
api_post("moveto", {"pos": [20, 0, 0, 0], "vel": 100, "acc": 100})
print("开始进行挥手")
while True:
    robot.joint_move(joint_pos1,ABS,True,0.83)  
    robot.joint_move(joint_pos2,ABS,True,0.63) 

time.sleep(3)  
robot.logout()  
print("程序结束") 
