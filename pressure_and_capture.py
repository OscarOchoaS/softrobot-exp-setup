# Soft Robot data adquisition and capture
# Oscar Ochoa 
# March 2024

import nidaqmx
import time
import depthai as dai
import subprocess
import csv
import os
import serial
import threading
import queue

def pressure_measurement(device_name, channel, num_samples):
    voltage_range = 5.0   # Voltage range
    sample_rate = 1000.0  # Desired sample rate in Hz
    
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(f"{device_name}/{channel}",
                                             min_val=0,
                                             max_val=voltage_range)

        task.timing.cfg_samp_clk_timing(rate=sample_rate, samps_per_chan=num_samples)
        voltage_data = task.read(number_of_samples_per_channel=num_samples)

    pressure_data = [((voltage - 0.5) * 100.0 / 4.0 + 35.4) * 1.08 for voltage in voltage_data]
    pressure = sum(pressure_data)/num_samples
    return pressure

def digital_output(device_name, channel, io):
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan(f"{device_name}/{channel}")
        task.write(io)

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

def export_video(video_file_path):
    # Convert to mp4 
    ffmpeg_command = f'ffmpeg -y -framerate 50 -i {video_file_path} -c:v libx264 -crf 23 {video_file_path[:-5]}.mp4'
    # Cut first frame of video 
    #ffmpeg_command2 = f'ffmpeg -y -i {video_file_path[:-5]}_i.mp4 -ss 0.00001 -c copy {video_file_path[:-5]}.mp4'
    subprocess.run(ffmpeg_command, shell=True)
    #subprocess.run(ffmpeg_command2, shell=True)
    #video_file_path_i = f'{video_file_path[:-5]}_i.mp4'
    # os.remove(video_file_path_i)

def export_csv(csv_file_path, time_list, pressure_list, force_list):
    with open(csv_file_path, mode='w', newline='') as data_file:
        data_writer = csv.writer(data_file)
        # data_writer.writerow(['Time (s)', 'Pressure (KPa)'])
        data_writer.writerow(['Time (s)', 'Pressure (KPa)','Force (N)'])  # Write header row  

        for t, pressure, force in zip(time_list, pressure_list, force_list):
            data_writer.writerow([t, pressure, force])

def capture_frame(video_file_path, pipeline):
    with dai.Device(pipeline) as device:
        q = device.getOutputQueue(name="h265", maxSize=30, blocking=True)
        while not camera_stop_event.is_set():
            h265Packet = q.get()
            with open(video_file_path, 'ab') as videoFile:
                h265Packet.getData().tofile(videoFile)

def pwm_airpump(duty_cycle):
    while not pwm_sw_event.is_set(): 
        ttot = 0.01
        t1 = duty_cycle * ttot
        t2 = ttot - t1
        digital_output(device_name, channel_pump, True)
        time.sleep(t1)
        digital_output(device_name, channel_pump, False)
        time.sleep(t2)

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

def serial_read(port):
    try:
        ser = serial.Serial(port, 9600)
        while not serial_sw_event.is_set():
            line = ser.readline().decode().strip()
            serial_data_queue.put(line)  # Put received data into queue
    except PermissionError as e:
        print(f"Permission error: {e}")
    except Exception as e:
        print(f"Error reading from serial port: {e}")
    finally:
        ser.close()  # Close the serial port when the loop exits

serial_data_queue = queue.Queue()
pwm_sw_event = threading.Event()
serial_sw_event = threading.Event()
camera_stop_event = threading.Event()

# # # # #
# Experiment name
id = 'Test_AUX10'
date = time.strftime("%d-%m-%y")

folder_name = create_folder(id)
# Update file paths to include folder name
video_file_path = os.path.join(folder_name, f'video_{id}_{date}.h265')
csv_file_path = os.path.join(folder_name, f'data_{id}_{date}.csv')
pipeline = init_camera()        #Initialize camera


# Device info
device_name = "Dev2"
channel_psensor = "ai3"
channel_pump = "port1/line0"
channel_valve = "port1/line1" 
channel_lock = "port1/line2" 
serial_port = "COM3"
num_samples = 5                 # From pressure sensor (average will be used)
goal_pressure = 45              # To achieve


# Open valve before recording
digital_output(device_name, channel_valve, True)
time.sleep(0.5)  # Wait for 1 second
digital_output(device_name, channel_valve, False)

# Strart threads
dc = 0.005
pwm_thread = threading.Thread(target=pwm_airpump, args=(dc, ))
serial_thread = threading.Thread(target=serial_read, args=(serial_port, ))
camera_thread = threading.Thread(target=capture_frame, args=(video_file_path, pipeline,))
camera_thread.start()
serial_thread.start()


# Open valve lock
digital_output(device_name, channel_lock, True)

pwm_thread.start()

pressure_list = []           # List to store pressure
time_list = []               # List to store time
force_list = []              # List to store force
start_time = time.time()     # Get the start time
avg_pressure = 0             # Initializa pressure variable



while True:         
    
    # Capture data
    elapsed_time = time.time() - start_time  # Calculate elapsed time
    pressure = pressure_measurement(device_name, channel_psensor, num_samples)
    force = serial_data_queue.get()
    print("Current Pressure: ", pressure, " KPa")
    print("Current Force: ", force, " Kg")
            
    # Store data
    time_list.append(elapsed_time)
    pressure_list.append(pressure)
    force_list.append(force)

    if pressure >= goal_pressure:

        pwm_sw_event.set()
        serial_sw_event.set()

        # Close valve lock
        digital_output(device_name, channel_lock, False)
        print("Target Pressure achieved")
        break

# Turn on the valve again
digital_output(device_name, channel_valve, True)
camera_stop_event.set()

# join threads
camera_thread.join()
pwm_thread.join()
serial_thread.join()

# Make exports
export_video(video_file_path)
export_csv(csv_file_path, time_list, pressure_list, force_list)

