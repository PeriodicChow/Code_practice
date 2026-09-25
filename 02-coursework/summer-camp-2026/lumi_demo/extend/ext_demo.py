# 外部轴控制
import json
import requests
import time
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # lumi_demo 目录
sys.path.insert(0, parent_dir)
import config


def api_post(url, data,req_type=0):
    """发送POST请求到API"""
    try:
        if(req_type == 0):
            response = requests.post(url, json=data)
        else:
            response = requests.get(url,json=data)
        if response.status_code == 200:
            print(f"{url} ok")
            return response.json() if response.content else True
        else:
            print(f"Error [{url}]: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed [{url}]: {e}")
        return None


if __name__ == "__main__":
    # 上使能
    api_post(config.EXT_ENABLE_URL, {"enable": 1})
    # 初始姿态
    api_post(config.EXT_MOVETO_URL, {"pos": [5, 0, 0, 0], "vel": 100, "acc": 100})   
    for i in range(3):
        # 移动
        api_post(config.EXT_MOVETO_URL, {"pos": [5, 140, -175, -4], "vel": 100, "acc": 100})
        api_post(config.EXT_MOVETO_URL, {"pos": [355, -140, 175, 34], "vel": 100, "acc": 100})
    # 回初始姿态
    api_post(config.EXT_MOVETO_URL, {"pos": [5, 0, 0, 0], "vel": 100, "acc": 100})    
    # 状态
    status = api_post(config.EXT_STATUS_URL,None,1)
    print("当前状态为：",status)