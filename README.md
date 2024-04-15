# SoftRobot Pneumatic Setup

## Overview

This project provides tools for setting up an experimental environment to characterize pneumatic soft actuators. The system integrates pneumatic components (pump, valves, pressure sensor) controlled by data acquisition with a NI DAQ, along with video capturing for computational vision analysis. Additionally, it offers the capability to receive serial data from a port for incorporating measurements from external sensors or microcontrollers.

## Features

- Integration of pneumatic system components with NI DAQ for precise control and monitoring.
- Video capturing capabilities for analyzing soft actuator behavior using computational vision techniques.
- Flexibility to incorporate data from external sensors or microcontrollers via serial communication.
- Modular design for easy integration into experimental setups.
- Extensible architecture allowing for further customization and expansion.

## Installation

To use this project, ensure you have the required packages installed. You can find the list of required packages in the `requirements.txt` file.

```bash
pip install -r requirements.txt

## Usage

1. Clone this repository to your local machine.
2. Ensure all required hardware components (pneumatic system, NI DAQ, camera) are properly connected.
3. Install the necessary Python packages using the command mentioned above.
4. Modify the configuration files or scripts as needed for your specific experimental setup.
5. Run the main script to start data acquisition and video capturing.
6. Data will be stored in a CSV file, and the video in a MP4 and a HEVC file
7. Analyze the collected data and video footage to characterize the behavior of pneumatic soft actuators.

Happy analysis!

## Contribution

Contributions to this project are welcome! If you have ideas for improvements or new features, feel free to open an issue or submit a pull request.

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE License.