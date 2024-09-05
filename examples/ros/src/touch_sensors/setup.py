from setuptools import setup

package_name = 'touch_sensors'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    description='Simple example for two ROS 2 nodes communicating touch sensor data',
    license='LICENCE',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'talker = touch_sensors.publisher:main',
            'listener = touch_sensors.subscriber:main',
        ],
    },
)
