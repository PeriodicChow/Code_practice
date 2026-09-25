# -*- coding: utf-8 -*-
"""
==============================================================================
  robot_lab - 机器人实验室教学工程 主程序入口
==============================================================================

  完整取放货流程：
    步骤1: 底盘移动到取货点
    步骤2: 打开相机，获取彩色图和深度图
    步骤3: YOLO 识别目标
    步骤4: 计算目标中心像素坐标
    步骤5: 像素坐标 + 深度 → 3D 世界坐标
    步骤6: 机械臂逆解，移动到目标点
    步骤7: 规划抓取路径，执行抓取
    步骤8: 底盘移动到放置点，放下物品

用法：
    python main.py
==============================================================================
"""

from modules.delivery import DeliveryController
from modules.grasp_planner import GraspPlanner
from modules.robot_arm import RobotArm
from modules.coord_transform import CoordinateTransformer
from modules.center_calc import CenterCalculator
from modules.detector import YOLODetector
from modules.depth_camera import DepthCamera
from modules.chassis import ChassisController
import os
import sys
import json


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def load_config():
    """加载配置文件"""
    config_path = os.path.join(PROJECT_ROOT, "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# =============================================================================
#  8 个步骤函数 —— 每个函数做一件事，输入明确，输出明确
# =============================================================================

def step_1_chassis_move(config):
    """
    步骤1：底盘移动控制
    让 AGV 底盘导航到取货点的 marker 位置
    """
    print("\n" + "=" * 60)
    print("  步骤1：底盘移动控制")
    print("=" * 60)

    sys_cfg = config["system_config"]
    agv_cfg = config["agv_config"]

    chassis = ChassisController(
        agv_ip=sys_cfg["agv_ip"],
        agv_port=sys_cfg["agv_port"],
    )

    marker = agv_cfg["pickup_marker"]
    print(f"  目标标记点: {marker}")

    success = chassis.move_to_marker(marker)
    print(f"  结果: {'✅ 成功' if success else '❌ 失败'}")

    return chassis  # 返回底盘控制器，后面步骤8还要用


def step_2_get_depth_image(config):
    """
    步骤2：获取深度图数据
    打开 Orbbec 深度相机，多帧采样获取稳定的彩色图和深度图
    """
    print("\n" + "=" * 60)
    print("  步骤2：获取深度图数据")
    print("=" * 60)

    cam_cfg = config["camera_config"]

    camera = DepthCamera(
        serial_number=cam_cfg.get("serial_number", ""),
        align_mode=cam_cfg.get("align_mode", "HW"),
    )
    camera.open()

    # 多帧采样取中位数，消除深度噪声
    num_frames = cam_cfg.get("stable_frames", 5)
    color_image, depth_data, depth_image = camera.get_stable_frame(
        num_frames=num_frames)

    if color_image is None:
        print("  结果: ❌ 采集失败")
        return None, None, None

    print(f"  彩色图尺寸: {color_image.shape}")
    print(f"  深度图尺寸: {depth_data.shape}")
    print(f"  结果: ✅ 成功")

    # 保存图像方便查看
    output_dir = os.path.join(
        PROJECT_ROOT, config["detection_config"].get("output_dir", "output"))
    os.makedirs(output_dir, exist_ok=True)
    import cv2
    cv2.imwrite(os.path.join(output_dir, "color_image.jpg"), color_image)
    cv2.imwrite(os.path.join(output_dir, "depth_image.jpg"), depth_image)

    return color_image, depth_data, camera  # 返回彩色图、深度图、相机对象


def step_3_yolo_detect(config, color_image):
    """
    步骤3：YOLO 模型识别
    用 YOLO 对彩色图做目标检测，返回检测框列表
    """
    print("\n" + "=" * 60)
    print("  步骤3：YOLO 模型识别")
    print("=" * 60)

    det_cfg = config["detection_config"]
    model_path = det_cfg["model_path"]
    if not os.path.isabs(model_path):
        model_path = os.path.join(PROJECT_ROOT, model_path)

    detector = YOLODetector(model_path)

    save_path = os.path.join(PROJECT_ROOT, det_cfg.get(
        "output_dir", "output"), "detection_result.jpg")
    result = detector.detect(
        image=color_image,
        target_tags=det_cfg["target_tags"],
        confidence=det_cfg["confidence_threshold"],
        iou=det_cfg["iou_threshold"],
        save_path=save_path,
    )

    print(f"  检测到 {len(result['labels'])} 个目标: {result['labels']}")
    print(f"  结果: {'✅ 成功' if result['labels'] else '❌ 未检测到目标'}")

    return result  # {"labels": [...], "bboxes": [...], "confidences": [...]}


def step_4_calc_center(detection_result):
    """
    步骤4：获取识别点中心位置
    从检测框中选出目标，计算中心像素坐标 (cx, cy)
    """
    print("\n" + "=" * 60)
    print("  步骤4：获取识别点中心位置（像素坐标）")
    print("=" * 60)

    calculator = CenterCalculator(selection_strategy="right")

    target = calculator.select_target(
        labels=detection_result["labels"],
        bboxes=detection_result["bboxes"],
        confidences=detection_result["confidences"],
    )

    if target is None:
        print("  结果: ❌ 未找到目标")
        return None

    print(f"  结果: ✅ 中心像素 = ({target['center_x']}, {target['center_y']})")

    return target  # {"center_x": int, "center_y": int, "bbox": [...], ...}


def step_5_pixel_to_3d(config, target, depth_data):
    """
    步骤5：像素坐标转相机坐标系（3D坐标）
    用中心像素坐标 + 该位置的深度值，算出目标在世界坐标系下的 3D 位置
    """
    print("\n" + "=" * 60)
    print("  步骤5：像素坐标 → 3D 世界坐标")
    print("=" * 60)

    calib = config["calibration"]
    transformer = CoordinateTransformer(
        K=calib["K"],
        R=calib["R_camera_to_world"],
        T=calib["T_camera_to_world"],
    )

    # 获取目标像素处的深度值（邻域中位数，更鲁棒）
    import numpy as np
    cx, cy = target["center_x"], target["center_y"]
    h, w = depth_data.shape[:2]
    px = int(np.clip(cx, 0, w - 1))
    py = int(np.clip(cy, 0, h - 1))
    radius = 3
    patch = depth_data[max(0, py-radius):py+radius+1,
                       max(0, px-radius):px+radius+1]
    valid = patch[(patch > 50) & (patch < 10000)]
    if valid.size == 0:
        print("  结果: ❌ 该位置无有效深度")
        return None
    depth_mm = float(np.median(valid))
    print(f"  深度值: {depth_mm:.1f} mm")

    # 坐标变换
    world_coord = transformer.pixel_to_world(cx, cy, depth_mm)

    print(
        f"  世界坐标: ({world_coord[0]:.1f}, {world_coord[1]:.1f}, {world_coord[2]:.1f}) mm")
    print(f"  结果: ✅ 成功")

    return world_coord  # numpy array [X, Y, Z]


def step_6_robot_move(config, world_coord):
    """
    步骤6：机器人移动至目标点
    连接 JAKA 机械臂，通过逆运动学计算关节角，运动到目标 3D 位置
    """
    print("\n" + "=" * 60)
    print("  步骤6：机器人移动至目标点")
    print("=" * 60)

    sys_cfg = config["system_config"]
    robot_params = config["robot_params"]

    arm = RobotArm(sys_cfg["robot_ip"])
    arm.connect()

    # 先回到初始姿态
    base_pose = robot_params.get("base_pose", [0, 0, 0, 0, 0, 0])
    if any(j != 0 for j in base_pose):
        arm.move_to_initial_pose(base_pose)

    # 移动到目标
    result = arm.move_to_world_coord(
        world_coord=world_coord.tolist(),
        robot_params=robot_params,
        speed=robot_params.get("move_speed", 200),
    )

    print(
        f"  结果: {'✅ 成功' if result['success'] else '❌ ' + result.get('error', '失败')}")

    return arm, result.get("target_joints")  # 返回机械臂对象和目标关节角


def step_7_grasp(config, arm, target_joints):
    """
    步骤7：机械臂抓取（运动学规划）
    规划抓取路径（前进→夹紧→抬升→撤退），然后执行
    """
    print("\n" + "=" * 60)
    print("  步骤7：机械臂抓取")
    print("=" * 60)

    grasp_cfg = config["grasp_config"]
    robot_params = config["robot_params"]

    planner = GraspPlanner(arm, io_tool=grasp_cfg.get("io_tool", 1))

    # 规划路径
    path = planner.plan_grasp_path(
        target_joints=target_joints,
        forward_move=grasp_cfg["forward_move"],
        lift_height=grasp_cfg["lift_height"],
        retract_distance=grasp_cfg["retract_distance"],
    )
    if path is None:
        print("  结果: ❌ 路径规划失败")
        return False

    # 执行抓取
    success = planner.execute_grasp(
        path,
        grab_wait_time=grasp_cfg.get("grab_wait_time", 0.5),
        move_wait_time=grasp_cfg.get("move_wait_time", 0.3),
        speed=robot_params.get("move_speed", 200),
    )

    print(f"  结果: {'✅ 抓取成功' if success else '❌ 抓取失败'}")

    return success


def step_8_delivery(config, chassis, arm):
    """
    步骤8：底盘移动至放置点
    AGV 后退 → 导航到投递点 → 松开夹爪放下物品 → 回到初始姿态
    """
    print("\n" + "=" * 60)
    print("  步骤8：底盘移动至放置点")
    print("=" * 60)

    agv_cfg = config["agv_config"]
    robot_params = config["robot_params"]
    grasp_cfg = config["grasp_config"]

    delivery = DeliveryController(chassis, arm)

    result = delivery.execute_delivery(
        delivery_marker=agv_cfg["delivery_marker"],
        base_pose=robot_params.get("base_pose", [0, 0, 0, 0, 0, 0]),
        backward_speed=agv_cfg.get("backward_speed", -0.25),
        backward_duration=agv_cfg.get("backward_duration", 2),
        grab_wait_time=grasp_cfg.get("grab_wait_time", 0.5),
        move_wait_time=grasp_cfg.get("move_wait_time", 0.3),
        speed=robot_params.get("move_speed", 200),
    )

    print(f"  结果: {'✅ 投递成功' if result['success'] else '❌ 投递失败'}")

    return result["success"]


# =============================================================================
#  主函数 —— 一目了然的流程串联
# =============================================================================

def main():
    config = load_config()
    print("配置已加载\n")

    # 步骤1: 底盘移动到取货点
    chassis = step_1_chassis_move(config)

    # 步骤2: 获取彩色图和深度图
    color_image, depth_data, camera = step_2_get_depth_image(config)
    if color_image is None:
        print("\n相机采集失败，流程终止")
        return

    # 步骤3: YOLO 目标检测
    detection_result = step_3_yolo_detect(config, color_image)
    if not detection_result["labels"]:
        print("\n未检测到目标，流程终止")
        return

    # 步骤4: 计算目标中心像素坐标
    target = step_4_calc_center(detection_result)
    if target is None:
        print("\n中心计算失败，流程终止")
        return

    # 步骤5: 像素坐标 → 3D 世界坐标
    world_coord = step_5_pixel_to_3d(config, target, depth_data)
    if world_coord is None:
        print("\n坐标变换失败，流程终止")
        return

    # 步骤6: 机械臂移动到目标点
    arm, target_joints = step_6_robot_move(config, world_coord)
    if target_joints is None:
        print("\n机器人移动失败，流程终止")
        return

    # 步骤7: 执行抓取
    grasp_ok = step_7_grasp(config, arm, target_joints)
    if not grasp_ok:
        print("\n抓取失败，流程终止")
        return

    # 步骤8: 底盘移动到放置点，放下物品
    step_8_delivery(config, chassis, arm)

    # 清理资源
    if camera:
        camera.close()
    if arm:
        arm.disconnect()

    print("\n全部步骤执行完毕！")


if __name__ == "__main__":
    main()
