# # Soft Robot data adquisition and capture # #
# exports.py

# By: Oscar Ochoa and Enrico Mendez
# September 2024

import subprocess
import csv
import os

def export_video(video_file_path):
    """
    Export a video file to mp4 format using ffmpeg.

    Args:
        video_file_path (str): The path of the video file to be exported.

    Returns:
        None
    """
    # Convert to mp4 
    ffmpeg_command = f'ffmpeg -y -framerate 50 -i {video_file_path} -c:v libx264 -crf 23 {video_file_path[:-5]}.mp4'
    subprocess.run(ffmpeg_command, shell=True)

def export_csv(csv_file_path, time_list, pressure_list, force_list):
    """
    Export data to a CSV file.

    Args:
        csv_file_path (str): The file path of the CSV file.
        time_list (list): A list of time values.
        pressure_list (list): A list of pressure values.
        force_list (list): A list of force values.

    Returns:
        None
    """

    with open(csv_file_path, mode='w', newline='') as data_file:
        data_writer = csv.writer(data_file)
        # data_writer.writerow(['Time (s)', 'Pressure (KPa)'])
        data_writer.writerow(['Time (s)', 'Pressure (KPa)','Force (N)'])  # Write header row  

        for t, pressure, force in zip(time_list, pressure_list, force_list):
            data_writer.writerow([t, pressure, force])

# Create folders
def create_folder(id, date):
    """
    Creates a folder with a unique name based on the given id and date.
    Args:
        id (str): The identifier for the folder.
        date (str): The date to be included in the folder name.
    Returns:
        tuple: A tuple containing the folder name and the index used to create the folder name.
    Raises:
        FileExistsError: If a folder with the same name already exists, a new name will be generated.
    """
    i = 1
    folder_name = f"{id}_{i}_{date}"
    try:
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created successfully.")
        return folder_name, i
    except FileExistsError: # If the folder already exists
        
        while True:
            folder_name = f"{id}_{i}_{date}"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                print(f"Folder '{folder_name}' created successfully.")
                return folder_name, i
            i += 1
