import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchDashboardSummary, fetchInventory, fetchRecentAlerts } from '../api';
import StockGauge from '../components/StockGauge';
import TelemetryChart from '../components/TelemetryChart';

// Demo data for initial render (before API connects)
const DEMO_SUMMARY = {
  totalItems: 12, lowStockCount: 3, criticalStockCount: 1,
  activeAlerts: 4, avgTemperature: 4.2, avgHumidity: 55.3,
  sensorsOnline: 16, sensorsOffline: 2,
};

const DEMO_ITEMS = [
  { id: 'item-001', name: 'Basmati Rice', stockPercentage: 0.72, shelfId: 'shelf-01', depletionRate: 0.12 },
  { id: 'item-002', name: 'All-Purpose Flour', stockPercentage: 0.45, shelfId: 'shelf-02', depletionRate: 0.08 },
  { id: 'item-003', name: 'Granulated Sugar', stockPercentage: 0.88, shelfId: 'shelf-03', depletionRate: 0.05 },
  { id: 'item-004', name: 'Whole Milk', stockPercentage: 0.18, shelfId: 'shelf-04', depletionRate: 0.25 },
  { id: 'item-005', name: 'Cheddar Cheese', stockPercentage: 0.62, shelfId: 'shelf-05', depletionRate: 0.06 },
  { id: 'item-006', name: 'Chicken Breast', stockPercentage: 0.33, shelfId: 'shelf-06', depletionRate: 0.18 },
  { id: 'item-007', name: 'Frozen Vegetables', stockPercentage: 0.91, shelfId: 'shelf-07', depletionRate: 0.04 },
  { id: 'item-008', name: 'Ice Cream', stockPercentage: 0.55, shelfId: 'shelf-08', depletionRate: 0.07 },
  { id: 'item-009', name: 'Olive Oil', stockPercentage: 0.78, shelfId: 'shelf-09', depletionRate: 0.03 },
  { id: 'item-010', name: 'Orange Juice', stockPercentage: 0.12, shelfId: 'shelf-10', depletionRate: 0.20 },
  { id: 'item-011', name: 'Canned Tomatoes', stockPercentage: 0.67, shelfId: 'shelf-11', depletionRate: 0.06 },
  { id: 'item-012', name: 'Penne Pasta', stockPercentage: 0.41, shelfId: 'shelf-12', depletionRate: 0.09 },
];

const DEMO_ALERTS = [
  { id: 1, alertType: 'LOW_STOCK', severity: 'WARNING', message: '⚠️ LOW STOCK: Whole Milk — 2.16 kg remaining', shelfId: 'shelf-04', createdAt: new Date().toISOString() },
  { id: 2, alertType: 'TEMP_SPIKE', severity: 'CRITICAL', message: '🌡️ TEMP SPIKE: shelf-06 at 9.2°C (max: 8.0°C)', shelfId: 'shelf-06', createdAt: new Date(Date.now() - 300000).toISOString() },
  { id: 3, alertType: 'LOW_STOCK', severity: 'CRITICAL', message: '⚠️ LOW STOCK: Orange Juice — 1.92 kg remaining', shelfId: 'shelf-10', createdAt: new Date(Date.now() - 600000).toISOString() },
  { id: 4, alertType: 'LOW_STOCK', severity: 'WARNING', message: '⚠️ LOW STOCK: Chicken Breast — 3.30 kg remaining', shelfId: 'shelf-06', createdAt: new Date(Date.now() - 900000).toISOString() },
];

export default function Dashboard() {
  const [summary, setSummary] = useState(DEMO_SUMMARY);
  const [items, setItems] = useState(DEMO_ITEMS);
  const [alerts, setAlerts] = useState(DEMO_ALERTS);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [s, inv, al] = await Promise.all([
          fetchDashboardSummary(),
          fetchInventory(),
          fetchRecentAlerts(10)
        ]);
        setSummary(s);
        setItems(inv);
        setAlerts(al);
      } catch (err) {
        console.log('Using demo data (API not available):', err.message);
      }
    };

    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Generate chart data from items
  const chartLabels = items.map(i => i.name?.split(' ')[0] || i.id);
  const chartData = items.map(i => Math.round((i.stockPercentage || 0) * 100));
  const chartColors = items.map(i => {
    const pct = i.stockPercentage || 0;
    if (pct > 0.8) return '#10b981';
    if (pct > 0.4) return '#3b82f6';
    if (pct > 0.2) return '#f59e0b';
    return '#ef4444';
  });

  const timeLabels = Array.from({ length: 12 }, (_, i) => {
    const d = new Date();
    d.setHours(d.getHours() - 11 + i);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  });

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Real-time inventory monitoring and sensor telemetry</p>
      </div>

      {/* Summary Cards */}
      <div className="summary-grid">
        <div className="glass-card summary-card blue">
          <div className="card-icon">📦</div>
          <div className="card-value">{summary.totalItems}</div>
          <div className="card-label">Total Items Tracked</div>
        </div>
        <div className="glass-card summary-card amber">
          <div className="card-icon">⚠️</div>
          <div className="card-value">{summary.lowStockCount}</div>
          <div className="card-label">Low Stock Items</div>
        </div>
        <div className="glass-card summary-card crimson">
          <div className="card-icon">🚨</div>
          <div className="card-value">{summary.activeAlerts}</div>
          <div className="card-label">Active Alerts</div>
        </div>
        <div className="glass-card summary-card emerald">
          <div className="card-icon">📡</div>
          <div className="card-value">{summary.sensorsOnline}</div>
          <div className="card-label">Sensors Online</div>
        </div>
        <div className="glass-card summary-card cyan">
          <div className="card-icon">🌡️</div>
          <div className="card-value">{typeof summary.avgTemperature === 'number' ? summary.avgTemperature.toFixed(1) : '--'}°</div>
          <div className="card-label">Avg Temperature</div>
        </div>
        <div className="glass-card summary-card purple">
          <div className="card-icon">💧</div>
          <div className="card-value">{typeof summary.avgHumidity === 'number' ? summary.avgHumidity.toFixed(0) : '--'}%</div>
          <div className="card-label">Avg Humidity</div>
        </div>
      </div>

      {/* Charts */}
      <div className="chart-grid">
        <div className="glass-card chart-container">
          <TelemetryChart
            type="bar"
            labels={chartLabels}
            datasets={[{
              label: 'Stock Level %',
              data: chartData,
              color: '#3b82f6',
              overrides: {
                backgroundColor: chartColors.map(c => c + '80'),
                borderColor: chartColors,
                borderWidth: 1,
                borderRadius: 6,
              }
            }]}
            title="Current Stock Levels"
            yAxisLabel="Stock %"
          />
        </div>

        <div className="glass-card chart-container">
          <TelemetryChart
            type="line"
            labels={timeLabels}
            datasets={[
              {
                label: 'Whole Milk',
                data: Array.from({ length: 12 }, (_, i) => Math.max(1, 12 - i * 0.8 + Math.random() * 0.5)),
                color: '#ef4444',
                fill: true,
              },
              {
                label: 'Basmati Rice',
                data: Array.from({ length: 12 }, (_, i) => Math.max(5, 20 - i * 0.5 + Math.random())),
                color: '#3b82f6',
                fill: true,
              },
              {
                label: 'Ice Cream',
                data: Array.from({ length: 12 }, (_, i) => Math.max(3, 10 - i * 0.3 + Math.random() * 0.4)),
                color: '#8b5cf6',
                fill: true,
              },
            ]}
            title="Weight Trends (Last 12h)"
            yAxisLabel="Weight (kg)"
          />
        </div>
      </div>

      {/* Gauges + Alerts */}
      <div className="chart-grid">
        <div className="glass-card" style={{ padding: 24 }}>
          <div className="card-title" style={{ marginBottom: 20 }}>Stock Gauges</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: 16, justifyItems: 'center' }}>
            {items.slice(0, 8).map(item => (
              <Link key={item.id} to={`/inventory/${item.id}`} style={{ textDecoration: 'none' }}>
                <StockGauge
                  percentage={item.stockPercentage || 0}
                  label={item.name?.split(' ').slice(0, 2).join(' ') || item.id}
                />
              </Link>
            ))}
          </div>
        </div>

        <div className="glass-card" style={{ padding: 24 }}>
          <div className="card-title" style={{ marginBottom: 16 }}>Recent Alerts</div>
          <div className="alert-feed">
            {alerts.map(alert => (
              <div key={alert.id} className="alert-feed-item">
                <div className={`alert-icon ${alert.severity === 'CRITICAL' ? 'critical' : 'warning'}`}>
                  {alert.alertType === 'TEMP_SPIKE' ? '🌡️' : '📦'}
                </div>
                <div className="alert-content">
                  <div className="alert-message">{alert.message}</div>
                  <div className="alert-time">
                    {new Date(alert.createdAt).toLocaleTimeString()} · {alert.shelfId}
                  </div>
                </div>
              </div>
            ))}
            {alerts.length === 0 && (
              <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>
                ✅ No active alerts
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
