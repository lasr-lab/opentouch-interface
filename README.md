
# OpenTouch Interface

The OpenTouch Interface is a Python package designed to provide a unified interface for various touch sensors. It simplifies the process of interacting with touch sensors by providing a consistent API regardless of the specific sensor being used.

We also provide an easy-to-use web interface that lets you connect to the sensors and show their data stream without the need to code.

---

## Features

We currently offer a simple and unified API and web interface for the following touch sensors: 
- [Digit](https://digit.ml/)
- [GelSight Mini](https://www.gelsight.com/gelsightmini/)

## Installation

To install OpenTouch Interface, follow these steps:

```bash
git clone https://github.com/lasr-lab/opentouch-interface
cd opentouch-interface
pip install .
```

Additionally, depending on the specific sensors you are using, make sure you have all their necessary libraries installed by checking the installation guides of the respective sensors ([Digit](https://github.com/lasr-lab/digit-interface), [GelSight Mini](https://github.com/gelsightinc/gsrobotics)) or by following this quick installation guide:

- ### Digit

```bash
pip install digit-interface
```

- ### GelSight Mini

```bash
pip install git+ssh://git@github.com/gelsightinc/gsrobotics.git
```

## Web Interface

To start the web interface, run:

```bash
opentouch-dashboard
```
If errors occur, we recommend physically reconnecting your sensors as well as restarting the Streamlit application.

## Examples

### Simple Example

The script located at `examples/simple/demo.py` produces a continuous video stream from a touch sensor. For that, install the following requirements:

```bash
pip install hydra-core omegaconf --upgrade
```

To run this example, execute:

```bash
python examples/simple/demo.py
```

By default, the script uses the Digit sensor. However, you can specify a different sensor by providing an argument (`digit` or `gelsight_mini`). For example:

```bash
python examples/simple/demo.py sensor=gelsight_mini
```

Sensor settings can be customized in the corresponding `.yaml` file located in `examples/conf/sensor`. Note that not all sensors support every setting. Unsupported settings should be set to `null`.

For sensors that require a serial ID for their setup (e.g., the Digit), make sure to enter your serial ID in `examples/conf/sensor/<your-sensor>.yaml`.

### ROS2 Example (Work in Progress)

We are providing a ROS2 example. You can find the code and detailed instructions in `examples/ros/README.md`.