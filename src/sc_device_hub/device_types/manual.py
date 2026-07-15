from __future__ import annotations

from typing import Any

from sc_device_hub.models import Device


class ManualDeviceHandler:
  """
  Handler for ``manual`` devices.

  toggle  – flips the local is_on flag (no external calls).
  refresh – no-op; manual devices have no automatic status source.
  """

  async def toggle(self, device: Device) -> dict[str, Any]:
    new_state = not device.is_on
    action = f"{device.name} turned {'on' if new_state else 'off'}"
    return {
      "is_on": new_state,
      "last_action": action,
      "last_message": action,
    }

  async def refresh(self, device: Device) -> dict[str, Any]:
    return {"last_message": "Manual device – no automatic refresh available"}
