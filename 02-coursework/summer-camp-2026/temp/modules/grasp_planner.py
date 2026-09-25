# -*- coding: utf-8 -*-
"""
=============================================================
步骤7：机械臂抓取 - 运动学规划（Grasp Planning & Execution）
=============================================================

【教学要点】
  - 理解抓取轨迹规划的思路：
      不直接移动到目标点，而是规划一条安全的抓取路径：
      P0（预抓取点）→ P1（前进夹取）→ P2（抬升）→ P3（撤退）
  - 掌握夹爪控制（通过数字 IO 输出控制气动/电动夹爪）
  - 了解关节连续性检查：确保相邻路径点之间关节角度不会跳变过大
  - 学习通过正逆解组合进行路径点规划

【硬件依赖】
  - JAKA 机械臂
  - 夹爪（通过 DO1/DO2 数字 IO 控制）

【输入】
  - 目标关节角度（来自步骤6的逆解结果）
  - 抓取参数（前进距离、抬升高度、撤退距离）

【输出】
  - 机械臂完成抓取动作（夹紧物品并抬升撤退）
=============================================================
"""

import os
import sys
import time
import json
import math

# 导入机械臂控制器
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)
from modules.robot_arm import RobotArm, JAKA_SDK_AVAILABLE


class GraspPlanner:
    """
    抓取轨迹规划器
    
    规划一条从"预抓取位"到"完成抓取"的安全路径。
    
    抓取路径示意图（侧视图）：
    
            P3 (撤退)
             ↑
             │
            P2 (抬升)
             ↑
             │
        P0 → P1 (前进夹取)
       预抓取  夹紧
    
    路径点说明：
      P0 = 目标抓取位（逆解得到的关节角对应的 TCP 位姿）
      P1 = P0 沿 X 方向前进 forward_move mm（靠近物体）
      P2 = P1 沿 Z 方向抬升 lift_height mm（抬起物体）
      P3 = P2 沿 X 方向后退 retract_distance mm（安全撤退）
    """

    def __init__(self, robot_arm: RobotArm, io_tool: int = 1):
        """
        参数:
            robot_arm: RobotArm 实例（步骤6创建的）
            io_tool:   夹爪控制的 IO 通道号，默认 1
        """
        self.arm = robot_arm
        self.io_tool = io_tool

    def open_gripper(self, wait_time: float = 0.3):
        """
        张开夹爪
        
        原理：通过数字 IO 输出控制夹爪电磁阀
          DO1 = 0, DO2 = 1 → 夹爪张开
        
        参数:
            wait_time: 动作后等待时间（秒），确保夹爪完全张开
        """
        print("[步骤7] 🔓 张开夹爪...")
        if not JAKA_SDK_AVAILABLE or self.arm.robot is None:
            print("[步骤7] ⚠️ 模拟模式: 夹爪已张开")
            time.sleep(wait_time)
            return

        with self.arm._sdk_lock:
            self.arm.robot.set_digital_output(self.io_tool, -1, 0)  # DO1=0
            time.sleep(0.2)
            self.arm.robot.set_digital_output(self.io_tool, -1, 1)  # DO2=1
            time.sleep(0.1)
            # 重复一次确保动作完成
            self.arm.robot.set_digital_output(self.io_tool, -1, 0)
            time.sleep(0.2)
            self.arm.robot.set_digital_output(self.io_tool, -1, 1)
            time.sleep(0.1)

        time.sleep(wait_time)
        print("[步骤7] ✅ 夹爪已张开")

    def close_gripper(self, wait_time: float = 0.5):
        """
        闭合夹爪（夹紧物体）
        
        原理：
          DO1 = 0, DO2 = 0 → 夹爪闭合
        
        参数:
            wait_time: 动作后等待时间（秒），确保夹爪完全闭合
        """
        print("[步骤7] 🔒 闭合夹爪（夹紧）...")
        if not JAKA_SDK_AVAILABLE or self.arm.robot is None:
            print("[步骤7] ⚠️ 模拟模式: 夹爪已闭合")
            time.sleep(wait_time)
            return

        with self.arm._sdk_lock:
            self.arm.robot.set_digital_output(self.io_tool, 0, 0)  # DO1=0
            time.sleep(0.3)
            self.arm.robot.set_digital_output(self.io_tool, 0, 1)  # DO2=0
            time.sleep(0.1)
            # 重复一次确保夹紧
            self.arm.robot.set_digital_output(self.io_tool, 0, 0)
            time.sleep(0.3)
            self.arm.robot.set_digital_output(self.io_tool, 0, 1)
            time.sleep(0.1)

        time.sleep(wait_time)
        print("[步骤7] ✅ 夹爪已闭合")

    def plan_grasp_path(self, target_joints: tuple,
                        forward_move: float = 100.0,
                        lift_height: float = 150.0,
                        retract_distance: float = -100.0,
                        max_joint_delta_deg: float = 45.0) -> dict:
        """
        规划抓取路径（核心方法）
        
        流程：
          1. 正解：target_joints → P0 (TCP 位姿)
          2. 构造 P1, P2, P3（笛卡尔空间偏移）
          3. 逆解：P1, P2, P3 → 对应关节角
          4. 检查关节连续性（相邻点关节角变化不超过阈值）
        
        参数:
            target_joints:       目标抓取关节角（来自步骤6的逆解）
            forward_move:        前进距离 (mm)，沿 X 轴正方向
            lift_height:         抬升高度 (mm)，沿 Z 轴正方向
            retract_distance:    撤退距离 (mm)，通常为负值（沿 X 轴负方向）
            max_joint_delta_deg: 关节角最大变化量（度），超过则路径无效
        
        返回:
            {
                "poses":  [P0, P1, P2, P3],    # 各点的 TCP 位姿
                "joints": [J0, J1, J2, J3],    # 各点的关节角
            }
            失败返回 None
        """
        print(f"[步骤7] ━━━ 规划抓取路径 ━━━")
        print(f"[步骤7] 参数: 前进={forward_move}mm, 抬升={lift_height}mm, "
              f"撤退={retract_distance}mm")

        # ---- P0: 正解得到目标关节角对应的 TCP 位姿 ----
        P0 = self.arm.forward_kinematics(target_joints)
        if P0 is None:
            print("[步骤7] ❌ P0 正解失败")
            return None
        P0 = list(P0)
        print(f"[步骤7] P0 (预抓取位): X={P0[0]:.1f}, Y={P0[1]:.1f}, Z={P0[2]:.1f}")

        # ---- P1: 前进 ----
        P1 = P0.copy()
        P1[0] += forward_move
        print(f"[步骤7] P1 (前进夹取): X={P1[0]:.1f}, Y={P1[1]:.1f}, Z={P1[2]:.1f}")

        # ---- P2: 抬升 ----
        P2 = P1.copy()
        P2[2] += lift_height
        print(f"[步骤7] P2 (抬升):     X={P2[0]:.1f}, Y={P2[1]:.1f}, Z={P2[2]:.1f}")

        # ---- P3: 撤退 ----
        P3 = P2.copy()
        P3[0] += retract_distance
        print(f"[步骤7] P3 (撤退):     X={P3[0]:.1f}, Y={P3[1]:.1f}, Z={P3[2]:.1f}")

        poses = [P0, P1, P2, P3]
        joints = [target_joints]  # J0 已知

        # ---- 对 P1, P2, P3 执行逆解 ----
        ref_joint = target_joints
        for i in range(1, len(poses)):
            ik_result = self.arm.inverse_kinematics(ref_joint, tuple(poses[i]))
            if ik_result is None:
                print(f"[步骤7] ❌ P{i} 逆解失败")
                return None
            joints.append(ik_result)
            ref_joint = ik_result

        # ---- 检查关节连续性 ----
        max_delta = math.radians(max_joint_delta_deg)
        for i in range(len(joints) - 1):
            j1 = joints[i]
            j2 = joints[i + 1]
            for k in range(6):
                delta = abs(j2[k] - j1[k])
                if delta > max_delta:
                    print(f"[步骤7] ❌ 关节 {k+1} 跳变过大: "
                          f"{math.degrees(delta):.1f}° > {max_joint_delta_deg}°")
                    return None

        print("[步骤7] ✅ 抓取路径规划成功")
        return {"poses": poses, "joints": joints}

    def execute_grasp(self, grasp_path: dict,
                      grab_wait_time: float = 0.5,
                      move_wait_time: float = 0.3,
                      speed: int = 200,
                      close_joint_index: int = 1) -> bool:
        """
        执行抓取动作
        
        流程：
          1. 张开夹爪
          2. 移动到 P0（预抓取位）
          3. 移动到 P1（前进夹取）→ 在此点夹紧夹爪
          4. 移动到 P2（抬升）
          5. 移动到 P3（撤退）
        
        参数:
            grasp_path:         plan_grasp_path() 返回的路径字典
            grab_wait_time:     夹爪动作等待时间（秒）
            move_wait_time:     运动后等待时间（秒）
            speed:              运动速度
            close_joint_index:  在第几个路径点闭合夹爪（默认 1 = P1 前进后夹紧）
        
        返回:
            True = 抓取成功, False = 抓取失败
        """
        joints_seq = grasp_path["joints"]
        if not joints_seq:
            print("[步骤7] ❌ 抓取路径为空")
            return False

        print(f"[步骤7] ━━━ 执行抓取 ━━━")
        print(f"[步骤7] 路径点数: {len(joints_seq)}")

        # ---- 第1步：张开夹爪 ----
        self.open_gripper(grab_wait_time)

        # ---- 第2步：依次移动到各路径点 ----
        for i, joints in enumerate(joints_seq):
            print(f"[步骤7] 移动到 P{i}...")
            result = self.arm.joint_move(joints, speed=speed)
            if result != 0:
                print(f"[步骤7] ❌ 移动到 P{i} 失败")
                return False
            time.sleep(move_wait_time)

            # 在指定路径点闭合夹爪
            if i == close_joint_index:
                self.close_gripper(grab_wait_time)

        print("[步骤7] ✅ 抓取执行完成")
        return True


# =============================================================================
#  单独运行此步骤的入口函数
# =============================================================================

def run(config: dict, shared_state: dict = None) -> dict:
    """
    执行步骤7：机械臂抓取（运动学规划 + 执行）
    
    前置条件：
        shared_state 中需要有：
        - "target_joints": 目标关节角（来自步骤6）
        - "robot_arm": RobotArm 实例（来自步骤6）
    
    参数:
        config:       从 config.json 加载的完整配置字典
        shared_state: 各步骤间共享的状态字典
    
    返回:
        {"success": bool}
    """
    if shared_state is None:
        shared_state = {}

    grasp_cfg = config.get("grasp_config", {})
    robot_params = config.get("robot_params", {})

    print("=" * 60)
    print(f"  步骤7：机械臂抓取（运动学规划）")
    print(f"  前进: {grasp_cfg.get('forward_move', 100)}mm")
    print(f"  抬升: {grasp_cfg.get('lift_height', 150)}mm")
    print(f"  撤退: {grasp_cfg.get('retract_distance', -100)}mm")
    print("=" * 60)

    # ---- 获取前置数据 ----
    target_joints = shared_state.get("target_joints")
    arm = shared_state.get("robot_arm")

    if target_joints is None:
        print("[步骤7] ❌ 缺少目标关节角 (target_joints)")
        print("[步骤7] 💡 请先执行步骤6 获取逆解结果")
        return {"success": False, "error": "缺少目标关节角"}

    if arm is None:
        # 如果步骤6没有创建 RobotArm，则创建一个
        system_cfg = config.get("system_config", {})
        arm = RobotArm(system_cfg.get("robot_ip", ""))
        arm.connect()
        shared_state["robot_arm"] = arm

    # ---- 规划抓取路径 ----
    planner = GraspPlanner(arm, io_tool=grasp_cfg.get("io_tool", 1))
    grasp_path = planner.plan_grasp_path(
        target_joints=target_joints,
        forward_move=grasp_cfg.get("forward_move", 100),
        lift_height=grasp_cfg.get("lift_height", 150),
        retract_distance=grasp_cfg.get("retract_distance", -100),
    )

    if grasp_path is None:
        return {"success": False, "error": "抓取路径规划失败"}

    # ---- 执行抓取 ----
    success = planner.execute_grasp(
        grasp_path,
        grab_wait_time=grasp_cfg.get("grab_wait_time", 0.5),
        move_wait_time=grasp_cfg.get("move_wait_time", 0.3),
        speed=robot_params.get("move_speed", 200),
    )

    # 存入共享状态
    shared_state["grasp_path"] = grasp_path
    shared_state["step7_success"] = success

    print(f"\n{'=' * 60}")
    print(f"  步骤7 结果: {'✅ 抓取成功' if success else '❌ 抓取失败'}")
    print(f"{'=' * 60}\n")

    return {"success": success}


if __name__ == "__main__":
    sys.path.insert(0, _project_root)
    config_path = os.path.join(_project_root, "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    # 模拟测试
    shared = {
        "target_joints": (0.0, -0.5, 1.0, 0.0, 1.5, 0.0),
    }
    result = run(cfg, shared)
    print(f"最终结果: {result}")
