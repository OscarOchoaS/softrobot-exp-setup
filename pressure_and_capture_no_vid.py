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

serial_data_queue = queue.Queue()
pwm_sw_event = threading.Event()
serial_sw_event = threading.Event()

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

def export_csv(csv_file_path, time_list, pressure_list, force_list):
    with open(csv_file_path, mode='w', newline='') as data_file:
        data_writer = csv.writer(data_file)
        # data_writer.writerow(['Time (s)', 'Pressure (KPa)'])
        data_writer.writerow(['Time (s)', 'Pressure (KPa)','Force (N)'])  # Write header row  

        for t, pressure, force in zip(time_list, pressure_list, force_list):
            data_writer.writerow([t, pressure, force])

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
    while not serial_sw_event.is_set():
        try:
            ser = serial.Serial(port, 9600)
            while True:
                line = ser.readline().decode().strip()
                serial_data_queue.put(line)  # Put received data into queue
        except PermissionError as e:
            print(f"Permission error: {e}")
        except Exception as e:
            print(f"Error reading from serial port: {e}")

# # # # #
# Experiment name
id = 'Train_noR'
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
goal_pressure = 40              # To achieve

dc = 0.06
pwm_thread = threading.Thread(target=pwm_airpump, args=(dc, ))
serial_thread = threading.Thread(target=serial_read, args=(serial_port, ))
serial_thread.start()


# Open valve before recording
digital_output(device_name, channel_valve, True)
time.sleep(0.5)  # Wait for 1 second
digital_output(device_name, channel_valve, False)

# Open valve lock
digital_output(device_name, channel_lock, True)

pressure_list = []           # List to store pressure
time_list = []               # List to store time
force_list = []              # List to store force
start_time = time.time()     # Get the start time
avg_pressure = 0             # Initializa pressure variable

pwm_thread.start()

while True:         

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

# Make exports
export_csv(csv_file_path, time_list, pressure_list, force_list)

pwm_thread.join()
serial_thread.join()