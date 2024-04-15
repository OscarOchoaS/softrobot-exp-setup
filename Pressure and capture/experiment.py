# # Soft Robot data adquisition and capture
# Main: Experiment

# By: Oscar Ochoa 
# March 2024

import time
import os
import threading
import queue
import camera
import signal_managment
import exports

# Threads queues and events
pwm_sw_event = threading.Event()
pwm_pause_event = threading.Event()
serial_sw_event = threading.Event()
camera_stop_event = threading.Event()
serial_data_queue = queue.Queue()

pipeline = camera.init_camera()        #Initialize camera

# # # # #
# Experiment info               
id = 'HEX10'               # Experiment name
goal_pressure = 45              # Goal pressure in MPa

date = time.strftime("%d-%m-%y")
folder_name = exports.create_folder(id, date)
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
pressure_increment = 5          # Mpa pressure increments

# Open valve before recording (release prexisting pressure)
signal_managment.digital_output(device_name, channel_valve, True)
time.sleep(0.5)  # Wait for 0.5 seconds
signal_managment.digital_output(device_name, channel_valve, False)

# Strart threads
duty_cycle = 0.1 
pwm_thread = threading.Thread(target=signal_managment.pwm_airpump, args=(duty_cycle, device_name, channel_pump))
serial_thread = threading.Thread(target=signal_managment.serial_read, args=(serial_port, ))
camera_thread = threading.Thread(target=camera.capture_frame, args=(video_file_path, pipeline,))
time.sleep(1)
camera_thread.start()
serial_thread.start()

# Open valve lock
signal_managment.digital_output(device_name, channel_lock, True)

pwm_thread.start()

pressure_list = []           # List to store pressure
time_list = []               # List to store time
force_list = []              # List to store force
start_time = time.time()     # Get the start time
avg_pressure = 0             # Initializa pressure variable

while True:         

    # Capture data
    elapsed_time = time.time() - start_time  # Calculate elapsed time
    pressure = signal_managment.pressure_measurement(device_name, channel_psensor, num_samples)
    force = serial_data_queue.get()
    print("Current Pressure: ", pressure, " KPa")
    print("Current Force: ", force, " Kg")
            
    # Store data
    time_list.append(elapsed_time)
    pressure_list.append(pressure)
    force_list.append(force)

    if (pressure >= pressure_increment) and (pressure_increment != goal_pressure):
        signal_managment.digital_output(device_name, channel_lock, False)
        pwm_pause_event.set()            # Pause PWM signal for a second
        time.sleep(2)                   
        signal_managment.digital_output(device_name, channel_lock, True)    
        pressure_increment = pressure_increment + 5

    if pressure >= goal_pressure:

        pwm_sw_event.set()
        serial_sw_event.set()

        # Close valve lock
        signal_managment.digital_output(device_name, channel_lock, False)
        print("Target Pressure achieved")
        break

# Turn on the valve again
signal_managment.digital_output(device_name, channel_valve, True)
time.sleep(0.5)
camera_stop_event.set()

# join threads
camera_thread.join()
pwm_thread.join()
serial_thread.join()

# Make exports
exports.export_video(video_file_path)
exports.export_csv(csv_file_path, time_list, pressure_list, force_list)