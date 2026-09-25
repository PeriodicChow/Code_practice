# -*- coding: utf-8 -*-
"""
=============================================================
步骤6：机器人移动至目标点（Robot Arm Movement to Target）
=============================================================

【教学要点】
  - 理解机械臂的两种运动方式：
      关节空间运动（Joint Move）：指定各关节角度，机械臂沿关节空间插值运动
      笛卡尔空间运动（Linear Move）：指定 TCP 位姿，机械臂沿直线运动
  - 掌握逆运动学（Inverse Kinematics, IK）的概念：
      已知目标 TCP 位姿 (X, Y, Z, Rx, Ry, Rz)，求解各关节角度 (j1~j6)
  - 了解正运动学（Forward Kinematics, FK）的概念：
      已知各关节角度，计算 TCP 在笛卡尔空间中的位姿
  - 学习 JAKA SDK 的基本使用：连接、使能、关节运动、正逆解

【硬件依赖】
  - JAKA 机械臂（如 JAKA Zu 系列）

【输入】
  - 目标世界坐标 [X, Y, Z]（来自步骤5）
  - 机器人 IP 地址
  - 运动速度、偏移参数

【输出】
  - 机器人移动到目标位置附近（关节空间运动）
  - 返回目标关节角度
=============================================================
"""

import os
import sys
import time
import json
import math
import threading

# ---- JAKA SDK 导入 ----
# 需要从 libs/ 目录加载 JAKA 的动态库
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_libs_dir = os.path.join(_project_root, "libs")
if _libs_dir not in sys.path:
    sys.path.insert(0, _libs_dir)
if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(_libs_dir)
_libjaka_api = os.path.join(_libs_dir, "libjakaAPI.so")
if os.path.exists(_libjaka_api):
    import ctypes
    ctypes.CDLL(_libjaka_api, mode=ctypes.RTLD_GLOBAL)

try:
    from jkrc import jkrc
    JAKA_SDK_AVAILABLE = True
except ImportError:
    JAKA_SDK_AVAILABLE = False
    print("[步骤6] ⚠️ JAKA SDK 未安装，将使用模拟模式")


class RobotArm:
    """
    JAKA 机械臂控制器
    
    封装 JAKA SDK 的核心功能：
      - 连接/断开机器人
      - 关节空间运动（joint_move）
      - 正运动学（关节角 → TCP 位姿）
      - 逆运动学（TCP 位姿 → 关节角）
      - 获取当前关节角度
    
    坐标系说明：
      ┌───────────────────────────────┐
      │      机器人基坐标系             │
      │                               │
      │         ╱╲  TCP（工具中心点）   │
      │        ╱  ╲                    │
      │       ╱    ╲  ← 关节6          │
      │      ●      ● ← 关节5         │
      │      │      │                  │
      │      ●      │ ← 关节4         │
      │      │      │                  │
      │      ●      │ ← 关节3         │
      │      │      │                  │
      │      ●      │ ← 关节2         │
      │      │      │                  │
      │  ════●══════│ ← 关节1（基座）  │
      └───────────────────────────────┘
    """

    def __init__(self, robot_ip: str):
        """
        初始化机械臂控制器
        
        参数:
            robot_ip: JAKA 机器人的 IP 地址，例如 "192.168.1.100"
        """
        self.robot_ip = robot_ip
        self.robot = None
        self._sdk_lock = threading.RLock()
        print(f"[步骤6] 机械臂控制器初始化: IP={robot_ip}")

    def connect(self):
        """
        连接到 JAKA 机器人
        
        连接流程：
          1. 创建 RC（Robot Controller）对象
          2. 登录机器人
          3. 上电（power_on）
          4. 使能（enable_robot）—— 解除抱闸，允许运动
        """
        if not JAKA_SDK_AVAILABLE:
            print("[步骤6] ⚠️ 模拟模式: 跳过连接")
            return True

        with self._sdk_lock:
            self.robot = jkrc.RC(self.robot_ip)
            print("[步骤6] 正在连接机器人...")

            # 登录
            ret = self.robot.login(1)
            if ret[0] != 0:
                ret = self.robot.login()
            print(f"[步骤6] 登录结果: {ret}")

            if ret[0] != 0:
                raise ConnectionError(f"机器人登录失败: {ret}")

            # 上电
            power_ret = self.robot.power_on()
            print(f"[步骤6] 上电结果: {power_ret}")

            # 使能
            enable_ret = self.robot.enable_robot()
            print(f"[步骤6] 使能结果: {enable_ret}")

            if enable_ret[0] != 0:
                raise RuntimeError(f"机器人使能失败: {enable_ret}")

            # 初始化夹爪 IO
            self.robot.set_digital_output(1, -1, 1)
            self.robot.set_digital_output(1, 0, 1)

            print("[步骤6] ✅ 机器人连接成功")
            return True

    def get_joints(self) -> tuple:
        """
        获取当前各关节角度
        
        返回:
            6 个关节角度 (j1, j2, j3, j4, j5, j6)，单位：弧度
            失败返回 None
        """
        if not JAKA_SDK_AVAILABLE or self.robot is None:
            print("[步骤6] ⚠️ 模拟模式: 返回默认关节角 [0,0,0,0,0,0]")
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        with self._sdk_lock:
            ret = self.robot.get_joint_position()
        if ret[0] == 0:
            joints = ret[1]
            print(f"[步骤6] 当前关节角 (弧度): {[f'{j:.4f}' for j in joints]}")
            return joints
        else:
            print(f"[步骤6] ❌ 获取关节角失败: {ret}")
            return None

    def forward_kinematics(self, joints: tuple) -> tuple:
        """
        正运动学（Forward Kinematics, FK）
        
        已知各关节角度 → 计算 TCP（工具中心点）在笛卡尔空间的位姿
        
        参数:
            joints: 6 个关节角度 (j1~j6)，单位：弧度
        
        返回:
            TCP 位姿 (X, Y, Z, Rx, Ry, Rz)
            X, Y, Z 单位 mm; Rx, Ry, Rz 单位 rad
            失败返回 None
        """
        if not JAKA_SDK_AVAILABLE or self.robot is None:
            print("[步骤6] ⚠️ 模拟模式: 返回默认位姿 [0,0,500,3.14,0,0]")
            return (0.0, 0.0, 500.0, 3.14, 0.0, 0.0)

        with self._sdk_lock:
            ret = self.robot.kine_forward(joints)
        if ret[0] == 0:
            pose = ret[1]
            print(f"[步骤6] 正解结果: X={pose[0]:.1f}, Y={pose[1]:.1f}, Z={pose[2]:.1f}, "
                  f"Rx={pose[3]:.4f}, Ry={pose[4]:.4f}, Rz={pose[5]:.4f}")
            return pose
        else:
            print(f"[步骤6] ❌ 正解失败: {ret}")
            return None

    def inverse_kinematics(self, ref_joints: tuple, target_pose: tuple) -> tuple:
        """
        逆运动学（Inverse Kinematics, IK）
        
        已知目标 TCP 位姿 → 求解各关节角度
        
        为什么需要参考关节角 ref_joints？
          逆解通常有多组解（不同构型），参考关节角帮助选择
          最接近当前姿态的那组解，避免关节大幅跳变。
        
        参数:
            ref_joints:   参考关节角（通常用当前关节角），单位：弧度
            target_pose:  目标 TCP 位姿 (X, Y, Z, Rx, Ry, Rz)
        
        返回:
            目标关节角 (j1, j2, j3, j4, j5, j6)，单位：弧度
            失败返回 None
        """
        if not JAKA_SDK_AVAILABLE or self.robot is None:
            print("[步骤6] ⚠️ 模拟模式: 返回参考关节角")
            return ref_joints

        with self._sdk_lock:
            ret = self.robot.kine_inverse(ref_joints, target_pose)
        if ret[0] == 0:
            joints = ret[1]
            print(f"[步骤6] 逆解成功: {[f'{j:.4f}' for j in joints]}")
            return joints
        else:
            print(f"[步骤6] ❌ 逆解失败: error_code={ret[0]}")
            print(f"       目标位姿: {target_pose}")
            return None

    def joint_move(self, joints: tuple, speed: int = 200, mode: int = 0) -> int:
        """
        关节空间运动
        
        将机械臂各关节移动到指定的角度位置。
        
        参数:
            joints: 目标关节角 (j1~j6)，单位：弧度
            speed:  运动速度（1~300），默认 200
            mode:   运动模式
                    0 = 绝对运动（移动到绝对角度）
                    1 = 增量运动（相对当前角度偏移）
        
        返回:
            0 = 成功, -1 = 失败
        """
        if not JAKA_SDK_AVAILABLE or self.robot is None:
            print(f"[步骤6] ⚠️ 模拟模式: 假装移动到 {[f'{j:.4f}' for j in joints]}")
            time.sleep(1)  # 模拟运动耗时
            return 0

        with self._sdk_lock:
            ret = self.robot.joint_move_extend(
                joint_pos=joints,
                move_mode=mode,
                is_block=True,   # 阻塞等待运动完成
                speed=speed,
                acc=200,
                tol=0.1
            )

        print(f"[步骤6] 关节运动返回: {ret}")
        if ret[0] == 0 or ret[0] == -12:
            return 0
        return -1

    def move_to_world_coord(self, world_coord: list, robot_params: dict,
                            speed: int = 200) -> dict:
        """
        将机械臂移动到世界坐标指定的位置
        
        流程：
          1. 应用偏移量（抓取时不一定对准中心，需要 X/Y/Z 偏移）
          2. 构建目标 TCP 位姿 (X, Y, Z, Rx, Ry, Rz)
          3. 获取当前关节角作为参考
          4. 执行逆运动学求解
          5. 关节运动到目标角度
        
        参数:
            world_coord:  世界坐标 [X, Y, Z]，单位 mm
            robot_params: 机器人参数（偏移量、固定姿态角等）
            speed:        运动速度
        
        返回:
            {"success": bool, "target_joints": tuple}
        """
        print(f"[步骤6] ━━━ 移动机械臂到目标位置 ━━━")
        print(f"[步骤6] 目标世界坐标: ({world_coord[0]:.1f}, {world_coord[1]:.1f}, {world_coord[2]:.1f}) mm")

        # ---- 第1步：应用偏移量 ----
        offset_x = robot_params.get("relative_offset_x", 0.0)
        offset_y = robot_params.get("relative_offset_y", 0.0)
        offset_z = robot_params.get("relative_offset_z", 0.0)
        rx_fix = robot_params.get("rx_fix", 3.14)
        ry_fix = robot_params.get("ry_fix", 0.0)
        rz_fix = robot_params.get("rz_fix", 0.0)

        target_pose = (
            world_coord[0] + offset_x,
            world_coord[1] + offset_y,
            world_coord[2] + offset_z if offset_z != 0 else world_coord[2],
            rx_fix,
            ry_fix,
            rz_fix,
        )

        print(f"[步骤6] 目标 TCP 位姿: X={target_pose[0]:.1f}, Y={target_pose[1]:.1f}, "
              f"Z={target_pose[2]:.1f}, Rx={target_pose[3]:.4f}, "
              f"Ry={target_pose[4]:.4f}, Rz={target_pose[5]:.4f}")

        # ---- 第2步：获取当前关节角 ----
        current_joints = self.get_joints()
        if current_joints is None:
            return {"success": False, "error": "获取当前关节角失败"}

        # ---- 第3步：逆运动学求解 ----
        target_joints = self.inverse_kinematics(current_joints, target_pose)
        if target_joints is None:
            return {"success": False, "error": "逆运动学求解失败"}

        # ---- 第4步：关节运动 ----
        move_result = self.joint_move(target_joints, speed=speed)
        if move_result != 0:
            return {"success": False, "error": "关节运动失败"}

        print(f"[步骤6] ✅ 机械臂已移动到目标位置")
        return {"success": True, "target_joints": target_joints}

    def move_to_initial_pose(self, base_pose: list, speed: int = 200) -> bool:
        """
        移动机械臂到初始姿态（安全位置）
        
        参数:
            base_pose: 初始关节角 [j1, j2, j3, j4, j5, j6]
            speed:     运动速度
        """
        print("[步骤6] 回到初始姿态...")
        result = self.joint_move(tuple(base_pose), speed=speed)
        if result == 0:
            print("[步骤6] ✅ 已回到初始姿态")
            return True
        print("[步骤6] ❌ 回到初始姿态失败")
        return False

    def disconnect(self):
        """断开与机器人的连接"""
        if self.robot is not None:
            try:
                self.robot.logout()
                print("[步骤6] 机器人已断开连接")
            except Exception as e:
                print(f"[步骤6] ⚠️ 断开连接异常: {e}")
            self.robot = None


# =============================================================================
#  单独运行此步骤的入口函数
# =============================================================================

def run(config: dict, shared_state: dict = None) -> dict:
    """
    执行步骤6：机器人移动至目标点
    
    前置条件：
        shared_state 中需要有 "world_coord"（来自步骤5的 3D 坐标）
    
    参数:
        config:       从 config.json 加载的完整配置字典
        shared_state: 各步骤间共享的状态字典
    
    返回:
        {"success": bool, "target_joints": tuple}
    """
    if shared_state is None:
        shared_state = {}

    system_cfg = config.get("system_config", {})
    robot_params = config.get("robot_params", {})

    print("=" * 60)
    print(f"  步骤6：机器人移动至目标点")
    print(f"  机器人 IP: {system_cfg.get('robot_ip', '未配置')}")
    print("=" * 60)

    # ---- 获取前置数据 ----
    world_coord = shared_state.get("world_coord")
    if world_coord is None:
        print("[步骤6] ❌ 缺少世界坐标 (world_coord)")
        print("[步骤6] 💡 请先执行步骤5 进行坐标变换")
        return {"success": False, "error": "缺少世界坐标"}

    # ---- 创建机器人并连接 ----
    robot_ip = system_cfg.get("robot_ip", "")
    arm = RobotArm(robot_ip)

    try:
        arm.connect()

        # 先回到初始姿态
        base_pose = robot_params.get("base_pose", [0, 0, 0, 0, 0, 0])
        if base_pose and any(j != 0 for j in base_pose):
            arm.move_to_initial_pose(base_pose)
            time.sleep(robot_params.get("move_wait_time", 0.3))

        # 移动到目标位置
        speed = robot_params.get("move_speed", 200)
        result = arm.move_to_world_coord(world_coord, robot_params, speed)

        # 存入共享状态
        shared_state["robot_arm"] = arm
        shared_state["target_joints"] = result.get("target_joints")
        shared_state["step6_success"] = result["success"]

        print(f"\n{'=' * 60}")
        print(f"  步骤6 结果: {'✅ 成功' if result['success'] else '❌ ' + result.get('error', '失败')}")
        print(f"{'=' * 60}\n")

        return result

    except Exception as e:
        print(f"[步骤6] ❌ 异常: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    sys.path.insert(0, _project_root)
    config_path = os.path.join(_project_root, "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    # 模拟测试
    shared = {"world_coord": [300.0, 100.0, 200.0]}
    result = run(cfg, shared)
    print(f"最终结果: {result}")
