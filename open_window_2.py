class RobotMain(object):
    """Robot Main Class"""
    def __init__(self, robot, **kwargs):
        self.alive = True
        self._arm = robot
        self._tcp_speed = 2000  # Increased TCP speed
        self._tcp_acc = 2000  # Increased TCP acceleration
        self._angle_speed = 100  # Increased angle speed
        self._angle_acc = 300  # Increased angle acceleration
        self._vars = {}
        self._funcs = {}
        self._robot_init()

    def _robot_init(self):
        self._arm.clean_warn()
        self._arm.clean_error()
        self._arm.motion_enable(True)
        self._arm.set_mode(0)
        self._arm.set_state(0)
        time.sleep(1)
        self._arm.register_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.register_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'register_count_changed_callback'):
            self._arm.register_count_changed_callback(self._count_changed_callback)

    def _error_warn_changed_callback(self, data):
        if data and data['error_code'] != 0:
            self.alive = False
            self.pprint('err={}, quit'.format(data['error_code']))
            self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)

    def _state_changed_callback(self, data):
        if data and data['state'] == 4:
            self.alive = False
            self.pprint('state=4, quit')
            self._arm.release_state_changed_callback(self._state_changed_callback)

    def _count_changed_callback(self, data):
        if self.is_alive:
            self.pprint('counter val: {}'.format(data['count']))

    def _check_code(self, code, label):
        if not self.is_alive or code != 0:
            self.alive = False
            ret1 = self._arm.get_state()
            ret2 = self._arm.get_err_warn_code()
            self.pprint('{}, code={}, connected={}, state={}, error={}, ret1={}. ret2={}'.format(label, code, self._arm.connected, self._arm.state, self._arm.error_code, ret1, ret2))
        return self.is_alive

    @staticmethod
    def pprint(*args, **kwargs):
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
        except:
            print(*args, **kwargs)

    @property
    def arm(self):
        return self._arm

    @property
    def VARS(self):
        return self._vars

    @property
    def FUNCS(self):
        return self._funcs

    @property
    def is_alive(self):
        if self.alive and self._arm.connected and self._arm.error_code == 0:
            if self._arm.state == 5:
                cnt = 0
                while self._arm.state == 5 and cnt < 5:
                    cnt += 1
                    time.sleep(0.1)
            return self._arm.state < 4
        else:
            return False

    def move_to_position(self, x, y, z, roll, pitch, yaw, wait=True, sleep_time=0):
        code = self._arm.set_position(x, y, z, roll, pitch, yaw, speed=self._tcp_speed, mvacc=self._tcp_acc, radius=0.0, wait=wait)
        if not self._check_code(code, 'set_position'):
            return
        time.sleep(sleep_time)

    def move_gripper(self, dist, wait=True, speed=5000, auto_enable=True, sleep_time=0):
        code = self._arm.set_gripper_position(dist, wait=wait, speed=speed, auto_enable=auto_enable)
        if not self._check_code(code, 'set_position'):
            return
        time.sleep(sleep_time)

    def move_servo(self, angle, wait=True):
        code = self._arm.set_servo_angle(angle=angle, speed=self._angle_speed, mvacc=self._angle_acc, wait=wait, radius=0.0)
        if not self._check_code(code, 'set_servo_angle'):
            return

    def initialise_robi(self, wait=False):
        self.move_servo([0, -20, -140, 0, 0, 0], wait=wait)
        self.move_gripper(300, wait=wait, speed=5000, auto_enable=True, sleep_time=0)

    def perform_movement(self, trajectory_data, frequency):
        time_step = 1.0 / frequency

        for index, data_point in enumerate(trajectory_data):
            # Start closing the gripper at the midpoint of the trajectory
            if index == len(trajectory_data) // 2:
                self.move_gripper(0, wait=False, speed=5000, auto_enable=True)  # Start closing the gripper

            # Release the gripper at a specific point in the trajectory (optional)
            if index == (3 * len(trajectory_data)) // 4:  # For example, 3/4 through the trajectory
                self.move_gripper(850, wait=False, speed=5000, auto_enable=True)  # Releasing the gripper

            # Continue moving the robot while the gripper is closing/opening
            self.move_servo(
                angle=data_point[:7], 
                wait=False  # Ensure the robot continues moving without waiting
            )
            time.sleep(time_step)

        print("Movement completed.")

# Function to parse the .traj file
def parse_traj_file(file_path):
    trajectory_data = []
    frequency = 250.0  # Default frequency in case it's missing

    with open(file_path, 'r') as file:
        lines = file.readlines()

        if lines[0].startswith("# frequency="):
            frequency = float(lines[0].split('=')[1].strip())

        for line in lines[1:]:
            line = line.strip().rstrip(',')  # Remove trailing commas
            if line:
                try:
                    data_point = list(map(float, line.split(',')))
                    trajectory_data.append(data_point)
                except ValueError as e:
                    print(f"Skipping invalid line: {line}. Error: {e}")

    return trajectory_data, frequency

# Main function to execute the script
def main(traj_file_path, robot_ip):
    # Initialize the robot using the XArm API
    arm = XArmAPI(robot_ip)
    
    # Initialize RobotMain with the arm
    robot_main = RobotMain(arm)
    
    # Parse the .traj file and extract trajectory data and frequency
    trajectory_data, frequency = parse_traj_file(traj_file_path)
    
    # Perform the movement on the robot
    robot_main.perform_movement(trajectory_data, frequency)
    
    # Disconnect the robot after completion
    arm.disconnect()

# Example usage
if __name__ == "__main__":
    traj_file_path = "C:/Users/WolfgangKienreich/Documents/coding/Open_Window_Alessio/Open_Window.traj"  # Replace with the actual path to your .traj file
    robot_ip = "192.168.1.209"  # Replace with your robot's IP address
    main(traj_file_path, robot_ip)