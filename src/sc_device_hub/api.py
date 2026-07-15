from __future__ import annotations

import asyncio
import ipaddress
import platform
import socket
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from sc_device_hub.models import Device, DeviceType, DeviceState, store
from sc_device_hub.tuya import TuyaControlError, TuyaDevice


api_v1_router = APIRouter(prefix="/api/v1")


def _now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()


def _validate_ip_or_host(value: str) -> str:
  try:
    ipaddress.ip_address(value)
    return value
  except ValueError:
    if not value or len(value) > 255:
      raise ValueError("Host must be a valid IP address or hostname")
    socket.getaddrinfo(value, None)
    return value


async def ping_host(host: str, timeout_seconds: float = 1.5) -> tuple[bool, str]:
  _validate_ip_or_host(host)
  command = ["ping", "-c", "1", "-W", str(max(1, int(timeout_seconds))), host]
  if platform.system().lower().startswith("win"):
    command = ["ping", "-n", "1", "-w", str(int(timeout_seconds * 1000)), host]

  try:
    process = await asyncio.create_subprocess_exec(
      *command,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
    )
  except FileNotFoundError:
    return await _tcp_probe(host, timeout_seconds)

  try:
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds + 1)
  except asyncio.TimeoutError:
    process.kill()
    return False, f"Ping timed out for {host}"

  if process.returncode == 0:
    return True, stdout.decode().strip() or f"{host} is reachable"
  return False, stderr.decode().strip() or stdout.decode().strip() or f"{host} is unreachable"


async def _tcp_probe(host: str, timeout_seconds: float) -> tuple[bool, str]:
  def probe() -> tuple[bool, str]:
    try:
      with socket.create_connection((host, 80), timeout=timeout_seconds):
        return True, f"{host} accepted a TCP connection on port 80"
    except OSError as exc:
      return False, str(exc)

  return await asyncio.to_thread(probe)


def _tuya_from_device(device: Device) -> TuyaDevice:
  return TuyaDevice(
    name=device.name,
    tuya_device_id=device.tuya_device_id,
    is_on=device.is_on,
  )


@api_v1_router.get("/devices")
async def list_devices() -> list[dict[str, Any]]:
  return [device.to_payload() for device in store.list()]



@api_v1_router.get("/devices/{device_id}")
async def get_device(device_id: str) -> dict[str, Any]:
  try:
    return store.get(device_id).to_payload()
  except KeyError as exc:
    raise HTTPException(status_code=404, detail="Device not found") from exc


@api_v1_router.post("/devices/{device_id}/ping")
async def refresh_ping(device_id: str) -> dict[str, Any]:
  try:
    device = store.get(device_id)
  except KeyError as exc:
    raise HTTPException(status_code=404, detail="Device not found") from exc

  if not device.ip_address:
    raise HTTPException(status_code=400, detail="This device has no IP address to ping")

  reachable, message = await ping_host(device.ip_address)
  store.update(
    device_id,
    state=DeviceState.online if reachable else DeviceState.offline,
    last_seen=_now_iso(),
    last_message=message,
  )
  return store.get(device_id).to_payload()


@api_v1_router.post("/devices/{device_id}/toggle")
async def toggle_device(device_id: str) -> dict[str, Any]:
  try:
    device = store.get(device_id)
  except KeyError as exc:
    raise HTTPException(status_code=404, detail="Device not found") from exc

  if device.type is DeviceType.tuya_outlet:
    tuya_device = _tuya_from_device(device)
    try:
      action = tuya_device.toggle()
    except TuyaControlError as exc:
      raise HTTPException(status_code=400, detail=str(exc)) from exc
    device_state = tuya_device.is_on
    store.update(device_id, is_on=device_state)
  else:
    action = f"Toggled {device.name}"

  device = store.update(
    device_id,
    last_action=action,
    last_message=action,
    last_seen=_now_iso(),
  )
  return device.to_payload()


@api_v1_router.post("/devices/{device_id}/refresh")
async def refresh_device(device_id: str) -> dict[str, Any]:
  try:
    device = store.get(device_id)
  except KeyError as exc:
    raise HTTPException(status_code=404, detail="Device not found") from exc

  if device.ip_address:
    reachable, message = await ping_host(device.ip_address)
    state = DeviceState.online if reachable else DeviceState.offline
  else:
    state = device.state

  message = "Device status refreshed"

  device = store.update(device_id, state=state, last_seen=_now_iso(), last_message=message)
  return device.to_payload()



@api_v1_router.get("/status")
async def api_status() -> dict[str, Any]:
  return {
    "service": "sc-device-hub",
    "devices": len(store.list()),
  }