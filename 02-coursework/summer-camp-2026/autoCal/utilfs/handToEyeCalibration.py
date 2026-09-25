import json
import os
import random
import cv2
from math import *
import numpy as np
import matplotlib.pyplot as plt

class Calibration:
    def __init__(self,boardWidth,boardHeight,squareSize,ShowCorners=False):

        self.boardWidth=boardWidth  
        self.boardHeight=boardHeight  
        self.squareSize=squareSize
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        self.ShowCorners=ShowCorners
        # Auto filtering parameters for low-quality calibration samples.
        self.enableAutoSampleFilter = True
        self.minSamplesAfterFilter = 12
        self.maxFilterIterations = 8
        self.minReprojThresholdPx = 0.2
        self.reprojMadSigma = 2.8
        self.lastKeptSampleIndices = []
        self.lastPerViewErrors = []

    def calibCamera(self,images,boardWidth,boardHeight,squareSize,criteria,ShowCorners=False):
        objp = np.zeros((boardWidth * boardHeight, 3), np.float32)
        objp[:, :2] = np.mgrid[0:boardWidth, 0:boardHeight].T.reshape(-1, 2)
        objp = objp * squareSize  # 18.1 mm

        objectPoints = []  
        imagePoints = []  

        if isinstance(images, str):
            imgPaht=images
            images=[]
            imgs = [os.path.join(imgPaht, tmp) for tmp in sorted(os.listdir(imgPaht))]
            print(imgs)
            for fname in imgs:
                img = cv2.imread(fname)
                images.append(img)
        else:
            images=images

        print("Finding corners...")

        grayshape=list()
        detectedImageIndices = []

        for i,img in enumerate(images):
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            grayshape = gray.shape[::-1]
            ret, corners = cv2.findChessboardCorners(gray, (boardWidth, boardHeight), None)
            if ret == True:
                cv2.cornerSubPix(gray, corners, (3, 3), (-1, -1), criteria)
                objectPoints.append(objp)
                imagePoints.append(corners)
                detectedImageIndices.append(i)
                if ShowCorners:
                    print("img: ",i)
                    cv2.drawChessboardCorners(img, (boardWidth, boardHeight), corners, ret)
                    cv2.namedWindow('findCorners', cv2.WINDOW_NORMAL)
                    cv2.resizeWindow('findCorners', 1280, 640)
                    cv2.imshow('findCorners', img)
                    cv2.waitKey(1000)
                    cv2.destroyAllWindows()
                # make folder   
                if not os.path.exists("../DetectedCorners-k1"):
                    os.makedirs("../DetectedCorners-k1")

                cv2.imwrite("DetectedCorners-k1/DetectedCorners" + str(i) + ".png", img)

        if len(objectPoints) < 6:
            raise ValueError(
                f"Not enough valid chessboard samples for calibration: {len(objectPoints)} (need >= 6)."
            )

        objectPoints, imagePoints, detectedImageIndices, ret, mtx, dist, rvecs, tvecs = self._filter_and_calibrate(
            objectPoints, imagePoints, grayshape, detectedImageIndices
        )
        print("ret:", ret)  
        # print("mtx:\n", mtx)  
        # print("dist:\n", dist) 
        # print("rvecs:\n", rvecs) 
        # print("tvecs:\n", tvecs)  

        self.lastKeptSampleIndices = detectedImageIndices
        self.lastPerViewErrors = self._compute_per_view_reprojection_errors(
            objectPoints, imagePoints, rvecs, tvecs, mtx, dist
        ).tolist()

        print("The projection error from the calibration is: ",
              self.calculate_reprojection_error(objectPoints, imagePoints, rvecs, tvecs, mtx, dist, False))

        return objectPoints,imagePoints,mtx, dist

    def _compute_per_view_reprojection_errors(self, objpoints, imgpoints, rvecs, tvecs, mtx, dist):
        errors = []
        for i in range(len(objpoints)):
            imgpoints_projected, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
            imgpoints_projected = imgpoints_projected.reshape(-1, 1, 2)
            point_count = len(imgpoints_projected)
            l2_error = cv2.norm(imgpoints[i], imgpoints_projected, cv2.NORM_L2)
            per_image_rmse = l2_error / np.sqrt(max(point_count, 1))
            errors.append(per_image_rmse)
        return np.array(errors, dtype=np.float64)

    def _robust_upper_bound(self, values, minBound=0.2, sigma=2.8):
        values = np.asarray(values, dtype=np.float64)
        if values.size == 0:
            return minBound
        med = float(np.median(values))
        mad = float(np.median(np.abs(values - med)))
        robustStd = 1.4826 * mad
        if robustStd < 1e-9:
            return max(minBound, med * 1.5)
        return max(minBound, med + sigma * robustStd)

    def _filter_and_calibrate(self, objectPoints, imagePoints, grayshape, detectedImageIndices):
        keepLocalIdx = list(range(len(objectPoints)))
        minSamples = max(6, min(self.minSamplesAfterFilter, len(keepLocalIdx)))
        iteration = 0

        while True:
            currentObjectPoints = [objectPoints[i] for i in keepLocalIdx]
            currentImagePoints = [imagePoints[i] for i in keepLocalIdx]
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
                currentObjectPoints, currentImagePoints, grayshape, None, None
            )
            perViewErrors = self._compute_per_view_reprojection_errors(
                currentObjectPoints, currentImagePoints, rvecs, tvecs, mtx, dist
            )
            threshold = self._robust_upper_bound(
                perViewErrors, self.minReprojThresholdPx, self.reprojMadSigma
            )

            if not self.enableAutoSampleFilter:
                break
            if iteration >= self.maxFilterIterations:
                print(f"[AutoFilter] Stop: reached max iterations ({self.maxFilterIterations}).")
                break
            if len(keepLocalIdx) <= minSamples:
                print(f"[AutoFilter] Stop: reached min sample count ({minSamples}).")
                break

            worstLocal = int(np.argmax(perViewErrors))
            worstError = float(perViewErrors[worstLocal])
            if worstError <= threshold:
                break

            dropLocal = keepLocalIdx.pop(worstLocal)
            print(
                f"[AutoFilter] Drop sample index={detectedImageIndices[dropLocal]}, "
                f"reproj={worstError:.4f}px, threshold={threshold:.4f}px"
            )
            iteration += 1

        finalObjectPoints = [objectPoints[i] for i in keepLocalIdx]
        finalImagePoints = [imagePoints[i] for i in keepLocalIdx]
        finalDetectedIndices = [detectedImageIndices[i] for i in keepLocalIdx]
        print(
            f"[AutoFilter] Keep {len(finalObjectPoints)}/{len(objectPoints)} samples "
            f"after filtering."
        )
        return finalObjectPoints, finalImagePoints, finalDetectedIndices, ret, mtx, dist, rvecs, tvecs

    def get_RT_from_chessboard(self,imagePoints,objectPoints,mtx,dist,Testing=False):

        R_target2camera_list = []
        T_target2camera_list = []

        for i,corners in enumerate(imagePoints):
            _, rvec, tvec = cv2.solvePnP(objectPoints[i], corners, mtx, distCoeffs=dist)
            if Testing == True:
                print("Current iteration: ", i, " out of ", len(imagePoints[0]), " iterations.")
            Matrix_target2camera = np.column_stack(((cv2.Rodrigues(rvec))[0], tvec))
            Matrix_target2camera = np.row_stack((Matrix_target2camera, np.array([0, 0, 0, 1])))
            R_target2camera = Matrix_target2camera[:3, :3]
            T_target2camera = Matrix_target2camera[:3, 3].reshape((3, 1))
            R_target2camera_list.append(R_target2camera)
            T_target2camera_list.append(T_target2camera)

        return R_target2camera_list, T_target2camera_list


    def calculate_reprojection_error(self, objpoints, imgpoints, rvecs, tvecs, mtx, dist, ShowPlot=False):
        """Calculates the reprojection error of the camera for each image. The output is the mean reprojection error
        If ShowPlot is True, it will show the reprojection error for each image in a bar graph"""
        total_squared_error = 0.0
        total_points = 0
        errors = []
        for i in range(len(objpoints)):
            imgpoints_projected, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
            imgpoints_projected = imgpoints_projected.reshape(-1, 1, 2)
            point_count = len(imgpoints_projected)
            l2_error = cv2.norm(imgpoints[i], imgpoints_projected, cv2.NORM_L2)
            # RMSE in pixel for each image.
            per_image_rmse = l2_error / np.sqrt(point_count)
            errors.append(per_image_rmse)
            total_squared_error += l2_error ** 2
            total_points += point_count

        mean_error = np.sqrt(total_squared_error / max(total_points, 1))

        if ShowPlot:
            # Plotting the bar graph
            fig, ax = plt.subplots()
            img_indices = range(1, len(errors) + 1)
            ax.bar(img_indices, errors)
            ax.set_xlabel('Image Index')
            ax.set_ylabel('Reprojection Error')
            ax.set_title('Reprojection Error for Each Image')
            plt.show()
            print(errors)

            # Save the bar plot as a .png
            fig.savefig('ReprojectionError.png')

        return mean_error

    def attitudeVectorToMatrix(self,worldTcpPos, useQuaternion=False, seq=""):
        '''
        :param worldTcpPos: [x, y, z, rx, ry, rz]
        :param use_quaternion:
        :param seq:
        :return:
        '''
        assert worldTcpPos.size in [6, 10], "Input matrix must have 6 or 10 elements."
        Matrix_gripper2base = np.eye(4, dtype=np.float64)
        if useQuaternion:
            quaternion_vec = worldTcpPos[3:7].flatten()
            R_gripper2base = self.quaternionToRotatedMatrix(quaternion_vec)
            Matrix_gripper2base[:3, :3] = R_gripper2base
        else:
            if worldTcpPos.size == 6:
                rot_vec = worldTcpPos[3:].flatten()
            else:
                rot_vec = worldTcpPos[7:].flatten()
            if seq == "":
                Matrix_gripper2base[:3, :3]=cv2.Rodrigues(rot_vec)
            else:
                R_gripper2base = self.eulerAngleToRotatedMatrix(rot_vec, seq)
                Matrix_gripper2base[:3, :3] = R_gripper2base

        Matrix_gripper2base[:3, 3] = worldTcpPos[:3].flatten()
        return Matrix_gripper2base
    def quaternionToRotatedMatrix(self,q):
        w, x, y, z = q
        x2 = x * x
        y2 = y * y
        z2 = z * z
        xy = x * y
        xz = x * z
        yz = y * z
        wx = w * x
        wy = w * y
        wz = w * z

        res = np.array([
            [1 - 2 * (y2 + z2), 2 * (xy - wz), 2 * (xz + wy)],
            [2 * (xy + wz), 1 - 2 * (x2 + z2), 2 * (yz - wx)],
            [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (x2 + y2)]
        ])

        return res

    def eulerAngleToRotatedMatrix(self,euler_angle, seq):
        rx, ry, rz=euler_angle
        rot_x = np.array([[1, 0, 0],
                          [0, np.cos(rx), -np.sin(rx)],
                          [0, np.sin(rx), np.cos(rx)]])
        rot_y = np.array([[np.cos(ry), 0, np.sin(ry)],
                          [0, 1, 0],
                          [-np.sin(ry), 0, np.cos(ry)]])
        rot_z = np.array([[np.cos(rz), -np.sin(rz), 0],
                          [np.sin(rz), np.cos(rz), 0],
                          [0, 0, 1]])

        # Combine rotations based on sequence
        if seq == "zyx":
            rot_mat = np.dot(rot_x, np.dot(rot_y, rot_z))
        elif seq == "yzx":
            rot_mat = np.dot(rot_x, np.dot(rot_z, rot_y))
        elif seq == "zxy":
            rot_mat = np.dot(rot_y, np.dot(rot_x, rot_z))
        elif seq == "xzy":
            rot_mat = np.dot(rot_y, np.dot(rot_z, rot_x))
        elif seq == "yxz":
            rot_mat = np.dot(rot_z, np.dot(rot_x, rot_y))
        elif seq == "xyz":
            rot_mat = np.dot(rot_z, np.dot(rot_y, rot_x))
        else:
            raise ValueError("Euler angle sequence string is wrong.")
        return rot_mat

    # process  calibrator.process(calibrateImages, robotPoses)
    def process(self, imgs, worldPoses,isEyeToHand=True):
        if isinstance(imgs, str):
            images=[]
            imgs = [os.path.join(imgs, tmp) for tmp in sorted(os.listdir(imgs))]
            print(imgs)
            for fname in imgs:
                img = cv2.imread(fname)
                images.append(img)
        else:
            images=imgs

        if isinstance(worldPoses, str):
            # worldPoses = np.loadtxt('../data1/robotTcpPos.txt', delimiter=',')
            worldPoses = np.loadtxt(worldPoses, delimiter=',') 

        worldPoses = np.asarray(worldPoses, dtype=np.float64)
        if worldPoses.ndim == 1:
            worldPoses = worldPoses.reshape(1, -1)

        objectPoints, imagePoints, mtx, dist = self.calibCamera(images, self.boardWidth,
                                                                                    self.boardHeight, self.squareSize,
                                                                                    self.criteria, self.ShowCorners)

        keptIndices = list(getattr(self, "lastKeptSampleIndices", []))
        if keptIndices:
            if max(keptIndices) < len(worldPoses):
                worldPoses = worldPoses[keptIndices]
            else:
                print(
                    "[AutoFilter] Warn: world pose count is smaller than kept image index. "
                    "Will fallback to truncation alignment."
                )

        if len(worldPoses) != len(imagePoints):
            pairCount = min(len(worldPoses), len(imagePoints))
            print(
                f"[AutoFilter] Warn: sample mismatch pose={len(worldPoses)}, image={len(imagePoints)}; "
                f"use first {pairCount} pairs."
            )
            worldPoses = worldPoses[:pairCount]
            objectPoints = objectPoints[:pairCount]
            imagePoints = imagePoints[:pairCount]

        if len(worldPoses) < 6:
            raise ValueError(
                f"Not enough paired samples for hand-eye calibration: {len(worldPoses)} (need >= 6)."
            )

        R_target2camera_list, T_target2camera_list = self.get_RT_from_chessboard(imagePoints,objectPoints, mtx,dist, Testing=False)

        R_gripper2base_list = []
        T_gripper2base_list = []
        for worldPos in worldPoses:
            Matrix_gripper2base = self.attitudeVectorToMatrix(np.array(worldPos), False, "xyz") # R_gripper2base, T_gripper2base
  
            if isEyeToHand:
                Matrix_gripper2base=np.linalg.inv(Matrix_gripper2base)
            R_gripper2base=Matrix_gripper2base[:3, :3]
            T_gripper2base=Matrix_gripper2base[:3,3].reshape((3, 1))

            R_gripper2base_list.append(R_gripper2base)
            T_gripper2base_list.append(T_gripper2base)

        print("T_gripper2base_list: ",np.array(T_gripper2base_list).shape)
        print("T_target2camera_list: ", np.array(T_target2camera_list).shape)

        R_camera2base, T_camera2base = cv2.calibrateHandEye(R_gripper2base_list, T_gripper2base_list,
                                                            R_target2camera_list, T_target2camera_list)

        RT_camera2base = np.column_stack((R_camera2base, T_camera2base))
        RT_camera2base = np.row_stack((RT_camera2base, np.array([0, 0, 0, 1])))  

        print(RT_camera2base)

        self.SaveCalibResult(mtx, dist, R_camera2base, T_camera2base) # save params to json

        self.CalculateExtrinsicEyeToHandRms(worldPoses,RT_camera2base,R_target2camera_list,T_target2camera_list)

        return RT_camera2base,R_camera2base, T_camera2base, R_gripper2base_list, T_gripper2base_list, R_target2camera_list, T_target2camera_list

    def rotation_matrix_to_eulerAngles(self,R):
        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        singular = sy < 1e-6

        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0

        return np.array([x, y, z])

    def homogeneous_matrix_to_pose(self,world_pos):
        """Convert a homogeneous transformation matrix to a RobotPose-like dictionary."""
        # Extract translation (T)
        T = world_pos[:3, 3]
        # Extract rotation matrix (R)
        R = world_pos[:3, :3]  # Assuming a typo in the original code, should be full 3x3 or clarify intent
        # Convert rotation matrix to Euler angles
        euler_angles_degrees=self.rotation_matrix_to_eulerAngles(R)
        # Pack into a dictionary similar to RobotPose
        ret_pose = {
            'X': round(T[0],3),
            'Y': round(T[1],3),
            'Z': round(T[2],3),
            'Rx': round(euler_angles_degrees[0],3),
            'Ry': round(euler_angles_degrees[1],3),
            'Rz': round(euler_angles_degrees[2],3),
        }
        return ret_pose

    def CalculateExtrinsicEyeToHandRms(self,worldPoses,RT_camera2base,R_target2camera_list,T_target2camera_list):
        # Build base<-target for every sample: base<-camera * camera<-target
        RT_target2camera = []
        base_target_list = []
        for i in range(len(R_target2camera_list)):
            tmp = np.column_stack((R_target2camera_list[i], T_target2camera_list[i]))
            tmp = np.row_stack((tmp, np.array([0, 0, 0, 1])))
            RT_target2camera.append(tmp)
            base_target = np.dot(RT_camera2base, tmp)
            base_target_list.append(base_target)
            pose = self.homogeneous_matrix_to_pose(base_target)
            print(f"{i + 1}: {pose['X']}, {pose['Y']}, {pose['Z']}")

        pair_count = min(len(base_target_list), len(worldPoses))
        if pair_count == 0:
            print("CalibrationTool|Eye To Hand Consistency RMS: invalid sample count.")
            return

        if len(base_target_list) != len(worldPoses):
            print(
                "CalibrationTool|Warn: sample mismatch, "
                f"target={len(base_target_list)}, robot={len(worldPoses)}; use first {pair_count} pairs."
            )

        base_gripper_list = []
        for world_pos in worldPoses[:pair_count]:
            # Robot API pose is treated as base<-gripper in xyz-euler(rad), consistent with process().
            base_gripper_list.append(
                self.attitudeVectorToMatrix(np.array(world_pos, dtype=np.float64), False, "xyz")
            )

        # For eye-to-hand with board mounted on gripper, gripper<-target should be constant.
        gripper_target_list = []
        for i in range(pair_count):
            gripper_target = np.linalg.inv(base_gripper_list[i]) @ base_target_list[i]
            gripper_target_list.append(gripper_target)

        offsets = np.array([tmp[:3, 3] for tmp in gripper_target_list])
        offset_mean = np.mean(offsets, axis=0)
        offset_residual = np.linalg.norm(offsets - offset_mean, axis=1)
        extrinsic_rms = np.sqrt(np.mean(np.square(offset_residual)))

        print(
            "CalibrationTool|Eye To Hand Consistency RMS(mm): "
            f"{extrinsic_rms:.3f}"
        )
        print(
            "CalibrationTool|Estimated gripper->target offset mean(mm): "
            f"{offset_mean.round(3).tolist()}"
        )

        # Debug metric: distance between predicted target and TCP position.
        # This is NOT calibration RMS unless target frame is exactly TCP frame.
        tcp_distances = []
        for i in range(pair_count):
            tcp_xyz = base_gripper_list[i][:3, 3]
            target_xyz = base_target_list[i][:3, 3]
            tcp_distances.append(np.linalg.norm(target_xyz - tcp_xyz))
        tcp_distance_rms = np.sqrt(np.mean(np.square(tcp_distances)))
        print(
            "CalibrationTool|Target-vs-TCP distance RMS(mm, debug only): "
            f"{tcp_distance_rms:.3f}"
        )

    def check_result(self, R_cg, T_cg, R_gb, T_gb, R_tc, T_tc):
        for i in range(len(R_gb)):
            RT_gripper2base = np.column_stack((R_gb[i], T_gb[i]))
            RT_gripper2base = np.row_stack((RT_gripper2base, np.array([0, 0, 0, 1])))
            print("RT_gripper2base: ",RT_gripper2base)

            RT_camera2gripper = np.column_stack((R_cg, T_cg))
            RT_camera2gripper = np.row_stack((RT_camera2gripper, np.array([0, 0, 0, 1])))
            print("RT_camera_to_gripper: ",RT_camera2gripper)

            RT_target2camera = np.column_stack((R_tc[i], T_tc[i]))
            RT_target2camera = np.row_stack((RT_target2camera, np.array([0, 0, 0, 1])))
            print("RT_target_to_camera: ",RT_target2camera)

            RT_target2base = RT_gripper2base @ RT_camera2gripper @ RT_target2camera
            RT_target2base = np.linalg.inv(RT_target2base)

            print(RT_target2base)
            print('')

    def SaveCalibResult(self,mtx,dist,R_camera2base, T_camera2base):
        print("CameraMatrix:",mtx)
        print("CameraDistCoeffs: ",dist)
        print("RotationMat: ",R_camera2base)
        print("TranslationMat: ",T_camera2base)


        calibrateCameraResult=dict()
        calibrateCameraResult["CameraMatrix"]=mtx.tolist()
        calibrateCameraResult["CameraDistCoeffs"] = dist.tolist()
        calibrateCameraResult["RotationMat"] = R_camera2base.tolist()
        calibrateCameraResult["TranslationMat"] = T_camera2base.tolist()

        try:
            with open("./conf/CalibParams-lumi.json", "w") as f:
                f.write(json.dumps(calibrateCameraResult, indent=4, ensure_ascii=False))
            print("【SAVE SUCCESS...】")
        except:
            print("【SAVE FAILURE...】")

if __name__ == "__main__":
    calibrator = Calibration(9, 7, 0.001)
    worldPos=[]
    for i in range(9):
        tmp=[random.randint(-300,300),random.randint(-300,300),random.randint(-300,300),random.randint(-180,180),random.randint(-180,180),random.randint(-180,180)]
        worldPos.append(tmp)
    print(worldPos)
    calibrator.process('./data/pic',worldPos)
