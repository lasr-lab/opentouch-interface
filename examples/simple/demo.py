import logging

import hydra
from opentouch_interface.interface.opentouch_interface import OpentouchInterface
from omegaconf import DictConfig

# Configure logging to capture debug messages (optional)
logging.basicConfig(level=logging.DEBUG)


@hydra.main(version_base=None, config_path='conf', config_name='config')
def run(cfg: DictConfig):

    # Create a sensor object
    sensor = OpentouchInterface(config=cfg)

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
    sensor.show(attr=sensor.config.stream, recording=sensor.config.recording)

    # Close the connection to the sensor
    sensor.disconnect()


if __name__ == '__main__':
    run()
