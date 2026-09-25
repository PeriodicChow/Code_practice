# -*- coding: utf-8 -*-
"""
相机帧格式转换工具
将 Orbbec 相机原始帧数据转换为 OpenCV 可用的 BGR 图像格式
支持 YUYV、UYVY、I420、NV21、NV12、MJPG、RGB、BGR 等格式
"""

from typing import Union, Optional
import cv2
import numpy as np

from pyorbbecsdk import FormatConvertFilter, VideoFrame, OBFormat, OBConvertFormat


def yuyv_to_bgr(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """YUYV 格式转 BGR"""
    yuyv = frame.reshape((height, width, 2))
    return cv2.cvtColor(yuyv, cv2.COLOR_YUV2BGR_YUY2)


def uyvy_to_bgr(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """UYVY 格式转 BGR"""
    uyvy = frame.reshape((height, width, 2))
    return cv2.cvtColor(uyvy, cv2.COLOR_YUV2BGR_UYVY)


def i420_to_bgr(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """I420 格式转 BGR"""
    y = frame[0:height, :]
    u = frame[height:height + height // 4].reshape(height // 2, width // 2)
    v = frame[height + height // 4:].reshape(height // 2, width // 2)
    yuv_image = cv2.merge([y, u, v])
    return cv2.cvtColor(yuv_image, cv2.COLOR_YUV2BGR_I420)


def nv21_to_bgr(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """NV21 格式转 BGR"""
    y = frame[0:height, :]
    uv = frame[height:height + height // 2].reshape(height // 2, width)
    yuv_image = cv2.merge([y, uv])
    return cv2.cvtColor(yuv_image, cv2.COLOR_YUV2BGR_NV21)


def nv12_to_bgr(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """NV12 格式转 BGR"""
    y = frame[0:height, :]
    uv = frame[height:height + height // 2].reshape(height // 2, width)
    yuv_image = cv2.merge([y, uv])
    return cv2.cvtColor(yuv_image, cv2.COLOR_YUV2BGR_NV12)


def determine_convert_format(frame: VideoFrame):
    """根据帧格式确定转换目标格式"""
    format_map = {
        OBFormat.I420: OBConvertFormat.I420_TO_RGB888,
        OBFormat.MJPG: OBConvertFormat.MJPG_TO_RGB888,
        OBFormat.YUYV: OBConvertFormat.YUYV_TO_RGB888,
        OBFormat.NV21: OBConvertFormat.NV21_TO_RGB888,
        OBFormat.NV12: OBConvertFormat.NV12_TO_RGB888,
        OBFormat.UYVY: OBConvertFormat.UYVY_TO_RGB888,
    }
    return format_map.get(frame.get_format(), None)


def frame_to_rgb_frame(frame: VideoFrame) -> Union[Optional[VideoFrame], any]:
    """将原始帧转换为 RGB 格式帧"""
    if frame.get_format() == OBFormat.RGB:
        return frame
    convert_format = determine_convert_format(frame)
    if convert_format is None:
        print(f"不支持的帧格式: {frame.get_format()}")
        return None
    convert_filter = FormatConvertFilter()
    convert_filter.set_format_convert_format(convert_format)
    rgb_frame = convert_filter.process(frame)
    if rgb_frame is None:
        print(f"转换 {frame.get_format()} 到 RGB 失败")
    return rgb_frame


def frame_to_bgr_image(frame: VideoFrame) -> Union[Optional[np.ndarray], any]:
    """
    将 Orbbec 原始帧转换为 BGR 图像（numpy 数组）
    这是最常用的接口，可直接用于 OpenCV 后续处理
    """
    width = frame.get_width()
    height = frame.get_height()
    color_format = frame.get_format()
    data = np.asanyarray(frame.get_data())
    image = np.zeros((height, width, 3), dtype=np.uint8)

    if color_format == OBFormat.RGB:
        image = np.resize(data, (height, width, 3))
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    elif color_format == OBFormat.BGR:
        image = np.resize(data, (height, width, 3))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    elif color_format == OBFormat.YUYV:
        image = np.resize(data, (height, width, 2))
        image = cv2.cvtColor(image, cv2.COLOR_YUV2BGR_YUYV)
    elif color_format == OBFormat.MJPG:
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    elif color_format == OBFormat.I420:
        return i420_to_bgr(data, width, height)
    elif color_format == OBFormat.NV12:
        return nv12_to_bgr(data, width, height)
    elif color_format == OBFormat.NV21:
        return nv21_to_bgr(data, width, height)
    elif color_format == OBFormat.UYVY:
        image = np.resize(data, (height, width, 2))
        image = cv2.cvtColor(image, cv2.COLOR_YUV2BGR_UYVY)
    else:
        print(f"不支持的颜色格式: {color_format}")
        return None
    return image
