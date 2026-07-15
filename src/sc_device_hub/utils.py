from __future__ import annotations

import asyncio
import ipaddress
import platform
import socket


def _validate_ip_or_host(value: str) -> str:
  try:
    ipaddress.ip_address(value)
    return value
  except ValueError:
    if not value or len(value) > 255:
      raise ValueError("Host must be a valid IP address or hostname")
    return value


async def _tcp_probe(host: str, timeout_seconds: float) -> tuple[bool, str]:
  def probe() -> tuple[bool, str]:
    try:
      with socket.create_connection((host, 80), timeout=timeout_seconds):
        return True, f"{host} accepted a TCP connection on port 80"
    except OSError as exc:
      return False, str(exc)

  return await asyncio.to_thread(probe)


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
