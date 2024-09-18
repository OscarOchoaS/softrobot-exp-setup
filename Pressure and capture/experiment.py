
# # Soft Robot data acquisition and capture
# Main: Experiment

# By: Oscar Ochoa and Enrico Mendez
# September 2024

import time
import os
import threading
import camera
import signal_managment
import utils 

def initialize_experiment(id, goal_pressure, device_name, channels, serial_port, num_samples, pressure_increment):
    """
    Initializes the experiment by setting up folder structure, file paths, and device initialization.

    Args:
        id (str): Experiment name or identifier.
        goal_pressure (float): The target pressure for the experiment in MPa.
        device_name (str): The name of the DAQ device.
        channels (dict): Dictionary containing channel mappings for sensor, pump, valve, and lock.
        serial_port (str): The serial port for communication.
        num_samples (int): Number of samples to average from the pressure sensor.
        pressure_increment (float): Pressure increment steps in MPa.

    Returns:
        tuple: Paths to the video and CSV files, pipeline object, and folder name.
    """
    pipeline = camera.init_camera()  # Initialize camera
    time.sleep(1)

    # Create folder and file paths
    date = time.strftime("%d-%m-%y")
    folder_name, i = utils.create_folder(id, date)
    video_file_path = os.path.join(folder_name, f'video_{id}_{i}_{date}.h265')
    csv_file_path = os.path.join(folder_name, f'data_{id}_{i}_{date}.csv')

    return video_file_path, csv_file_path, pipeline, folder_name

def run_experiment(video_file_path, pipeline, device_name, channels, serial_port, num_samples, goal_pressure, pressure_increment):
    """
    Runs the main experiment loop, capturing data and controlling hardware.

    Args:
        video_file_path (str): Path to the output video file.
        pipeline (dai.Pipeline): DepthAI pipeline object.
        device_name (str): The name of the DAQ device.
        channels (dict): Dictionary containing channel mappings for sensor, pump, valve, and lock.
        serial_port (str): The serial port for communication.
        num_samples (int): Number of samples to average from the pressure sensor.
        goal_pressure (float): The target pressure for the experiment in MPa.
        pressure_increment (float): Pressure increment steps in MPa.

    Returns:
        tuple: Lists of time, pressure, and force data.
    """
    # Define threads
    duty_cycle = 0.04
    pwm_thread = threading.Thread(target=signal_managment.pwm_airpump, args=(duty_cycle, device_name, channels['pump']))
    serial_thread = threading.Thread(target=signal_managment.serial_read, args=(serial_port,))
    camera_thread = threading.Thread(target=camera.capture_frame, args=(video_file_path, pipeline))
    pwm_pause_event  = threading.Event()

    camera_thread.start()
    serial_thread.start()
    time.sleep(4)

    # Open valve before recording (release pre-existing pressure)
    signal_managment.digital_output(device_name, channels['valve'], True)
    time.sleep(0.5)  # Wait for 0.5 seconds
    signal_managment.digital_output(device_name, channels['valve'], False)
    signal_managment.digital_output(device_name, channels['lock'], True)  # Open valve lock

    pressure_list = []  # List to store pressure
    time_list = []  # List to store time
    force_list = []  # List to store force
    start_time = time.time()  # Get the start time
    pwm_thread.start()

    while True:
        # Capture data
        elapsed_time = time.time() - start_time  # Calculate elapsed time
        pressure = signal_managment.pressure_measurement(device_name, channels['psensor'], num_samples)
        force = signal_managment.serial_data_queue.get()
        print("Current Pressure: ", pressure, " KPa")
        print("Current Force: ", force, " Kg")

        # Store data
        time_list.append(elapsed_time)
        pressure_list.append(pressure)
        force_list.append(force)

        if (pressure >= pressure_increment) and (pressure_increment != goal_pressure):
            signal_managment.digital_output(device_name, channels['lock'], False)
            pwm_pause_event.set()  # Pause PWM signal for a second
            time.sleep(2)
            signal_managment.digital_output(device_name, channels['lock'], True)
            pressure_increment += 5

        if pressure >= goal_pressure:
            signal_managment.digital_output(device_name, channels['lock'], False)
            pwm_pause_event.set()  # Pause PWM signal for a second
            time.sleep(2)
            signal_managment.digital_output(device_name, channels['lock'], True)

            signal_managment.pwm_sw_event.set()
            signal_managment.serial_sw_event.set()

            # Close valve lock
            signal_managment.digital_output(device_name, channels['lock'], False)
            print("Target Pressure achieved")
            break

    # Turn on the valve again
    signal_managment.digital_output(device_name, channels['valve'], True)
    time.sleep(0.5)
    camera.camera_stop_event.set()

    # Join threads
    camera_thread.join()
    pwm_thread.join()
    serial_thread.join()

    return time_list, pressure_list, force_list

def finalize_experiment(video_file_path, csv_file_path, time_list, pressure_list, force_list):
    """
    Finalizes the experiment by exporting data and cleaning up.

    Args:
        video_file_path (str): Path to the output video file.
        csv_file_path (str): Path to the output CSV file.
        time_list (list): List of time data.
        pressure_list (list): List of pressure data.
        force_list (list): List of force data.

    Returns:
        None
    """
    # Make exports
    utils.export_video(video_file_path)
    utils.export_csv(csv_file_path, time_list, pressure_list, force_list)

def main():
    # User-configurable parameters
    id = 'test'               # Experiment name
    goal_pressure = 45             # Goal pressure in MPa
    device_name = "Dev2"
    channels = {
        'psensor': "ai3",
        'pump': "port1/line0",
        'valve': "port1/line1",
        'lock': "port1/line2"
    }
    serial_port = "COM3"
    num_samples = 5                # From pressure sensor (average will be used)
    pressure_increment = 5         # MPa pressure increments

    # Initialize experiment
    video_file_path, csv_file_path, pipeline, folder_name = initialize_experiment(
        id, goal_pressure, device_name, channels, serial_port, num_samples, pressure_increment
    )

    # Run experiment
    time_list, pressure_list, force_list = run_experiment(
        video_file_path, pipeline, device_name, channels, serial_port, num_samples, goal_pressure, pressure_increment
    )

    # Finalize and export data
    finalize_experiment(video_file_path, csv_file_path, time_list, pressure_list, force_list)

if __name__ == "__main__":
    main()
