from __future__ import annotations

import os
import time
from dataclasses import dataclass

import tinytuya
from dotenv import load_dotenv

load_dotenv()

TUYA_ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
TUYA_ACCESS_KEY = os.getenv("TUYA_ACCESS_KEY")

if not TUYA_ACCESS_ID or not TUYA_ACCESS_KEY:
  raise RuntimeError("TUYA_ACCESS_ID and TUYA_ACCESS_KEY must be set in the environment")


class TuyaControlError(RuntimeError):
  """Custom exception raised when Tuya Cloud operations fail."""
  pass


class TuyaClient:
  """
  A client that wraps the tinytuya.Cloud interface to facilitate easy communication
  with the Tuya Cloud platform.
  """
  def __init__(self) -> None:
    self.cloud = tinytuya.Cloud(
      "eu",
      TUYA_ACCESS_ID,
      TUYA_ACCESS_KEY,
    )

  def status(self, device_id: str) -> dict:
    """
    Fetch the current status of a device from the Tuya Cloud.
    """
    return self.cloud.getstatus(device_id)

  def command(self, device_id: str, code: str, value: bool) -> dict:
    """
    Send a command to a specific device on the Tuya Cloud platform.
    """
    return self.cloud.sendcommand(
      device_id,
      {"commands": [{"code": code, "value": value}]},
    )


# Single shared client instance for Tuya platform operations
tuya = TuyaClient()


@dataclass(slots=True)
class TuyaDevice:
  """
  Represents a physical Tuya device instance, providing high-level commands
  such as refresh, toggle, turn_on, and turn_off.
  """
  name: str
  tuya_device_id: str
  is_on: bool = False

  def refresh(self) -> bool:
    """
    Query the Tuya Cloud API to refresh and synchronize the device's local is_on state.
    
    Returns:
        bool: The current switch state of the device (is_on).
    """
    try:
      status = tuya.status(self.tuya_device_id)
      for item in status.get("result", []):
        if item.get("code") == "switch_1":
          self.is_on = item.get("value", False)
          return self.is_on
      raise TuyaControlError("switch_1 status not found")
    except Exception as exc:
      raise TuyaControlError(f"Failed to refresh {self.name}: {exc}") from exc

  def set_state(self, state: bool) -> str:
    """
    Send a command to Tuya Cloud to set the device switch state, and poll the
    cloud status endpoint until the state change propagates and is confirmed.
    
    Args:
        state (bool): The target switch state (True for On, False for Off).
        
    Returns:
        str: A message indicating the successful action.
    """
    try:
      command = tuya.command(self.tuya_device_id, "switch_1", state)
      if not command.get("success"):
        raise TuyaControlError(
          f"Failed to set state for {self.name}: {command.get('msg', 'Unknown error')}"
        )
      
      # Wait/poll for the state change to propagate to Tuya Cloud status endpoint
      for _ in range(5):
        time.sleep(0.3)
        try:
          self.refresh()
          if self.is_on == state:
            break
        except Exception:
          pass

      return f"{self.name} turned {'on' if state else 'off'}"
    except Exception as exc:
      raise TuyaControlError(f"Failed to set state for {self.name}: {exc}") from exc

  def turn_on(self) -> str:
    """Turn the Tuya device switch on."""
    return self.set_state(True)

  def turn_off(self) -> str:
    """Turn the Tuya device switch off."""
    return self.set_state(False)

  def toggle(self) -> str:
    """
    Toggle the switch state of the Tuya device by refreshing the current state
    first and then sending the inverted command.
    """
    self.refresh()
    return self.turn_off() if self.is_on else self.turn_on()
