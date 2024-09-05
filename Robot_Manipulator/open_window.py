import time
from xarm.wrapper import XArmAPI

# Function to parse the .traj file
def parse_traj_file(file_path):
    trajectory_data = []
    frequency = 250.0  # Default frequency in case it's missing

    with open(file_path, 'r') as file:
        lines = file.readlines()

        # Extract the frequency from the header
        if lines[0].startswith("# frequency="):
            frequency = float(lines[0].split('=')[1].strip())

        # Process the rest of the lines as trajectory data
        for line in lines[1:]:
            line = line.strip().rstrip(',')  # Remove any trailing whitespace and commas
            if line:  # Skip empty lines
                try:
                    # Convert the line into a list of floats (joint angles)
                    data_point = list(map(float, line.split(',')))
                    trajectory_data.append(data_point)
                except ValueError as e:
                    print(f"Skipping invalid line: {line}. Error: {e}")

    return trajectory_data, frequency

# Function to perform the movement on the xArm robot
def perform_movement(arm, trajectory_data, frequency):
    # Calculate the time step based on the frequency
    time_step = 1.0 / frequency
    
    for data_point in trajectory_data:
        # Send joint angles or positions to the robot
        # Assuming the data points represent joint angles (adjust if needed)
        arm.set_servo_angle(angle=data_point[:7], wait=False, is_radian=True)  # Sending the first 7 values as joint angles
        
        # Wait for the next step
        time.sleep(time_step)
    
    print("Movement completed.")

# Main function to execute the script
def main(traj_file_path, robot_ip):
    # Initialize the robot using the XArm API
    arm = XArmAPI(robot_ip)
    
    # Ensure the arm is in position mode and cleared of previous errors
    arm.motion_enable(True)
    arm.set_mode(0)  # 0 for position control mode
    arm.clean_warn()
    arm.clean_error()

    # Parse the .traj file and extract trajectory data and frequency
    trajectory_data, frequency = parse_traj_file(traj_file_path)
    
    # Perform the movement on the robot
    perform_movement(arm, trajectory_data, frequency)
    
    # Disconnect the robot after completion
    arm.disconnect()

# Example usage
if __name__ == "__main__":
    traj_file_path = "C:/Users/WolfgangKienreich/Documents/coding/Open_Window_Alessio/Open_Window.traj"  # Replace with the actual path to your .traj file
    robot_ip = "192.168.1.209"  # Replace with your robot's IP address
    main(traj_file_path, robot_ip)
