import os
import sys
import time
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # lumi_demo 目录
sys.path.insert(0, parent_dir)
import config
from JAKA_SDK_WINDOWS import jkrc

joint_pos1=[
    -25.581,35.010,71.403,10.117,41.249,32.812
]
joint_pos2=[
    -25.58,33.628,54.273,10.118,41.249,32.812
]
home_pos = [
    -90,70,90,90,90,0
]

def angle_to_rad(joints):
    res = []
    for joint in joints:
        res.append(joint*3.14/180)
    return res

if __name__ == "__main__":
    # 机械臂移动到初始姿态
    robot = jkrc.RC(config.ROBOT_IP)#返回机器人对象 
   

    ret = robot.login(1,"jaka_sdk")
    
    print(ret)
    print("正在给机械臂上电/使能")
    robot.power_on() #上电  
    robot.enable_robot()  
    joint_pos1 = angle_to_rad(joint_pos1)
    joint_pos2 = angle_to_rad(joint_pos2)
    home_pos = angle_to_rad(home_pos)

    # 原点位置
    s = time.time()
    ret = robot.joint_move(home_pos,0,True,61) 
    
    print("返回结果:",ret)
    for i in range(10):
        # 挥手位置1
        robot.joint_move(joint_pos1,0,True,83) 
        # 挥手位置2 
        robot.joint_move(joint_pos2,0,True,63) 
    time.sleep(1)  
    # 返回原点
    robot.joint_move(home_pos,0,True,63) 
    robot.logout()  
    print("程序结束") 