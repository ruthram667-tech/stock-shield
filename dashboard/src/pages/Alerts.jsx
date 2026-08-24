import { useState, useEffect } from 'react';
import { fetchRecentAlerts } from '../api';

const DEMO_ALERTS = [
  { id: 1, alertType: 'LOW_STOCK', severity: 'CRITICAL', message: '⚠️ LOW STOCK: Orange Juice — 1.92 kg remaining (reorder point: 4.00 kg, ~9.6 hours remaining)', shelfId: 'shelf-10', itemId: 'item-010', currentValue: 1.92, thresholdValue: 4.0, acknowledged: false, createdAt: new Date().toISOString() },
  { id: 2, alertType: 'TEMP_SPIKE', severity: 'CRITICAL', message: '🌡️ TEMP SPIKE: shelf-06 at 9.2°C (max: 8.0°C)', shelfId: 'shelf-06', itemId: 'item-006', currentValue: 9.2, thresholdValue: 8.0, acknowledged: false, createdAt: new Date(Date.now() - 300000).toISOString() },
  { id: 3, alertType: 'LOW_STOCK', severity: 'WARNING', message: '⚠️ LOW STOCK: Whole Milk — 2.16 kg remaining (reorder point: 3.00 kg, ~8.6 hours remaining)', shelfId: 'shelf-04', itemId: 'item-004', currentValue: 2.16, thresholdValue: 3.0, acknowledged: false, createdAt: new Date(Date.now() - 600000).toISOString() },
  { id: 4, alertType: 'LOW_STOCK', severity: 'WARNING', message: '⚠️ LOW STOCK: Chicken Breast — 3.30 kg remaining (reorder point: 2.50 kg, ~18.3 hours remaining)', shelfId: 'shelf-06', itemId: 'item-006', currentValue: 3.3, thresholdValue: 2.5, acknowledged: true, createdAt: new Date(Date.now() - 1800000).toISOString() },
  { id: 5, alertType: 'TEMP_SPIKE', severity: 'WARNING', message: '🌡️ TEMP SPIKE: shelf-04 at 7.8°C (max: 8.0°C)', shelfId: 'shelf-04', itemId: 'item-004', currentValue: 7.8, thresholdValue: 8.0, acknowledged: true, createdAt: new Date(Date.now() - 3600000).toISOString() },
  { id: 6, alertType: 'LOW_STOCK', severity: 'CRITICAL', message: '⚠️ LOW STOCK: Orange Juice — 3.20 kg remaining (reorder point: 4.00 kg)', shelfId: 'shelf-10', itemId: 'item-010', currentValue: 3.2, thresholdValue: 4.0, acknowledged: true, createdAt: new Date(Date.now() - 7200000).toISOString() },
];

const SEVERITY_FILTERS = ['All', 'CRITICAL', 'WARNING'];
const TYPE_FILTERS = ['All', 'LOW_STOCK', 'TEMP_SPIKE', 'HUMIDITY_OUT_OF_RANGE', 'SENSOR_OFFLINE'];

export default function Alerts() {
  const [alerts, setAlerts] = useState(DEMO_ALERTS);
  const [severityFilter, setSeverityFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [showAcknowledged, setShowAcknowledged] = useState(true);

  useEffect(() => {
    fetchRecentAlerts(50)
      .then(setAlerts)
      .catch(() => console.log('Using demo alert data'));
  }, []);

  const filtered = alerts.filter(a => {
    if (severityFilter !== 'All' && a.severity !== severityFilter) return false;
    if (typeFilter !== 'All' && a.alertType !== typeFilter) return false;
    if (!showAcknowledged && a.acknowledged) return false;
    return true;
  });

  const activeCount = alerts.filter(a => !a.acknowledged).length;
  const criticalCount = alerts.filter(a => a.severity === 'CRITICAL' && !a.acknowledged).length;

  const formatTime = (iso) => {
    const d = new Date(iso);
    const now = new Date();
    const diff = now - d;
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.round(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.round(diff / 3600000)}h ago`;
    return d.toLocaleDateString();
  };

  return (
    <>
      <div className="page-header">
        <h2>Alert Center</h2>
        <p>Monitor and manage system alerts across all sensors and inventory items</p>
      </div>

      {/* Alert Summary */}
      <div className="summary-grid" style={{ marginBottom: 24 }}>
        <div className="glass-card summary-card crimson">
          <div className="card-icon">🚨</div>
          <div className="card-value">{criticalCount}</div>
          <div className="card-label">Critical Alerts</div>
        </div>
        <div className="glass-card summary-card amber">
          <div className="card-icon">⚠️</div>
          <div className="card-value">{activeCount - criticalCount}</div>
          <div className="card-label">Warning Alerts</div>
        </div>
        <div className="glass-card summary-card emerald">
          <div className="card-icon">✅</div>
          <div className="card-value">{alerts.filter(a => a.acknowledged).length}</div>
          <div className="card-label">Acknowledged</div>
        </div>
        <div className="glass-card summary-card blue">
          <div className="card-icon">📊</div>
          <div className="card-value">{alerts.length}</div>
          <div className="card-label">Total Alerts</div>
        </div>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>SEVERITY:</span>
        {SEVERITY_FILTERS.map(f => (
          <button key={f} className={`filter-btn ${severityFilter === f ? 'active' : ''}`} onClick={() => setSeverityFilter(f)}>
            {f}
          </button>
        ))}
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, marginLeft: 16 }}>TYPE:</span>
        {TYPE_FILTERS.map(f => (
          <button key={f} className={`filter-btn ${typeFilter === f ? 'active' : ''}`} onClick={() => setTypeFilter(f)}>
            {f.replace(/_/g, ' ')}
          </button>
        ))}
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.82rem', color: 'var(--text-secondary)', marginLeft: 'auto', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={showAcknowledged}
            onChange={() => setShowAcknowledged(!showAcknowledged)}
            style={{ accentColor: 'var(--accent-blue)' }}
          />
          Show acknowledged
        </label>
      </div>

      {/* Alert List */}
      <div className="glass-card">
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 40 }}></th>
                <th>Alert</th>
                <th>Type</th>
                <th>Shelf</th>
                <th>Value</th>
                <th>Threshold</th>
                <th>Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(alert => (
                <tr key={alert.id} style={{ opacity: alert.acknowledged ? 0.6 : 1 }}>
                  <td>
                    <div className={`alert-icon ${alert.severity === 'CRITICAL' ? 'critical' : 'warning'}`}
                         style={{ width: 28, height: 28, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12 }}>
                      {alert.alertType === 'TEMP_SPIKE' ? '🌡️' : alert.alertType === 'SENSOR_OFFLINE' ? '📡' : '📦'}
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-primary)', fontWeight: 500, maxWidth: 400 }}>
                    {alert.message}
                  </td>
                  <td>
                    <span className={`badge ${alert.severity === 'CRITICAL' ? 'critical' : 'low'}`}>
                      {alert.alertType.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td>{alert.shelfId}</td>
                  <td style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 600, color: alert.severity === 'CRITICAL' ? 'var(--accent-crimson)' : 'var(--accent-amber)' }}>
                    {alert.currentValue?.toFixed(1)}
                  </td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {alert.thresholdValue?.toFixed(1)}
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                    {formatTime(alert.createdAt)}
                  </td>
                  <td>
                    {alert.acknowledged ? (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Acknowledged</span>
                    ) : (
                      <button className="filter-btn" style={{ fontSize: '0.75rem', padding: '4px 10px' }}>
                        Acknowledge
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
            ✅ No alerts matching your filters
          </div>
        )}
      </div>
    </>
  );
}
