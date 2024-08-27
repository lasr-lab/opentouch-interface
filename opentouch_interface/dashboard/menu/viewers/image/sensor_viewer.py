from typing import TypeAlias, Union

from opentouch_interface.dashboard.menu.viewers.image.digit_viewer import DigitViewer
from opentouch_interface.dashboard.menu.viewers.image.file_viewer import FileViewer
from opentouch_interface.dashboard.menu.viewers.image.gelsight_viewer import GelsightViewer

SensorViewer: TypeAlias = Union[FileViewer, DigitViewer, GelsightViewer]
