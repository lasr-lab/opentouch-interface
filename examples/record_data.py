import logging
import os
import pprint
import time

import hydra
from omegaconf import OmegaConf, DictConfig

from opentouch_interface.core.sensor_group import SensorGroup

# Configure logging to capture debug messages (optional)
logging.basicConfig(level=logging.DEBUG)


# Run `python demo.py`
# To change the config (e.g. to gelsight), run `python demo.py --config-name gelsight.yaml`

@hydra.main(config_path=os.path.join(os.path.dirname(__file__), "config"), config_name='digit.yaml', version_base='1.4')
def run(cfg: DictConfig):
    config = OmegaConf.to_container(cfg, resolve=True)
    sensor_group = SensorGroup(config=config)

    # Add metadata (e.g., data of recording) to payload
    sensor_group.payload.add({
        'type': 'text_input',
        'label': 'time',
        'default': str(time.time())
    })

    # Retrieve and configure a specific sensor by name
    digit = sensor_group.get_sensor('First Gripper')
    digit.set('rgb', [0, 0, 15])

    # Record data
    sensor_group.start_recording()
    time.sleep(2)  # Simulate workload
    sensor_group.stop_recording()

    # Display the current group configuration
    config = sensor_group.get_config()
    pprint.pprint(config)

    # Or simply use:
    sensor_group.info()

    # Set a new recording path before starting another recording session
    new_path = 'my_recording'
    if sensor_group.set_destination(new_path):
        # Record data
        sensor_group.start_recording()
        time.sleep(1)  # Simulate workload
        sensor_group.stop_recording()

    # Disconnect all sensors to safely terminate
    sensor_group.disconnect()


if __name__ == '__main__':
    run()
