# Soft Robot data adquisition and capture
# By: Oscar Ochoa 
# March 2024

import time
import os
import threading
import queue
from camera import init_camera, capture_frame
from signal_managment import pressure_measurement, digital_output, serial_read, pwm_airpump
from exports import export_video, export_csv, create_folder

# Threads queues and events
pwm_sw_event = threading.Event()
serial_sw_event = threading.Event()
camera_stop_event = threading.Event()
serial_data_queue = queue.Queue()

pipeline = init_camera()        #Initialize camera

# # # # #
# Experiment info               
id = 'Test_AUX10'               # Experiment name
goal_pressure = 45              # Goal pressure in MPa

date = time.strftime("%d-%m-%y")
folder_name = create_folder(id, date)
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
pwm_thread = threading.Thread(target=pwm_airpump, args=(duty_cycle, device_name, channel_pump))
serial_thread = threading.Thread(target=serial_read, args=(serial_port, ))
camera_thread = threading.Thread(target=capture_frame, args=(video_file_path, pipeline,))
time.sleep(1)
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
time.sleep(0.5)
camera_stop_event.set()

# join threads
camera_thread.join()
pwm_thread.join()
serial_thread.join()

# Make exports
export_video(video_file_path)
export_csv(csv_file_path, time_list, pressure_list, force_list)