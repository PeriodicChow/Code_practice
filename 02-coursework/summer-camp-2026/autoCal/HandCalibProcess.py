
'''
手动标定：眼在手外
'''

from utilfs.handToEyeCalibration import *
import cv2
from OrbbecSDK.orbbecCamera import Camera
from utilfs.jaka import *
from utilfs.tools import loadJsonFile,findCorners

PI=3.1415926



mapJsonData = loadJsonFile('./conf/userCmdControl.json')

boardRowNums=mapJsonData["calibrateParams"]["boardRowNums"]
boardCowNums = mapJsonData["calibrateParams"]["boardCowNums"]
boardLength = mapJsonData["calibrateParams"]["boardLength"]
autoFilterParams = mapJsonData["calibrateParams"].get("autoSampleFilter", {})

CalibrateImageSaveDir = mapJsonData["calibrateParams"]["CalibrateImageSaveDir"]
if not os.path.exists(CalibrateImageSaveDir):
    os.makedirs(CalibrateImageSaveDir)

save_pos_path = os.path.join(CalibrateImageSaveDir, 'robotTcpPos.txt')
save_joint_path = os.path.join(CalibrateImageSaveDir, 'robotJointPos.txt')
print('------:',save_pos_path)
print('------:',save_joint_path)

tcp = JAKA(mapJsonData["calibrateParams"]["robotIP"])
oberrecCamera = Camera("AY8V743010L")

startIndex=0
robotPoses = []
robotJoints = []
calibrateImages = []
print('--------------请按下k进行数据采集-------')
while True:
    # 实时显示相机图像和角点检测结果（不保存）
    color_image = oberrecCamera.getColorImage()
    display_img = color_image.copy()
    
    # 实时检测角点
    gray = cv2.cvtColor(display_img, cv2.COLOR_BGR2GRAY)
    # Keep the same corner order used by capture/calibration to avoid confusion.
    ret_corners, corners = cv2.findChessboardCorners(gray, (boardRowNums, boardCowNums), None)
    
    if ret_corners:
        cv2.drawChessboardCorners(display_img, (boardRowNums, boardCowNums), corners, ret_corners)
        cv2.putText(display_img, "Chessboard detected - Press 'k' to capture", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv2.putText(display_img, "No chessboard - Adjust position", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow('Real-time Detection', display_img)
    c = cv2.waitKey(1)

    if c == ord('k'):
        print("开始采集数据...")
        currentTcpPos = tcp.get_tcp_pos()
        currentJointPos = tcp.get_joint_pos()

        print("currentTcpPos: ",currentTcpPos)
        print("currentJointPos: ",currentJointPos)

        color_image = oberrecCamera.getColorImage()
        print("get color_image  success.")

        if findCorners(color_image,boardRowNums,boardCowNums):
            robotPoses.append(currentTcpPos)
            robotJoints.append(currentJointPos)
            calibrateImages.append(color_image)
            cv2.imwrite(os.path.join(CalibrateImageSaveDir, "{:04d}.png".format(int(startIndex))), color_image)
            startIndex+=1
            print("本次数据采集成功")
        else:
            print("舍弃本次采集...")

    if c == ord('p'):
        print("开始标定...")
        if len(calibrateImages)==len(robotPoses):
            print("数据一致,开始标定")
            np.savetxt(save_pos_path,robotPoses, fmt='%f', delimiter=',')
            np.savetxt(save_joint_path,robotJoints, fmt='%f', delimiter=',')
            print("位姿保存成功...")
            calibrator = Calibration(boardRowNums, boardCowNums, boardLength)
            # 自动筛样参数（可选，配置不存在时使用默认值）
            calibrator.enableAutoSampleFilter = autoFilterParams.get("enable", True)
            calibrator.minSamplesAfterFilter = autoFilterParams.get("minSamplesAfterFilter", 12)
            calibrator.maxFilterIterations = autoFilterParams.get("maxFilterIterations", 8)
            calibrator.minReprojThresholdPx = autoFilterParams.get("minReprojThresholdPx", 0.2)
            calibrator.reprojMadSigma = autoFilterParams.get("reprojMadSigma", 2.8)
            print(
                "[AutoFilter] enable={}, minSamplesAfterFilter={}, maxFilterIterations={}, "
                "minReprojThresholdPx={}, reprojMadSigma={}".format(
                    calibrator.enableAutoSampleFilter,
                    calibrator.minSamplesAfterFilter,
                    calibrator.maxFilterIterations,
                    calibrator.minReprojThresholdPx,
                    calibrator.reprojMadSigma,
                )
            )
            calibrator.process(calibrateImages, robotPoses)
        else:
            print("图像和位姿数量不一致...")

    if c == ord('q'):
        break












