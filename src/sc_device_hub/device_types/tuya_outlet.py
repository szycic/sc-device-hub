from __future__ import annotations

import asyncio
from typing import Any

from sc_device_hub.models import Device, DeviceState
from sc_device_hub.integrations.tuya import TuyaControlError, TuyaDevice
from sc_device_hub.utils import ping_host


class TuyaOutletHandler:
  """
  Handler for ``tuya_outlet`` devices.

  toggle  – sends on/off command via Tuya Cloud.
  refresh – pings the device IP for connectivity *and* queries the Tuya Cloud
            for the current switch state (is_on).
  """

  async def toggle(self, device: Device) -> dict[str, Any]:
    tuya_device = TuyaDevice(
      name=device.name,
      tuya_device_id=device.tuya_device_id,
      is_on=device.is_on,
    )
    # TuyaControlError propagates to api.py which maps it to HTTP 400
    action = await asyncio.to_thread(tuya_device.toggle)
    return {
      "is_on": tuya_device.is_on,
      "last_action": action,
      "last_message": action,
    }

  async def refresh(self, device: Device) -> dict[str, Any]:
    updates: dict[str, Any] = {}

    # 1. Ping IP for network reachability
    if device.ip_address:
      reachable, ping_msg = await ping_host(device.ip_address)
      updates["state"] = DeviceState.online if reachable else DeviceState.offline

    # 2. Query Tuya Cloud for current switch state
    try:
      tuya_device = TuyaDevice(
        name=device.name,
        tuya_device_id=device.tuya_device_id,
        is_on=device.is_on,
      )
      await asyncio.to_thread(tuya_device.refresh)
      updates["is_on"] = tuya_device.is_on
    except TuyaControlError:
      pass

    from datetime import datetime
    time_str = datetime.now().strftime("%H:%M:%S")
    updates["last_message"] = f"Refreshed at {time_str}"
    return updates
