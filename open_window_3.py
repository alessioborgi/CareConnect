import time
from xarm.wrapper import XArmAPI
import traceback

class RobotMain(object):
    """Robot Main Class"""
    def __init__(self, robot, **kwargs):
        self.alive = True
        self._arm = robot
        self._tcp_speed = 20  # Very slow TCP speed
        self._tcp_acc = 20  # Very slow TCP acceleration
        self._angle_speed = 5  # Very slow angle speed
        self._angle_acc = 10  # Very slow angle acceleration
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

    # Callback for error/warn changes
    def _error_warn_changed_callback(self, data):
        if data and data['error_code'] != 0:
            self.alive = False
            self.pprint(f"Error {data['error_code']} occurred. Quitting...")
            self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)

    # Callback for state changes
    def _state_changed_callback(self, data):
        if data and data['state'] == 4:  # state 4 typically means "STOPPED"
            self.alive = False
            self.pprint("State=4 (STOPPED), quitting...")
            self._arm.release_state_changed_callback(self._state_changed_callback)

    # Callback for count changes (if applicable)
    def _count_changed_callback(self, data):
        if self.is_alive:
            self.pprint(f"Counter value: {data['count']}")

    def _check_code(self, code, label):
        if not self.is_alive or code != 0:
            self.alive = False
            ret1 = self._arm.get_state()
            ret2 = self._arm.get_err_warn_code()
            self.pprint(f"{label}, code={code}, connected={self._arm.connected}, state={self._arm.state}, error={self._arm.error_code}, ret1={ret1}. ret2={ret2}")
        return self.is_alive

    @staticmethod
    def pprint(*args, **kwargs):
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}][{stack_tuple[1]}] {' '.join(map(str, args))}")
        except:
            print(*args, **kwargs)

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

    def move_servo(self, angle, wait=True):
        code = self._arm.set_servo_angle(angle=angle, speed=self._angle_speed, mvacc=self._angle_acc, wait=wait, is_radian=True, radius=0.0)
        if not self._check_code(code, 'set_servo_angle'):
            return

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

def perform_movement(robot_main, trajectory_data, frequency):
    time_step = 1.0 / frequency

    for data_point in trajectory_data:
        robot_main.move_servo(angle=data_point[:7], wait=False)
        time.sleep(time_step)

    print("Movement completed.")

def main(traj_file_path, robot_ip):
    arm = XArmAPI(robot_ip)
    robot_main = RobotMain(arm)
    
    trajectory_data, frequency = parse_traj_file(traj_file_path)
    
    perform_movement(robot_main, trajectory_data, frequency)
    
    arm.disconnect()

if __name__ == "__main__":
    traj_file_path = "C:/Users/WolfgangKienreich/Documents/coding/Open_Window_Alessio/window_traj.traj"  # Replace with the actual path to your .traj file
    robot_ip = "192.168.1.196"  # Replace with your robot's IP address
    main(traj_file_path, robot_ip)

