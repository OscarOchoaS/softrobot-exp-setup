# # Soft Robot data adquisition and capture # #
# signal_managment.py

# By: Oscar Ochoa and Enrico Mendez
# September 2024

import nidaqmx
import threading
import queue
import serial
import time
import sys

serial_data_queue = queue.Queue()
pwm_sw_event = threading.Event()
pwm_pause_event = threading.Event()
serial_sw_event = threading.Event()

# Analog input from pressure sensor
def pressure_measurement(device_name, channel, num_samples):
    """
    Measure the pressure using a voltage signal from a specified device and channel.
    Parameters:
    - device_name (str): The name of the device.
    - channel (str): The channel of the device to measure the voltage signal from.
    - num_samples (int): The number of samples to acquire.
    Returns:
    - pressure (float): The calculated pressure value.
    """
    voltage_range = 5.0   # Voltage range
    sample_rate = 1000.0  # Desired sample rate in Hz
    
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(f"{device_name}/{channel}",
                                             min_val=0,
                                             max_val=voltage_range)

        task.timing.cfg_samp_clk_timing(rate=sample_rate, samps_per_chan=num_samples)
        voltage_data = task.read(number_of_samples_per_channel=num_samples)

    # Equation obtained from datasheet
    pressure_data = [((voltage - 0.5) / 4.0)for voltage in voltage_data]
    pressure = sum(pressure_data)/num_samples
    return pressure

# Digital inputs
def digital_output(device_name, channel, io):
    """
    Writes a digital output signal to the specified device and channel.

    Parameters:
    - device_name (str): The name of the device.
    - channel (str): The channel to write the signal to.
    - io (bool): The value to write to the channel.

    Returns:
    None
    """
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan(f"{device_name}/{channel}")
        task.write(io)

# Read serial port
def serial_read(port):
    """
    Reads data from a serial port.

    Args:
        port (str): The port name or device file of the serial port.

    Raises:
        PermissionError: If a permission error occurs while accessing the serial port.
        serial.SerialException: If a serial exception occurs (e.g., device not found).
        Exception: If any other unexpected error occurs.

    Returns:
        None
    """
    ser = None  # Initialize serial object outside the try block
    try:
        ser = serial.Serial(port, 9600)
        while not serial_sw_event.is_set():
            line = ser.readline().decode().strip()
            serial_data_queue.put(line)  # Put received data into queue
    except PermissionError as e:
        # If a Permission Error occurs
        print(f"Permission error: {e}")
    except serial.SerialException as e:
        # If a Serial Exception occurs (e.g., device not found)
        print(f"Serial error: {e}")
    except Exception as e:
        # If any other unexpected error occurs
        print(f"Error reading from serial port: {e}")
    finally:
        if ser is not None:
            ser.close()  # Close the serial port when the loop exits

# Control the air pump with PWM
def pwm_airpump(duty_cycle, device_name, channel_pump):
    """
    Controls the PWM signal for an air pump.

    Args:
        duty_cycle (float): The duty cycle of the PWM signal.
        device_name (str): The name of the device.
        channel_pump (int): The channel of the pump.

    Raises:
        Exception: If an error occurs in the thread generation.

    """


    try:

        # Check if the pause event is set
        if pwm_pause_event.is_set():
            # Pause for a second
            time.sleep(2)
            # Clear the pause event to continue
            pwm_pause_event.clear()

        while not pwm_sw_event.is_set(): 
            time_total = 0.015               # Total time of work 10ms
            t1 = duty_cycle * time_total    # Time ON
            t2 = time_total - t1            # Time OFF
            digital_output(device_name, channel_pump, True)
            time.sleep(t1)
            digital_output(device_name, channel_pump, False)
            time.sleep(t2)

    except Exception as e:
        # If an Error ocurrs in the thread generation
        print(f"Error in pwm_airpump thread: {e}")  
