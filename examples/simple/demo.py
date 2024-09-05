import logging
# import time

import hydra

from opentouch_interface.interface.dataclasses.validation.validator import Validator
from opentouch_interface.interface.opentouch_interface import OpentouchInterface
from omegaconf import OmegaConf, DictConfig

# Configure logging to capture debug messages (optional)
logging.basicConfig(level=logging.DEBUG)


@hydra.main(version_base=None, config_path='conf', config_name='config')
def run(cfg: DictConfig):

    # Use a validator to make sure the sensor config is valid
    _, _, sensors, _validator = Validator(file=dict(OmegaConf.to_container(cfg, resolve=True))).validate()
    sensor_config = sensors[0]

    # Create a sensor object
    sensor = OpentouchInterface(config=sensor_config)

    # Initialize the sensor
    sensor.initialize()

    # Connect to the sensor
    sensor.connect()

    # Calibrate sensor
    sensor.calibrate()

    # Set lighting intensity
    # sensor.set(SensorSettings.INTENSITY, value=0)

    # Display information about sensor
    sensor.info()

    # Display a video stream of the sensor data
    sensor.show(attr=sensor.config.stream)

    # You can also record your sensor data.
    # However, it is recommended doing so by using the dashboard as right now you can't specify meta-data.

    # sensor.path = "test.touch"
    # sensor.start_recording()
    # time.sleep(5)
    # sensor.stop_recording()

    # Close the connection to the sensor
    sensor.disconnect()


if __name__ == '__main__':
    run()
