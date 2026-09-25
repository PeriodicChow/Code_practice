
import cv2
import json
from http import HTTPStatus
import numpy as np
import os
import pyaudio
import wave
from contextlib import redirect_stderr


PI=3.1415926

def loadJsonFile(jsonFile):
    with open(jsonFile,"r",encoding='utf8') as file:
        data=json.load(file)
        return data
    

def pixel_to_world(pixel_xy, depth, K, R_camera_to_world, T_camera_to_world):
    u, v = pixel_xy
    #  # Intrinsic parameters
    fx, fy = K[0][0], K[1][1]  
    cx, cy = K[0][2], K[1][2]  

    x_n = (u - cx) / fx
    y_n = (v - cy) / fy

    X_c = depth * x_n
    Y_c = depth * y_n
    Z_c = depth

    P_camera=np.array([X_c,Y_c,Z_c])
    T_camera_to_world=np.array(T_camera_to_world).reshape(3)
    P_world=np.dot(np.array(R_camera_to_world),P_camera)+T_camera_to_world
    print('Pix_to_world:' ,P_world)
    return P_world

def findCorners(img,boardWidth,boardHeight):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (boardWidth, boardHeight), None)
    return ret

def generatorNearPoints(current_pos,near_point_interval=2,nums=2):
    # currentPos = [10, 10]
    points = []
    points.append(current_pos)
    for i in range(1, nums + 1):
        left_top_x = current_pos[0] - near_point_interval * i
        left_top_y = current_pos[1] - near_point_interval * i

        right_bottom_x = current_pos[0] + near_point_interval * i
        right_bottom_y = current_pos[1] + near_point_interval * i

        for x in range(left_top_x, right_bottom_x + near_point_interval, near_point_interval):
            points.append([x, left_top_y])
            points.append([x, right_bottom_y])
        for y in range(left_top_y + near_point_interval, right_bottom_y, near_point_interval):
            points.append([left_top_x, y])
            points.append([right_bottom_x, y])

    return points

def saveOriginImg(color_image,save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 获取目录下已有的文件数量
    files = os.listdir(save_dir)
    img_name = f"{len(files) + 1}.jpg"
    # 构造保存路径
    img_path = os.path.join(save_dir, img_name)
    
    # 保存图像
    cv2.imwrite(img_path, color_image)
    return os.path.abspath(img_path)


def get_device():
    """
    根据指定的输出设备名称，返回对应的设备 ID。
    如果未找到指定设备，则返回默认设备的 ID。
    """
    with open(os.devnull, 'w') as devnull:
        with redirect_stderr(devnull):
            p = pyaudio.PyAudio()

    output_name = "USB Audio Device"

    default_output_id = p.get_default_output_device_info()['index']
    output_device_id = default_output_id

    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        device_name = device_info['name']
        if "pulse" in device_name.lower() or "default" in device_name.lower():
            continue
        if output_name and output_name.lower() in str(device_name).lower():
            output_device_id = i

    if output_name and output_device_id == default_output_id:
        print(f"未找到输出设备 '{output_name}'，返回默认输出设备 ID：{default_output_id}")

    p.terminate()
    return int(output_device_id) if output_device_id is not None else None


def play_wav(wav_path, device_id=None, volume=1.0):
    """
    播放指定路径的wav格式音频文件。
    :param wav_path: wav文件路径
    :param device_id: 输出设备ID（可选），不传则自动获取
    :param volume: 音量缩放系数，默认1.0（可大于1以增强音量，由调用方决定）
    """
    if device_id is None:
        try:
            device_id = get_device()
        except Exception as e:
            print(f"获取音频设备失败: {e}")
            device_id = None
    try:
        wf = wave.open(wav_path, 'rb')
    except Exception as e:
        print(f"无法打开音频文件: {wav_path}, 错误: {e}")
        return

    with open(os.devnull, 'w') as devnull:
        with redirect_stderr(devnull):
            p = pyaudio.PyAudio()

    try:
        with open(os.devnull, 'w') as devnull:
            with redirect_stderr(devnull):
                stream = p.open(
                    format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=device_id
                )
    except Exception as e:
        print(f"无法打开音频输出流: {e}")
        wf.close()
        p.terminate()
        return

    chunk = 8192
    data = wf.readframes(chunk)
    sample_width = wf.getsampwidth()
    dtype = None
    if sample_width == 2:
        dtype = np.int16
    elif sample_width == 1:
        dtype = np.uint8
    elif sample_width == 4:
        dtype = np.int32
    else:
        print(f"暂不支持的采样宽度: {sample_width}")
        stream.stop_stream()
        stream.close()
        wf.close()
        p.terminate()
        return

    while data:
        audio_array = np.frombuffer(data, dtype=dtype)
        if dtype == np.uint8:
            audio_array = ((audio_array.astype(np.int16) - 128) * volume + 128).clip(0, 255).astype(np.uint8)
        else:
            max_val = np.iinfo(dtype).max
            min_val = np.iinfo(dtype).min
            audio_array = (audio_array.astype(np.float32) * volume).clip(min_val, max_val).astype(dtype)
        stream.write(audio_array.tobytes())
        data = wf.readframes(chunk)

    stream.stop_stream()
    stream.close()
    wf.close()
    p.terminate()



