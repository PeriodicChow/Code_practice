# from OrbbecSDK.pyorbbecsdk import *
from pyorbbecsdk import *
import pyorbbecsdk as ob
from utils import frame_to_bgr_image

import cv2
import numpy as np
import sys
import time

ESC_KEY = 27
PRINT_INTERVAL = 1  # seconds
MIN_DEPTH = 20  # 20mm
MAX_DEPTH = 10000  # 10000mm

class TemporalFilter:
    def __init__(self, alpha):
        self.alpha = alpha
        self.previous_frame = None

    def process(self, frame):
        if self.previous_frame is None:
            result = frame
        else:
            result = cv2.addWeighted(frame, self.alpha, self.previous_frame, 1 - self.alpha, 0)
        self.previous_frame = result
        return result

class Camera():
    # print('orbbec camera-------')
    def __init__(self, serial_number=None, align_mode="HW", enable_sync=True):
        # Create a context to enumerate devices
        self.context = Context()
        self.pipeline = None
        
        # Get the list of connected devices
        device_list = self.context.query_devices()
        
        # 检测是否有连接的设备
        try:
            # 尝试获取第一个设备来检查是否有设备连接
            device_test = device_list.get_device_by_index(0)
            if not device_test:
                print("No devices connected!")
                return
        except Exception as e:
            print(f"No devices connected! Error: {e}")
            return
            
        # If no serial number specified, use the first device
        if serial_number is None:
            self.pipeline = Pipeline()
            device = self.pipeline.get_device()
            device_info = device.get_device_info()
            print(f"Using default device: {device_info.get_name()} (SN: {device_info.get_serial_number()})")
        else:
            # Find the device with the matching serial number
            device = None
            index = 0
            
            # 使用索引方法枚举设备
            try:
                while True:
                    dev = device_list.get_device_by_index(index)
                    if not dev:
                        break
                        
                    dev_info = dev.get_device_info()
                    dev_sn = dev_info.get_serial_number()
                    dev_name = dev_info.get_name()
                    
                    # 精确匹配序列号（区分大小写）
                    if dev_sn == serial_number:
                        device = dev
                        print(f"✅ Found matching camera: {dev_name} (SN: {dev_sn})")
                        break
                    
                    index += 1
            except Exception as e:
                print(f"⚠️ Device enumeration completed or error: {e}")
            
            # 尝试通过UID直接获取设备（如果序列号匹配失败）
            if device is None:
                try:
                    device = device_list.get_device_by_uid(serial_number)
                    if device:
                        dev_info = device.get_device_info()
                        print(f"✅ Found device by UID: {dev_info.get_name()} (SN: {dev_info.get_serial_number()})")
                except Exception as e:
                    print(f"⚠️ Cannot get device by UID: {e}")
            
            if device is None:
                print(f"❌ Camera with serial number '{serial_number}' not found")
                print("⚠️ Using default camera (first available device)")
                self.pipeline = Pipeline()
                device = self.pipeline.get_device()
                device_info = device.get_device_info()
                print(f"📷 Using default camera: {device_info.get_name()} (SN: {device_info.get_serial_number()})")
            else:
                # Create pipeline with the specific device
                self.pipeline = Pipeline(device)
                device_info = device.get_device_info()
        
        device_info = self.pipeline.get_device().get_device_info()
        device_pid = device_info.get_pid()
        config = Config()

        try:
            color_profiles = self.pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
            color_profile = color_profiles.get_video_stream_profile(1280, 800, OBFormat.RGB, 15)
            config.enable_stream(color_profile)

            depth_profiles = self.pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            assert depth_profiles is not None
            depth_profile = depth_profiles.get_video_stream_profile(1280, 800, OBFormat.RLE, 15)
            assert depth_profile is not None
            config.enable_stream(depth_profile)
        except Exception as e:
            print(f"Error configuring streams: {e}")
            return
        
        if align_mode == 'HW':
            if device_pid == 0x066B:
                # Femto Mega does not support hardware D2C, and it is changed to software D2C
                config.set_align_mode(OBAlignMode.SW_MODE)
            else:
                config.set_align_mode(OBAlignMode.HW_MODE)
        elif align_mode == 'SW':
            config.set_align_mode(OBAlignMode.SW_MODE)
        else:
            config.set_align_mode(OBAlignMode.DISABLE)
        
        if enable_sync:
            try:
                self.pipeline.enable_frame_sync()
            except Exception as e:
                print(f"Error enabling frame sync: {e}")
                return
        
        try:
            self.pipeline.start(config)
        except Exception as e:
            print(f"Error starting pipeline: {e}")
            return

        # 尝试获取初始帧
        max_attempts = 5
        attempt = 0
        success = False
        
        while attempt < max_attempts and not success:
            try:
                frames = self.pipeline.wait_for_frames(1000)
                if frames is None:
                    attempt += 1
                    time.sleep(0.5)
                    continue
                    
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()
                
                if color_frame is None or depth_frame is None:
                    attempt += 1
                    time.sleep(0.5)
                    continue
                
                if depth_frame.get_width() > 0 and depth_frame.get_height() > 0:
                    color_image = frame_to_bgr_image(color_frame)
                    if color_image is not None and color_image.size > 0:
                        success = True
                        print("Successfully initialized camera with valid frames")
                    else:
                        print(f"Invalid color image data, attempt {attempt+1}/{max_attempts}")
                else:
                    print(f"Invalid depth frame dimensions, attempt {attempt+1}/{max_attempts}")
                
                attempt += 1
                if not success:
                    time.sleep(0.5)
                
            except Exception as e:
                print(f"Error getting initial frames (attempt {attempt+1}/{max_attempts}): {e}")
                attempt += 1
                time.sleep(0.5)
        
        if not success:
            print("Failed to initialize camera after multiple attempts")
            self.close()

    def getColorImage(self):
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                frames: FrameSet = self.pipeline.wait_for_frames(1000)
                if frames is None:
                    attempt += 1
                    continue

                color_frame = frames.get_color_frame()
                if color_frame is None:
                    attempt += 1
                    continue

                if color_frame is not None:
                    color_image = frame_to_bgr_image(color_frame)
                    if color_image is not None and isinstance(color_image, np.ndarray):
                        return color_image
                    else:
                        attempt += 1
                        continue
            except Exception as e:
                print(f"Error in getColorImage: {e}")
                attempt += 1
        
        # 返回空数组而不是列表，保持类型一致性
        return np.array([])
                
    def getColorDepthData(self):
        """
        返回: (color_image, depth_data, depth_image)
        失败时返回 (None, None, None) 而不是空列表
        """
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                frames: FrameSet = self.pipeline.wait_for_frames(1000)
                if frames is None:
                    attempt += 1
                    continue

                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()
                if color_frame is None or depth_frame is None:
                    attempt += 1
                    continue

                # 处理彩色图像
                color_image = frame_to_bgr_image(color_frame)
                if color_image is None or not isinstance(color_image, np.ndarray):
                    attempt += 1
                    continue
                
                if color_image.size == 0:
                    attempt += 1
                    continue

                # 处理深度数据
                try:
                    if not hasattr(self, "_ob_spatial_filter"):
                        self._ob_spatial_filter = ob.SpatialFilter()
                        self._ob_temporal_filter = ob.TemporalFilter()
                        self._ob_hole_filling_filter = ob.HoleFillingFilter()

                    depth_frame_filtered = self._ob_spatial_filter.process(depth_frame)
                    depth_frame_filtered = self._ob_temporal_filter.process(depth_frame_filtered)
                    depth_frame_filtered = self._ob_hole_filling_filter.process(depth_frame_filtered)
                except Exception as e:
                    # 如果SDK滤波失败，使用原始深度帧
                    depth_frame_filtered = depth_frame

                try:
                    width = depth_frame_filtered.get_width()
                    height = depth_frame_filtered.get_height()
                    scale = depth_frame_filtered.get_depth_scale()
                except:
                    width = 1280
                    height = 800
                    scale = 1.0

                # 复制深度数据
                try:
                    depth_data_bytes = depth_frame_filtered.get_data()
                    depth_data = np.frombuffer(depth_data_bytes, dtype=np.uint16).copy()
                    depth_data = depth_data.reshape((height, width))
                    depth_data = depth_data.astype(np.float32) * scale
                except Exception as e:
                    print(f"Error processing depth data: {e}")
                    attempt += 1
                    continue

                # 时间平滑滤波
                if not hasattr(self, '_temporal_filter'):
                    self._temporal_filter = TemporalFilter(alpha=0.5)

                # 应用深度范围过滤
                depth_data = np.where((depth_data > MIN_DEPTH) & (depth_data < MAX_DEPTH), depth_data, 0)
                depth_data = depth_data.astype(np.uint16)
                depth_data = self._temporal_filter.process(depth_data)

                # 生成彩色深度图用于显示
                depth_normalized = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                depth_image = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)
                
                # 叠加彩色图像
                depth_image = cv2.addWeighted(color_image, 0.5, depth_image, 0.5, 0)

                # 成功返回 numpy 数组
                return color_image, depth_data, depth_image
                
            except Exception as e:
                print(f"Error in getColorDepthData (attempt {attempt+1}/{max_attempts}): {e}")
                attempt += 1
                if attempt >= max_attempts:
                    break
                time.sleep(0.1)
        
        # 所有尝试都失败，返回 None 而不是空列表
        return None, None, None

    def close(self):
        if self.pipeline:
            try:
                self.pipeline.stop()
                print("Camera pipeline stopped")
            except Exception as e:
                print(f"Error stopping pipeline: {e}")
            
    def list_connected_devices(self):
        """List all connected Orbbec devices and their serial numbers"""
        device_list = self.context.query_devices()
        
        devices_info = []
        device_count = 0
        
        try:
            while True:
                device = device_list.get_device_by_index(device_count)
                if device:
                    dev_info = device.get_device_info()
                    devices_info.append({
                        "index": device_count,
                        "name": dev_info.get_name(),
                        "serial_number": dev_info.get_serial_number(),
                        "pid": dev_info.get_pid(),
                        "vid": dev_info.get_vid()
                    })
                    device_count += 1
                else:
                    break
        except Exception as e:
            # 当没有更多设备时，这是正常的
            pass
        
        print(f"Found {device_count} device(s)")
        return devices_info


if __name__ == "__main__":
    import cv2
    import time

    # 可选：列出所有连接的设备
    # temp_cam = Camera()
    # devices = temp_cam.list_connected_devices()
    # for dev in devices:
    #     print(f"  [{dev['index']}] {dev['name']} - SN: {dev['serial_number']}")
    # del temp_cam
    
    # 指定相机序列号（可选）
    serial_number = None  # 或 "AY8V74300H1" 之类
    cam = Camera(serial_number=serial_number)
    
    if cam.pipeline is None:
        print("Failed to initialize camera. Exiting.")
        exit(1)
    
    print("Camera initialized. Starting capture loop...")
    print("Press 'ESC' or 'q' to exit")
    
    frame_count = 0
    success_count = 0
    
    try:
        while True:
            # 获取一帧 color/depth 数据
            color_img, depth_data, depth_image = cam.getColorDepthData()
            
            # 正确的有效性判断 - 检查是否为 None
            if color_img is None or depth_data is None:
                print(f"[Frame {frame_count}] Failed to get valid camera data, skipping")
                frame_count += 1
                continue
            
            # 进一步验证数据类型和形状
            if not isinstance(color_img, np.ndarray):
                print(f"[Frame {frame_count}] color_img is not numpy array: {type(color_img)}")
                frame_count += 1
                continue
                
            if not isinstance(depth_data, np.ndarray):
                print(f"[Frame {frame_count}] depth_data is not numpy array: {type(depth_data)}")
                frame_count += 1
                continue
            
            if color_img.size == 0 or depth_data.size == 0:
                print(f"[Frame {frame_count}] Empty array received")
                frame_count += 1
                continue
            
            success_count += 1
            
            # 打印信息
            print(f"[Frame {success_count}] Color shape: {color_img.shape}, Depth shape: {depth_data.shape}")
            
            # 显示图像
            cv2.imshow("Color Image", color_img)
            
            if depth_image is not None and isinstance(depth_image, np.ndarray):
                cv2.imshow("Depth Image", depth_image)
            
            # 按键处理
            key = cv2.waitKey(1) & 0xFF
            if key == ESC_KEY or key == ord('q'):
                print("Exit requested by user")
                break
                
            frame_count += 1
            
            # 每秒打印一次统计信息
            if frame_count % 30 == 0:
                success_rate = (success_count / frame_count) * 100 if frame_count > 0 else 0
                print(f"Stats: {success_count}/{frame_count} successful frames ({success_rate:.1f}%)")
                
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Unexpected error in main loop: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭相机
        cam.close()
        cv2.destroyAllWindows()
        print("Camera closed.")