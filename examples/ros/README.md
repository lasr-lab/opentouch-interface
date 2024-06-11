## ROS2 example
This is a simple example of how a publisher and subscriber node can be used in [ROS 2 (Foxy)](https://docs.ros.org/en/foxy/Installation/Ubuntu-Install-Debians.html) to send and receive image data from the Digit.

### How to run
1. Enter your Digit serial ID in `ros2_ws/src/touch_sensors/touch_sensors/publisher.py` 
2. If necessary, source your ROS 2 installation to make `ros2` commands available. The specific command depends on your terminal shell type (choose between `.bash`, `.sh`, or `.zsh`)
```bash
source /opt/ros/foxy/setup.bash
```
3. Navigate to the `digit-interface/ros2_ws` directory.
```bash
cd ros2_ws
```
4. Build the `touch_sensors` package.
```bash
colcon build --packages-select touch_sensors
```
5. Open a second terminal and source the ROS 2 environment in both terminals.
```bash
source install/setup.bash
```
6. Start the `publisher` node in the first terminal.
```bash
ros2 run touch_sensors talker
```
7. Start the `subscriber` node in the second terminal.
```bash
ros2 run touch_sensors listener
```

### Troubleshooting
If you installed the `digit_interface` using `python setup.py install` and encounter a `ModuleNotFoundError: No module named 'digit_interface'` when running `ros2 run touch_sensors talker`, update your `PYTHONPATH` environment variable.
```bash
export PYTHONPATH=$PYTHONPATH:/path/to/digit-interface  
```
