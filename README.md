
# OpenTouch Interface

The OpenTouch Interface is a Python package designed to provide a unified interface for various touch sensors. It simplifies the process of interacting with touch sensors by providing a consistent API regardless of the specific sensor being used.

We also provide an easy-to-use web interface that lets you connect to the sensors and show their data stream without the need to code.

---

## Features

We currently offer a unified API along with a simple web interface for the following touch sensors:
- [Digit](https://digit.ml/)
- [GelSight Mini](https://www.gelsight.com/gelsightmini/)

Key features include:

- **Unified API**: Interact with multiple types of touch sensors using a single, consistent API.
- **Web Dashboard**: Manage sensors, record and replay data, and annotate data directly through a web interface.
- **Easy Configuration**: Use YAML config files to quickly set up and manage sensors.

## Installation

OpenTouch Interface requires Python 3.11 or higher and has been tested on Ubuntu 20.04.
You can install it in one of two ways: either via `pip` or by cloning the repository.

### Method 1: Install via `pip`

```bash
pip install opentouch-interface
```

### Method 2: Install via Cloning the Repository

```bash
git clone https://github.com/lasr-lab/opentouch-interface
cd opentouch-interface
pip install .
```

### Example of Setting Up a Virtual Environment with Python 3.11

If you are using a system with multiple Python versions, you can create a virtual environment with Python 3.11 like this:

```bash
python3.11 -m venv venv
source venv/bin/activate
```

Then, proceed with the installation using one of the methods above.

### Additional Sensor-Specific Dependencies

Depending on the specific sensors you are using, make sure you have all their necessary libraries 
installed by checking the installation guides of the respective sensors or by following this quick installation guide:

- #### [Digit](https://github.com/facebookresearch/digit-interface)

```bash
pip install digit-interface
```

- #### [GelSight Mini](https://www.gelsight.com/gelsightmini/)

```bash
Supported by default
```

## Connecting Sensors

You can connect touch sensors to the OpenTouch Interface in two main ways:

### 1. Dashboard (Web Interface)

The dashboard provides an intuitive web-based interface with the following features:

- **Group multiple sensors**
- **Record and replay data**
- **Annotate data with user input**

To start the dashboard, run:

```bash
opentouch-dashboard
```

If you encounter any errors, try reconnecting your sensors and restarting the dashboard.

#### Adding Sensors to the Dashboard

You can add sensors to the dashboard by:

1. **Manual Entry**: Enter sensor details directly in the dashboard.
2. **YAML Configuration**: Use a YAML config file to define sensor groups and settings.

When using the dashboard, sensors are assigned to one group exactly.
Therefore, **sensor names must be unique inside a group**.
An example config file is provided as [`group.yaml`](examples/simple/conf/sensor/group.yaml).
It is structured as follows:
```yaml
group_name: "Robotic hand"  # Group name.
path: "test.touch"          # File path where data should be saved (optional).

sensors:      # List of sensors belonging to that group
  - ...       # Sensor 1
  - ...       # Sensor 2

payload:      # List of input elements used for data annotations (optional).
  - ...       # e.g., text input
  - ...       # e.g., slider
```

Currently, the following sensors with their respective config files are supported:
- **Digit**
```yaml
# Mandatory
sensor_type: "DIGIT"            # Use "DIGIT".
sensor_name: "First Gripper"    # Sensor name (unique inside a group).
serial_id: "D20804"             # Sensor's serial ID.

# Optional
intensity: 15                   # LED brightness (0-15). Default: 15.
resolution: "QVGA"              # Image resolution (VGA/QVGA). Default: QVGA.
fps: 60                         # Frame rate (30/60). Default: 60.
sampling_frequency: 30          # Data request rate (Hz). Default: 30.
recording_frequency: 30         # Recording rate (Hz). Default: sampling_frequency.
```

- **GelSight Mini**
```yaml
# Mandatory
sensor_type: "GELSIGHT_MINI"    # Use "GELSIGHT_MINI".
sensor_name: "Second Gripper"   # Sensor name (arbitrary).

# Optional
sampling_frequency: 30          # Data request rate (Hz). Default: 30.
recording_frequency: 30         # Recording rate (Hz). Default: sampling_frequency.
```

You can use the following elements for user input:
- [Slider](https://docs.streamlit.io/develop/api-reference/widgets/st.slider)
```yaml
type: slider                    # Use 'slider'.
label: "Difficulty"             # Label that will be displayed to the user.
min_value: -10                  # Minimum value (int). Default: 0.
max_value: 20                   # Maximum value (int). Default: 10.
default: 8                      # Default value (int). Default: 0.
```

- [Text input](https://docs.streamlit.io/develop/api-reference/widgets/st.text_input)
```yaml
type: text_input                # Use 'text_input'.
label: "Grasped object"         # Label that will be displayed to the user.
default: "apple"                # Default value (str). Default: "".
```

### 2. Using Code

For users who prefer a programmatic approach, the OpenTouch Interface also allows direct interaction through code.

You can instantiate sensors and configure them using a config file. Here’s how to run an example script that produces a continuous video stream from a touch sensor:

```bash
python examples/simple/demo.py
```

By default, this script uses the [`digit.yaml`](examples/simple/conf/sensor/digit.yaml) config file. You can modify this in the [`config.yaml`](examples/simple/conf/config.yaml) or specify a different config file via the terminal:

```bash
python examples/simple/demo.py sensor=<your-yaml-config>
```

As the interface internally uses Hydra, all attributes in the config file can be modified via the terminal. For instance, to update the serial ID of your Digit sensor, run:

```bash
python examples/simple/demo.py sensor=digit sensor.serial_id=<your-serial-id>
```

#### Features

For a complete overview of features, refer to the methods defined in the [`TouchInterface`](opentouch_interface/interface/touch_sensor.py) class. To understand the underlying implementation, check out the specific sensor classes, such as the [`Digit`](opentouch_interface/interface/sensors/digit.py).

#### Limitations

Currently, the code interface does not support grouping of multiple sensors, data annotations or the replay of recorded data.
For that, please use the dashboard.

## Limitations

- **No Grouping in Code Interface**: The code interface currently does not support the grouping of multiple sensors.
- **Limited Data Annotation and Replay**: Data annotations and replay of recorded data are only available through the dashboard.

---

## Contribution
If you want to contribute to OpenTouch Interface, you can find an explanation on how to do so [here](CONTRIBUTING.md).

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
