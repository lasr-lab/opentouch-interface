import logging

import hydra
from opentouch_interface.opentouch_interface import OpentouchInterface
from opentouch_interface.options import SetOptions, Streams
from opentouch_interface.touch_sensor import TouchSensor
from omegaconf import DictConfig

# Configure logging to capture debug messages (optional)
logging.basicConfig(level=logging.DEBUG)


@hydra.main(version_base=None, config_path='conf', config_name='config')
def run(cfg: DictConfig):

    # Create a sensor object
    sensor = OpentouchInterface(TouchSensor.SensorType[cfg.sensor.type])

    # Initialize the sensor with name, serial ID and path for reading and storing sensor data
    sensor.initialize(name=cfg.sensor.name, serial=cfg.sensor.serial_id, path=cfg.sensor.path)

    # Connect to the sensor
    sensor.connect()

    # Calibrate sensor
    sensor.calibrate()

    # Set lighting intensity
    sensor.set(SetOptions.INTENSITY, value=cfg.sensor.lighting)

    # Set camera resolution and frame rate
    sensor.set(SetOptions.RESOLUTION, value=cfg.sensor.resolution)
    sensor.set(SetOptions.FPS, value=cfg.sensor.fps)

    # Display information about sensor
    sensor.info()

    # Display a video stream of the sensor data
    sensor.show(attr=Streams[cfg.sensor.stream], recording=cfg.sensor.recording)

    # Close the connection to the sensor
    sensor.disconnect()


if __name__ == '__main__':
    run()
