# SoftRobot Pneumatic Setup

## Overview

This project provides tools for setting up an experimental environment to characterize pneumatic soft actuators. The system integrates pneumatic components controlled by a National Instruments (NI) Data Acquisition (DAQ) system, video capturing for computational vision analysis, and serial communication for external sensor data.

## Features

- **Precise Control**: Manage pneumatic components via NI DAQ for accurate pressure control and monitoring.
- **High-Quality Video Capture**: Record video data for computational analysis of soft actuator behavior.
- **Flexible Data Integration**: Incorporate external sensor data via serial communication.
- **Modular Design**: Easily integrate this setup into various experimental configurations.
- **Data Export**: Automatically export collected data to CSV and video files in MP4 and HEVC formats.

## Hardware Requirements

To set up and run the experiments, ensure you have the following hardware components:

### 1. **Pneumatic Components**
- **Air Pump**: Provides controlled air flow to the soft actuators.
  - *Used*: [Parker BTC brushless slutless motor](https://www.parker.com/mx/es/home.html)
- **Solenoid Valves**: Controls the air flow paths within the system.
  - *Used*: [MAC 34B-AAA-GDNA-1BA 12VDC 4W](https://www.macvalves.com/)
- **Pressure Sensor**: Measures the internal pressure of the actuators.
  - *Used*: [CFSensor XGZP6847A](https://cfsensor.com/en/)
  
### 2. **Data Acquisition System**
- **NI DAQ Device**: Interfaces with the pneumatic components for control and data collection.
  - *Used*: [NI USB-6009](https://www.ni.com/en-us/support/model.usb-6009.html)

### 3. **Camera System**
- **DepthAI Camera**: Captures high-resolution video for visual analysis.
  - *Used*: [OAK-D Camera](https://store.opencv.ai/products/oak-d)
  
### 4. **External Sensors (Optional)**
- **Force Sensor or Other Sensors**: Connect via serial communication for additional data streams.
  - *Used*: [Phidgets Load Cell](https://www.phidgets.com/?tier=3&catid=46&pcid=42)

### 5. **Computer**
- **Computer**: A machine capable of running Python 3.8+ with necessary USB ports and performance specifications.


## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/softrobot-pneumatic-setup.git
   cd softrobot-pneumatic-setup
   ```

2. **Create a Virtual Environment (Optional)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Required Packages**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install NI DAQmx Drivers**
   - Download and install from the [National Instruments website](https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html).

5. **Install DepthAI SDK**
   ```bash
   pip install depthai
   ```

## Using `experiment.py`

The `experiment.py` script controls the entire experimental setup, handling data acquisition, camera control, and hardware interaction.

### Configurable Parameters:
The following parameters can be customized for your experiment:
- `id` (str): Name of the experiment, used for file naming.
- `goal_pressure` (float): Target pressure in MPa.
- `device_name` (str): Name of the DAQ device (e.g., "Dev2").
- `channels` (dict): Mapping of sensor and control channels for the DAQ device (e.g., pump, valve, lock).
- `serial_port` (str): Serial port to receive external sensor data (e.g., "COM3").
- `num_samples` (int): Number of samples to average from the pressure sensor.
- `pressure_increment` (float): Pressure increments in MPa for the experiment.

### Example:
To run the experiment with a target pressure of 45 MPa and save data with the experiment name "test_run":
```bash
python experiment.py
```

### Step-by-Step Instructions:
1. **Setup Hardware**: Ensure all components are properly connected and configured.
2. **Modify Parameters**: Adjust the parameters in `experiment.py` as needed.
3. **Run the Script**: Start the experiment by running `python experiment.py`.
4. **Monitor the Experiment**: Observe the console output for real-time updates on pressure and force.
5. **Analyze Data**: Once the experiment completes, data will be saved in the specified folder. Review the CSV and video files for analysis.

### Output Files:

After running the experiment, the following output files are generated:

- **CSV Data File**: Contains timestamped readings of pressure and force.
  - **Location**: `./<experiment_folder>/data_<id>_<index>_<date>.csv`
  - **Format**:

    | Time (s) | Pressure (KPa) | Force (N) |
    |----------|----------------|-----------|
    | 0.0      | 5.0            | 0.2       |
    | 0.5      | 10.0           | 0.4       |
    | ...      | ...            | ...       |

- **Video Files**:
  - **MP4 Format**: Converted video suitable for standard playback.
    - **Location**: `./<experiment_folder>/video_<id>_<index>_<date>.mp4`
  
  - **HEVC Format**: High-efficiency video coding for higher compression.
    - **Location**: `./<experiment_folder>/video_<id>_<index>_<date>.h265`



## Contribution

Contributions to this project are welcome! If you have ideas for improvements or new features, feel free to open an issue or submit a pull request.

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE.
