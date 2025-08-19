# This file contains all registries related to decorators

class SensorClassRegistry:
    _sensors = {}

    @classmethod
    def register_sensor(cls, name: str):
        # print(f"Registered sensor {name}")

        def decorator(sensor_cls):
            cls._sensors[name] = sensor_cls
            return sensor_cls

        return decorator

    @classmethod
    def get_sensor(cls, name: str):
        return cls._sensors.get(name, None)

    @classmethod
    def get_sensors(cls):
        return cls._sensors.values()

    @classmethod
    def get_sensor_names(cls):
        return cls._sensors.keys()


class ConfigClassRegistry:
    _configs = {}

    @classmethod
    def register_config(cls, name: str):
        # print(f"Registered config {name}")

        def decorator(validator_cls):
            cls._configs[name] = validator_cls
            return validator_cls

        return decorator

    @classmethod
    def get_config(cls, name: str):
        return cls._configs.get(name, None)

    @classmethod
    def get_configs(cls):
        return cls._configs

    @classmethod
    def get_config_names(cls):
        return cls._configs.keys()


class WidgetConfigRegistry:
    _widgets = {}

    @classmethod
    def register_widget(cls, name: str):
        # print(f"Registered widget config {name}")

        def decorator(widget_cls):
            cls._widgets[name] = widget_cls
            return widget_cls

        return decorator

    @classmethod
    def get_config(cls, name: str):
        return cls._widgets.get(name, None)

    @classmethod
    def get_configs(cls):
        return cls._widgets

    @classmethod
    def get_widget_names(cls):
        return list(cls._widgets.keys())


class ViewerClassRegistry:
    _viewers = {}

    @classmethod
    def register_viewer(cls, name: str):
        # print(f"Registered viewer {name}")

        def decorator(view_cls):
            cls._viewers[name] = view_cls
            return view_cls

        return decorator

    @classmethod
    def get_viewer(cls, name: str):
        return cls._viewers.get(name, None)

    @classmethod
    def get_viewers(cls):
        return cls._viewers

    @classmethod
    def get_viewer_names(cls):
        return cls._viewers.keys()


class SensorFormRegistry:
    _forms = {}

    @classmethod
    def register_form(cls, name: str):
        # print(f'Registered form {name}')

        def decorator(form_cls):
            cls._forms[name] = form_cls

            # Add sensor_type to validator_cls
            form_cls.sensor_type = name

            return form_cls

        return decorator

    @classmethod
    def get_form(cls, name: str):
        return cls._forms.get(name, None)

    @classmethod
    def get_form_names(cls):
        return cls._forms.keys()


class DataClassRegistry:
    _data_classes = {}

    @classmethod
    def register(cls, name: str | list):
        # print(f"Registered data class {cls.__name__}")

        def decorator(data_cls):
            sensor_names = name if isinstance(name, list) else [name]
            for sensor_name in sensor_names:
                key = f'{sensor_name}.{data_cls.__name__}'
                cls._data_classes[key] = data_cls
            return data_cls

        return decorator

    @classmethod
    def get(cls, sensor_name: str, class_name: str):
        key = f'{sensor_name}.{class_name}'
        return cls._data_classes.get(key, None)


class SerializerClassRegistry:
    _serializers = {}

    @classmethod
    def register(cls, sensor_type: str):
        """Decorator to register a sensor serializer class."""

        def decorator(serializer_cls):
            cls._serializers[sensor_type] = serializer_cls
            return serializer_cls

        return decorator

    @classmethod
    def get_serializer(cls, sensor_type: str):
        return cls._serializers.get(sensor_type, None)
