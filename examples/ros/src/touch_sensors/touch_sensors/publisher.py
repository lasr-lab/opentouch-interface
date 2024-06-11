import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import time

from opentouch_interface.opentouch_interface import OpentouchInterface
from opentouch_interface.options import SetOptions, Streams
from digit_interface.digit import Digit

from cv_bridge import CvBridge
bridge = CvBridge()


class SensorPublisher(Node):

    def __init__(self):
        fps = 30    # Choose only 30 or 60

        super().__init__('sensor_publisher')
        self.publisher_ = self.create_publisher(Image, 'touch_sensor_data', 10)
        self.timer = self.create_timer(1 / Digit.STREAMS["QVGA"]["fps"][f"{fps}fps"], self.timer_callback)

        self.sensor = OpentouchInterface(OpentouchInterface.SensorType.DIGIT)
        self.sensor.initialize("Left Gripper", "D20804")
        self.sensor.connect()
        self.sensor.set(SetOptions.INTENSITY, Digit.LIGHTING_MAX)
        self.sensor.set(SetOptions.RESOLUTION, Digit.STREAMS["QVGA"])
        self.sensor.set(SetOptions.FPS, Digit.STREAMS["QVGA"]["fps"][f"{fps}fps"])

        self.call_count = 0
        self.last_time = time.time()

    def timer_callback(self):
        image = bridge.cv2_to_imgmsg(self.sensor.read(Streams.FRAME), encoding="bgr8")
        self.publisher_.publish(image)


def main(args=None):
    rclpy.init(args=args)

    sensor_publisher = SensorPublisher()

    rclpy.spin(sensor_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    sensor_publisher.destroy_node()
    rclpy.shutdown()
    sensor_publisher.sensor.close()


if __name__ == '__main__':
    main()
