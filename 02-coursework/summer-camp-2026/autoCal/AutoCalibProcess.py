# coding: utf-8
"""
自动标定：眼在手外
流程：
1. 使用预设关节角序列自动运动
2. 每个点位自动采图并检测棋盘格角点
3. 保存有效图像与对应 TCP 位姿
4. 自动执行手眼标定

注意：
- 运行前请确认机器人工作空间安全，急停有效。
- 该脚本会真实驱动机械臂运动。
"""

import os
import time
import numpy as np
import cv2

from JAKA_SDK_LINUX import jkrc
from utilfs.handToEyeCalibration import Calibration
from OrbbecSDK.orbbecCamera import Camera
from utilfs.tools import loadJsonFile, findCorners


# 运动模式
ABS = 0

# 你提供的关节角（单位：弧度）
RAW_JOINTS_CSV = """
-2.114902,0.737021,1.688064,0.094120,0.638715,1.828066
-1.976880,0.835135,1.725203,0.256998,0.638859,1.797027
-1.606507,0.967310,1.735665,-0.020941,0.527226,2.201698
-1.606483,1.251863,1.550857,-0.156219,0.379137,2.108054
-1.940568,1.251863,1.461826,-0.387490,0.379185,2.109540
-1.940532,1.531335,1.347257,0.045332,0.299454,2.114429
-1.714030,1.531335,1.361842,0.097823,0.302222,2.081700
-1.713958,1.657110,1.138528,0.466662,0.470636,2.024440
-2.304756,1.800453,0.368853,0.620443,1.520670,1.407791
-2.304720,1.835543,0.368913,0.458033,1.255220,1.407827
-2.181307,2.027638,0.373011,0.457997,0.918511,1.407911
-1.724875,2.031688,0.645664,0.461149,0.412022,1.689648
-1.488499,2.030766,0.784693,0.399178,0.196030,2.101486
-1.086368,1.741227,1.140948,1.842163,-0.799955,0.601996
-1.086212,1.787438,1.254703,1.969232,-0.531856,0.601816
-1.086176,1.150333,1.737044,2.032508,-0.594318,0.601816
-1.333602,1.150548,1.772805,1.950273,-0.708396,0.601840
-1.333567,1.567947,1.292225,1.877576,-0.687363,0.601828
-1.490859,1.579260,1.428749,1.403421,-0.200169,0.608360
-2.0961587226957508, 1.5170978166053721, 1.4151953370576966, 1.0470216394612892, 0.5161284871470828, 1.065030557548605
-1.0060017245570272, 1.6902458928565178, 1.1120423797611814, 2.2603285285686643, -0.9217987336735811, 0.8649419454828179
"""


def parse_joint_targets(raw_csv: str):
    joints = []
    lines = [line.strip() for line in raw_csv.strip().splitlines() if line.strip()]
    for line in lines:
        nums = [float(x) for x in line.split(',')]
        if len(nums) != 6:
            raise ValueError(f"关节角格式错误: {line}")
        joints.append(nums)
    return joints


def safe_robot_login(robot):
    ret = robot.login()
    print(f"robot login: {ret}")


def main():
    map_json = loadJsonFile('./conf/userCmdControl.json')
    calibrate_cfg = map_json['calibrateParams']
    auto_filter_cfg = calibrate_cfg.get('autoSampleFilter', {})

    board_row_nums = calibrate_cfg['boardRowNums']
    board_col_nums = calibrate_cfg['boardCowNums']
    board_length = calibrate_cfg['boardLength']
    robot_ip = calibrate_cfg['robotIP']

    # 可按需改成你自己的相机序列号
    camera_sn = calibrate_cfg.get('cameraSN', 'AY8V743010L')

    calibrate_image_save_dir = calibrate_cfg['CalibrateImageSaveDir']
    if not os.path.exists(calibrate_image_save_dir):
        os.makedirs(calibrate_image_save_dir)

    save_pose_path = os.path.join(calibrate_image_save_dir, 'robotTcpPos.txt')
    save_joint_path = os.path.join(calibrate_image_save_dir, 'robotJointPos.txt')

    # 运行参数
    # 关节速度
    motion_speed = calibrate_cfg.get('autoMotionSpeed', 10) 
    # 到位稳定等待    
    settle_time_s = calibrate_cfg.get('autoSettleTime', 3) 
    # 每点采集重试次数   
    retry_per_pose = calibrate_cfg.get('autoCaptureRetry', 3)
    # 最小有效样本数 
    min_samples = calibrate_cfg.get('autoMinSamples', 10)   

    joint_targets = parse_joint_targets(RAW_JOINTS_CSV)
    print(f"待执行关节点数: {len(joint_targets)}")

    camera = Camera(camera_sn)

    robot = jkrc.RC(robot_ip)
    safe_robot_login(robot)
    robot.power_on()
    robot.enable_robot()

    calibrate_images = []
    robot_poses = []
    robot_joints = []
    save_index = 0

    try:
        for i, joint_target in enumerate(joint_targets):
            print(f"\n[{i+1}/{len(joint_targets)}] move to joint: {joint_target}")
            move_ret = robot.joint_move(
                joint_pos=joint_target,
                move_mode=ABS,
                is_block=True,
                speed=motion_speed,
            )
            print(f"joint_move ret: {move_ret}")
            if not isinstance(move_ret, tuple) or move_ret[0] != 0:
                print(f"关节点 {i+1} 运动失败，跳过")
                continue

            time.sleep(settle_time_s)
            got_this_pose = False
            for retry_idx in range(retry_per_pose):
                color_image = camera.getColorImage()
                if color_image is None or len(color_image) == 0:
                    print(f"  第 {retry_idx+1} 次采图失败")
                    time.sleep(0.2)
                    continue

                # 为了和原流程保持一致，必须检测到棋盘格才保存
                ok = findCorners(color_image, board_row_nums, board_col_nums)
                if not ok:
                    print(f"  第 {retry_idx+1} 次未检测到棋盘格")
                    time.sleep(0.2)
                    continue

                tcp_ret = robot.get_tcp_position()
                if isinstance(tcp_ret, tuple) and tcp_ret[0] == 0:
                    current_tcp = list(tcp_ret[1])
                else:
                    current_tcp = None

                joint_ret = robot.get_joint_position()
                if isinstance(joint_ret, tuple) and joint_ret[0] == 0:
                    current_joint = list(joint_ret[1])
                else:
                    current_joint = list(joint_target)

                if current_tcp is None:
                    print("  获取TCP失败，本次采集丢弃")
                    time.sleep(0.2)
                    continue

                robot_poses.append(current_tcp)
                robot_joints.append(current_joint)
                calibrate_images.append(color_image)

                img_path = os.path.join(calibrate_image_save_dir, f"{save_index:04d}.png")
                cv2.imwrite(img_path, color_image)
                save_index += 1

                print(f"  采集成功，已保存: {img_path}")
                got_this_pose = True
                break

            if not got_this_pose:
                print(f"位姿 {i+1} 采集失败，已跳过")

        print(f"\n有效样本数: {len(calibrate_images)}")

        if len(calibrate_images) != len(robot_poses):
            raise RuntimeError("图像和位姿数量不一致，终止标定")

        if len(calibrate_images) < min_samples:
            raise RuntimeError(
                f"有效样本不足: {len(calibrate_images)} < {min_samples}，建议补采"
            )

        np.savetxt(save_pose_path, robot_poses, fmt='%.6f', delimiter=',')
        np.savetxt(save_joint_path, robot_joints, fmt='%.6f', delimiter=',')
        print(f"位姿保存成功: {save_pose_path}")
        print(f"关节角保存成功: {save_joint_path}")

        calibrator = Calibration(board_row_nums, board_col_nums, board_length)
        # 自动筛样参数（可选，配置不存在时使用默认值）
        calibrator.enableAutoSampleFilter = auto_filter_cfg.get('enable', True)
        calibrator.minSamplesAfterFilter = auto_filter_cfg.get('minSamplesAfterFilter', 12)
        calibrator.maxFilterIterations = auto_filter_cfg.get('maxFilterIterations', 8)
        calibrator.minReprojThresholdPx = auto_filter_cfg.get('minReprojThresholdPx', 0.2)
        calibrator.reprojMadSigma = auto_filter_cfg.get('reprojMadSigma', 2.8)
        print(
            "[AutoFilter] enable={}, minSamplesAfterFilter={}, maxFilterIterations={}, "
            "minReprojThresholdPx={}, reprojMadSigma={}".format(
                calibrator.enableAutoSampleFilter,
                calibrator.minSamplesAfterFilter,
                calibrator.maxFilterIterations,
                calibrator.minReprojThresholdPx,
                calibrator.reprojMadSigma,
            )
        )
        calibrator.process(calibrate_images, robot_poses)
        print("自动标定完成")

    finally:
        try:
            robot.logout()
        except Exception:
            pass
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
