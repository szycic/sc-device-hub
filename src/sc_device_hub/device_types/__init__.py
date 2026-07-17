"""
Registration registry for mapping device types to their respective device handlers.
"""
from __future__ import annotations

from sc_device_hub.models import DeviceType
from sc_device_hub.device_types.base import DeviceHandler
from sc_device_hub.device_types.tuya_outlet import TuyaOutletHandler
from sc_device_hub.device_types.ping_device import PingDeviceHandler
from sc_device_hub.device_types.manual import ManualDeviceHandler

_registry: dict[DeviceType, DeviceHandler] = {
  DeviceType.tuya_outlet: TuyaOutletHandler(),
  DeviceType.ping_device: PingDeviceHandler(),
  DeviceType.manual: ManualDeviceHandler(),
}


def get_handler(device_type: DeviceType) -> DeviceHandler:
  """Return the handler for the given device type."""
  try:
    return _registry[device_type]
  except KeyError:
    raise NotImplementedError(f"No handler registered for device type: {device_type!r}")
