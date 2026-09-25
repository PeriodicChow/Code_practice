# -*- coding: utf-8 -*-
"""
=============================================================
步骤1：底盘移动控制（AGV Chassis Movement Control）
=============================================================

【教学要点】
  - 了解 AGV（自动导引车）底盘的通信方式：TCP Socket + JSON 协议
  - 掌握通过 marker（标记点）进行导航移动的原理
  - 理解轮询等待机制：发送命令后需要持续查询移动状态

【硬件依赖】
  - AGV 底盘（通过 TCP/IP 通信）

【输入】
  - AGV IP 地址和端口
  - 目标 marker 名称

【输出】
  - 底盘移动到指定位置，返回是否成功
=============================================================
"""

import socket
import json
import time


class ChassisController:
    """
    AGV 底盘控制器
    
    通过 TCP Socket 向 AGV 发送 JSON 格式的控制命令，
    实现底盘的前进、后退、导航移动等功能。
    
    通信协议：
        发送: GET /api/move?marker=<marker_name> HTTP/1.1
        接收: {"error_code": 0, "error_msg": "ok", "results": {...}}
    """

    def __init__(self, agv_ip: str, agv_port: int):
        """
        初始化底盘控制器
        
        参数:
            agv_ip:   AGV 底盘的 IP 地址，例如 "192.168.1.200"
            agv_port: AGV 底盘的通信端口，例如 8080
        """
        self.agv_ip = agv_ip
        self.agv_port = agv_port
        print(f"[步骤1] 底盘控制器初始化: {agv_ip}:{agv_port}")

    def _send_command(self, command: str) -> dict:
        """
        向 AGV 发送 TCP 命令（内部方法）
        
        原理：
          1. 建立 TCP 连接
          2. 发送 HTTP 格式的命令字符串
          3. 接收 JSON 格式的响应
          4. 关闭连接
        
        参数:
            command: HTTP 路径格式的命令，例如 "/api/move?marker=station1"
        
        返回:
            AGV 返回的 JSON 字典，失败返回 None
        """
        if not self.agv_ip or not self.agv_port:
            print("[步骤1] ❌ AGV 连接信息未配置")
            return None
        try:
            # 创建 TCP Socket 连接
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.agv_ip, self.agv_port))
                sock.sendall(command.encode('utf-8'))
                response = sock.recv(4096).decode('utf-8')
                return json.loads(response)
        except Exception as e:
            print(f"[步骤1] ❌ 发送 AGV 命令失败: {e}")
            return None

    def move_to_marker(self, marker_name: str, check_interval: float = 1.0) -> bool:
        """
        控制底盘移动到指定的 marker 标记点
        
        流程：
          1. 发送移动命令 /api/move?marker=<name>
          2. 等待 AGV 确认接收命令
          3. 轮询查询 AGV 状态，等待移动完成（running_status == "idle"）
        
        参数:
            marker_name:    目标标记点名称（在 AGV 地图上预先标定的位置）
            check_interval: 状态查询间隔时间（秒），默认 1.0s
        
        返回:
            True = 移动成功, False = 移动失败
        """
        print(f"[步骤1] 🚗 开始移动到底盘标记点: {marker_name}")

        # ---- 第1步：发送移动命令 ----
        response = self._send_command(f"/api/move?marker={marker_name}")
        if not response:
            print("[步骤1] ❌ 发送移动命令失败，无响应")
            return False

        # 检查命令是否被接受
        error_code = response.get("error_code", 0)
        if error_code not in (0, "0", None):
            error_msg = response.get("error_msg") or response.get("msg", "未知错误")
            print(f"[步骤1] ❌ 移动命令返回错误: code={error_code}, msg={error_msg}")
            return False

        print(f"[步骤1] ✅ 移动命令已接受，等待底盘到达...")
        time.sleep(2)  # 等待 AGV 开始运动

        # ---- 第2步：轮询等待移动完成 ----
        while True:
            status_response = self._send_command("/api/robot_status")
            if not status_response:
                print("[步骤1] ⚠️ 状态查询失败，继续等待...")
                time.sleep(check_interval)
                continue

            results = status_response.get("results", {})
            running_status = results.get("running_status")

            if running_status == "idle":
                # AGV 已停止，检查移动是否成功
                move_status = results.get("move_status")
                if move_status and move_status not in ("succeeded", "idle", "none"):
                    print(f"[步骤1] ⚠️ 移动结束但状态异常: move_status={move_status}")
                    return False
                print(f"[步骤1] ✅ 底盘已到达标记点: {marker_name}")
                return True

            print(f"[步骤1] 🔄 底盘移动中... (status={running_status})")
            time.sleep(check_interval)

    def get_status(self) -> dict:
        """
        查询 AGV 底盘当前状态
        
        返回:
            包含 running_status, move_status 等字段的状态字典
        """
        return self._send_command("/api/robot_status")

    def stop(self) -> bool:
        """
        立即停止底盘运动（发送速度为 0 的遥控命令）
        
        原理：
          通过 joy_control 接口发送 angular_velocity=0, linear_velocity=0
          相当于松开油门，底盘立即刹车
        
        返回:
            True = 停止成功, False = 停止失败
        """
        response = self._send_command(
            "/api/joy_control?angular_velocity=0&linear_velocity=0&uuid=123456"
        )
        if response:
            print("[步骤1] ✅ 底盘已停止")
            return True
        print("[步骤1] ❌ 停止命令发送失败")
        return False

    def backward(self, speed: float = -0.25, duration: float = 2.0) -> bool:
        """
        控制底盘后退
        
        参数:
            speed:    后退速度（负值表示后退），默认 -0.25 m/s
            duration: 后退持续时间（秒），默认 2.0s
        
        返回:
            True = 后退成功, False = 后退失败
        """
        print(f"[步骤1] 🔄 底盘后退中，持续 {duration} 秒...")
        command = f"/api/joy_control?angular_velocity=0&linear_velocity={speed}&uuid=123456"

        # 持续发送后退命令
        elapsed = 0.0
        interval = 0.5
        while elapsed < duration:
            response = self._send_command(command)
            if not response:
                print("[步骤1] ❌ 后退命令发送失败")
                return False
            time.sleep(interval)
            elapsed += interval

        # 发送停止命令
        self.stop()
        print("[步骤1] ✅ 底盘后退完成")
        return True

    def estop(self, flag: str = "true") -> bool:
        """
        急停控制
        
        参数:
            flag: "true" 触发急停, "false" 解除急停
        
        返回:
            True = 操作成功, False = 操作失败
        """
        response = self._send_command(f"/api/estop?flag={flag}")
        if response:
            print(f"[步骤1] {'🛑 急停已触发' if flag == 'true' else '✅ 急停已解除'}")
            return True
        print("[步骤1] ❌ 急停命令发送失败")
        return False


# =============================================================================
#  单独运行此步骤的入口函数
# =============================================================================

def run(config: dict, shared_state: dict = None) -> dict:
    """
    执行步骤1：底盘移动到取货点
    
    参数:
        config:       从 config.json 加载的完整配置字典
        shared_state: 各步骤间共享的状态字典（可选）
    
    返回:
        {"success": bool, "marker": str}
    """
    if shared_state is None:
        shared_state = {}

    system_cfg = config.get("system_config", {})
    agv_cfg = config.get("agv_config", {})

    # 创建底盘控制器
    chassis = ChassisController(
        agv_ip=system_cfg.get("agv_ip", ""),
        agv_port=system_cfg.get("agv_port", 8080)
    )

    # 目标 marker 名称
    marker = shared_state.get("target_marker") or agv_cfg.get("pickup_marker", "station1")

    print("=" * 60)
    print(f"  步骤1：底盘移动控制 -> 目标标记点: {marker}")
    print("=" * 60)

    # 执行移动
    success = chassis.move_to_marker(marker)

    # 将结果存入共享状态
    shared_state["chassis"] = chassis
    shared_state["step1_success"] = success
    shared_state["current_marker"] = marker

    print(f"\n{'=' * 60}")
    print(f"  步骤1 结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"{'=' * 60}\n")

    return {"success": success, "marker": marker}


if __name__ == "__main__":
    # 直接运行此模块进行测试
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    result = run(cfg)
    print(f"最终结果: {result}")
