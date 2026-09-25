# -*- coding: utf-8 -*-
"""
=============================================================
步骤3：获取识别点中心位置（Pixel Center Calculation）
=============================================================

【教学要点】
  - 理解图像坐标系：原点(0,0)在左上角，x 向右增长，y 向下增长
  - 掌握从边界框 (x1, y1, x2, y2) 计算中心点的方法
  - 了解目标选择策略：当检测到多个同类目标时如何选取最优目标

【硬件依赖】
  - 无（纯数学计算）

【输入】
  - YOLO 检测结果：边界框列表、标签列表、置信度列表

【输出】
  - 选中目标的中心像素坐标 (center_x, center_y)
  - 选中目标的边界框、标签、置信度
=============================================================
"""

import cv2
import numpy as np
import json
import os


class CenterCalculator:
    """
    目标中心点计算器

    从 YOLO 检测结果中选取目标，计算其中心像素坐标。
    当存在多个同类目标时，支持多种选择策略。

    图像坐标系：
        (0,0)─────────────────────(W,0)
          │                         │
          │       ● (cx, cy)       │
          │     ┌──────────┐       │
          │     │  目标     │       │
          │     └──────────┘       │
          │                         │
        (0,H)─────────────────────(W,H)
    """

    def __init__(self, selection_strategy: str = "right"):
        """
        参数:
            selection_strategy: 多目标选择策略
                - "right": 选最右边的目标（x2 最大）
                - "left":  选最左边的目标（x1 最小）
                - "center": 选最靠近画面中心的目标
                - "highest_conf": 选置信度最高的目标
        """
        self.selection_strategy = selection_strategy

    def calculate_center(self, bbox: list) -> tuple:
        """
        从边界框坐标计算中心点

        边界框格式: [x1, y1, x2, y2]
            x1, y1 = 左上角坐标
            x2, y2 = 右下角坐标

        计算公式:
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

        参数:
            bbox: [x1, y1, x2, y2] 边界框坐标

        返回:
            (center_x, center_y) 中心像素坐标（整数）
        """
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        return center_x, center_y

    def select_target(self, labels: list, bboxes: list, confidences: list,
                      target_label: str = None,
                      image_width: int = 1280) -> dict:
        """
        从检测结果中选取最优目标并计算中心坐标

        参数:
            labels:      所有检测到的类别标签列表
            bboxes:      所有检测框坐标列表 [[x1,y1,x2,y2], ...]
            confidences: 所有置信度列表
            target_label: 指定目标类别（None 则选所有类别中置信度最高的）
            image_width:  图像宽度（用于 center 策略）

        返回:
            {
                "label": str,          # 选中目标的类别
                "bbox": [x1,y1,x2,y2], # 选中目标的边界框
                "confidence": float,    # 选中目标的置信度
                "center_x": int,        # 中心 x 坐标
                "center_y": int,        # 中心 y 坐标
            }
            如果未找到目标，返回 None
        """
        # ---- 第1步：按类别过滤 ----
        if target_label:
            indices = [i for i, lbl in enumerate(
                labels) if lbl == target_label]
        else:
            indices = list(range(len(labels)))

        if not indices:
            print(f"[步骤3] ❌ 未找到目标: {target_label}")
            return None

        # ---- 第2步：按策略选取 ----
        if len(indices) == 1:
            best_idx = indices[0]
        else:
            print(
                f"[步骤3] 检测到 {len(indices)} 个同类目标，使用策略: {self.selection_strategy}")
            best_idx = self._apply_strategy(
                indices, bboxes, confidences, image_width)

        # ---- 第3步：计算中心坐标 ----
        bbox = bboxes[best_idx]
        center_x, center_y = self.calculate_center(bbox)

        result = {
            "label": labels[best_idx],
            "bbox": bbox,
            "confidence": confidences[best_idx],
            "center_x": center_x,
            "center_y": center_y,
        }

        print(f"[步骤3] ✅ 选中目标: {result['label']}")
        print(f"       边界框: [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]")
        print(f"       中心点: ({center_x}, {center_y})")
        print(f"       置信度: {result['confidence']:.3f}")

        return result

    def _apply_strategy(self, indices, bboxes, confidences, image_width) -> int:
        """根据策略从候选目标中选取最优的一个"""
        if self.selection_strategy == "right":
            # 选最右边的（x2 最大）
            return max(indices, key=lambda i: bboxes[i][2])
        elif self.selection_strategy == "left":
            # 选最左边的（x1 最小）
            return min(indices, key=lambda i: bboxes[i][0])
        elif self.selection_strategy == "center":
            # 选最靠近画面水平中心的
            img_center = image_width // 2
            return min(indices, key=lambda i: abs(
                (bboxes[i][0] + bboxes[i][2]) / 2 - img_center
            ))
        elif self.selection_strategy == "highest_conf":
            # 选置信度最高的
            return max(indices, key=lambda i: confidences[i])
        else:
            # 默认选第一个
            return indices[0]

    def draw_result(self, image: np.ndarray, target_info: dict) -> np.ndarray:
        """
        在图像上绘制选中目标的标注信息（用于可视化教学）

        参数:
            image:       BGR 彩色图像
            target_info: select_target() 返回的目标信息字典

        返回:
            标注后的图像
        """
        if target_info is None or image is None:
            return image

        result = image.copy()
        bbox = target_info["bbox"]
        cx, cy = target_info["center_x"], target_info["center_y"]
        label = target_info["label"]
        conf = target_info["confidence"]

        # 绘制边界框
        cv2.rectangle(result, (bbox[0], bbox[1]),
                      (bbox[2], bbox[3]), (0, 0, 255), 2)

        # 绘制中心点（红色圆点）
        cv2.circle(result, (cx, cy), 8, (0, 0, 255), -1)

        # 绘制十字线
        cv2.line(result, (cx - 20, cy), (cx + 20, cy), (0, 0, 255), 1)
        cv2.line(result, (cx, cy - 20), (cx, cy + 20), (0, 0, 255), 1)

        # 绘制标签文字
        cv2.putText(result, f"{label} ({conf:.2f})",
                    (bbox[0], bbox[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # 绘制中心坐标文字
        cv2.putText(result, f"Center: ({cx}, {cy})",
                    (cx + 10, cy - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        return result


# =============================================================================
#  单独运行此步骤的入口函数
# =============================================================================

def run(config: dict, shared_state: dict = None) -> dict:
    """
    执行步骤3：计算目标中心像素坐标

    前置条件：
        shared_state 中需要有 "detection_result"（来自步骤2的检测结果）

    参数:
        config:       从 config.json 加载的完整配置字典
        shared_state: 各步骤间共享的状态字典

    返回:
        {"success": bool, "center_x": int, "center_y": int, ...}
    """
    if shared_state is None:
        shared_state = {}

    print("=" * 60)
    print(f"  步骤3：获取识别点中心位置（像素坐标）")
    print("=" * 60)

    # 获取步骤2的检测结果
    detection_result = shared_state.get("detection_result")
    if detection_result is None:
        print("[步骤3] ❌ shared_state 中没有 detection_result")
        print("[步骤3] 💡 请先执行步骤2（YOLO 检测）获取检测结果")
        return {"success": False, "error": "无检测结果"}

    labels = detection_result.get("labels", [])
    bboxes = detection_result.get("bboxes", [])
    confidences = detection_result.get("confidences", [])

    if not labels:
        print("[步骤3] ❌ 检测结果为空，没有检测到目标")
        return {"success": False, "error": "检测结果为空"}

    # 确定目标类别
    det_cfg = config.get("detection_config", {})
    target_tags = det_cfg.get("target_tags", [])
    target_label = target_tags[0] if target_tags else None

    # 创建计算器并选取目标
    calculator = CenterCalculator(selection_strategy="right")
    target_info = calculator.select_target(
        labels=labels,
        bboxes=bboxes,
        confidences=confidences,
        target_label=target_label,
    )

    if target_info is None:
        return {"success": False, "error": "未找到匹配的目标"}

    # 绘制标注图像（如果有的话）
    annotated_image = detection_result.get("annotated_image")
    if annotated_image is not None:
        marked_image = calculator.draw_result(annotated_image, target_info)
        shared_state["marked_image"] = marked_image

        # 保存标注图像
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        output_dir = det_cfg.get("output_dir", "output")
        save_path = os.path.join(project_root, output_dir, "center_marked.jpg")
        save_dir = os.path.dirname(save_path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        cv2.imwrite(save_path, marked_image)
        print(f"[步骤3] 📷 标注图已保存: {save_path}")

    # 存入共享状态
    shared_state["target_info"] = target_info
    shared_state["center_x"] = target_info["center_x"]
    shared_state["center_y"] = target_info["center_y"]
    shared_state["step3_success"] = True

    print(f"\n{'=' * 60}")
    print(
        f"  步骤3 结果: ✅ 中心像素坐标 = ({target_info['center_x']}, {target_info['center_y']})")
    print(f"{'=' * 60}\n")

    return {"success": True, **target_info}


if __name__ == "__main__":
    # 模拟测试
    test_labels = ["LaysBBQ", "LaysBBQ", "NfSpring"]
    test_bboxes = [[100, 200, 300, 400], [
        500, 200, 700, 400], [50, 50, 150, 150]]
    test_confs = [0.95, 0.88, 0.72]

    calculator = CenterCalculator(selection_strategy="right")
    result = calculator.select_target(
        test_labels, test_bboxes, test_confs, "LaysBBQ")
    print(f"测试结果: {result}")
