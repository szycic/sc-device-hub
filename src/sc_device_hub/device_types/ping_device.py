from __future__ import annotations

from typing import Any

from sc_device_hub.models import Device, DeviceState
from sc_device_hub.utils import ping_host


class PingDeviceHandler:
  """
  Handler for ``ping_device`` devices.

  toggle  – no real action (ping devices have no controllable switch).
  refresh – pings the device IP to determine online/offline state.
  """

  async def toggle(self, device: Device) -> dict[str, Any]:
    message = f"{device.name} does not support toggling"
    return {
      "last_action": message,
      "last_message": message,
    }

  async def refresh(self, device: Device) -> dict[str, Any]:
    if not device.ip_address:
      return {"last_message": "No IP address configured – cannot ping"}

    reachable, message = await ping_host(device.ip_address)
    from datetime import datetime
    time_str = datetime.now().strftime("%H:%M:%S")
    return {
      "state": DeviceState.online if reachable else DeviceState.offline,
      "last_message": f"Refreshed at {time_str}",
    }
