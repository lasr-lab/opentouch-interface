import logging

from opentouch_interface.opentouch_interface import OpentouchInterface
from opentouch_interface.options import SetOptions, Streams
from digit_interface.digit import Digit

# Configure logging to capture debug messages (optional)
logging.basicConfig(level=logging.DEBUG)

# Create a Digit sensor object
sensor = OpentouchInterface(OpentouchInterface.SensorType.DIGIT)

# Initialize the Digit device with name and serial ID
sensor.initialize("Left Gripper", "D20804")

# Connect to the Digit device
sensor.connect()

# Set lighting intensity to minimum
sensor.set(SetOptions.INTENSITY, Digit.LIGHTING_MIN)

# Set lighting intensity to maximum
sensor.set(SetOptions.INTENSITY, Digit.LIGHTING_MAX)

# Set camera resolution to QVGA and frame rate to 30fps
sensor.set(SetOptions.RESOLUTION, Digit.STREAMS["QVGA"])
sensor.set(SetOptions.FPS, Digit.STREAMS["QVGA"]["fps"]["30fps"])

# Display a video stream of the Digit sensor data
sensor.show(Streams.FRAME)

# Close the connection to the Digit device
sensor.close()
