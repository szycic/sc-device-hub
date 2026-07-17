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
  pass


class TuyaClient:
  def __init__(self) -> None:
    self.cloud = tinytuya.Cloud(
      "eu",
      TUYA_ACCESS_ID,
      TUYA_ACCESS_KEY,
    )

  def status(self, device_id: str) -> dict:
    return self.cloud.getstatus(device_id)

  def command(self, device_id: str, code: str, value: bool) -> dict:
    return self.cloud.sendcommand(
      device_id,
      {"commands": [{"code": code, "value": value}]},
    )


tuya = TuyaClient()


@dataclass(slots=True)
class TuyaDevice:
  name: str
  tuya_device_id: str
  is_on: bool = False

  def refresh(self) -> bool:
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
    try:
      command = tuya.command(self.tuya_device_id, "switch_1", state)
      if not command.get("success"):
        raise TuyaControlError(
          f"Failed to set state for {self.name}: {command.get('msg', 'Unknown error')}"
        )
      
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
    return self.set_state(True)

  def turn_off(self) -> str:
    return self.set_state(False)

  def toggle(self) -> str:
    self.refresh()
    return self.turn_off() if self.is_on else self.turn_on()
