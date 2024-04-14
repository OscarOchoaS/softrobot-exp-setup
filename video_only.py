# Video capture
# Oscar Ochoa 
# April 2024

import time
import depthai as dai
import subprocess
import os
import keyboard


def init_camera():
    print("Initializing camera" )

    # Create pipeline object
    pipeline = dai.Pipeline()
    camRgb = pipeline.create(dai.node.ColorCamera)
    videoEnc = pipeline.create(dai.node.VideoEncoder)
    xout = pipeline.create(dai.node.XLinkOut)
    xout.setStreamName('h265')
    
    # Initial Settings
    camRgb.initialControl.setBrightness(-4)
    camRgb.initialControl.setManualFocus(145)
    camRgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    videoEnc.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.H265_MAIN)

    camRgb.video.link(videoEnc.input)
    videoEnc.bitstream.link(xout.input)

    return pipeline

def export_video(video_file_path):
    # Convert to mp4 
    ffmpeg_command = f'ffmpeg -y -framerate 50 -i {video_file_path} -c:v libx264 -crf 23 {video_file_path[:-5]}.mp4'
    # Cut first frame of video 
    #ffmpeg_command2 = f'ffmpeg -y -i {video_file_path[:-5]}_i.mp4 -ss 0.00001 -c copy {video_file_path[:-5]}.mp4'
    subprocess.run(ffmpeg_command, shell=True)
    #subprocess.run(ffmpeg_command2, shell=True)
    #video_file_path_i = f'{video_file_path[:-5]}_i.mp4'
    # os.remove(video_file_path_i)

def capture_frame(q, video_file_path):
    h265Packet = q.get()
    h265Packet.getData().tofile(video_file_path)

def create_folder(id):
    folder_name = f"{id}_test_{date}"
    try:
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created successfully.")
        return folder_name
    except FileExistsError:
        i = 1
        while True:
            folder_name = f"{id}_{i}_test_{date}"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                print(f"Folder '{folder_name}' created successfully.")
                return folder_name
            i += 1

# # # # #
# Experiment name
id = 'Train_noR'
date = time.strftime("%d-%m-%y")

folder_name = create_folder(id)
# Update file paths to include folder name
video_file_path = os.path.join(folder_name, f'video_{id}_{date}.h265')
pipeline = init_camera()        #Initialize camera

with dai.Device(pipeline) as device, open(video_file_path, 'wb') as videoFile:

    q = device.getOutputQueue(name="h265", maxSize=30, blocking=True)
    while True:


        capture_frame(q, videoFile)

        if keyboard.is_pressed('q'):
            print("The 'q' key was pressed.")
            break      


# Make exports
export_video(video_file_path)
