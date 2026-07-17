from __future__ import annotations

import json
import os
import uuid
from dotenv import load_dotenv
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

load_dotenv()

class DeviceType(str, Enum):
  tuya_outlet = "tuya_outlet"
  ping_device = "ping_device"
  manual = "manual"


class DeviceStatus(str, Enum):
  online = "online"
  offline = "offline"
  unknown = "unknown"


@dataclass(slots=True)
class Device:
  """
  Data model representing a device in the hub, containing its details,
  reachability status, and power state.
  """
  name: str
  type: DeviceType
  ip_address: str | None = None
  tuya_device_id: str | None = None
  is_on: bool = False
  status: DeviceStatus = DeviceStatus.unknown
  last_seen: str | None = None
  last_action: str | None = None
  last_message: str | None = None
  id: str = field(default_factory=lambda: uuid.uuid4().hex)

  def to_payload(self) -> dict[str, Any]:
    """
    Serialize the Device model instance to a JSON-compatible dictionary payload.
    """
    payload = asdict(self)
    payload["type"] = self.type.value
    payload["status"] = self.status.value
    payload["can_toggle"] = self.can_toggle
    return payload

  @property
  def can_toggle(self) -> bool:
    """
    Determine if this device type supports power toggling commands.
    """
    return self.type is DeviceType.tuya_outlet


class DeviceStore:
  """
  An in-memory store for managing device models.
  """
  def __init__(self) -> None:
    self._devices: dict[str, Device] = {}

  def list(self) -> list[Device]:
    """
    List all devices registered in the store.
    """
    return list(self._devices.values())

  def get(self, device_id: str) -> Device:
    """
    Retrieve a specific device by its ID.
    """
    try:
      return self._devices[device_id]
    except KeyError as exc:
      raise KeyError(device_id) from exc

  def add(self, device: Device) -> Device:
    """
    Add a new device to the store.
    """
    self._devices[device.id] = device
    return device

  def update(self, device_id: str, **changes: Any) -> Device:
    """
    Update field values on a registered device in the store.
    """
    device = self.get(device_id)
    for key, value in changes.items():
      if hasattr(device, key):
        setattr(device, key, value)
    return device

  def delete(self, device_id: str) -> None:
    """
    Remove a device from the store.
    """
    del self._devices[device_id]


store = DeviceStore()


def seed_devices() -> None:
  if store.list():
    return

  json_path = os.getenv("DEVICES_JSON_PATH", "devices.json")

  # If devices.json does not exist, copy from devices.json.sample if available
  if not os.path.exists(json_path):
    sample_path = "devices.json.sample"
    if os.path.exists(sample_path):
      try:
        with open(sample_path, "r") as sf:
          content = sf.read()
        with open(json_path, "w") as df:
          df.write(content)
      except Exception:
        pass

  if not os.path.exists(json_path):
    data = [
      {
        "name": "Tuya Outlet",
        "type": "tuya_outlet",
        "ip_address": "<tuya_outlet_ip_address>",
        "tuya_device_id": "<tuya_device_id>"
      },
      {
        "name": "Local Ping Device",
        "type": "ping_device",
        "ip_address": "127.0.0.1"
      }
    ]
  else:
    try:
      with open(json_path, "r") as f:
        data = json.load(f)
    except Exception as exc:
      print(f"Error loading {json_path}: {exc}")
      return

  if not isinstance(data, list):
    print("Invalid devices.json structure (expected a JSON array)")
    return

  for item in data:
    if not isinstance(item, dict):
      continue
    name = item.get("name")
    type_str = item.get("type")
    if not name or not type_str:
      continue
    try:
      device_type = DeviceType(type_str)
    except ValueError:
      continue

    dev_id = item.get("id")
    if not dev_id:
      # Generate deterministic UUID based on name
      dev_id = uuid.uuid5(uuid.NAMESPACE_DNS, name).hex
      
    device = Device(
      id=dev_id,
      name=name,
      type=device_type,
      ip_address=item.get("ip_address"),
      tuya_device_id=item.get("tuya_device_id"),
      is_on=item.get("is_on", False),
      status=DeviceStatus(item.get("status") or item.get("state") or "unknown"),
      last_seen=item.get("last_seen"),
      last_action=item.get("last_action"),
      last_message=item.get("last_message")
    )
    store.add(device)