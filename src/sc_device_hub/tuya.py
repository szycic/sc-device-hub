from __future__ import annotations

import os
from dotenv import load_dotenv

from dataclasses import dataclass
import tinytuya

load_dotenv()

TUYA_ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
TUYA_ACCESS_KEY = os.getenv("TUYA_ACCESS_KEY")

if not TUYA_ACCESS_ID or not TUYA_ACCESS_KEY:
  raise RuntimeError("TUYA_ACCESS_ID and TUYA_ACCESS_KEY must be set in the environment")

class TuyaControlError(RuntimeError):
  pass


@dataclass(slots=True)
class TuyaDevice:
  name: str
  ip_address: str | None = None
  tuya_device_id: str | None = None
  is_on: bool = False
  
  def connect(self) -> tinytuya.Cloud:
    if not self.ip_address:
      raise TuyaControlError("ip_address is required for Tuya controls")
    if not self.tuya_device_id:
      raise TuyaControlError("tuya_device_id is required for Tuya controls")

    cloud = tinytuya.Cloud(
      "eu",
      TUYA_ACCESS_ID,
      TUYA_ACCESS_KEY
    )
    
    return cloud
  
  def refresh(self) -> bool:
    cloud = self.connect()
    try:
      status = cloud.getstatus(self.tuya_device_id)
      
      for item in status.get("result", []):
        if item.get("code") == "switch_1":
          self.is_on = item.get("value", False)
          return self.is_on
      
      raise TuyaControlError("switch_1 status not found")
    
    except Exception as exc:
      raise TuyaControlError(f"Failed to refresh {self.name}: {exc}") from exc

  def turn_on(self) -> str:
    cloud = self.connect()
    
    try:
      command = cloud.sendcommand(
        self.tuya_device_id,
        {
          "commands": [
            {
              "code": "switch_1",
              "value": True
            }
          ]
        }
      )
      if not command.get("success"):
        raise TuyaControlError(f"Failed to turn on {self.name}: {command.get('msg', 'Unknown error')}")
      return f"{self.name} turned on"
    except Exception as exc:
      raise TuyaControlError(f"Failed to turn on {self.name}: {exc}") from exc

  def turn_off(self) -> str:
    cloud = self.connect()
    try:
      command = cloud.sendcommand(
        self.tuya_device_id,
        {
          "commands": [
            {
              "code": "switch_1",
              "value": False
            }
          ]
        }
      )
      if not command.get("success"):
        raise TuyaControlError(f"Failed to turn off {self.name}: {command.get('msg', 'Unknown error')}")
      return f"{self.name} turned off"
    except Exception as exc:
      raise TuyaControlError(f"Failed to turn off {self.name}: {exc}") from exc

  def toggle(self) -> str:
    try:
      self.refresh()
      
      if self.is_on:
        return self.turn_off()
      else:
        return self.turn_on()
      
    except Exception as exc:
      raise TuyaControlError(f"Failed to toggle {self.name}: {exc}") from exc