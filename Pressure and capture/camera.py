# # Soft Robot data adquisition and capture # #
# camera.py

# By: Oscar Ochoa 
# April 2024

import time
import depthai as dai
import threading

# Define camera_stop_event as a global variable
camera_stop_event = threading.Event()

# Initialization sequence
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
    time.sleep(2)

    return pipeline

# Camera frame capture Thread
def capture_frame(video_file_path, pipeline):
    try:
        with dai.Device(pipeline) as device:
            q = device.getOutputQueue(name="h265", maxSize=30, blocking=True)
            while not camera_stop_event.is_set():
                h265Packet = q.get()
                with open(video_file_path, 'ab') as videoFile:
                    h265Packet.getData().tofile(videoFile)
    except Exception as e:
        print(f"Error in capture_frame thread: {e}")
