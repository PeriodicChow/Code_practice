import json
from utilfs.tools import pixel_to_world, loadJsonFile, generatorNearPoints
from OrbbecSDK.orbbecCamera import Camera  # 引用已有的Camera类
import cv2
import numpy as np
import sys
import time

PI = 3.1415926
ESC_KEY = 27

# 全局变量
depth_data = None
color_image = None
calib_data = None
camera = None

def on_EVENT_LBUTTONDOWN(event, x, y, flags, param):
    """鼠标左键点击回调函数"""
    global depth_data, color_image, calib_data
    
    if event == cv2.EVENT_LBUTTONDOWN:
        # 获取点击点的坐标和深度值
        xy = f"{x},{y}"
        depth = depth_data[y, x]
        print(f"点击坐标: {xy}, 深度值: {depth}mm")
        
        # 如果深度为0，尝试从附近点获取有效深度
        if int(depth) == 0:
            genCenterPoints = generatorNearPoints([x, y], 1, 4)
            for i, centerPoint in enumerate(genCenterPoints):
                depth = depth_data[centerPoint[0][1], centerPoint[0][0]]
                if int(depth) != 0 or i == len(genCenterPoints) - 1:
                    break
            print(f"附近点深度: {depth}mm")
        
        # 转换到世界坐标
        if depth > 0:
            worldPos = pixel_to_world([x, y], depth, 
                                     calib_data["CameraMatrix"], 
                                     calib_data["RotationMat"], 
                                     calib_data["TranslationMat"])
            print(f"世界坐标: {worldPos}")
        else:
            print("无效的深度值，无法转换到世界坐标")
        
        # 在图像上标记点击点
        cv2.circle(color_image, (x, y), 3, (0, 0, 255), -1)
        cv2.putText(color_image, f"({x},{y})", (x + 10, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow("Camera View", color_image)

def load_calibration_data(calib_file_path):
    """加载标定数据"""
    try:
        with open(calib_file_path, "r") as f:
            data = json.load(f)
        print("✅ 标定参数加载成功")
        print(f"相机内参矩阵: {data.get('CameraMatrix', 'N/A')}")
        return data
    except FileNotFoundError:
        print(f"❌ 标定文件未找到: {calib_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return None

def init_camera(serial_number=None):
    """初始化相机"""
    try:
        # 如果指定了序列号，使用指定相机
        if serial_number:
            print(f"尝试连接相机: {serial_number}")
            cam = Camera(serial_number=serial_number)
        else:
            print("使用默认相机")
            cam = Camera()
        
        # 测试获取一帧数据验证相机是否工作
        test_color, test_depth, _ = cam.getColorDepthData()
        if len(test_color) > 0 and len(test_depth) > 0:
            print("✅ 相机初始化成功")
            return cam
        else:
            print("❌ 相机无法获取有效数据")
            return None
            
    except Exception as e:
        print(f"❌ 相机初始化失败: {e}")
        return None

def main():
    global depth_data, color_image, calib_data, camera
    
    # 1. 加载标定数据
    calib_file_path = "/media/jaka/HomeDir/project/autoCal/conf/CalibParams-lumi.json"
    calib_data = load_calibration_data(calib_file_path)
    if calib_data is None:
        print("程序退出：缺少标定数据")
        return
    
    # 2. 初始化相机
    # 可选：指定相机序列号，如 "AY8V74300NB"
    camera = init_camera(serial_number="AY8V743010L")  # 使用默认相机
    if camera is None:
        print("程序退出：相机初始化失败")
        return
    
    # 3. 创建窗口并设置鼠标回调
    window_name = "Camera View"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    cv2.setMouseCallback(window_name, on_EVENT_LBUTTONDOWN)
    
    print("\n=== 程序说明 ===")
    print("• 鼠标左键点击图像上的点，获取该点的世界坐标")
    print("• 按 'q' 或 ESC 键退出程序")
    print("=" * 50 + "\n")
    
    try:
        while True:
            # 获取彩色图和深度数据
            color_img, depth_arr, depth_viz = camera.getColorDepthData()
            
            if len(color_img) == 0 or len(depth_arr) == 0:
                print("⚠️ 获取图像失败，重试中...")
                time.sleep(0.1)
                continue
            
            # 更新全局变量供回调使用
            color_image = color_img.copy()
            depth_data = depth_arr.copy()
            
            # 显示图像
            cv2.imshow(window_name, color_image)
            
            # 按键处理
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ESC_KEY:
                print("\n用户退出程序")
                break
                
    except KeyboardInterrupt:
        print("\n程序被中断")
    finally:
        # 清理资源
        if camera:
            camera.close()
        cv2.destroyAllWindows()
        print("程序结束")

if __name__ == "__main__":
    main()