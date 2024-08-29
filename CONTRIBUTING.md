# Contributing to OpenTouch Interface

We welcome contributions from everyone, whether you're fixing a bug, adding a new feature, or improving documentation. This document provides guidelines for contributing to the project and outlines the steps needed to add a new sensor to the interface.

## How to Contribute

### Reporting Issues
If you encounter a bug or have a feature request, please open an issue in the [GitHub issue tracker](https://github.com/lasr-lab/opentouch-interface/issues). When reporting a bug, provide as much detail as possible, including steps to reproduce the issue and any relevant logs or screenshots.

### Submitting Code
If you want to contribute code to the project, please follow these steps:

1. **Fork the Repository**: Click the "Fork" button at the top right of the repository page to create your own fork of the project.

2. **Clone Your Fork**: Clone the forked repository to your local machine using:
   ```bash
   git clone https://github.com/<your-username>/opentouch-interface.git
   cd opentouch-interface
   ```

3. **Create a New Branch**: Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature-or-bugfix-name
   ```

4. **Make Your Changes**: Implement your changes in the appropriate files. Make sure to follow the existing code style (**flake8**) and test any new features.

5. **Commit and Push**: Commit your changes with a descriptive message and push them to your forked repository:
   ```bash
   git add .
   git commit -m "Description of your changes"
   git push origin feature-or-bugfix-name
   ```

6. **Create a Pull Request**: Go to the original repository on GitHub and create a pull request from your forked branch. Provide a clear description of your changes and any relevant information.


## Adding a New Sensor to the Interface

These are the core steps necessary to add a new sensor to the interface.
We encourage you
to take inspiration from existing code mainly the digit sensor as it currently is the most feature rich sensor.

### 1. Create a Config Class
First, create a configuration class for your sensor that validates its settings.

1. Navigate to the [`sensors`](opentouch_interface/interface/dataclasses/validation/sensors) directory.
2. Create a new Python file named after your sensor, e.g., `my_sensor_config.py`.
3. Define a configuration class in this file based on pydantic. The following attributes are mandatory:
   ```yaml
   sensor_name: str
   sensor_type: str
   stream: Union[str, DataStream]
   sampling_frequency: int
   recording_frequency: int
   ```

**Example**: [`digit_config.py`](opentouch_interface/interface/dataclasses/validation/sensors/digit_config.py)

### 2. Create Your Sensor Class
Next, implement the sensor's functionality by creating a sensor class.

1. Navigate to the [`sensors`](opentouch_interface/interface/sensors) directory.
2. Create a new Python file for your sensor, e.g., `my_sensor.py`.
3. Implement the sensor class that inherits from the base `TouchSensor` class. This class should define how your sensor interacts with the interface.

**Example**: [`digit.py`](opentouch_interface/interface/sensors/digit.py)

### 3. Add Your Sensor to the Validator
After creating the sensor class, ensure that the interface recognizes the new sensor.

1. Navigate to the [`navigator.py`](opentouch_interface/interface/dataclasses/validation/validator.py) directory.
2. Add your config class to the `def _validate_yaml(self)` method.

### 4. Create a Streamlit Viewer for Your Sensor
Finally, create a viewer for your sensor that can be used in the Streamlit dashboard.

1. Navigate to the [`image`](opentouch_interface/dashboard/menu/viewers/image) directory.
2. Create a new Python file for your sensor's viewer, e.g., `my_sensor_viewer.py`.
3. Implement the viewer class that inherits from the base [`BaseImageViewer`](opentouch_interface/dashboard/menu/viewers/base/image_viewer.py) 

**Examples**:
- Easy example with no settings: [`gelsight_viewer.py`](opentouch_interface/dashboard/menu/viewers/image/gelsight_viewer.py)
- More complex examples with settings to change at runtime: [`digit_viewer.py`](opentouch_interface/dashboard/menu/viewers/image/digit_viewer.py)

### Testing and Documentation
After adding your sensor, test its functionality thoroughly and update the documentation.
Add an example config file of your sensor to [`sensor`](examples/simple/conf/sensor) and explain it in the [`README.md`](README.md).

## Getting Help
If you need help with your contribution, feel free to ask questions in the [GitHub Discussions](https://github.com/lasr-lab/opentouch-interface/discussions)

Thank you for contributing to OpenTouch Interface!
