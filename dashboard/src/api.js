const API_BASE = '/api';

export async function fetchDashboardSummary() {
  const res = await fetch(`${API_BASE}/dashboard/summary`);
  if (!res.ok) throw new Error('Failed to fetch dashboard summary');
  return res.json();
}

export async function fetchInventory() {
  const res = await fetch(`${API_BASE}/inventory`);
  if (!res.ok) throw new Error('Failed to fetch inventory');
  return res.json();
}

export async function fetchInventoryItem(id) {
  const res = await fetch(`${API_BASE}/inventory/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch item ${id}`);
  return res.json();
}

export async function fetchAlertItems() {
  const res = await fetch(`${API_BASE}/inventory/alerts`);
  if (!res.ok) throw new Error('Failed to fetch alert items');
  return res.json();
}

export async function fetchRecentAlerts(limit = 20) {
  const res = await fetch(`${API_BASE}/dashboard/alerts/recent?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch alerts');
  return res.json();
}

export async function fetchTelemetry(shelfId, range = '24h') {
  const res = await fetch(`${API_BASE}/telemetry/${shelfId}?range=${range}`);
  if (!res.ok) throw new Error(`Failed to fetch telemetry for ${shelfId}`);
  return res.json();
}

export async function fetchEnvironmentHistory(shelfId, range = '24h') {
  const res = await fetch(`${API_BASE}/telemetry/environment/${shelfId}?range=${range}`);
  if (!res.ok) throw new Error(`Failed to fetch environment for ${shelfId}`);
  return res.json();
}

export async function fetchThresholds() {
  const res = await fetch(`${API_BASE}/thresholds`);
  if (!res.ok) throw new Error('Failed to fetch thresholds');
  return res.json();
}
