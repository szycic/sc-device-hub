from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from sc_device_hub.models import Device


@runtime_checkable
class DeviceHandler(Protocol):
  """Common interface every device-type handler must satisfy."""

  async def toggle(self, device: Device) -> dict[str, Any]:
    """
    Perform the toggle action for this device type.

    Returns a dict of field updates to apply to the store
    (e.g. ``{"is_on": True, "last_action": "...", "last_message": "..."}``)
    and raises an appropriate exception on failure.
    """
    ...

  async def refresh(self, device: Device) -> dict[str, Any]:
    """
    Refresh the device's current status.

    Returns a dict of field updates to apply to the store
    (e.g. ``{"status": DeviceStatus.online, "is_on": False, "last_message": "..."}``)
    """
    ...
