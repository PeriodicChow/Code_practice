# -*- coding: utf-8 -*-
"""
=============================================================
步骤2：YOLO 模型识别（Object Detection with YOLO）
=============================================================

【教学要点】
  - 理解 YOLO（You Only Look Once）目标检测算法的基本原理
  - 学习使用 ultralytics 库加载预训练模型并进行推理
  - 了解 OBB（旋转边界框）检测与普通矩形框检测的区别
  - 掌握置信度阈值、IoU 阈值对检测结果的影响

【硬件依赖】
  - 无（纯软件算法）

【输入】
  - YOLO 模型权重文件（.pt）
  - 相机采集的 BGR 彩色图像（numpy 数组）
  - 目标类别名称列表
  - 置信度阈值、IoU 阈值

【输出】
  - 检测到的目标列表：标签、边界框坐标、置信度、旋转角度
=============================================================
"""

import os
import cv2
import numpy as np
import json
from pathlib import Path


class YOLODetector:
    """
    YOLO 目标检测器
    
    基于 ultralytics 库封装的 YOLO 推理引擎，
    支持标准矩形框检测和 OBB（旋转边界框）检测。
    
    检测流程：
      1. 加载 YOLO 模型权重
      2. 对输入图像进行预处理（可选 ROI 裁剪）
      3. 执行推理，获取检测结果
      4. 解析检测框坐标、类别、置信度
      5. 返回结构化的检测结果
    """

    def __init__(self, model_path: str):
        """
        初始化 YOLO 检测器
        
        参数:
            model_path: YOLO 模型权重文件路径（.pt 格式）
        
        注意:
            模型采用延迟加载策略，首次调用 detect() 时才真正加载到显存
        """
        self.model_path = model_path
        self.model = None
        print(f"[步骤2] YOLO 检测器初始化，模型路径: {model_path}")

    def _load_model(self):
        """
        延迟加载 YOLO 模型
        
        为什么要延迟加载？
          - 模型加载需要时间（几秒），放在构造函数中会拖慢初始化
          - 如果权重文件损坏或缺失，可以在运行时捕获错误而不是启动失败
        """
        if self.model is not None:
            return self.model

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"YOLO 模型权重文件不存在: {self.model_path}\n"
                f"请将 .pt 权重文件放入 weights/ 目录"
            )

        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            print(f"[步骤2] ✅ YOLO 模型加载成功: {self.model_path}")
            return self.model
        except Exception as e:
            raise RuntimeError(
                f"YOLO 模型加载失败: {e}\n"
                f"常见原因：权重文件损坏、PyTorch 版本不兼容"
            )

    def detect(self, image: np.ndarray, target_tags: list,
               confidence: float = 0.85, iou: float = 0.8,
               save_path: str = None) -> dict:
        """
        对输入图像执行 YOLO 目标检测
        
        参数:
            image:        BGR 格式的彩色图像（numpy 数组，来自 OpenCV）
            target_tags:  需要检测的目标类别名称列表，例如 ["LaysBBQ", "NfSpring"]
            confidence:   置信度阈值（0~1），低于此值的检测结果将被过滤
            iou:          IoU（交并比）阈值，用于非极大值抑制（NMS）
            save_path:    检测结果图片保存路径（可选），用于可视化调试
        
        返回:
            {
                "labels": ["LaysBBQ", "LaysBBQ"],     # 检测到的类别标签
                "bboxes": [[x1,y1,x2,y2], ...],       # 边界框坐标（像素）
                "confidences": [0.95, 0.88],           # 每个目标的置信度
                "angles": [0.0, 12.5],                 # 旋转角度（OBB 模式）
                "annotated_image": np.ndarray          # 标注后的图像（可选）
            }
        """
        yolo_model = self._load_model()

        if image is None or image.size == 0:
            raise ValueError("[步骤2] ❌ 输入图像为空")

        print(f"[步骤2] 🔍 开始 YOLO 检测: 目标={target_tags}, "
              f"置信度阈值={confidence}, 图像尺寸={image.shape}")

        # ---- 执行推理 ----
        results = yolo_model.predict(
            source=image,
            conf=confidence,
            iou=iou,
            imgsz=1280,         # 推理分辨率
            half=False,         # 是否使用半精度（FP16），CPU 上建议 False
            max_det=80,         # 最大检测数量
            visualize=False,    # 不显示可视化窗口
            augment=False,      # 不使用测试时增强
            agnostic_nms=False, # 类别感知 NMS
            show=False,
            save=False,
        )

        # ---- 解析检测结果 ----
        detections = []
        annotated_image = image.copy()

        for result in results:
            # 优先尝试 OBB（旋转边界框）检测
            obb_boxes = getattr(result, 'obb', None)
            if obb_boxes is not None and hasattr(obb_boxes, 'xyxyxyxy'):
                detections.extend(self._parse_obb_results(
                    result, obb_boxes, annotated_image, target_tags
                ))
            else:
                # 回退到标准矩形框检测
                boxes = getattr(result, 'boxes', None)
                if boxes is not None and len(boxes) > 0:
                    detections.extend(self._parse_box_results(
                        result, boxes, annotated_image, target_tags
                    ))

        # 按置信度降序排列
        detections.sort(key=lambda d: -d["conf"])

        # 构建返回结果
        labels = [d["label"] for d in detections]
        bboxes = [d["bbox"] for d in detections]
        confidences = [d["conf"] for d in detections]
        angles = [d["angle"] for d in detections]

        print(f"[步骤2] ✅ 检测完成: 找到 {len(labels)} 个目标")
        for i, (lbl, conf) in enumerate(zip(labels, confidences)):
            print(f"       目标 {i+1}: {lbl} (置信度: {conf:.2f})")

        # 保存标注图像
        if save_path:
            save_dir = os.path.dirname(save_path)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir)
            cv2.imwrite(save_path, annotated_image)
            print(f"[步骤2] 📷 检测结果图已保存: {save_path}")

        return {
            "labels": labels,
            "bboxes": bboxes,
            "confidences": confidences,
            "angles": angles,
            "annotated_image": annotated_image,
        }

    def _parse_obb_results(self, result, obb_boxes, annotated_image, target_tags) -> list:
        """解析 OBB（旋转边界框）检测结果"""
        detections = []
        xyxyxyxys = obb_boxes.xyxyxyxy

        for i, xyxyxyxy in enumerate(xyxyxyxys):
            # 将 4 个角点转为 numpy 数组
            points = xyxyxyxy.cpu().numpy().reshape(4, 2)
            rect = cv2.minAreaRect(points.astype(np.float32))

            # 计算旋转角度（归一化到 -45° ~ 45°）
            angle = rect[2]
            if angle < -45:
                angle = 90 + angle

            # 获取最小外接矩形
            box = cv2.boxPoints(rect).astype(int)
            cls = int(obb_boxes.cls[i].item())
            conf_val = obb_boxes.conf[i].item()
            label = result.names[cls]

            if label not in target_tags:
                continue

            # 计算外接矩形的坐标
            x1, y1 = box[:, 0].min(), box[:, 1].min()
            x2, y2 = box[:, 0].max(), box[:, 1].max()

            detections.append({
                "label": label,
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "conf": float(conf_val),
                "angle": float(angle),
            })

            # 在图像上绘制检测框
            cv2.drawContours(annotated_image, [box], 0, (0, 255, 0), 2)
            cv2.putText(annotated_image, f"{label} {conf_val:.2f}",
                        (int(x2) + 6, int(y1) + 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

        return detections

    def _parse_box_results(self, result, boxes, annotated_image, target_tags) -> list:
        """解析标准矩形框检测结果"""
        detections = []

        for i in range(len(boxes)):
            cls = int(boxes.cls[i].item())
            conf_val = boxes.conf[i].item()
            label = result.names[cls]

            if label not in target_tags:
                continue

            xyxy = boxes.xyxy[i].cpu().numpy().astype(int).tolist()
            x1, y1, x2, y2 = xyxy

            detections.append({
                "label": label,
                "bbox": xyxy,
                "conf": float(conf_val),
                "angle": 0.0,
            })

            # 在图像上绘制检测框
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated_image, f"{label} {conf_val:.2f}",
                        (x2 + 6, y1 + 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

        return detections


# =============================================================================
#  单独运行此步骤的入口函数
# =============================================================================

def run(config: dict, shared_state: dict = None) -> dict:
    """
    执行步骤2：YOLO 目标检测
    
    前置条件：
        shared_state 中需要有 "color_image"（来自相机采集的彩色图像）
        如果没有，将尝试从摄像头或测试图片获取
    
    参数:
        config:       从 config.json 加载的完整配置字典
        shared_state: 各步骤间共享的状态字典
    
    返回:
        {"success": bool, "labels": [...], "bboxes": [...], ...}
    """
    if shared_state is None:
        shared_state = {}

    det_cfg = config.get("detection_config", {})
    model_path = det_cfg.get("model_path", "weights/wyh.pt")
    confidence = det_cfg.get("confidence_threshold", 0.85)
    iou = det_cfg.get("iou_threshold", 0.8)
    target_tags = det_cfg.get("target_tags", ["LaysBBQ"])
    output_dir = det_cfg.get("output_dir", "output")

    # 确保模型路径正确（相对于工程根目录）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isabs(model_path):
        model_path = os.path.join(project_root, model_path)

    print("=" * 60)
    print(f"  步骤2：YOLO 模型识别")
    print(f"  模型: {model_path}")
    print(f"  目标类别: {target_tags}")
    print(f"  置信度阈值: {confidence}")
    print("=" * 60)

    # 获取输入图像
    color_image = shared_state.get("color_image")
    if color_image is None:
        print("[步骤2] ⚠️ shared_state 中没有 color_image")
        print("[步骤2] 💡 请先执行步骤4（depth_camera）获取相机图像")
        print("[步骤2] 💡 或手动加载一张测试图片")
        return {"success": False, "error": "无输入图像"}

    # 创建检测器并执行检测
    detector = YOLODetector(model_path)
    save_path = os.path.join(project_root, output_dir, "detection_result.jpg")
    result = detector.detect(
        image=color_image,
        target_tags=target_tags,
        confidence=confidence,
        iou=iou,
        save_path=save_path,
    )

    # 存入共享状态
    shared_state["detection_result"] = result
    shared_state["step2_success"] = len(result["labels"]) > 0

    success = len(result["labels"]) > 0
    print(f"\n{'=' * 60}")
    print(f"  步骤2 结果: {'✅ 成功，检测到 ' + str(len(result['labels'])) + ' 个目标' if success else '❌ 未检测到目标'}")
    print(f"{'=' * 60}\n")

    return {"success": success, **result}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    # 测试时使用一张测试图片
    test_img_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "test_image.jpg"
    )
    if os.path.exists(test_img_path):
        test_img = cv2.imread(test_img_path)
        shared = {"color_image": test_img}
    else:
        print("请准备 test_image.jpg 测试图片，或先执行步骤4获取相机图像")
        shared = {}

    result = run(cfg, shared)
    print(f"最终结果: {result}")
