# from OrbbecSDK.pyorbbecsdk import *
from pyorbbecsdk import *
from OrbbecSDK.orbbecUtils import frame_to_bgr_image

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
    print('orbbec camera-------')
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
            
            print(f"🔍 正在查找序列号为 '{serial_number}' 的相机...")
            
            # 使用索引方法枚举设备
            try:
                while True:
                    dev = device_list.get_device_by_index(index)
                    if not dev:
                        break
                        
                    dev_info = dev.get_device_info()
                    dev_sn = dev_info.get_serial_number()
                    dev_name = dev_info.get_name()
                    print(f"  [设备 {index}] 名称: {dev_name}, 序列号: {dev_sn}")
                    
                    # 精确匹配序列号（区分大小写）
                    if dev_sn == serial_number:
                        device = dev
                        print(f"✅ 找到匹配的相机设备: {dev_name} (SN: {dev_sn})")
                        break
                    
                    index += 1
            except Exception as e:
                print(f"⚠️ 设备枚举完成或出错: {e}")
            
            # 尝试通过UID直接获取设备（如果序列号匹配失败）
            if device is None:
                try:
                    device = device_list.get_device_by_uid(serial_number)
                    if device:
                        dev_info = device.get_device_info()
                        print(f"✅ 通过UID找到设备: {dev_info.get_name()} (SN: {dev_info.get_serial_number()})")
                except Exception as e:
                    print(f"⚠️ 无法通过UID获取设备: {e}")
            
            if device is None:
                print(f"❌ 未找到序列号为 '{serial_number}' 的相机")
                print("⚠️ 将使用默认相机（第一个可用设备）")
                self.pipeline = Pipeline()
                device = self.pipeline.get_device()
                device_info = device.get_device_info()
                print(f"📷 使用默认相机: {device_info.get_name()} (SN: {device_info.get_serial_number()})")
            else:
                # Create pipeline with the specific device
                self.pipeline = Pipeline(device)
                device_info = device.get_device_info()
                print(f"✅ 成功创建指定相机的pipeline: {device_info.get_name()} (SN: {device_info.get_serial_number()})")
        
        device_info = self.pipeline.get_device().get_device_info()
        device_pid = device_info.get_pid()
        config = Config()
        # d2C
        # align_mode = "HW" # align mode, HW=hardware mode,SW=software mode,NONE=disable align
        # enable_sync = True  # enable sync
        try:
            color_profiles = self.pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
            color_profile = color_profiles.get_video_stream_profile(640, 400, OBFormat.RGB, 15)
            # color_profile = profile_list.get_default_video_stream_profile()
            config.enable_stream(color_profile)

            depth_profiles = self.pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            assert depth_profiles is not None
            # depth_profile = depth_profiles.get_default_video_stream_profile()
            depth_profile = depth_profiles.get_video_stream_profile(640, 400, OBFormat.RLE, 15)
            assert depth_profile is not None
            print("color profile : {}x{}@{}_{}".format(color_profile.get_width(),
                                                       color_profile.get_height(),
                                                       color_profile.get_fps(),
                                                       color_profile.get_format()))
            print("depth profile : {}x{}@{}_{}".format(depth_profile.get_width(),
                                                       depth_profile.get_height(),
                                                       depth_profile.get_fps(),
                                                       depth_profile.get_format()))
            config.enable_stream(depth_profile)
        except Exception as e:
            print(f"Error configuring streams: {e}")
            return
        if align_mode == 'HW':
            print('--------align_mode: HW')
            if device_pid == 0x066B:
                # Femto Mega does not support hardware D2C, and it is changed to software D2C
                config.set_align_mode(OBAlignMode.SW_MODE)
            else:
                config.set_align_mode(OBAlignMode.HW_MODE)
        elif align_mode == 'SW':
            print('--------align_mode: SW')
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

        # 尝试获取初始帧，但加入更多的错误处理
        max_attempts = 5
        attempt = 0
        success = False
        
        while attempt < max_attempts and not success:
            try:
                frames = self.pipeline.wait_for_frames(1000)
                if frames is None:
                    print(f"Initial frames are None, attempt {attempt+1}/{max_attempts}")
                    attempt += 1
                    time.sleep(0.5)
                    continue
                    
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()
                
                if color_frame is None:
                    print(f"Initial color frame is None, attempt {attempt+1}/{max_attempts}")
                    attempt += 1
                    time.sleep(0.5)
                    continue
                    
                if depth_frame is None:
                    print(f"Initial depth frame is None, attempt {attempt+1}/{max_attempts}")
                    attempt += 1
                    time.sleep(0.5)
                    continue
                
                # 确认帧有效性
                if depth_frame.get_width() > 0 and depth_frame.get_height() > 0:
                    # 获取彩色图像数据，确认数据有效
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
            self.close()  # 确保释放资源
            return

    def getColorImage(self):
        # print('--1--')
        # 获取一帧图像
        while True:
            try:
                frames: FrameSet = self.pipeline.wait_for_frames(1000)
                if frames is None:
                    print('frame is none')
                    continue

                color_frame = frames.get_color_frame()
                if color_frame is None:
                    print('color frame is None')
                    continue

                if color_frame is not None:
                    # covert to RGB format
                    color_image = frame_to_bgr_image(color_frame)
                    return color_image
                break
            except Exception as e:
                print("e: ",e)
                return []
                
    def getColorDepthData(self):
        # 获取一帧图像（限制重试次数，避免无限循环导致资源耗尽）
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

                # 立即复制帧数据，避免帧对象被释放后访问底层数据导致段错误
                if color_frame is not None:
                    color_image = frame_to_bgr_image(color_frame)
                    if color_image is None:
                        attempt += 1
                        continue

                if depth_frame is not None:
                    try:
                        width = depth_frame.get_width()
                        height = depth_frame.get_height()
                        scale = depth_frame.get_depth_scale()
                    except:
                        width = 640
                        height = 400
                        scale = 1.0

                    # 立即复制深度数据，避免帧对象释放后访问导致段错误
                    try:
                        depth_data_bytes = depth_frame.get_data()
                        # 创建numpy数组的副本，确保数据独立
                        depth_data = np.frombuffer(depth_data_bytes, dtype=np.uint16).copy()
                        depth_data = depth_data.reshape((height, width))
                        depth_data = depth_data.astype(np.float32) * scale
                    except Exception as e:
                        print(f"Error processing depth data: {e}")
                        attempt += 1
                        continue

                    # 只在第一次初始化temporal_filter，避免每次都创建新对象
                    if not hasattr(self, '_temporal_filter'):
                        self._temporal_filter = TemporalFilter(alpha=0.5)
                    
                    depth_data = np.where((depth_data > MIN_DEPTH) & (depth_data < MAX_DEPTH), depth_data, 0)
                    depth_data = depth_data.astype(np.uint16)
                    # Apply temporal filtering
                    depth_data = self._temporal_filter.process(depth_data)

                    depth_image = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                    depth_image = cv2.applyColorMap(depth_image, cv2.COLORMAP_JET)

                    # overlay color image on depth image
                    depth_image = cv2.addWeighted(color_image, 0.5, depth_image, 0.5, 0)

                    return color_image, depth_data, depth_image
                else:
                    attempt += 1
            except Exception as e:
                print(f"Error getting color/depth data: {e}")
                attempt += 1
                if attempt >= max_attempts:
                    break
        
        # 所有尝试都失败
        return [],[],[]

    def close(self):
        if self.pipeline:
            self.pipeline.stop()
            
    def list_connected_devices(self):
        """List all connected Orbbec devices and their serial numbers"""
        device_list = self.context.query_devices()
        
        # 检测设备数量的正确方法
        devices_info = []
        device_count = 0
        
        # 尝试枚举设备，直到抛出异常
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
        except Exception as e:
            # 当没有更多设备时会抛出异常，这是正常的
            print(f"已找到 {device_count} 个设备")
        
        return devices_info


if __name__ == "__main__":
    # 可选：指定相机序列号
    serial_number = "AY8V74300NB"  # 或 "AY8V74300H1" 之类
    cam = Camera()
    print("Camera initialized.")

    # 获取一帧 color/depth 数据
    color_img, depth_data, depth_image = cam.getColorDepthData()
    max_value = np.max(depth_data)
    depth_normalized = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX)
    depth_display = depth_normalized.astype(np.uint8)
    print(max_value)
    print("getColorDepthData returned.")

    print("Color image shape:", color_img.shape)
    print("Depth data shape:", depth_data.shape)
    # 显示图像
    cv2.imshow("Color Image", color_img)
    cv2.imshow("Depth Data", depth_data)
    cv2.imshow("Depth Image", depth_image)
    # print("Press any key to exit...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    # 可选：保存图片
    # cv2.imwrite("color.jpg", color_img)
    # cv2.imwrite("depth.jpg", depth_image)

    # 关闭相机
    cam.close()
    print("Camera closed.")
