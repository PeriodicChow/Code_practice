# -*- coding: utf-8 -*-
"""
=============================================================
步骤5：像素坐标转相机坐标系（Pixel to 3D Coordinate Transform）
=============================================================

【教学要点】
  - 理解三种坐标系的关系：
      像素坐标系 (u, v)       → 2D，单位：像素
      相机坐标系 (Xc, Yc, Zc) → 3D，单位：mm，原点在相机光心
      世界坐标系 (Xw, Yw, Zw) → 3D，单位：mm，原点在机器人基座
  - 掌握相机内参矩阵 K 的含义：
      K = [[fx, 0, cx],    fx, fy = 焦距（像素单位）
           [0, fy, cy],    cx, cy = 光心像素坐标
           [0,  0,  1]]
  - 理解像素→相机坐标的转换公式：
      Xc = depth × (u - cx) / fx
      Yc = depth × (v - cy) / fy
      Zc = depth
  - 理解相机→世界坐标的转换（外参矩阵）：
      P_world = R × P_camera + T

【硬件依赖】
  - 无（纯数学计算，但需要相机标定参数）

【输入】
  - 像素坐标 (u, v)
  - 深度值 depth（mm）
  - 相机内参矩阵 K
  - 旋转矩阵 R 和平移向量 T

【输出】
  - 相机坐标系下的 3D 坐标 (Xc, Yc, Zc)
  - 世界坐标系下的 3D 坐标 (Xw, Yw, Zw)
=============================================================
"""

import numpy as np
import json
import os


class CoordinateTransformer:
    """
    坐标变换器
    
    实现三种坐标系之间的转换：
      像素坐标 → 相机坐标 → 世界坐标
    
    数学原理：
    
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   像素坐标 (u, v, depth)                                    │
    │       │                                                     │
    │       │  ① 像素 → 相机坐标                                  │
    │       │     Xc = depth × (u - cx) / fx                      │
    │       │     Yc = depth × (v - cy) / fy                      │
    │       │     Zc = depth                                      │
    │       ▼                                                     │
    │   相机坐标 (Xc, Yc, Zc)                                     │
    │       │                                                     │
    │       │  ② 相机 → 世界坐标                                  │
    │       │     P_world = R × P_camera + T                      │
    │       ▼                                                     │
    │   世界坐标 (Xw, Yw, Zw)                                     │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """

    def __init__(self, K: list, R: list, T: list):
        """
        初始化坐标变换器
        
        参数:
            K: 相机内参矩阵 3x3，格式:
               [[fx, 0, cx],
                [0, fy, cy],
                [0,  0,  1]]
            
            R: 相机到世界的旋转矩阵 3x3，格式:
               [[r11, r12, r13],
                [r21, r22, r23],
                [r31, r32, r33]]
            
            T: 相机到世界的平移向量 [tx, ty, tz]，单位 mm
        """
        self.K = np.array(K, dtype=np.float64)
        self.R = np.array(R, dtype=np.float64)
        self.T = np.array(T, dtype=np.float64).reshape(3)

        # 提取内参
        self.fx = self.K[0][0]
        self.fy = self.K[1][1]
        self.cx = self.K[0][2]
        self.cy = self.K[1][2]

        print(f"[步骤5] 坐标变换器初始化:")
        print(f"       焦距: fx={self.fx:.1f}, fy={self.fy:.1f}")
        print(f"       光心: cx={self.cx:.1f}, cy={self.cy:.1f}")

    def pixel_to_camera(self, pixel_u: int, pixel_v: int, depth_mm: float) -> np.ndarray:
        """
        像素坐标 → 相机坐标系（3D）
        
        这是针孔相机模型的反投影过程：
        
          像素 (u, v) 加上深度值 depth，就可以确定该点在
          相机坐标系中的 3D 位置：
        
                  depth
                   │
                   │     ● (Xc, Yc, Zc)   ← 实际 3D 点
                   │    /
                   │   /
                   │  /
          相机光心 ●─────────► 成像平面
                        (u, v) ← 像素坐标
        
        公式:
            Xc = depth × (u - cx) / fx
            Yc = depth × (v - cy) / fy
            Zc = depth
        
        参数:
            pixel_u:  像素 u 坐标（列）
            pixel_v:  像素 v 坐标（行）
            depth_mm: 该像素对应的深度值（单位：mm）
        
        返回:
            相机坐标系下的 3D 坐标 [Xc, Yc, Zc]（单位：mm）
        """
        # 归一化坐标（去除内参影响）
        x_n = (pixel_u - self.cx) / self.fx
        y_n = (pixel_v - self.cy) / self.fy

        # 乘以深度，得到相机坐标系下的 3D 坐标
        Xc = depth_mm * x_n
        Yc = depth_mm * y_n
        Zc = depth_mm

        camera_coord = np.array([Xc, Yc, Zc])
        print(f"[步骤5] 像素 ({pixel_u}, {pixel_v}) + 深度 {depth_mm:.1f}mm")
        print(f"       → 相机坐标: ({Xc:.1f}, {Yc:.1f}, {Zc:.1f}) mm")

        return camera_coord

    def camera_to_world(self, camera_coord: np.ndarray) -> np.ndarray:
        """
        相机坐标系 → 世界坐标系
        
        使用外参矩阵（旋转 R + 平移 T）将相机坐标转换到世界坐标：
        
            P_world = R × P_camera + T
        
        其中：
          - R: 3x3 旋转矩阵，描述相机相对于世界坐标系的朝向
          - T: 3x1 平移向量，描述相机相对于世界坐标系原点的位置
        
        参数:
            camera_coord: 相机坐标系下的 3D 坐标 [Xc, Yc, Zc]
        
        返回:
            世界坐标系下的 3D 坐标 [Xw, Yw, Zw]
        """
        P_camera = np.array(camera_coord, dtype=np.float64)
        P_world = np.dot(self.R, P_camera) + self.T

        print(f"[步骤5] 相机坐标 ({camera_coord[0]:.1f}, {camera_coord[1]:.1f}, {camera_coord[2]:.1f})")
        print(f"       → 世界坐标: ({P_world[0]:.1f}, {P_world[1]:.1f}, {P_world[2]:.1f}) mm")

        return P_world

    def pixel_to_world(self, pixel_u: int, pixel_v: int, depth_mm: float) -> np.ndarray:
        """
        像素坐标 → 世界坐标（一步完成）
        
        这是最常用的接口，将步骤 ① 和 ② 合并为一个调用。
        
        参数:
            pixel_u:  像素 u 坐标
            pixel_v:  像素 v 坐标
            depth_mm: 深度值（mm）
        
        返回:
            世界坐标系下的 3D 坐标 [Xw, Yw, Zw]
        """
        print(f"[步骤5] ━━━ 坐标变换: 像素→相机→世界 ━━━")

        # 第1步：像素 → 相机坐标
        camera_coord = self.pixel_to_camera(pixel_u, pixel_v, depth_mm)

        # 第2步：相机 → 世界坐标
        world_coord = self.camera_to_world(camera_coord)

        print(f"[步骤5] ✅ 最终世界坐标: ({world_coord[0]:.1f}, {world_coord[1]:.1f}, {world_coord[2]:.1f}) mm")
        return world_coord


# =============================================================================
#  单独运行此步骤的入口函数
# =============================================================================

def run(config: dict, shared_state: dict = None) -> dict:
    """
    执行步骤5：像素坐标转 3D 世界坐标
    
    前置条件：
        shared_state 中需要有：
        - "center_x", "center_y": 目标中心像素坐标（来自步骤3）
        - "depth_data": 深度数据数组（来自步骤4）
    
    参数:
        config:       从 config.json 加载的完整配置字典
        shared_state: 各步骤间共享的状态字典
    
    返回:
        {"success": bool, "world_coord": [X, Y, Z], "camera_coord": [Xc, Yc, Zc]}
    """
    if shared_state is None:
        shared_state = {}

    print("=" * 60)
    print(f"  步骤5：像素坐标转相机坐标系（3D 坐标）")
    print("=" * 60)

    # ---- 获取前置数据 ----
    center_x = shared_state.get("center_x")
    center_y = shared_state.get("center_y")
    depth_data = shared_state.get("depth_data")

    if center_x is None or center_y is None:
        print("[步骤5] ❌ 缺少中心像素坐标 (center_x, center_y)")
        print("[步骤5] 💡 请先执行步骤3 获取目标中心位置")
        return {"success": False, "error": "缺少中心像素坐标"}

    if depth_data is None:
        print("[步骤5] ❌ 缺少深度数据 (depth_data)")
        print("[步骤5] 💡 请先执行步骤4 获取深度图")
        return {"success": False, "error": "缺少深度数据"}

    # ---- 获取标定参数 ----
    calib = config.get("calibration", {})
    K = calib.get("K")
    R = calib.get("R_camera_to_world")
    T = calib.get("T_camera_to_world")

    if not K or not R or not T:
        print("[步骤5] ❌ 缺少相机标定参数（K, R, T）")
        print("[步骤5] 💡 请在 config.json 的 calibration 字段中配置")
        return {"success": False, "error": "缺少标定参数"}

    # ---- 获取目标像素处的深度值 ----
    # 使用邻域中位数提高鲁棒性
    h, w = depth_data.shape[:2]
    cx = int(np.clip(center_x, 0, w - 1))
    cy = int(np.clip(center_y, 0, h - 1))
    radius = 3
    x1, x2 = max(0, cx - radius), min(w, cx + radius + 1)
    y1, y2 = max(0, cy - radius), min(h, cy + radius + 1)
    patch = depth_data[y1:y2, x1:x2]
    valid = patch[(patch > 50) & (patch < 10000)]
    
    if valid.size == 0:
        print(f"[步骤5] ❌ 像素 ({center_x},{center_y}) 处无有效深度值")
        return {"success": False, "error": "无有效深度值"}

    depth_mm = float(np.median(valid))
    print(f"[步骤5] 目标像素 ({center_x}, {center_y}) 深度: {depth_mm:.1f} mm")

    # ---- 执行坐标变换 ----
    transformer = CoordinateTransformer(K, R, T)
    world_coord = transformer.pixel_to_world(center_x, center_y, depth_mm)
    camera_coord = transformer.pixel_to_camera(center_x, center_y, depth_mm)

    # 存入共享状态
    shared_state["world_coord"] = world_coord.tolist()
    shared_state["camera_coord"] = camera_coord.tolist()
    shared_state["target_depth_mm"] = depth_mm
    shared_state["step5_success"] = True

    print(f"\n{'=' * 60}")
    print(f"  步骤5 结果: ✅ 成功")
    print(f"  相机坐标: ({camera_coord[0]:.1f}, {camera_coord[1]:.1f}, {camera_coord[2]:.1f}) mm")
    print(f"  世界坐标: ({world_coord[0]:.1f}, {world_coord[1]:.1f}, {world_coord[2]:.1f}) mm")
    print(f"{'=' * 60}\n")

    return {
        "success": True,
        "camera_coord": camera_coord.tolist(),
        "world_coord": world_coord.tolist(),
        "depth_mm": depth_mm,
    }


if __name__ == "__main__":
    # 使用示例参数测试
    test_K = [[905.0, 0.0, 640.0], [0.0, 905.0, 400.0], [0.0, 0.0, 1.0]]
    test_R = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    test_T = [0, 0, 0]

    transformer = CoordinateTransformer(test_K, test_R, test_T)

    # 假设图像中心点 (640, 400)，深度 500mm
    result = transformer.pixel_to_world(640, 400, 500)
    print(f"测试结果: {result}")
