# Soft Robot data adquisition and capture
# By: Oscar Ochoa 
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

def create_folder(id):
    folder_name = f"{id}_test_{date}"
    try:
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created successfully.")
        return folder_name
    except FileExistsError: # If the folder already exists
        i = 1
        while True:
            folder_name = f"{id}_{i}_test_{date}"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                print(f"Folder '{folder_name}' created successfully.")
                return folder_name
            i += 1

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

# # Threads # #
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

def pwm_airpump(duty_cycle):
    try:
        while not pwm_sw_event.is_set(): 
            time_total = 0.01               # Total time of work 10ms
            t1 = duty_cycle * time_total    # Time ON
            t2 = time_total - t1            # Time OFF
            digital_output(device_name, channel_pump, True)
            time.sleep(t1)
            digital_output(device_name, channel_pump, False)
            time.sleep(t2)
    except Exception as e:
        print(f"Error in pwm_airpump thread: {e}")

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
        try:
            ser.close()  # Close the serial port when the loop exits
        except NameError:  # Handle the case where 'ser' is not defined
            pass

# # Exports # #
def export_video(video_file_path):
    # Convert to mp4 
    ffmpeg_command = f'ffmpeg -y -framerate 50 -i {video_file_path} -c:v libx264 -crf 23 {video_file_path[:-5]}.mp4'
    subprocess.run(ffmpeg_command, shell=True)

def export_csv(csv_file_path, time_list, pressure_list, force_list):
    with open(csv_file_path, mode='w', newline='') as data_file:
        data_writer = csv.writer(data_file)
        # data_writer.writerow(['Time (s)', 'Pressure (KPa)'])
        data_writer.writerow(['Time (s)', 'Pressure (KPa)','Force (N)'])  # Write header row  

        for t, pressure, force in zip(time_list, pressure_list, force_list):
            data_writer.writerow([t, pressure, force])

# Threads queues and events
serial_data_queue = queue.Queue()
pwm_sw_event = threading.Event()
serial_sw_event = threading.Event()
camera_stop_event = threading.Event()

pipeline = init_camera()        #Initialize camera

# # # # #
# Experiment info               
id = 'Test_AUX10'               # Experiment name
goal_pressure = 45              # Goal pressure in MPa

date = time.strftime("%d-%m-%y")
folder_name = create_folder(id)
# Update file paths to include folder name
video_file_path = os.path.join(folder_name, f'video_{id}_{date}.h265')
csv_file_path = os.path.join(folder_name, f'data_{id}_{date}.csv')

# Device info
device_name = "Dev2"
channel_psensor = "ai3"
channel_pump = "port1/line0"
channel_valve = "port1/line1" 
channel_lock = "port1/line2" 
serial_port = "COM3"
num_samples = 5                 # From pressure sensor (average will be used)

# Open valve before recording (release prexisting pressure)
digital_output(device_name, channel_valve, True)
time.sleep(0.5)  # Wait for 0.5 seconds
digital_output(device_name, channel_valve, False)

# Strart threads
duty_cycle = 0.1 
pwm_thread = threading.Thread(target=pwm_airpump, args=(duty_cycle, ))
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