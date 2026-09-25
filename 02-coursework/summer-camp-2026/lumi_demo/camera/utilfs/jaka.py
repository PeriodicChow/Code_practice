# coding:UTF-8
'''
JAKA SDK Python API custom-made software development (CSD)
Discription:
    JAKA robot movement control library.
'''
import os
import time
import threading

try:
    from JAKA_SDK_ARM import jkrc
except:
    raise NameError("JAKA SDK path error! current work path: ", os.path.abspath('.'))

# 注意：音频播放功能已移至应用层，底层库不再直接处理音频
# 障碍检测通过回调函数通知应用层，由应用层处理音频播放

class JAKA():
    # parameters
    _ABS = 0
    _INRC = 1
    _homePose = None

    def __init__(self, address=None, connect=True, ext_base_url=None, agv_ip=None, agv_port=None, robot_ip=None, obstacle_callback=None):
        # 兼容旧参数名 address 与 新参数名 robot_ip
        if robot_ip is not None:
            address = robot_ip
        self.address = address
        self.robot = None
        # 集成控制可选参数
        self.ext_base_url = ext_base_url
        self.agv_ip = agv_ip
        self.agv_port = agv_port
        # 障碍检测回调函数（由应用层设置，用于处理障碍事件）
        self.obstacle_callback = obstacle_callback
        if self.ext_base_url:
            self.EXT_MOVETO_URL = f"{self.ext_base_url}/moveto"
            self.EXT_SYSINFO_URL = f"{self.ext_base_url}/sysinfo"
            self.EXT_RESET_URL = f"{self.ext_base_url}/reset"
            self.EXT_ENABLE_URL = f"{self.ext_base_url}/enable"
            self.EXT_GETSTATE_URL = f"{self.ext_base_url}/status"

        # 默认参数
        self.DEFAULT_EXT_VEL = 200
        self.DEFAULT_EXT_ACC = 150
        self.DEFAULT_ROB_VEL = 90

        if (connect):
            self.jaka_connect()

    def _login(self):  # 3,5
        self.jaka_connect()

    def _logout(self):  # 4,6
        self.robot_disconnect()

    def _get_sdk_version(self):  # 9
        ret = self.robot.get_sdk_version()
        # print("SDK version	is:", ret[1])
        return ret

    def _get_controller_ip(self):  # 10
        ret = self.robot.get_controller_ip()
        print("controller ip is:", ret[1])
        return ret[1]

    def _drag_mode_enable(self):  # 11
        self.robot.drag_mode_enable(True)
        ret = self.robot.is_in_drag_mode()
        return ret[0]

    def _drag_mode_unable(self):  # 12
        self.robot.drag_mode_enable(False)
        ret = self.robot.is_in_drag_mode()
        return ret[0]

    def _is_in_drag_mode(self):
        ret = self.robot.is_in_drag_mode()
        return ret[0]

    def _set_debug_mode(self):  # 14
        ret = self.robot.set_debug_mode(True)
        return ret[0]

    def _unset_debug_mode(self):  # 15
        ret = self.robot.set_debug_mode(False)
        return ret[0]

    def send_tio(self,channel,cmd):
        return self.robot.send_tio_rs_command(channel, cmd)


    def set_user_frame_origin(self,id,user_frame, name):
        # '''
        # :param id: 用户坐标系 ID，可选 ID 为 1 到 10,0 代表机器人基坐标系
        # :param user_frame:用户坐标系参数[x,y,z,rx,ry,rz]
        # :param name:用户坐标系别名
        # :return:
        # '''
        ret=self.robot.set_user_frame_data(id, user_frame, name)
        if ret[0]==0:
            return 0
        else:
            return -1

    def get_user_frame_origin(self):
        # '''
        # :return: 成功：(0, id, tcp), id : 用户坐标系 ID，可选 ID 为 1 到 10, 0 代表机器人基坐标系
        #                             tcp: 用户坐标系参数[x,y,z,rx,ry,rz]
        # '''
        ret=self.robot.get_user_frame_data()
        return ret

    def set_user_frame_id_origin(self,id):
        ret = self.robot.set_user_frame_id(id)
        if ret[0]==0:
            return 0
        else:
            return -1

    def get_user_frame_id_origin(self):
        ret = self.robot.get_user_frame_id() # 成功：(0, id)，id 值范围为 0 到 10, 0 代表机器人基坐标系
        if ret[0] == 0:
            return ret[1]
        else:
            return -1
    

    def grab_action(self,send_tio):
        if send_tio == 0:
            # open
            self.robot.set_digital_output(1, 0, 0)# IO_TOOL =1,设置 DO1 的引脚输出值为 0
            time.sleep(0.1)
            self.robot.set_digital_output(1, 1, 0)#设置 DO2 的引脚输出值为 0
            time.sleep(0.5)
            
        if send_tio == 1:
            # close
            self.robot.set_digital_output(1, 0, 1)# IO_TOOL =1,设置 DO1 的引脚输出值为 0
            time.sleep(0.1)
            self.robot.set_digital_output(1, 1, 0)#设置 DO2 的引脚输出值为 0
            time.sleep(0.5)
        return 


    #夹爪控制
    def gripper_action(self,send_tio):
        # todo 信号量设置PNP型
        # #信号量初始化，PNP型，且都预先设置为高电平
        # self.robot.set_digital_output(1, 0, 1)# IO_TOOL =1,设置 DO1 的引脚输出值为 0
        # time.sleep(0.05)
        # self.robot.set_digital_output(1, 1, 1)#设置 DO2 的引脚输出值为 0

        # if send_tio == 0:
        #     # open
        #     self.robot.set_digital_output(1, 0, 0)#DO1信号量为0，开夹爪
        #     time.sleep(0.1)
        #     self.robot.set_digital_output(1, 0, 1)#DO1信号量重置为1
        #     time.sleep(0.5)
            
        # if send_tio == 1:
        #     # close
        #     self.robot.set_digital_output(1, 1, 0)#DO2信号量为0，关夹爪
        #     time.sleep(0.1)
        #     self.robot.set_digital_output(1, 1, 1)#DO2信号量重置为1
        #     time.sleep(0.5)

        if send_tio == 0:
            # open
            print("----open-----")
            self.robot.set_digital_output(1, -1, 0)#DO1信号量为0，开夹爪
            time.sleep(0.1)
            self.robot.set_digital_output(1, -1, 1)#DO1信号量重置为1
            time.sleep(0.5)
            
        if send_tio == 1:
            # close
            print("----close-----")
            self.robot.set_digital_output(1, 0, 0)#DO2信号量为0，关夹爪
            time.sleep(0.1)
            self.robot.set_digital_output(1, 0, 1)#DO2信号量重置为1
            time.sleep(0.5)
        return 
    



    def joint_move_origin(self, joints, sp,move_mode):
        # joints = 180*joints/pi
        move_mode=move_mode if move_mode else 0
        sp=sp if sp else 30
        ret=self.robot.joint_move(joint_pos=joints, move_mode=move_mode, is_block=True, speed=sp)
        # time.sleep(0.08)
        if ret[0] == 0:
            return 0
        else:
            return -1

    def getjoints(self):
        ret = self.robot.get_joint_position()
        if ret[0] == 0:
            return ret[1]
        else:
            return None

    def tcp_pos(self, homepos):
        ret = self.robot.kine_forward(homepos)
        if ret[0] == 0:
            return ret[1]
        
    def set_analogoutput(self,iotype,index,value):
        ret = self.robot.set_analog_output(iotype,index,value)
        return ret


    # 计算指定位姿在当前工具、当前安装角度以及当前用户坐标系设置下的逆解。
    def kine_inverse_origin(self,ref_pos, cartesian_pose):
        # '''
        # :param ref_pos: 关节空间参考位置，建议选用机器人当前关节位置。
        # :param cartesian_pose: 笛卡尔空间位姿计算结果.
        # :return:(0 , joint_pos)	joint_pos 是一个包含 6 位元素的元组 (j1, j2, j3,	j4, j5, j6)，
        #                                 j1, j2, j3, j4, j5, j6 分别代表关节 1 到关节 6 的角度值
        # '''
        ret=self.robot.kine_inverse(ref_pos, cartesian_pose)
        return ret
    

    def linear_move(self, end_pos, move_mode, is_block, speed):
        ret = self.robot.linear_move(end_pos=end_pos, move_mode=move_mode, is_block=is_block, speed=speed)
        return ret


    def moveInWorldCoordinate(self, INCRPose, speedInput=20):
        curPose = self.getpos6DoF()
        tarPose = [0, 0, 0, 0, 0, 0]
        for i in range(3):
            INCRPose[i] = curPose[i] + INCRPose[i]
        ret = self.robot.linear_move(end_pos=INCRPose, move_mode=self._ABS, is_block=True, speed=speedInput)
        if (ret[0] == -4):
            print("[JAKA] Inverse solution failed")
        return ret


    # get pose
    # get [X, Y, Z] pose
    def getposXYZ(self):
        ret = self.robot.get_tcp_position()
        if ret[0] == 0:
            return ret[1][0:3]

    def get_tcp_pos(self):
        ret = self.robot.get_tcp_position()
        if ret[0] == 0:
            return ret[1]

    # get [Roll, Pitch, Yaw] pose
    def getposRPY(self):
        ret = self.robot.get_tcp_position()
        ret = self.robot.get_robot_status()
        if ret[0] == 0:
        #     return ret[1][18][3:]
        # else:
            print("positon get:", ret)
        # get [X, Y, Z, Roll, Pitch, Yaw] pose

    def getpos6DoF(self):
        ret = self.robot.get_robot_status()
        return ret[1][18]

    # download program
    def download_file(self, local, remote, opt=2):
        self.robot.init_ftp_client()
        result = self.robot.download_file(local, remote, opt)
        print('download file  from APP state is : ' + str(result))
        self.robot.close_ftp_client()

    # upload  program
    def upload_file(self, local, remote, opt=2):
        self.robot.init_ftp_client()
        result = self.robot.upload_file(local, remote, opt)
        print('upload file to APP, the state is : ' + str(result))
        self.robot.close_ftp_client()

    # run program
    def run_program(self, program):
        # program:'./sdk_exam'
        ret = self.robot.program_load(program)
        if ret[0] == 0:
            print('load program success! start running......')
        self.robot.get_loaded_program()
        ret = self.robot.program_run()
        if ret[0] == 0:
            print('running program over !!! ')

    # disconnect from the robot
    def robot_disconnect(self):
        self.robot.power_off()
        print("[JAKA] power_off successfully")
        self.robot.logout()
        print("[JAKA] logout successfully")

    def jaka_connect(self):
        self.robot = jkrc.RC(self.address)
        print("[JAKA] logining...")
        
        # 从配置文件读取SDK版本配置
        try:
            import json
            import os
            config_path = './conf/userCmdControl-supermarket.json'
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                sdk_config = config.get('sdkVersionConfig', {})
                sdk_version = sdk_config.get('sdk_version', 'V1.7')
                sdk_username = sdk_config.get('sdk_username', '')
                sdk_password = sdk_config.get('sdk_password', '')
            else:
                sdk_version = 'V1.7'
                sdk_username = ''
                sdk_password = ''
        except Exception as e:
            print(f"[JAKA] 读取SDK版本配置失败，使用默认V1.7: {e}")
            sdk_version = 'V1.7'
            sdk_username = ''
            sdk_password = ''
        
        # 根据版本调用不同的login函数
        if sdk_version == 'V1.7':
            print("[JAKA] 使用V1.7版本登录: login()")
            ret = self.robot.login()
        elif sdk_version == 'V3.2':
            print("[JAKA] 使用V3.2版本登录: login(1)")
            ret = self.robot.login(1)
        elif sdk_version == 'V3.3':
            if not sdk_username or not sdk_password:
                print("[JAKA] 警告: V3.3版本需要用户名和密码，但配置中未找到，尝试使用空字符串")
                sdk_username = sdk_username or ''
                sdk_password = sdk_password or ''
            print(f"[JAKA] 使用V3.3版本登录: login(1, \"{sdk_username}\", \"***\")")
            ret = self.robot.login(1, sdk_username, sdk_password)
        else:
            # 默认使用V1.7
            print(f"[JAKA] 未知版本 {sdk_version}，使用默认V1.7登录: login()")
            ret = self.robot.login()
        
        print("login status: "+str(ret))
        if not self.robot.power_on():
            print("[JAKA] power_on successfully")
        if not self.robot.enable_robot():
            print("[JAKA] enable_robot successfully")
        # else:
        #     print("[JAKA] enable_robot failed.")

    # ===========================
    # 集成控制扩展（外部轴 / AGV / 系统初始化）
    # ===========================

    def _load_ext_axis_limits(self):
        try:
            import json
            # 以超市配置为主
            with open('./conf/userCmdControl-supermarket.json', 'r') as f:
                config = json.load(f)
            if "extAxisLimits" in config:
                return config["extAxisLimits"]
            else:
                return {
                    "joint1": {"min": 0, "max": 400, "desc": "升降，单位mm"},
                    "joint2": {"min": -160, "max": 160, "desc": "腰部旋转，单位度"},
                    "joint3": {"min": -180, "max": 180, "desc": "头部旋转，单位度"},
                    "joint4": {"min": -5, "max": 35, "desc": "头部俯仰，单位度"}
                }
        except Exception as e:
            print(f"加载外部轴限制失败: {e}，使用默认值")
            return {
                "joint1": {"min": 0, "max": 400, "desc": "升降，单位mm"},
                "joint2": {"min": -160, "max": 160, "desc": "腰部旋转，单位度"},
                "joint3": {"min": -180, "max": 180, "desc": "头部旋转，单位度"},
                "joint4": {"min": -5, "max": 35, "desc": "头部俯仰，单位度"}
            }

    def _adjust_to_joint_limits(self, point):
        if not hasattr(self, 'ext_axis_limits') or self.ext_axis_limits is None:
            self.ext_axis_limits = self._load_ext_axis_limits()
        adjusted = False
        messages = []
        result = list(point)
        joint_names = ["joint1", "joint2", "joint3", "joint4"]
        for i, (joint_name, value) in enumerate(zip(joint_names, point)):
            if joint_name in self.ext_axis_limits:
                min_val = self.ext_axis_limits[joint_name]["min"]
                max_val = self.ext_axis_limits[joint_name]["max"]
                desc = self.ext_axis_limits[joint_name]["desc"]
                if value < min_val:
                    messages.append(f"{joint_name}({desc})超出最小限制: {value} < {min_val}")
                    result[i] = min_val
                    adjusted = True
                elif value > max_val:
                    messages.append(f"{joint_name}({desc})超出最大限制: {value} > {max_val}")
                    result[i] = max_val
                    adjusted = True
        adjustment_msg = "; ".join(messages) if messages else "无需调整"
        return result, adjusted, adjustment_msg

    # 外部轴
    def ext_check_connection(self):
        if not self.ext_base_url:
            print("外部轴URL未配置")
            return False
        try:
            import requests
            response = requests.get(self.EXT_SYSINFO_URL, timeout=2)
            if response.status_code == 200:
                print("外部轴连接正常")
                return True
            else:
                print(f"外部轴连接错误: {response.status_code}")
                return False
        except Exception as e:
            print(f"外部轴连接异常: {e}")
            return False

    def ext_reset(self):
        if not self.ext_base_url:
            print("外部轴URL未配置")
            return False
        import requests
        response = requests.post(self.EXT_RESET_URL, json={})
        return response.status_code == 200

    def ext_enable(self, enable=True):
        if not self.ext_base_url:
            print("外部轴URL未配置")
            return False
        import requests
        response = requests.post(self.EXT_ENABLE_URL, json={"enable": 1 if enable else 0})
        return response.status_code == 200

    def ext_get_state(self):
        if not self.ext_base_url:
            print("外部轴URL未配置")
            return None
        import requests, json as _json
        response = requests.get(self.EXT_GETSTATE_URL)
        if response.status_code == 200:
            return _json.loads(response.text)
        return None

    def ext_moveto(self, point, vel=None, acc=None):
        # print("----------外部轴运动------------")
        if not self.ext_base_url:
            print("外部轴URL未配置")
            return False
        import requests
        # print("----------2.7------------")
        adjusted_point, was_adjusted, adjustment_msg = self._adjust_to_joint_limits(point)
        # print("----------2.8------------")
        if was_adjusted:
            print(f"警告: {adjustment_msg}")
            print(f"原始位置: {point} -> 调整后位置: {adjusted_point}")
            point = adjusted_point
        vel = vel if vel is not None else self.DEFAULT_EXT_VEL
        acc = acc if acc is not None else self.DEFAULT_EXT_ACC
        response = requests.post(self.EXT_MOVETO_URL, json={"pos": point, "vel": vel, "acc": acc})
        # print("----------2.9-----------")
        return response.status_code == 200

    # AGV
    def _send_command_to_agv(self, command):
        if not self.agv_ip or not self.agv_port:
            print("AGV连接信息未配置")
            return None
        try:
            import socket, json as _json
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.agv_ip, self.agv_port))
                sock.sendall(command.encode('utf-8'))
                response = sock.recv(4096).decode('utf-8')
                return _json.loads(response)
        except Exception as e:
            print(f"发送AGV命令时发生错误: {e}")
            return None

    def agv_get_status(self):
        return self._send_command_to_agv("/api/robot_status")

    def agv_moveto(self, point_name):
        """
        控制AGV移动到指定标记点
        参考AGV API手册：检测到位置才返回到位信号，避免遇到障碍也认为到达目标位置
        
        :param point_name: 目标标记点名称
        :return: 成功返回True，失败返回False
        """
        response = self._send_command_to_agv(f"/api/move?marker={point_name}")
        if not response:
            print("发送AGV移动命令失败")
            return False
            
        print(f"AGV开始移动到标记点 {point_name}")
        import json as _json
        # print(_json.dumps(response, indent=4))
        
        import time as _time
        max_wait_time = 300  # 最大等待时间（秒）
        check_interval = 0.5  # 检查间隔（秒）
        start_time = _time.time()
        is_done = False
        # 重置障碍相关状态（每次新的移动任务开始时重置）
        if hasattr(self, '_waiting_for_obstacle_clear'):
            self._waiting_for_obstacle_clear = False
        
        while not is_done:
            _time.sleep(check_interval)
            
            # 检查超时
            elapsed_time = _time.time() - start_time
            if elapsed_time > max_wait_time:
                print(f"❌ AGV移动到标记点 {point_name} 超时（超过{max_wait_time}秒）")
                return False
            
            try:
                status_response = self._send_command_to_agv("/api/robot_status")
                if not status_response:
                    print(f"⚠️ 无法获取AGV状态，继续等待...")
                    continue
                
                results = status_response.get('results', {})
                move_status = results.get('move_status', '')
                
                # # 调试输出：打印完整的状态信息（用于调试障碍检测）
                # print(f"🔍 AGV状态详情（完整JSON）:")
                # print(_json.dumps(status_response, indent=2, ensure_ascii=False))
                
                # 实时检测障碍（在移动过程中检测）
                # 检查results中的collision_state字段，不为0表示有障碍
                collision_state = results.get('collision_state', 0)
                has_obstacle = (collision_state != 0)
                
                # 如果检测到障碍
                if has_obstacle:
                    # 如果还没有进入等待障碍清除的状态，则进入等待状态
                    if not hasattr(self, '_waiting_for_obstacle_clear'):
                        self._waiting_for_obstacle_clear = False
                    
                    if not self._waiting_for_obstacle_clear:
                        print(f"⚠️ AGV检测到障碍（collision_state={collision_state}），AGV已停下等待障碍清除...")
                        # 发送停止命令确保AGV停下
                        stop_command = "/api/joy_control?angular_velocity=0&linear_velocity=0&uuid=123456"
                        stop_response = self._send_command_to_agv(stop_command)
                        if stop_response:
                            print(f"✅ 已发送停止命令")
                        
                        # 触发障碍回调（播放音频）
                        if self.obstacle_callback and callable(self.obstacle_callback):
                            try:
                                obstacle_info = {
                                    'error_msg': f'检测到障碍，collision_state={collision_state}',
                                    'move_status': move_status,
                                    'point_name': point_name
                                }
                                self.obstacle_callback(obstacle_info)
                            except Exception as callback_error:
                                print(f"⚠️ 障碍回调函数执行失败: {callback_error}")
                        
                        # 标记进入等待障碍清除状态
                        self._waiting_for_obstacle_clear = True
                        # 记录开始等待的时间
                        self._obstacle_wait_start_time = _time.time()
                    else:
                        # 已经在等待状态，继续等待并定期播放音频提醒
                        elapsed_wait_time = _time.time() - self._obstacle_wait_start_time
                        # 每5秒打印一次等待信息
                        if not hasattr(self, '_last_obstacle_wait_log_time'):
                            self._last_obstacle_wait_log_time = 0
                        if (_time.time() - self._last_obstacle_wait_log_time) > 5.0:
                            print(f"⏳ AGV仍在等待障碍清除（已等待 {elapsed_wait_time:.1f} 秒）...")
                            self._last_obstacle_wait_log_time = _time.time()
                            # 每15秒重新播放一次音频提醒
                            if elapsed_wait_time > 0 and int(elapsed_wait_time) % 15 == 0:
                                if self.obstacle_callback and callable(self.obstacle_callback):
                                    try:
                                        obstacle_info = {
                                            'error_msg': f'障碍仍存在，已等待 {elapsed_wait_time:.0f} 秒',
                                            'move_status': move_status,
                                            'point_name': point_name
                                        }
                                        self.obstacle_callback(obstacle_info)
                                    except Exception as callback_error:
                                        print(f"⚠️ 障碍回调函数执行失败: {callback_error}")
                    
                    # 继续循环，等待障碍清除
                    continue
                else:
                    # 没有障碍，如果之前在等待状态，说明障碍已清除
                    if hasattr(self, '_waiting_for_obstacle_clear') and self._waiting_for_obstacle_clear:
                        print(f"✅ 障碍已清除，AGV将继续移动到目标位置 {point_name}...")
                        # 清除等待状态标记
                        self._waiting_for_obstacle_clear = False
                        # 重新发送移动命令
                        response = self._send_command_to_agv(f"/api/move?marker={point_name}")
                        if response:
                            print(f"✅ 已重新发送移动命令")
                        else:
                            print(f"❌ 重新发送移动命令失败")
                            return False
                        # 继续循环检查移动状态
                        continue
                
                # 检查移动状态
                if move_status == "succeeded":
                    # 关键改进：在验证到达之前，先检查是否有障碍信息
                    # 即使move_status是"succeeded"，如果有障碍信息，也不应该认为到达
                    # 检查collision_state字段，不为0表示有障碍
                    verify_collision_state = results.get('collision_state', 0)
                    has_obstacle_in_success = (verify_collision_state != 0)
                    
                    # 打印障碍检查信息，用于调试
                    print(f"🔍 检查succeeded状态下的障碍信息:")
                    print(f"   move_status: '{move_status}'")
                    print(f"   collision_state: {verify_collision_state}")
                    if has_obstacle_in_success:
                        print(f"   ⚠️ 检测到障碍（collision_state={verify_collision_state}）")
                    
                    # 如果succeeded状态下有障碍信息，不认为到达，进入等待障碍清除流程
                    if has_obstacle_in_success:
                        # 如果还没有进入等待障碍清除的状态，则进入等待状态
                        if not hasattr(self, '_waiting_for_obstacle_clear'):
                            self._waiting_for_obstacle_clear = False
                        
                        if not self._waiting_for_obstacle_clear:
                            print(f"⚠️ AGV移动状态为succeeded，但检测到障碍（collision_state={verify_collision_state}），AGV已停下等待障碍清除...")
                            # 发送停止命令确保AGV停下
                            stop_command = "/api/joy_control?angular_velocity=0&linear_velocity=0&uuid=123456"
                            stop_response = self._send_command_to_agv(stop_command)
                            if stop_response:
                                print(f"✅ 已发送停止命令")
                            
                            # 触发障碍回调（播放音频）
                            if self.obstacle_callback and callable(self.obstacle_callback):
                                try:
                                    self.obstacle_callback({
                                        'error_msg': f'检测到障碍，collision_state={verify_collision_state}',
                                        'move_status': move_status,
                                        'point_name': point_name
                                    })
                                except Exception as callback_error:
                                    print(f"⚠️ 障碍回调函数执行失败: {callback_error}")
                            
                            # 标记进入等待障碍清除状态
                            self._waiting_for_obstacle_clear = True
                            # 记录开始等待的时间
                            self._obstacle_wait_start_time = _time.time()
                        else:
                            # 已经在等待状态，继续等待并定期播放音频提醒
                            elapsed_wait_time = _time.time() - self._obstacle_wait_start_time
                            # 每5秒打印一次等待信息
                            if not hasattr(self, '_last_obstacle_wait_log_time'):
                                self._last_obstacle_wait_log_time = 0
                            if (_time.time() - self._last_obstacle_wait_log_time) > 5.0:
                                print(f"⏳ AGV仍在等待障碍清除（已等待 {elapsed_wait_time:.1f} 秒）...")
                                self._last_obstacle_wait_log_time = _time.time()
                                # 每15秒重新播放一次音频提醒
                                if elapsed_wait_time > 0 and int(elapsed_wait_time) % 15 == 0:
                                    if self.obstacle_callback and callable(self.obstacle_callback):
                                        try:
                                            obstacle_info = {
                                                'error_msg': f'障碍仍存在，已等待 {elapsed_wait_time:.0f} 秒',
                                                'move_status': move_status,
                                                'point_name': point_name
                                            }
                                            self.obstacle_callback(obstacle_info)
                                        except Exception as callback_error:
                                            print(f"⚠️ 障碍回调函数执行失败: {callback_error}")
                        
                        # 继续循环，等待障碍清除
                        continue
                    
                    # 关键改进：验证当前位置是否真的到达目标标记点
                    # 根据AGV API手册，robot_status可能包含当前位置信息
                    # 尝试多种可能的字段名（不同版本的API可能字段名不同）
                    current_marker = (results.get('current_marker') or 
                                     results.get('marker') or 
                                     results.get('position_marker') or
                                     results.get('current_position') or
                                     results.get('location_marker'))
                    
                    if current_marker:
                        # 如果获取到当前位置标记点，验证是否为目标标记点
                        if str(current_marker).strip() == str(point_name).strip():
                            print(f"✅ AGV已到达标记点 {point_name}（当前位置验证通过：{current_marker}）")
                            is_done = True
                        else:
                            # 当前位置不是目标标记点，继续等待
                            print(f"⏳ AGV移动状态为succeeded，但当前位置为 '{current_marker}'，目标为 '{point_name}'，继续等待...")
                            # 继续循环，等待真正到达目标位置
                    else:
                        # 如果无法获取当前位置信息，采用保守策略：
                        # 等待一段时间确保稳定，然后验证move_status仍然为succeeded且无障碍信息
                        print(f"⚠️ 无法获取当前位置标记点，等待3秒后验证移动状态...")
                        _time.sleep(0.2)
                        
                        # 再次检查状态，确保move_status仍然为succeeded且无障碍
                        verify_response = self._send_command_to_agv("/api/robot_status")
                        if verify_response:
                            verify_results = verify_response.get('results', {})
                            verify_move_status = verify_results.get('move_status', '')
                            # 检查collision_state字段，不为0表示有障碍
                            verify_collision_state_2 = verify_results.get('collision_state', 0)
                            has_obstacle = (verify_collision_state_2 != 0)
                            
                            if verify_move_status == "succeeded" and not has_obstacle:
                                # 如果仍然为succeeded且无障碍，认为到达
                                print(f"✅ AGV已到达标记点 {point_name}（移动状态验证通过，无障碍信息）")
                                is_done = True
                            elif has_obstacle:
                                # 有障碍信息，不认为到达
                                print(f"⚠️ AGV移动状态为succeeded，但检测到障碍（collision_state={verify_collision_state_2}），继续等待...")
                                # 如果还没有进入等待障碍清除的状态，则进入等待状态
                                if not hasattr(self, '_waiting_for_obstacle_clear'):
                                    self._waiting_for_obstacle_clear = False
                                
                                if not self._waiting_for_obstacle_clear:
                                    # 发送停止命令确保AGV停下
                                    stop_command = "/api/joy_control?angular_velocity=0&linear_velocity=0&uuid=123456"
                                    stop_response = self._send_command_to_agv(stop_command)
                                    if stop_response:
                                        print(f"✅ 已发送停止命令")
                                    
                                    # 触发障碍回调（播放音频）
                                    if self.obstacle_callback and callable(self.obstacle_callback):
                                        try:
                                            self.obstacle_callback({
                                                'error_msg': f'检测到障碍，collision_state={verify_collision_state_2}',
                                                'move_status': verify_move_status,
                                                'point_name': point_name
                                            })
                                        except Exception as callback_error:
                                            print(f"⚠️ 障碍回调函数执行失败: {callback_error}")
                                    
                                    # 标记进入等待障碍清除状态
                                    self._waiting_for_obstacle_clear = True
                                    # 记录开始等待的时间
                                    self._obstacle_wait_start_time = _time.time()
                                
                                # 继续等待，不返回失败
                                continue
                            else:
                                print(f"⚠️ AGV移动状态变化: {verify_move_status}，继续等待...")
                        else:
                            print(f"⚠️ 无法获取验证状态，继续等待...")
                elif move_status == "failed" or move_status == "error":
                    error_msg = results.get('error_message', '未知错误')
                    print(f"❌ AGV移动到标记点 {point_name} 失败: {error_msg}")
                    
                    # 检查是否可能是障碍（人）导致的失败
                    obstacle_keywords = ['obstacle', '障碍', 'blocked', 'block', '碰撞', 'collision', '人', 'person', 'human']
                    is_obstacle = any(keyword.lower() in error_msg.lower() for keyword in obstacle_keywords)
                    if is_obstacle:
                        # 通过回调函数通知应用层
                        if self.obstacle_callback and callable(self.obstacle_callback):
                            try:
                                self.obstacle_callback({
                                    'error_msg': error_msg,
                                    'move_status': move_status,
                                    'point_name': point_name
                                })
                            except Exception as callback_error:
                                print(f"⚠️ 障碍回调函数执行失败: {callback_error}")
                    
                    return False
                # 如果move_status为其他状态（如"moving"），继续等待
                
            except Exception as e:
                print(f"⚠️ 检查AGV状态时发生错误: {e}，继续等待...")
                # 不立即返回False，继续尝试
        
        return True

    # 系统初始化/关闭与站点移动
    def setup_system(self):
        self.jaka_connect()
        robot_ok = True
        ext_ok = True
        if self.ext_base_url:
            ext_ok = self.ext_check_connection()
            if ext_ok:
                self.ext_reset()
                self.ext_enable(True)
        return robot_ok and ext_ok

    def shutdown_system(self):
        if self.robot:
            self.robot_disconnect()
        if self.ext_base_url:
            self.ext_enable(False)
        print("系统已关闭")

    def move_to_station(self, station_name, agv_marker):
        print(f"开始移动到工作站: {station_name}")
        if self.agv_ip and self.agv_port:
            agv_result = self.agv_moveto(agv_marker)
            if not agv_result:
                print(f"AGV移动到工作站 {station_name} 失败")
                return False
        print(f"已到达工作站: {station_name}")
        return True

    def agv_backward(self, backward_speed=-0.3, backward_duration=2):
        """
        AGV后退功能
        :param backward_speed: 后退速度（负值表示后退）
        :param backward_duration: 后退持续时间（秒）
        :return: 成功返回True，失败返回False
        """
        if not self.agv_ip or not self.agv_port:
            print("AGV连接信息未配置")
            return False
            
        try:
            print(f"开始执行AGV后退操作，目标: {self.agv_ip}:{self.agv_port}")
            
            # 构建后退命令（负的线速度表示后退）
            back_command = f"/api/joy_control?angular_velocity=0&linear_velocity={backward_speed}&uuid=123456"
            
            # 发送后退命令
            response = self._send_command_to_agv(back_command)
            if response:
                print(f"AGV后退命令响应: {response}")
            else:
                print("AGV后退命令发送失败")
                return False
            
            # 后退持续指定时间
            print(f"AGV后退中，持续 {backward_duration} 秒...")
            import time as _time
            _time.sleep(backward_duration)
            
            # 发送停止命令
            stop_command = "/api/joy_control?angular_velocity=0&linear_velocity=0&uuid=123456"
            response = self._send_command_to_agv(stop_command)
            if response:
                print(f"AGV停止命令响应: {response}")
            else:
                print("AGV停止命令发送失败")
                return False
            
            print("✅ AGV后退操作完成")
            return True
            
        except Exception as e:
            print(f"❌ AGV后退操作失败: {e}")
            return False

    def agv_get_battery_status(self):
        """
        获取AGV电池状态
        使用正确的API: /api/get_power_status
        :return: 电池信息字典 {"battery_percentage": float, "is_charging": bool, "battery_voltage": float, "battery_current": float} 或 None
        """
        if not self.agv_ip or not self.agv_port:
            print("AGV连接信息未配置")
            return None
            
        try:
            # 使用正确的API接口
            response = self._send_command_to_agv("/api/get_power_status")
            if not response:
                print("获取AGV电源状态失败")
                return None
            
            # 检查响应状态
            if response.get('status') != 'OK':
                error_msg = response.get('error_message', '未知错误')
                print(f"❌ AGV返回错误: {error_msg}")
                return None
            
            # # 打印原始响应用于调试
            # print(f"🔍 AGV原始响应: {response}")
            
            # # 从results中提取电池信息（使用正确的字段名）
            results = response.get('results', {})
            
            # # 打印results内容用于调试
            # print(f"🔍 results内容: {results}")
            
            # 根据API文档使用正确的字段名
            battery_capacity = results.get('battery_capacity', 0)  # 电量百分比
            charger_connected = results.get('charger_connected_notice', False)  # 是否充电中
            battery_voltage = results.get('battery_voltage', 0)  # 电池电压
            battery_current = results.get('battery_current', 0)  # 电池电流
            charge_voltage = results.get('charge_voltage', 0)  # 充电电压
            head_current = results.get('head_current', 0)  # 上位机耗电电流
            
            battery_info = {
                "battery_percentage": battery_capacity,
                "is_charging": charger_connected,
                "battery_voltage": battery_voltage,
                "battery_current": battery_current,
                "charge_voltage": charge_voltage,
                "head_current": head_current
            }
            
            # print(f"🔋 解析后的电池信息: 电量={battery_capacity}%, 充电中={charger_connected}, 电压={battery_voltage}V, 电流={battery_current}A")
            
            return battery_info
            
        except Exception as e:
            print(f"❌ 获取AGV电池状态失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def agv_go_charging(self, charging_marker="charging_station"):
        """
        控制AGV前往充电站充电
        :param charging_marker: 充电站标记点名称
        :return: 成功返回True，失败返回False
        """
        if not self.agv_ip or not self.agv_port:
            print("AGV连接信息未配置")
            return False
            
        try:
            # print(f"🔋 开始引导AGV前往充电站: {charging_marker}")
            
            # 使用AGV导航API前往充电站
            result = self.agv_moveto(charging_marker)
            
            if result:
                # print(f"✅ AGV已到达充电站: {charging_marker}")
                # 等待一段时间确保充电连接
                import time as _time
                _time.sleep(2)
                
                # 检查是否正在充电
                battery_status = self.agv_get_battery_status()
                if battery_status and battery_status.get('is_charging'):
                    print(f"✅ AGV充电已开始，当前电量: {battery_status.get('battery_percentage')}%")
                else:
                    print(f"⚠️ AGV已到达充电站，但充电状态未确认，当前电量: {battery_status.get('battery_percentage', 'unknown')}%")
                
                return True
            else:
                print(f"❌ AGV前往充电站失败")
                return False
                
        except Exception as e:
            print(f"❌ AGV充电过程异常: {e}")
            return False

    def agv_check_battery_and_charge(self, low_battery_threshold=30, charging_marker="charging_station"):
        """
        检查电池电量，如果低于阈值则自动充电
        :param low_battery_threshold: 低电量阈值（百分比）
        :param charging_marker: 充电站标记点名称
        :return: (need_charge, success) 元组
        """
        try:
            battery_status = self.agv_get_battery_status()
            
            if not battery_status:
                print("⚠️ 无法获取电池状态")
                return (False, False)
            
            battery_percentage = battery_status.get('battery_percentage', 100)
            is_charging = battery_status.get('is_charging', False)
            
            # print(f"🔋 当前电量: {battery_percentage}%, 充电状态: {'充电中' if is_charging else '未充电'}")
            
            # 如果已经在充电，无需处理
            if is_charging:
                print("✅ AGV正在充电中")
                return (False, True)
            
            # 如果电量低于阈值，前往充电
            if battery_percentage < low_battery_threshold:
                print(f"⚠️ 电量不足（{battery_percentage}% < {low_battery_threshold}%），开始前往充电站...")
                result = self.agv_go_charging(charging_marker)
                return (True, result)
            else:
                print(f"✅ 电量充足（{battery_percentage}% >= {low_battery_threshold}%）")
                return (False, True)
                
        except Exception as e:
            print(f"❌ 电池检查与充电失败: {e}")
            return (False, False)

    # 关节移动（输入弧度）
    def rob_moveto(self, jpos_rad, vel=None):
        """接收弧度输入，直接调用 joint_move_origin。"""
        vel = vel if vel is not None else self.DEFAULT_ROB_VEL
        print(f"输入的关节角度(弧度): {jpos_rad}")
        print(f"开始执行关节运动, 速度: {vel}, 模式: 绝对运动(0)")
        ret = self.joint_move_origin(jpos_rad, vel, 0)
        print(f"关节运动结果: {ret}")
        return ret



