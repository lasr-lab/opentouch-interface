import pkgutil
import importlib

from opentouch_interface.core.validation.sensors import __path__ as config_path
from opentouch_interface.dashboard.forms import __path__ as forms_path
from opentouch_interface.core.sensors import __path__ as sensors_path
from opentouch_interface.dashboard.viewers.sensors import __path__ as viewers_path
from opentouch_interface.core.validation.streamlit import __path__ as widgets_path
from opentouch_interface.core.serialization import __path__ as serializers_path


# Helper function to dynamically import and register classes
def import_all_classes(package_path, package_name):
    for module_info in pkgutil.iter_modules(package_path):
        module_name = f"{package_name}.{module_info.name}"
        importlib.import_module(module_name)


# Import all config classes
import_all_classes(config_path, 'opentouch_interface.core.validation.sensors')

# Import all form classes
import_all_classes(forms_path, "opentouch_interface.dashboard.forms")

# Import all sensor classes
import_all_classes(sensors_path, "opentouch_interface.core.sensors")

# Import all viewer classes
import_all_classes(viewers_path, "opentouch_interface.dashboard.viewers.sensors")

# Import all streamlit widget validator classes
import_all_classes(widgets_path, "opentouch_interface.core.validation.streamlit")

# Import all serialization classes
import_all_classes(serializers_path, "opentouch_interface.core.serialization")
