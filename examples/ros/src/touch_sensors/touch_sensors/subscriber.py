import cv2
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

from cv_bridge import CvBridge
bridge = CvBridge()


class SensorSubscriber(Node):

    def __init__(self):
        super().__init__('sensor_subscriber')
        self.subscription = self.create_subscription(
            Image,
            'touch_sensor_data',
            self.listener_callback,
            10)

        self.call_count = 0
        self.last_time = time.time()

    @staticmethod
    def listener_callback(msg):
        cv_image = bridge.imgmsg_to_cv2(msg, "bgr8")
        cv2.imshow('Digit view', cv_image)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)

    minimal_subscriber = SensorSubscriber()

    rclpy.spin(minimal_subscriber)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
