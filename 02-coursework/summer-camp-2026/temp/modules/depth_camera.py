# -*- coding: utf-8 -*-
"""
=============================================================
步骤4：获取深度图数据（Depth Image Acquisition）
=============================================================

【教学要点】
  - 了解深度相机的工作原理（结构光 / ToF 飞行时间）
  - 理解深度图：每个像素值表示该点到相机的距离（单位：mm）
  - 学习 Orbbec SDK 的使用：Pipeline → 配置 → 采集帧 → 解析数据
  - 掌握深度数据对齐（D2C）的概念：深度图与彩色图像像素对齐

【硬件依赖】
  - Orbbec 深度相机（如 Astra 系列、Femto 系列）

【输入】
  - 相机序列号（可选，空串则使用默认相机）

【输出】
  - color_image:  BGR 彩色图像（numpy 数组）
  - depth_data:   深度数据（uint16 数组，单位 mm）
  - depth_image:  深度可视化图像（灰度/伪彩色）
=============================================================
"""

import cv2
import numpy as np
import time
import json
import os
import sys

# 导入相机帧格式转换工具
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from camera_utils.frame_convert import frame_to_bgr_image


class DepthCamera:
    """
    Orbbec 深度相机控制器
    
    通过 pyorbbecsdk 驱动 Orbbec 深度相机，
    同时获取彩色图像和深度数据。
    
    工作流程：
      1. 创建 Context（设备上下文）
      2. 查找并打开相机设备
      3. 配置彩色流和深度流参数（分辨率、帧率、格式）
      4. 启动 Pipeline（数据管道）
      5. 循环采集帧数据
    """

    # 有效深度范围
    MIN_DEPTH = 20     # 最小深度 20mm
    MAX_DEPTH = 10000  # 最大深度 10000mm (10m)

    def __init__(self, serial_number: str = "", align_mode: str = "HW"):
        """
        初始化深度相机
        
        参数:
            serial_number: 相机序列号，空串则使用第一个可用相机
            align_mode:    深度对齐模式
                           "HW" = 硬件对齐（推荐，延迟低）
                           "SW" = 软件对齐
                           "NONE" = 不对齐
        """
        self.serial_number = serial_number
        self.align_mode = align_mode
        self.pipeline = None
        self.context = None
        print(f"[步骤4] 深度相机初始化: SN={serial_number or '默认'}, 对齐模式={align_mode}")

    def open(self):
        """
        打开相机并启动数据流
        
        步骤：
          1. 创建 Context 枚举设备
          2. 按序列号查找设备（或使用默认设备）
          3. 配置彩色流和深度流
          4. 启动 Pipeline
          5. 验证初始帧是否有效
        """
        from pyorbbecsdk import (
            Context, Pipeline, Config, OBSensorType, OBFormat,
            OBAlignMode
        )

        self.context = Context()
        device_list = self.context.query_devices()

        # ---- 查找设备 ----
        if self.serial_number:
            # 按序列号查找
            device = None
            index = 0
            while True:
                try:
                    dev = device_list.get_device_by_index(index)
                    if not dev:
                        break
                    dev_info = dev.get_device_info()
                    if dev_info.get_serial_number() == self.serial_number:
                        device = dev
                        print(f"[步骤4] ✅ 找到相机: {dev_info.get_name()} (SN: {dev_info.get_serial_number()})")
                        break
                    index += 1
                except Exception:
                    break

            if device is None:
                raise RuntimeError(f"未找到序列号为 {self.serial_number} 的相机")
            self.pipeline = Pipeline(device)
        else:
            # 使用默认相机
            self.pipeline = Pipeline()

        # ---- 配置数据流 ----
        device_info = self.pipeline.get_device().get_device_info()
        device_pid = device_info.get_pid()
        print(f"[步骤4] 使用相机: {device_info.get_name()} (PID: 0x{device_pid:04X})")

        config = Config()

        # 配置彩色流
        color_profiles = self.pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
        try:
            color_profile = color_profiles.get_video_stream_profile(1280, 800, OBFormat.RGB, 15)
        except Exception:
            color_profile = color_profiles.get_default_video_stream_profile()
        config.enable_stream(color_profile)
        print(f"[步骤4] 彩色流: {color_profile.get_width()}x{color_profile.get_height()}@{color_profile.get_fps()}fps")

        # 配置深度流
        depth_profiles = self.pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        try:
            depth_profile = depth_profiles.get_video_stream_profile(1280, 800, OBFormat.RLE, 15)
        except Exception:
            depth_profile = depth_profiles.get_default_video_stream_profile()
        config.enable_stream(depth_profile)
        print(f"[步骤4] 深度流: {depth_profile.get_width()}x{depth_profile.get_height()}@{depth_profile.get_fps()}fps")

        # ---- 设置深度对齐模式 ----
        if self.align_mode == 'HW':
            if device_pid == 0x066B:  # Femto Mega 不支持硬件对齐
                config.set_align_mode(OBAlignMode.SW_MODE)
            else:
                config.set_align_mode(OBAlignMode.HW_MODE)
        elif self.align_mode == 'SW':
            config.set_align_mode(OBAlignMode.SW_MODE)
        else:
            config.set_align_mode(OBAlignMode.DISABLE)

        # ---- 启用帧同步 ----
        try:
            self.pipeline.enable_frame_sync()
        except Exception as e:
            print(f"[步骤4] ⚠️ 帧同步启用失败（非关键）: {e}")

        # ---- 启动数据流 ----
        self.pipeline.start(config)
        print("[步骤4] ✅ 相机数据流已启动")

        # ---- 验证初始帧 ----
        for attempt in range(5):
            try:
                frames = self.pipeline.wait_for_frames(1000)
                if frames and frames.get_color_frame() and frames.get_depth_frame():
                    print("[步骤4] ✅ 初始帧验证通过")
                    return
            except Exception as e:
                print(f"[步骤4] ⚠️ 初始帧获取失败 (尝试 {attempt+1}/5): {e}")
                time.sleep(0.5)
        print("[步骤4] ⚠️ 初始帧验证未通过，继续运行...")

    def get_frame(self) -> tuple:
        """
        采集一帧彩色图和深度图
        
        返回:
            (color_image, depth_data, depth_image)
            - color_image: BGR 彩色图像 (numpy uint8 数组, HxWx3)
            - depth_data:  深度数据 (numpy uint16 数组, HxW, 单位: mm)
            - depth_image: 深度可视化图 (numpy uint8 数组, HxW)
            失败时返回 (None, None, None)
        """
        if self.pipeline is None:
            print("[步骤4] ❌ 相机未打开，请先调用 open()")
            return None, None, None

        from pyorbbecsdk import FrameSet

        try:
            frames: FrameSet = self.pipeline.wait_for_frames(1000)
            if frames is None:
                print("[步骤4] ❌ 获取帧超时")
                return None, None, None

            # ---- 获取彩色帧 ----
            color_frame = frames.get_color_frame()
            if color_frame is None:
                print("[步骤4] ❌ 彩色帧为空")
                return None, None, None
            color_image = frame_to_bgr_image(color_frame)

            # ---- 获取深度帧 ----
            depth_frame = frames.get_depth_frame()
            if depth_frame is None:
                print("[步骤4] ❌ 深度帧为空")
                return None, None, None

            # 解析深度数据
            depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
            depth_data = depth_data.reshape((depth_frame.get_height(), depth_frame.get_width()))

            # ---- 生成深度可视化图 ----
            depth_image = self._create_depth_visualization(depth_data)

            return color_image, depth_data, depth_image

        except Exception as e:
            print(f"[步骤4] ❌ 获取帧失败: {e}")
            return None, None, None

    def get_stable_frame(self, num_frames: int = 5, retry: int = 3) -> tuple:
        """
        多帧采样获取稳定的深度数据
        
        原理：
          深度相机单帧噪声较大（深度值跳动、空洞等），
          通过连续采集多帧，对每个像素取中位数，可以有效消除噪声。
          如果采集失败会重试，确保拿到足够数量的帧。
        
        参数:
            num_frames: 采样帧数（默认 5 帧）
            retry:      采集失败时的重试次数（默认 3 次）
        
        返回:
            (color_image, depth_data, depth_image)
            - color_image: 最后一帧的彩色图（uint8, BGR）
            - depth_data:  多帧中位数深度图（uint16, 单位 mm）
            - depth_image: 深度可视化图（uint8, BGR）
        """
        if self.pipeline is None:
            print("[步骤4] ❌ 相机未打开，请先调用 open()")
            return None, None, None

        from pyorbbecsdk import FrameSet

        collected_color = None
        collected_depths = []

        for attempt in range(retry):
            try:
                frames: FrameSet = self.pipeline.wait_for_frames(1000)
                if frames is None:
                    print(f"[步骤4] ⚠️ 帧获取超时 (重试 {attempt+1}/{retry})")
                    continue

                # 取彩色帧
                color_frame = frames.get_color_frame()
                if color_frame is not None:
                    collected_color = frame_to_bgr_image(color_frame)

                # 取深度帧
                depth_frame = frames.get_depth_frame()
                if depth_frame is None:
                    print(f"[步骤4] ⚠️ 深度帧为空 (重试 {attempt+1}/{retry})")
                    continue

                depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
                depth_data = depth_data.reshape((depth_frame.get_height(), depth_frame.get_width()))
                collected_depths.append(depth_data.copy())

                print(f"[步骤4] 已采集 {len(collected_depths)}/{num_frames} 帧")

                # 采集够了就停止
                if len(collected_depths) >= num_frames:
                    break

            except Exception as e:
                print(f"[步骤4] ⚠️ 采集异常 (重试 {attempt+1}/{retry}): {e}")

        if len(collected_depths) == 0 or collected_color is None:
            print("[步骤4] ❌ 未能采集到有效帧")
            return None, None, None

        if len(collected_depths) < num_frames:
            print(f"[步骤4] ⚠️ 只采集到 {len(collected_depths)}/{num_frames} 帧，使用中位数")

        # 多帧取中位数，消除深度噪声
        depth_stack = np.stack(collected_depths, axis=0)
        stable_depth = np.median(depth_stack, axis=0).astype(np.uint16)

        print(f"[步骤4] ✅ 深度数据稳定完成（{len(collected_depths)} 帧中位数）")

        # 生成可视化
        depth_image = self._create_depth_visualization(stable_depth)

        return collected_color, stable_depth, depth_image

    def _create_depth_visualization(self, depth_data: np.ndarray) -> np.ndarray:
        """
        将原始深度数据转换为可视化图像
        
        原理：
          1. 裁剪到有效深度范围（20mm ~ 10000mm）
          2. 归一化到 0~255
          3. 应用伪彩色映射（JET 色彩），使深度差异更直观
        
        参数:
            depth_data: 原始深度数据（uint16, 单位 mm）
        
        返回:
            伪彩色深度可视化图像（BGR uint8）
        """
        # 归一化到 0~255
        depth_normalized = np.clip(depth_data, self.MIN_DEPTH, self.MAX_DEPTH)
        depth_normalized = ((depth_normalized - self.MIN_DEPTH) /
                            (self.MAX_DEPTH - self.MIN_DEPTH) * 255).astype(np.uint8)

        # 应用 JET 伪彩色映射
        depth_color = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)

        # 将无效区域（深度为 0）标为黑色
        invalid_mask = depth_data < self.MIN_DEPTH
        depth_color[invalid_mask] = [0, 0, 0]

        return depth_color

    def get_depth_at_pixel(self, depth_data: np.ndarray, x: int, y: int,
                           radius: int = 3) -> float:
        """
        获取指定像素位置的深度值（鲁棒版本）
        
        原理：
          不直接取单个像素的深度（可能有噪声），
          而是取目标像素周围一个邻域的中位数，提高鲁棒性。
        
        参数:
            depth_data: 深度数据数组
            x, y:       像素坐标
            radius:     邻域半径（默认 3，即 7x7 的邻域）
        
        返回:
            深度值（mm），无效返回 None
        """
        h, w = depth_data.shape[:2]
        cx = int(np.clip(x, 0, w - 1))
        cy = int(np.clip(y, 0, h - 1))

        # 截取邻域
        x1, x2 = max(0, cx - radius), min(w, cx + radius + 1)
        y1, y2 = max(0, cy - radius), min(h, cy + radius + 1)
        patch = depth_data[y1:y2, x1:x2]

        # 过滤无效深度值
        valid = patch[(patch > 50) & (patch < 10000)]
        if valid.size == 0:
            print(f"[步骤4] ⚠️ 像素 ({x},{y}) 邻域内无有效深度")
            return None

        depth = float(np.median(valid))
        print(f"[步骤4] 像素 ({x},{y}) 深度 = {depth:.1f} mm")
        return depth

    def close(self):
        """关闭相机，释放资源"""
        if self.pipeline is not None:
            try:
                self.pipeline.stop()
                print("[步骤4] 相机已关闭")
            except Exception as e:
                print(f"[步骤4] ⚠️ 关闭相机异常: {e}")
            self.pipeline = None


# =============================================================================
#  单独运行此步骤的入口函数
# =============================================================================

def run(config: dict, shared_state: dict = None) -> dict:
    """
    执行步骤4：获取深度图数据
    
    功能：
      1. 打开 Orbbec 深度相机
      2. 采集一帧彩色图和深度图
      3. 将数据存入 shared_state 供后续步骤使用
    
    参数:
        config:       从 config.json 加载的完整配置字典
        shared_state: 各步骤间共享的状态字典
    
    返回:
        {"success": bool, "color_image": np.ndarray, "depth_data": np.ndarray}
    """
    if shared_state is None:
        shared_state = {}

    cam_cfg = config.get("camera_config", {})
    det_cfg = config.get("detection_config", {})

    print("=" * 60)
    print(f"  步骤4：获取深度图数据")
    print(f"  相机序列号: {cam_cfg.get('serial_number', '') or '默认'}")
    print(f"  对齐模式: {cam_cfg.get('align_mode', 'HW')}")
    print("=" * 60)

    # 创建并打开相机
    camera = DepthCamera(
        serial_number=cam_cfg.get("serial_number", ""),
        align_mode=cam_cfg.get("align_mode", "HW"),
    )

    try:
        camera.open()

        # 采集一帧数据
        color_image, depth_data, depth_image = camera.get_frame()

        if color_image is None or depth_data is None:
            print("[步骤4] ❌ 采集帧失败")
            return {"success": False, "error": "采集帧失败"}

        # 保存图像到输出目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = det_cfg.get("output_dir", "output")
        save_dir = os.path.join(project_root, output_dir)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        cv2.imwrite(os.path.join(save_dir, "color_image.jpg"), color_image)
        cv2.imwrite(os.path.join(save_dir, "depth_image.jpg"), depth_image)
        print(f"[步骤4] 📷 图像已保存到 {save_dir}/")

        # 存入共享状态
        shared_state["camera"] = camera
        shared_state["color_image"] = color_image
        shared_state["depth_data"] = depth_data
        shared_state["depth_image"] = depth_image
        shared_state["step4_success"] = True

        print(f"\n{'=' * 60}")
        print(f"  步骤4 结果: ✅ 成功")
        print(f"  彩色图尺寸: {color_image.shape}")
        print(f"  深度图尺寸: {depth_data.shape}")
        print(f"  深度范围: {depth_data[depth_data > 0].min()} ~ {depth_data.max()} mm")
        print(f"{'=' * 60}\n")

        return {
            "success": True,
            "color_image": color_image,
            "depth_data": depth_data,
            "depth_image": depth_image,
        }

    except Exception as e:
        print(f"[步骤4] ❌ 异常: {e}")
        return {"success": False, "error": str(e)}
    finally:
        # 注意：如果后续步骤还需要相机数据，不要在这里关闭
        # camera.close() 由 main.py 在所有步骤完成后统一关闭
        pass


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    result = run(cfg)
    print(f"最终结果: {result['success']}")

    # 如果成功，关闭窗口
    if "camera" in (result or {}):
        pass  # 由调用者管理
