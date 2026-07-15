from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from sc_device_hub.models import store
from sc_device_hub.integrations.tuya import TuyaControlError
from sc_device_hub.device_types import get_handler


api_v1_router = APIRouter(prefix="/api/v1")


def _now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()


@api_v1_router.get("/devices")
async def list_devices() -> list[dict[str, Any]]:
  return [device.to_payload() for device in store.list()]


@api_v1_router.get("/devices/{device_id}")
async def get_device(device_id: str) -> dict[str, Any]:
  try:
    return store.get(device_id).to_payload()
  except KeyError as exc:
    raise HTTPException(status_code=404, detail="Device not found") from exc


@api_v1_router.post("/devices/refresh")
async def refresh_all_devices() -> list[dict[str, Any]]:
  """Refreshes all devices concurrently on the backend."""
  devices = store.list()

  async def refresh_one(device) -> None:
    handler = get_handler(device.type)
    updates = await handler.refresh(device)
    store.update(device.id, last_seen=_now_iso(), **updates)

  await asyncio.gather(*(refresh_one(d) for d in devices))
  return [device.to_payload() for device in store.list()]


@api_v1_router.post("/devices/{device_id}/ping")
async def refresh_ping(device_id: str) -> dict[str, Any]:
  """Quick connectivity ping – does not update switch state."""
  try:
    device = store.get(device_id)
  except KeyError as exc:
    raise HTTPException(status_code=404, detail="Device not found") from exc

  if not device.ip_address:
    raise HTTPException(status_code=400, detail="This device has no IP address to ping")

  from sc_device_hub.utils import ping_host
  from sc_device_hub.models import DeviceState

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

  handler = get_handler(device.type)
  try:
    updates = await handler.toggle(device)
  except TuyaControlError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc

  device = store.update(device_id, last_seen=_now_iso(), **updates)
  return device.to_payload()


@api_v1_router.post("/devices/{device_id}/refresh")
async def refresh_device(device_id: str) -> dict[str, Any]:
  """Full refresh – behaviour varies per device type."""
  try:
    device = store.get(device_id)
  except KeyError as exc:
    raise HTTPException(status_code=404, detail="Device not found") from exc

  handler = get_handler(device.type)
  updates = await handler.refresh(device)

  device = store.update(device_id, last_seen=_now_iso(), **updates)
  return device.to_payload()


@api_v1_router.get("/status")
async def api_status() -> dict[str, Any]:
  return {
    "service": "sc-device-hub",
    "devices": len(store.list()),
  }