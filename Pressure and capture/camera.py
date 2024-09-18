# # Soft Robot data adquisition and capture # #
# camera.py

# By: Oscar Ochoa and Enrico Mendez
# September 2024

import time
import depthai as dai
import threading

# Define camera_stop_event as a global variable
camera_stop_event = threading.Event()

# Initialization sequence
def init_camera():
    """
    Initializes the camera and returns a pipeline object.
    Returns:
        pipeline (dai.Pipeline): The pipeline object containing the camera and video encoder nodes.
    """
    # Code implementation goes here
    print("Initializing camera" )

    # Create pipeline object
    pipeline = dai.Pipeline()
    camRgb = pipeline.create(dai.node.ColorCamera)
    videoEnc = pipeline.create(dai.node.VideoEncoder)
    xout = pipeline.create(dai.node.XLinkOut)
    xout.setStreamName('h265')
    
    # Initial Settings
    # Adjust depending on experimental setup and lighting
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
    """
    Captures frames from a video stream and saves them to a file.

    Args:
        video_file_path (str): The path to the video file where frames will be saved.
        pipeline: The pipeline object used to configure the video stream.

    Raises:
        Exception: If an error occurs during the frame capture process.

    Returns:
        None
    """
    try:
        with dai.Device(pipeline) as device:
            q = device.getOutputQueue(name="h265", maxSize=30, blocking=True)
            while not camera_stop_event.is_set():
                h265Packet = q.get()
                with open(video_file_path, 'ab') as videoFile:
                    h265Packet.getData().tofile(videoFile)
    except Exception as e:
        # If an Error ocurrs in the thread generation
        print(f"Error in capture_frame thread: {e}")
