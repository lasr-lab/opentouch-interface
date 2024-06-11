# OpenTouch Interface

The OpenTouch Interface is a Python package designed to provide a unified interface for various touch sensors. It simplifies the process of interacting with touch sensors by providing a consistent API regardless of the specific sensor being used.

## Features

- Simple and unified API for the following touch sensors: [Digit](https://digit.ml/), [GelSight Mini](https://www.gelsight.com/gelsightmini/).

## Installation

To install OpenTouch Interface, follow these steps:

```bash
git clone https://github.com/lasr-lab/opentouch-interface
cd opentouch-interface
python setup.py install
```

Additionally, make sure you have all necessary libraries installed by checking the installation guides of the respective sensors ([Digit](https://github.com/lasr-lab/digit-interface), [GelSight Mini](https://github.com/gelsightinc/gsrobotics)).

## Examples

### Simple Example
The script located at `examples/simple/demo.py` produces a continuous video stream from a touch sensor. To run this example, execute the following command:
```bash
python examples/simple/demo.py
```

By default, the script uses the Digit sensor. However, you can specify a different sensor by providing an argument (`digit` or `gelsight_mini`). For example:
```bash
python examples/simple/demo.py sensor=gelsight_mini
```

Sensor settings can be customized in the corresponding `.yaml` file located in `examples/conf/sensor`. Note that not all sensors support every setting. Unsupported settings should be set to `null`.

### ROS2 Example (Work in Progress)
We are provide a ROS2 example. You can find the code and detailed instructions at the `examples/ros/README.md`.