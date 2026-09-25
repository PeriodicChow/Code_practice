import socket
import json
import time
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # lumi_demo 目录
sys.path.insert(0, parent_dir)
import config

def send_command_and_receive_response(command, host, port):
    try:
        # Create a TCP/IP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Connect to the server
            sock.connect((host, port))
            
            # Send the command
            sock.sendall(command.encode('utf-8'))
            
            # Receive the response
            response = sock.recv(4096).decode('utf-8')
            
            # Parse the JSON response
            response_json = json.loads(response)
            return response_json
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# 待测试
if __name__ == "__main__":
    # 需要建两个站点，实现两个站点间来回移动
    pos_names = ["p1","p3"]
    # pos_names = ["pos1","pos2"]
    i = 0
    cnt_ = 0
    while True:
        cnt_ += 1
        if cnt_>=5:
            break
        i = (i+1)%2
        MOVE_COMMAND = f"/api/estop?flag=true"
        # MOVE_COMMAND = f"/api/move?marker={pos_names[i]}"
        # 该命令为非阻塞的。 可以通过查询状态判断是否移动完成。
        response = send_command_and_receive_response(MOVE_COMMAND, config.AGV_HOST, config.AGV_PORT)
        print(response)

        # time.sleep(2)
        # while True:
        #     # 判断移动状态
        #     STATUS_COMMAND = f"/api/robot_status"
        #     response = send_command_and_receive_response(STATUS_COMMAND, config.AGV_HOST, config.AGV_PORT)
        #     if response["results"]["running_status"] == "idle":
        #         break
        #     # time.sleep(1)
        # print(cnt_)
        # a = input()