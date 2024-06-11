import logging

import hydra
from opentouch_interface.opentouch_interface import OpentouchInterface
from opentouch_interface.options import SetOptions, Streams
from omegaconf import DictConfig

# Configure logging to capture debug messages (optional)
logging.basicConfig(level=logging.DEBUG)


@hydra.main(version_base=None, config_path='conf', config_name='config')
def run(cfg: DictConfig):

    # Create a sensor object
    sensor = OpentouchInterface(OpentouchInterface.SensorType[cfg.sensor.type])

    # Initialize the sensor with name and serial ID
    sensor.initialize(name=cfg.sensor.name, serial=cfg.sensor.serial_id)

    # Connect to the sensor
    sensor.connect()

    # Set lighting intensity
    sensor.set(SetOptions.INTENSITY, value=cfg.sensor.lighting)

    # Set camera resolution and frame rate
    sensor.set(SetOptions.RESOLUTION, value=cfg.sensor.resolution)
    sensor.set(SetOptions.FPS, value=cfg.sensor.fps)

    # Display a video stream of the sensor data
    sensor.show(Streams[cfg.sensor.stream])

    # Close the connection to the sensor
    sensor.close()


if __name__ == '__main__':
    run()
