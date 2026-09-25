"""
系统配置常量定义
所有网络、设备、运动参数都在此配置
"""

# ============ 网络配置常量 ============
# AGV底盘配置
AGV_HOST = "192.168.10.10"
AGV_PORT = 31001

# 机械臂配置
ROBOT_IP = "192.168.10.90"
ROBOT_API_BASE_URL = f"http://{ROBOT_IP}:5000/api"

# 外部轴API端点
EXT_AXIS_API_URL = f"{ROBOT_API_BASE_URL}/extaxis"
EXT_ENABLE_URL = f"{EXT_AXIS_API_URL}/enable"
EXT_RESET_URL = f"{EXT_AXIS_API_URL}/reset"
EXT_MOVETO_URL = f"{EXT_AXIS_API_URL}/moveto"
EXT_STATUS_URL = f"{EXT_AXIS_API_URL}/status"
EXT_SYSINFO_URL = f"{EXT_AXIS_API_URL}/sysinfo"
