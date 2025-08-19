from opentouch_interface.core.registries.class_registries import ViewerClassRegistry
from opentouch_interface.core.sensors.touch_sensor import TouchSensor
from opentouch_interface.dashboard.viewers.base_viewer import BaseViewer


class ViewerFactory:
    """
    Factory class to create viewer instances based on the type of sensor.
    """

    def __new__(cls, sensor: TouchSensor, *args, **kwargs) -> BaseViewer:
        """
        Creates a new viewer instance based on the provided sensor type.
        """
        sensor_type = sensor.get('sensor_type')
        viewer_cls = ViewerClassRegistry.get_viewer(sensor_type)
        if viewer_cls is None:
            raise ValueError(f"Unsupported sensor type: {sensor_type} has no registered viewer")
        return viewer_cls(sensor)
