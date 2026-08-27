import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Package, AlertTriangle, Bell, Wifi, Thermometer, Droplets, CheckCircle2 } from 'lucide-react';
import { fetchDashboardSummary, fetchInventory, fetchRecentAlerts } from '../api';
import StockGauge from '../components/StockGauge';
import TelemetryChart from '../components/TelemetryChart';

// Demo data for initial render
const DEMO_SUMMARY = {
  totalItems: 12, lowStockCount: 3, criticalStockCount: 1,
  activeAlerts: 4, avgTemperature: 4.2, avgHumidity: 55.3,
  sensorsOnline: 16, sensorsOffline: 2,
};

const DEMO_ITEMS = [
  { id: 'item-001', name: 'Basmati Rice', stockPercentage: 0.72 },
  { id: 'item-002', name: 'All-Purpose Flour', stockPercentage: 0.45 },
  { id: 'item-003', name: 'Granulated Sugar', stockPercentage: 0.88 },
  { id: 'item-004', name: 'Whole Milk', stockPercentage: 0.18 },
  { id: 'item-005', name: 'Cheddar Cheese', stockPercentage: 0.62 },
  { id: 'item-006', name: 'Chicken Breast', stockPercentage: 0.33 },
  { id: 'item-007', name: 'Frozen Vegetables', stockPercentage: 0.91 },
  { id: 'item-008', name: 'Ice Cream', stockPercentage: 0.55 },
];

const DEMO_ALERTS = [
  { id: 1, alertType: 'LOW_STOCK', severity: 'WARNING', message: 'LOW STOCK: Whole Milk — 2.16 kg remaining', shelfId: 'shelf-04', createdAt: new Date().toISOString() },
  { id: 2, alertType: 'TEMP_SPIKE', severity: 'CRITICAL', message: 'TEMP SPIKE: shelf-06 at 9.2°C (max: 8.0°C)', shelfId: 'shelf-06', createdAt: new Date(Date.now() - 300000).toISOString() },
  { id: 3, alertType: 'LOW_STOCK', severity: 'CRITICAL', message: 'LOW STOCK: Orange Juice — 1.92 kg remaining', shelfId: 'shelf-10', createdAt: new Date(Date.now() - 600000).toISOString() },
  { id: 4, alertType: 'LOW_STOCK', severity: 'WARNING', message: 'LOW STOCK: Chicken Breast — 3.30 kg remaining', shelfId: 'shelf-06', createdAt: new Date(Date.now() - 900000).toISOString() },
];

function useAnimatedValue(target, duration = 600) {
  const [value, setValue] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    const start = value;
    const diff = target - start;
    if (diff === 0) return;
    const startTime = performance.now();

    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(start + diff * eased));
      if (progress < 1) ref.current = requestAnimationFrame(animate);
    };

    ref.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(ref.current);
  }, [target, duration]);

  return value;
}

function AnimatedValue({ value, suffix = '' }) {
  const animated = useAnimatedValue(typeof value === 'number' ? value : 0);
  return <>{animated}{suffix}</>;
}

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

  const chartLabels = items.map(i => i.name?.split(' ')[0] || i.id);
  const chartData = items.map(i => Math.round((i.stockPercentage || 0) * 100));

  const timeLabels = Array.from({ length: 12 }, (_, i) => {
    const d = new Date();
    d.setHours(d.getHours() - 11 + i);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  });

  const formatAlertTime = (iso) => {
    const diff = Date.now() - new Date(iso).getTime();
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.round(diff / 60000)}m ago`;
    return `${Math.round(diff / 3600000)}h ago`;
  };

  const summaryCards = [
    { label: 'Total Items', value: summary.totalItems, icon: Package, trend: '+2', trendDir: 'up' },
    { label: 'Low Stock', value: summary.lowStockCount, icon: AlertTriangle, trend: summary.lowStockCount > 0 ? `${summary.lowStockCount}` : '0', trendDir: summary.lowStockCount > 2 ? 'down' : 'neutral' },
    { label: 'Active Alerts', value: summary.activeAlerts, icon: Bell, trend: summary.activeAlerts > 3 ? 'High' : 'Normal', trendDir: summary.activeAlerts > 3 ? 'down' : 'neutral' },
    { label: 'Sensors Online', value: summary.sensorsOnline, icon: Wifi, trend: `${summary.sensorsOffline || 0} offline`, trendDir: (summary.sensorsOffline || 0) > 0 ? 'down' : 'up' },
    { label: 'Avg Temp', value: null, displayValue: `${typeof summary.avgTemperature === 'number' ? summary.avgTemperature.toFixed(1) : '--'}°`, icon: Thermometer, trend: 'Normal', trendDir: 'neutral' },
    { label: 'Avg Humidity', value: null, displayValue: `${typeof summary.avgHumidity === 'number' ? summary.avgHumidity.toFixed(0) : '--'}%`, icon: Droplets, trend: 'Normal', trendDir: 'neutral' },
  ];

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Real-time inventory monitoring and sensor telemetry</p>
      </div>

      {/* Summary Cards */}
      <div className="summary-grid">
        {summaryCards.map((card) => (
          <div key={card.label} className="summary-card">
            <div className="card-label">
              {card.label}
              <card.icon size={16} strokeWidth={2} />
            </div>
            <div className="card-value-row">
              <div className="card-value">
                {card.value !== null ? <AnimatedValue value={card.value} /> : card.displayValue}
              </div>
              {card.trend && (
                <span className={`card-trend ${card.trendDir}`}>
                  {card.trendDir === 'up' ? '↑' : card.trendDir === 'down' ? '↓' : '·'} {card.trend}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="chart-grid">
        <div className="glass-card chart-container">
          <div className="card-title" style={{ marginBottom: 16 }}>
            <Package size={16} strokeWidth={2} /> Stock Levels (%)
          </div>
          <TelemetryChart
            type="bar"
            labels={chartLabels}
            datasets={[{
              label: 'Stock %',
              data: chartData,
              color: '#2563eb', // solid primary
              overrides: {
                backgroundColor: 'rgba(37, 99, 235, 0.2)',
                borderColor: '#2563eb',
                borderWidth: 1,
                borderRadius: 4,
              }
            }]}
            yAxisLabel="Stock %"
          />
        </div>

        <div className="glass-card chart-container">
          <div className="card-title" style={{ marginBottom: 16 }}>
            <Thermometer size={16} strokeWidth={2} /> Weight Trends
          </div>
          <TelemetryChart
            type="line"
            labels={timeLabels}
            datasets={[
              {
                label: 'Whole Milk',
                data: Array.from({ length: 12 }, (_, i) => Math.max(1, 12 - i * 0.8 + Math.random() * 0.5)),
                color: '#dc2626',
                fill: false,
              },
              {
                label: 'Basmati Rice',
                data: Array.from({ length: 12 }, (_, i) => Math.max(5, 20 - i * 0.5 + Math.random())),
                color: '#2563eb',
                fill: false,
              }
            ]}
            yAxisLabel="Weight (kg)"
          />
        </div>
      </div>

      {/* Gauges + Alerts */}
      <div className="chart-grid">
        <div className="glass-card" style={{ padding: 24 }}>
          <div className="card-title" style={{ marginBottom: 20 }}>
            <Package size={16} strokeWidth={2} /> Stock Gauges
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: 24, justifyItems: 'center' }}>
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
          <div className="card-title" style={{ marginBottom: 16 }}>
            <Bell size={16} strokeWidth={2} /> Recent Alerts
          </div>
          <div className="alert-feed">
            {alerts.map(alert => (
              <div key={alert.id} className={`alert-feed-item severity-${alert.severity === 'CRITICAL' ? 'critical' : 'warning'}`}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="alert-message">{alert.message}</div>
                  <div className="alert-time">
                    {formatAlertTime(alert.createdAt)} · {alert.shelfId}
                  </div>
                </div>
              </div>
            ))}
            {alerts.length === 0 && (
              <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-low)' }}>
                <CheckCircle2 size={32} strokeWidth={1.5} style={{ margin: '0 auto 12px' }} />
                <p style={{ fontSize: '0.875rem' }}>No active alerts. All systems nominal.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
