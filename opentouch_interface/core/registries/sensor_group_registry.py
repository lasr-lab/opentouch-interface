from opentouch_interface.core.sensor_group import SensorGroup


class SensorGroupRegistry:
    def __init__(self):
        from opentouch_interface.core.sensor_group import SensorGroup
        self.sensor_groups: list[SensorGroup] = []

    def add(self, sensor_group: SensorGroup):
        self.sensor_groups.append(sensor_group)

    def remove(self, sensor_group: SensorGroup):
        self.sensor_groups.remove(sensor_group)
