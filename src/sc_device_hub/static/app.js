const deviceList = document.getElementById('device-list');
const deviceTemplate = document.getElementById('device-template');
const message = document.getElementById('message');
const deviceCount = document.getElementById('device-count');
const lastRefresh = document.getElementById('last-refresh');
const refreshAllButton = document.getElementById('refresh-all');

const stateLabels = {
  online: 'Online',
  offline: 'Offline',
  unknown: 'Unknown',
};

const statusBadgeRenderers = {
  tuya_outlet: (device) => ({
    text: device.is_on ? 'On' : 'Off',
    key: device.is_on ? 'on' : 'off',
  }),
  // ping_device: () => null,   // example: uncomment + fill in to add later
  // manual: () => null,
};

function showMessage(text, kind = 'info') {
  message.textContent = text;
  message.dataset.kind = kind;
}

function renderDevice(device) {
  const node = deviceTemplate.content.cloneNode(true);
  const row = node.querySelector('.device-row');
  const name = node.querySelector('.device-name');
  const id = node.querySelector('.device-id');
  const state = node.querySelector('.device-state');
  const status = node.querySelector('.device-status');
  const typeBadge = node.querySelector('.device-type-badge');
  const meta = node.querySelector('.device-meta');
  const note = node.querySelector('.device-note');
  const refreshAction = node.querySelector('.refresh-action');
  const pingAction = node.querySelector('.ping-action');
  const toggleAction = node.querySelector('.toggle-action');

  function formatLastSeen(isoString) {
    if (!isoString) return null;
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return null;
    return `Last seen: ${date.toLocaleTimeString(undefined, { hour12: false })}`;
  }

  name.textContent = device.name;
  id.textContent = device.id;
  state.textContent = stateLabels[device.state] || device.state;
  state.dataset.state = device.state;
  typeBadge.textContent = device.type.replace(/_/g, ' ');
  typeBadge.dataset.type = device.type;

  const metaParts = [
    device.ip_address ? `IP: ${device.ip_address}` : 'No IP configured'
  ];
  const lastSeenStr = formatLastSeen(device.last_seen);
  if (lastSeenStr) {
    metaParts.push(lastSeenStr);
  }
  meta.textContent = metaParts.join(' • ');

  note.textContent = device.last_message || device.last_action || 'No recent activity';

  const renderer = statusBadgeRenderers[device.type];
  const statusInfo = renderer ? renderer(device) : null;
  if (statusInfo) {
    status.textContent = statusInfo.text;
    status.dataset.statusKey = statusInfo.key;
    status.hidden = false;
  } else {
    status.hidden = true;
  }

  pingAction.hidden = !device.ip_address;
  toggleAction.hidden = !device.can_toggle;

  row.dataset.state = device.state;

  pingAction.addEventListener('click', async () => {
    await performAction(`/api/v1/devices/${device.id}/ping`, `${device.name} pinged`, pingAction);
  });

  refreshAction.addEventListener('click', async () => {
    await performAction(`/api/v1/devices/${device.id}/refresh`, `${device.name} status refreshed`, refreshAction);
  });

  if (device.can_toggle) {
    const TOGGLE_SETTLE_MS = 1500;

    toggleAction.addEventListener('click', async () => {
      const originalText = toggleAction.textContent;
      try {
        toggleAction.disabled = true;
        toggleAction.textContent = '...';

        const toggleRes = await fetch(`/api/v1/devices/${device.id}/toggle`, { method: 'POST' });
        const togglePayload = await toggleRes.json();
        if (!toggleRes.ok) throw new Error(togglePayload.detail || 'Toggle failed');

        showMessage(`${device.name} toggled – refreshing…`, 'info');
        await new Promise((resolve) => setTimeout(resolve, TOGGLE_SETTLE_MS));
        await fetch(`/api/v1/devices/${device.id}/refresh`, { method: 'POST' });

        showMessage(`${device.name} toggled`, 'success');
        await loadDevices();
      } catch (error) {
        showMessage(error.message, 'error');
        toggleAction.disabled = false;
        toggleAction.textContent = originalText;
      }
    });
  }

  row.dataset.deviceId = device.id;
  return node;
}

async function loadDevices() {
  const response = await fetch('/api/v1/devices');
  if (!response.ok) {
    throw new Error('Unable to load devices');
  }
  const devices = await response.json();
  deviceList.innerHTML = '';
  devices.forEach((device) => {
    deviceList.appendChild(renderDevice(device));
  });
  deviceCount.textContent = String(devices.length);
  return devices;
}

async function performAction(url, successMessage, button = null) {
  const originalText = button ? button.textContent : '';
  if (button) {
    button.disabled = true;
    button.textContent = '...';
  }
  try {
    const response = await fetch(url, { method: 'POST' });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || 'Action failed');
    }
    showMessage(successMessage, 'success');
    await loadDevices();
  } catch (error) {
    showMessage(error.message, 'error');
    if (button) {
      button.disabled = false;
      button.textContent = originalText;
    }
  }
}

async function refreshAllDevices() {
  const originalText = refreshAllButton.textContent;
  try {
    refreshAllButton.disabled = true;
    refreshAllButton.textContent = 'Refreshing...';

    const response = await fetch('/api/v1/devices/refresh', { method: 'POST' });
    if (!response.ok) {
      throw new Error('Global refresh failed');
    }
    const devices = await response.json();

    deviceList.innerHTML = '';
    devices.forEach((device) => {
      deviceList.appendChild(renderDevice(device));
    });
    deviceCount.textContent = String(devices.length);

    lastRefresh.textContent = new Date().toLocaleTimeString(undefined, { hour12: false });
    showMessage('Refreshed reachable devices', 'success');
  } catch (error) {
    showMessage(error.message, 'error');
  } finally {
    refreshAllButton.disabled = false;
    refreshAllButton.textContent = originalText;
  }
}

refreshAllButton.addEventListener('click', async () => {
  await refreshAllDevices();
});

const AUTO_REFRESH_MS = 30_000;

loadDevices().catch((error) => showMessage(error.message, 'error'));
refreshAllDevices().catch((error) => showMessage(error.message, 'error'));

setInterval(() => {
  refreshAllDevices().catch(() => {/* silent – don't disrupt the user on background failures */ });
}, AUTO_REFRESH_MS);
