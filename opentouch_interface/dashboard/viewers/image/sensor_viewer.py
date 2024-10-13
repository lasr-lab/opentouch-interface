from typing import Union

from opentouch_interface.dashboard.viewers.image.digit_viewer import DigitViewer
from opentouch_interface.dashboard.viewers.image.file_viewer import FileViewer
from opentouch_interface.dashboard.viewers.image.gelsight_viewer import GelsightViewer

# A type alias that refers to any of the three viewer types
SensorViewer = Union[FileViewer, DigitViewer, GelsightViewer]
