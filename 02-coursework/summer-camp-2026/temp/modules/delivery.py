# -*- coding: utf-8 -*-
"""
=============================================================
步骤8：底盘移动至放置点（Delivery - Move to Drop-off Point）
=============================================================

【教学要点】
  - 理解完整的取放货流程：取货 → 运输 → 放置
  - 复用步骤1的底盘控制器，导航到投递标记点
  - 学习放置动作：移动到投递位 → 机械臂移动到放置姿态 → 松开夹爪
  - 了解"回到初始姿态"的重要性：确保机器人处于安全状态

【硬件依赖】
  - AGV 底盘（复用步骤1）
  - JAKA 机械臂（复用步骤6）

【输入】
  - 投递标记点名称（来自配置）
  - 投递姿态（机械臂关节角）

【输出】
  - 底盘移动到投递点
  - 机械臂执行放置动作
  - 回到初始姿态
=============================================================
"""

import os
import sys
import time
import json

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from modules.chassis import ChassisController
from modules.robot_arm import RobotArm


class DeliveryController:
    """
    投递控制器
    
    负责将抓取到的物品运送并放置到指定位置。
    
    完整投递流程：
      1. AGV 后退（离开工位，腾出空间）
      2. 机械臂回到安全姿态（避免运输过程中碰撞）
      3. AGV 导航到投递标记点
      4. 机械臂移动到投递姿态
      5. 松开夹爪，放下物品
      6. 机械臂回到初始姿态
    """

    def __init__(self, chassis: ChassisController, robot_arm: RobotArm = None):
        """
        参数:
            chassis:    步骤1创建的底盘控制器（复用）
            robot_arm:  步骤6创建的机械臂控制器（可选，用于放置动作）
        """
        self.chassis = chassis
        self.arm = robot_arm

    def backward_from_station(self, speed: float = -0.25, duration: float = 2.0) -> bool:
        """
        从当前工位后退，腾出运输空间
        
        为什么需要后退？
          在货架前空间狭窄，直接转弯可能碰撞。
          先直线后退一段距离，再导航到投递点更安全。
        
        参数:
            speed:    后退速度（负值），默认 -0.25 m/s
            duration: 后退持续时间（秒）
        """
        print("[步骤8] 🔄 从工位后退...")
        return self.chassis.backward(speed=speed, duration=duration)

    def move_to_delivery_point(self, delivery_marker: str) -> bool:
        """
        导航到底盘投递标记点
        
        参数:
            delivery_marker: 投递点 marker 名称
        
        返回:
            True = 到达成功, False = 到达失败
        """
        print(f"[步骤8] 🚗 导航到投递点: {delivery_marker}")
        return self.chassis.move_to_marker(delivery_marker)

    def place_item(self, robot_arm: RobotArm, delivery_pose: list = None,
                   base_pose: list = None,
                   grab_wait_time: float = 0.5,
                   move_wait_time: float = 0.3,
                   speed: int = 200) -> bool:
        """
        执行放置动作
        
        流程：
          1. 如果有投递姿态：机械臂移动到投递位
          2. 松开夹爪，放下物品
          3. 机械臂回到初始姿态
        
        参数:
            robot_arm:       机械臂控制器
            delivery_pose:   投递姿态关节角 [j1~j6]（可选）
            base_pose:       初始姿态关节角 [j1~j6]
            grab_wait_time:  夹爪动作等待时间
            move_wait_time:  运动后等待时间
            speed:           运动速度
        """
        print("[步骤8] ━━━ 执行放置动作 ━━━")

        # 移动到投递姿态（如果配置了）
        if delivery_pose:
            print("[步骤8] 移动到投递姿态...")
            result = robot_arm.joint_move(tuple(delivery_pose), speed=speed)
            if result != 0:
                print("[步骤8] ❌ 移动到投递姿态失败")
                return False
            time.sleep(move_wait_time)

        # 松开夹爪
        from modules.grasp_planner import GraspPlanner
        planner = GraspPlanner(robot_arm)
        planner.open_gripper(grab_wait_time)

        # 回到初始姿态
        if base_pose:
            print("[步骤8] 回到初始姿态...")
            robot_arm.move_to_initial_pose(base_pose, speed=speed)
            time.sleep(move_wait_time)

        print("[步骤8] ✅ 放置完成")
        return True

    def execute_delivery(self, delivery_marker: str,
                         delivery_pose: list = None,
                         base_pose: list = None,
                         backward_speed: float = -0.25,
                         backward_duration: float = 2.0,
                         grab_wait_time: float = 0.5,
                         move_wait_time: float = 0.3,
                         speed: int = 200) -> dict:
        """
        执行完整的投递流程
        
        参数:
            delivery_marker:    投递标记点名称
            delivery_pose:      投递姿态关节角（可选）
            base_pose:          初始姿态关节角
            backward_speed:     后退速度
            backward_duration:  后退持续时间
            grab_wait_time:     夹爪等待时间
            move_wait_time:     运动等待时间
            speed:              运动速度
        
        返回:
            {"success": bool}
        """
        print("[步骤8] ━━━ 开始完整投递流程 ━━━")

        # ---- 第1步：后退 ----
        self.backward_from_station(backward_speed, backward_duration)

        # ---- 第2步：机械臂回到安全姿态 ----
        if self.arm and base_pose:
            print("[步骤8] 机械臂回到安全姿态...")
            self.arm.move_to_initial_pose(base_pose, speed=speed)
            time.sleep(move_wait_time)

        # ---- 第3步：导航到投递点 ----
        if not self.move_to_delivery_point(delivery_marker):
            return {"success": False, "error": "导航到投递点失败"}

        # ---- 第4步：执行放置动作 ----
        if self.arm:
            place_ok = self.place_item(
                self.arm,
                delivery_pose=delivery_pose,
                base_pose=base_pose,
                grab_wait_time=grab_wait_time,
                move_wait_time=move_wait_time,
                speed=speed,
            )
            if not place_ok:
                return {"success": False, "error": "放置动作失败"}

        print("[步骤8] ✅ 投递流程完成")
        return {"success": True}


# =============================================================================
#  单独运行此步骤的入口函数
# =============================================================================

def run(config: dict, shared_state: dict = None) -> dict:
    """
    执行步骤8：底盘移动至放置点
    
    前置条件：
        shared_state 中需要有：
        - "chassis": ChassisController 实例（来自步骤1）
        - "robot_arm": RobotArm 实例（来自步骤6，可选）
    
    参数:
        config:       从 config.json 加载的完整配置字典
        shared_state: 各步骤间共享的状态字典
    
    返回:
        {"success": bool}
    """
    if shared_state is None:
        shared_state = {}

    system_cfg = config.get("system_config", {})
    agv_cfg = config.get("agv_config", {})
    robot_params = config.get("robot_params", {})
    grasp_cfg = config.get("grasp_config", {})

    print("=" * 60)
    print(f"  步骤8：底盘移动至放置点")
    print(f"  投递标记点: {agv_cfg.get('delivery_marker', 'station4')}")
    print("=" * 60)

    # ---- 获取或创建底盘控制器 ----
    chassis = shared_state.get("chassis")
    if chassis is None:
        chassis = ChassisController(
            agv_ip=system_cfg.get("agv_ip", ""),
            agv_port=system_cfg.get("agv_port", 8080)
        )

    # ---- 获取机械臂控制器 ----
    arm = shared_state.get("robot_arm")

    # ---- 创建投递控制器并执行 ----
    delivery = DeliveryController(chassis, arm)

    delivery_marker = agv_cfg.get("delivery_marker", "station4")
    delivery_pose = robot_params.get("delivery_pose")  # 可选的投递姿态
    base_pose = robot_params.get("base_pose", [0, 0, 0, 0, 0, 0])

    result = delivery.execute_delivery(
        delivery_marker=delivery_marker,
        delivery_pose=delivery_pose,
        base_pose=base_pose,
        backward_speed=agv_cfg.get("backward_speed", -0.25),
        backward_duration=agv_cfg.get("backward_duration", 2),
        grab_wait_time=grasp_cfg.get("grab_wait_time", 0.5),
        move_wait_time=grasp_cfg.get("move_wait_time", 0.3),
        speed=robot_params.get("move_speed", 200),
    )

    # 存入共享状态
    shared_state["step8_success"] = result["success"]

    print(f"\n{'=' * 60}")
    print(f"  步骤8 结果: {'✅ 投递成功' if result['success'] else '❌ 投递失败'}")
    print(f"{'=' * 60}\n")

    return result


if __name__ == "__main__":
    sys.path.insert(0, _project_root)
    config_path = os.path.join(_project_root, "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    result = run(cfg)
    print(f"最终结果: {result}")
