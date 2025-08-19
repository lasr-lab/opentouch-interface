# This class is based on Meta's Digit360 project (https://github.com/facebookresearch/digit360),
# which is licensed under the Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) license.
# Please ensure compliance with the license terms when using or modifying this code.
import struct
import time
import warnings
from dataclasses import asdict, dataclass
from typing import Any

import betterproto
import cv2
import numpy as np
import pyudev
import serial
from cobs import cobs


class LightingChannel(betterproto.Enum):
    CHANNEL_NONE = 0
    CHANNEL_1 = 1
    CHANNEL_2 = 2
    CHANNEL_3 = 3
    CHANNEL_4 = 4
    CHANNEL_5 = 5
    CHANNEL_6 = 6
    CHANNEL_7 = 7
    CHANNEL_8 = 8
    CHANNEL_ALL = 9
    CHANNEL_1ST_HALF = 10
    CHANNEL_2ND_HALF = 11
    CHANNEL_ALL_RESET = 12


class ImuDataType(betterproto.Enum):
    NONE_IMU = 0
    ACC = 1
    GYRO = 2
    MAG = 3
    QUAT = 4
    EULER = 5
    AUX_IMU = 6


class ResetType(betterproto.Enum):
    NONE_RESET = 0
    ICS_BOOTLOADER = 1
    MCU_RESET = 2
    NCU_RESET = 3
    MCU_BOOTLOADER = 4


class PressureConfigTypes(betterproto.Enum):
    NONE_PRESSURE_CONFIG = 0
    OVERSAMPLING_1X = 1
    OVERSAMPLING_2X = 2
    OVERSAMPLING_4X = 3
    OVERSAMPLING_8X = 4
    OVERSAMPLING_16X = 5
    OVERSAMPLING_32X = 6
    OVERSAMPLING_64X = 7
    OVERSAMPLING_128X = 8
    IIR_FILTER_BYPASS = 9
    IIR_FILTER_COEFF_1 = 10
    IIR_FILTER_COEFF_3 = 11
    IIR_FILTER_COEFF_7 = 12
    IIR_FILTER_COEFF_15 = 13
    IIR_FILTER_COEFF_31 = 14
    IIR_FILTER_COEFF_63 = 15
    IIR_FILTER_COEFF_127 = 16


@dataclass(eq=False, repr=False)
class LightingControl(betterproto.Message):
    alpha: float = betterproto.float_field(1)
    channel: "LightingChannel" = betterproto.enum_field(2)
    r: int = betterproto.int32_field(3)
    g: int = betterproto.int32_field(4)
    b: int = betterproto.int32_field(5)


@dataclass(eq=False, repr=False)
class PressureControl(betterproto.Message):
    osr_t: "PressureConfigTypes" = betterproto.enum_field(2)
    osr_p: "PressureConfigTypes" = betterproto.enum_field(3)
    iir_t: "PressureConfigTypes" = betterproto.enum_field(4)
    iir_p: "PressureConfigTypes" = betterproto.enum_field(5)
    shadow_iir_t_enable: bool = betterproto.bool_field(6)
    shadow_iir_p_enable: bool = betterproto.bool_field(7)


@dataclass(eq=False, repr=False)
class RawImuData(betterproto.Message):
    sensor_: "ImuDataType" = betterproto.enum_field(1)
    ts_ght: int = betterproto.uint64_field(2)
    x: float = betterproto.float_field(3)
    y: float = betterproto.float_field(4)
    z: float = betterproto.float_field(5)


@dataclass(eq=False, repr=False)
class EulerData(betterproto.Message):
    ts_ght: int = betterproto.uint64_field(1)
    heading: float = betterproto.float_field(2)
    pitch: float = betterproto.float_field(3)
    roll: float = betterproto.float_field(4)


@dataclass(eq=False, repr=False)
class QuatData(betterproto.Message):
    ts_ght: int = betterproto.uint64_field(1)
    x: float = betterproto.float_field(2)
    y: float = betterproto.float_field(3)
    z: float = betterproto.float_field(4)
    w: float = betterproto.float_field(5)
    accuracy: float = betterproto.float_field(6)


@dataclass(eq=False, repr=False)
class ImuData(betterproto.Message):
    ts: int = betterproto.uint32_field(1)
    raw: "RawImuData" = betterproto.message_field(2, group="imu_type")
    euler: "EulerData" = betterproto.message_field(3, group="imu_type")
    quat: "QuatData" = betterproto.message_field(4, group="imu_type")


@dataclass(eq=False, repr=False)
class GasHtData(betterproto.Message):
    ts: int = betterproto.uint32_field(2)
    ts_ght: int = betterproto.uint64_field(3)
    temperature: float = betterproto.float_field(4)
    pressure: float = betterproto.float_field(5)
    humidity: float = betterproto.float_field(6)
    gas: float = betterproto.float_field(7)
    gas_index: float = betterproto.float_field(8)


@dataclass(eq=False, repr=False)
class PressureApData(betterproto.Message):
    ts: int = betterproto.uint32_field(1)
    channel_a: bytes = betterproto.bytes_field(2)
    channel_b: bytes = betterproto.bytes_field(3)


@dataclass(eq=False, repr=False)
class PressureData(betterproto.Message):
    ts: int = betterproto.uint32_field(1)
    pressure: float = betterproto.float_field(2)
    temperature: float = betterproto.float_field(3)


@dataclass(eq=False, repr=False)
class SystemData(betterproto.Message):
    version_minor: int = betterproto.int32_field(1)
    version_major: int = betterproto.int32_field(2)
    status: int = betterproto.int32_field(3)
    reset: "ResetType" = betterproto.enum_field(4)


@dataclass(eq=False, repr=False)
class Digit360Message(betterproto.Message):
    system_data: "SystemData" = betterproto.message_field(1, group="type")
    pressure_data: "PressureData" = betterproto.message_field(2, group="type")
    pressure_ap_data: "PressureApData" = betterproto.message_field(3, group="type")
    gasht_data: "GasHtData" = betterproto.message_field(4, group="type")
    imu_data: "ImuData" = betterproto.message_field(5, group="type")
    pressure_control: "PressureControl" = betterproto.message_field(6, group="type")
    lighting_control: "LightingControl" = betterproto.message_field(7, group="type")


@dataclass
class Digit360Descriptor:
    serial: str
    data: str
    audio: str
    ics: str
    base_version: str
    ics_version: str


class Digit360:
    # def __init__(self, port: str, port_timeout: float = None) -> None:
    def __init__(self, descriptor: Digit360Descriptor, port_timeout: float = None) -> None:
        self.overruns = 0  # Tracks the number of errors due to IndexError or KeyError while decoding
        self.tlc = 0  # Total life count of successfully processed packets
        self.cerr = 0  # Counts the number of COBS decoding errors encountered

        self._device_buffer = bytearray()  # A buffer to temporarily store incoming data from the device
        self._dev: serial.Serial | None = None  # Serial device instance, initialized later when connecting

        self.port = descriptor.data  # Serial port identifier
        self.port_timeout = port_timeout  # Timeout setting for the serial port (None means no timeout)
        self.ics = descriptor.ics

        if self.ics == '':
            raise ValueError("ICS must not be empty")

        self._camera: cv2.VideoCapture | None = None

        self.connect()

    def connect(self) -> None:
        self._dev = serial.Serial(self.port, timeout=self.port_timeout)
        if not self._dev.is_open:
            raise IOError(f"Unable to access device at {self.port}!")
        self._dev.reset_input_buffer()

        self._camera = cv2.VideoCapture(self.ics)

        if not self._camera or not self._camera.isOpened():
            warnings.warn("Digit360 camera is not found!", UserWarning)

    def get_frame(self, max_retries=3) -> np.ndarray | None:
        """
        Returns a single sensors frame for the device
        """
        retries = 0  # Counter for the number of reconnection attempts

        while retries <= max_retries:
            ret, frame = self._camera.read()
            if frame is not None:
                # Crop frame
                top_border = 0
                bottom_border = 30
                left_border = 295
                right_border = 295

                frame = frame[top_border:frame.shape[0] - bottom_border, left_border:frame.shape[1] - right_border]

                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                # Reconnect the camera immediately
                self._camera.release()
                self._camera = cv2.VideoCapture(self.ics)
                retries += 1

                warnings.warn(f'Reconnecting camera: attempt {retries} of {max_retries}', UserWarning)

                if not self._camera.isOpened():
                    warnings.warn('Failed to reconnect to the camera.', UserWarning)

        warnings.warn(f'Failed to reconnect after {max_retries} attempts. Returning None.', UserWarning)
        return None

    def _read_device(self) -> bytearray:
        i = self._device_buffer.find(b"\x00")
        if i >= 0:
            r = self._device_buffer[: i + 1]
            self._device_buffer = self._device_buffer[i + 1:]
            return r
        while True:
            i = max(1, min(2048, self._dev.in_waiting))
            data = self._dev.read(i)
            i = data.find(b"\x00")
            if i >= 0:
                r = self._device_buffer + data[: i + 1]
                self._device_buffer[0:] = data[i + 1:]
                return r
            else:
                self._device_buffer.extend(data)

    def read(self) -> Digit360Message:
        data = self._read_device()
        data = self.decode(data)
        return data

    def decode(self, data: bytes) -> Digit360Message:
        cobs_data = data.split(b"\x00", 1)[0]
        digit360_frame = Digit360Message()

        try:
            pb_data = cobs.decode(cobs_data)
            digit360_frame = digit360_frame.parse(pb_data)
            self.tlc += 1
        except cobs.DecodeError:
            self._dev.reset_input_buffer()
            self.cerr += 1
            # print("cobs decode error:", self.tlc)
        except (IndexError, KeyError):  # as e:
            self._dev.reset_input_buffer()
            self.overruns += 1
            # error_type = type(e).__name__.lower()
            # print(f"{error_type} error:", self.tlc)
        except struct.error:
            self._dev.reset_input_buffer()

        return digit360_frame

    def send(self, data: bytes) -> None:
        self._dev.write(bytes(data))
        self._dev.flush()

    @property
    def is_open(self) -> bool:
        return self._dev.is_open

    @staticmethod
    def _find_subsystems(context: pyudev.Context, descriptor: Digit360Descriptor) -> None:
        for child in context.children:
            subsystem = child.subsystem

            if subsystem == "tty":
                descriptor.data = child.properties.get("DEVNAME")
                descriptor.base_version = child.properties.get("ID_REVISION")

            elif subsystem == "sound" and "card" in child.sys_name:
                dev_name = f"hw:{child.sys_name[4:]},0"
                descriptor.audio = dev_name

            elif subsystem == "video4linux" and int(child.attributes.get("index", 0)) == 0:
                descriptor.ics = child.properties.get("DEVNAME")
                descriptor.ics_version = child.properties.get("ID_REVISION")

    @staticmethod
    def get_digit360_devices() -> list[Digit360Descriptor]:
        context = pyudev.Context()
        devices = context.list_devices(subsystem="usb", ID_MODEL="DIGIT360_Hub")
        digit360_serials = {d.properties["ID_SERIAL_SHORT"] for d in devices}

        digit360_devices = {
            serial_id: Digit360Descriptor(serial_id, "", "", "", "", "")
            for serial_id in digit360_serials
        }

        for dev in devices:
            serial_id = dev.properties["ID_SERIAL_SHORT"]
            Digit360._find_subsystems(dev, digit360_devices[serial_id])

        digit360_devices_sorted = sorted(digit360_devices.values(), key=lambda x: x.serial)

        return digit360_devices_sorted

    @staticmethod
    def get_digit360_by_serial(devices: list[Digit360Descriptor], serial_id: str) -> Digit360Descriptor | None:
        try:
            return next(device for device in devices if device.serial == serial_id)
        except StopIteration:
            return None

    @staticmethod
    def get_digit360_by_hand(devices: list[Digit360Descriptor], hand_cfg: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"name": finger, "parameters": cfg.params, "descriptor": digit360}
            for finger, cfg in hand_cfg.items()
            if (digit360 := Digit360.get_digit360_by_serial(devices, cfg.serial))
        ]

    @staticmethod
    def is_digit360_desc_valid(desc: Digit360Descriptor) -> bool:
        return all(value != "" for value in asdict(desc).values())

    def led_all_off(self) -> None:
        lighting_msg = LightingControl(channel=LightingChannel.CHANNEL_ALL_RESET)
        msg = Digit360Message(lighting_control=lighting_msg)

        if self.is_open:
            self.send(msg)
            time.sleep(0.001)

    def led_set_channel(self, channel: int, rgb: tuple) -> Digit360Message:
        lighting_msg = LightingControl()
        lighting_msg.channel = channel
        lighting_msg.r = rgb[0]
        lighting_msg.g = rgb[1]
        lighting_msg.b = rgb[2]

        msg = Digit360Message(lighting_control=lighting_msg)

        if self.is_open:
            self.send(msg)

        return msg

    def disconnect(self):
        self._camera.release()
        self._dev.close()
