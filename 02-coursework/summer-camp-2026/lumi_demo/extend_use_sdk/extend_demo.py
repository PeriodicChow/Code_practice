import os
import sys
import time
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # lumi_demo 目录
sys.path.insert(0, parent_dir)
import config
from JAKA_SDK_WINDOWS import jkrc

if __name__ == "__main__":
    # 机械臂移动到初始姿态
    robot = jkrc.RC(config.ROBOT_IP)#返回机器人对象 
    # 3.2控制器
    ret = robot.login(1,"jaka_sdk","QWEqwe123@@")#登录  
    print(ret)
    # 设置外部轴各个位置上电
    for i in range(4):
        ret = robot.enable_ext(i)
    ret = robot.jog_ext(0,90,80,30)
    print(ret)
    print(f"id: 0, ",ret)
    ret = robot.get_ext_status()
    print(ret)



