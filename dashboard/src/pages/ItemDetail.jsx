import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, Thermometer, Droplets } from 'lucide-react';
import { fetchInventoryItem, fetchTelemetry } from '../api';
import StockGauge from '../components/StockGauge';
import TelemetryChart from '../components/TelemetryChart';

const DEMO_ITEM = {
  id: 'item-004', name: 'Whole Milk 1L', category: 'dairy', zone: 'refrigerated',
  shelfId: 'shelf-04', currentWeight: 2.16, fullWeight: 12.0, reorderPoint: 3.0,
  unit: 'kg', stockPercentage: 0.18, stockLevel: 'CRITICAL', depletionRate: 0.25,
  estimatedHoursRemaining: 8.64, needsReorder: true, temperature: 4.1, humidity: 65.2,
};

export default function ItemDetail() {
  const { id } = useParams();
  const [item, setItem] = useState(null);
  const [range, setRange] = useState('24h');

  useEffect(() => {
    fetchInventoryItem(id)
      .then(setItem)
      .catch(() => {
        console.log('Using demo item data');
        setItem({ ...DEMO_ITEM, id });
      });
  }, [id]);

  if (!item) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <div className="skeleton" style={{ width: 200, height: 24, margin: '0 auto 16px' }} />
        <div className="skeleton" style={{ width: 300, height: 16, margin: '0 auto' }} />
      </div>
    );
  }

  // Generate demo chart data
  const hours = range === '24h' ? 24 : range === '7d' ? 168 : 720;
  const step = Math.max(1, Math.floor(hours / 48));
  const chartLabels = Array.from({ length: Math.ceil(hours / step) }, (_, i) => {
    const d = new Date();
    d.setHours(d.getHours() - hours + i * step);
    return range === '24h'
      ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  });

  const startWeight = item.fullWeight * (0.7 + Math.random() * 0.3);
  const weightData = chartLabels.map((_, i) => {
    const decay = startWeight * Math.exp(-0.003 * i * step);
    return Math.max(0, decay + (Math.random() - 0.5) * 0.5);
  });

  const formatTimeLeft = () => {
    const h = item.estimatedHoursRemaining;
    if (h > 999) return '∞';
    if (h > 24) return `${Math.round(h / 24)}d`;
    return `${Math.round(h)}h`;
  };

  return (
    <>
      <div className="page-header">
        <Link to="/inventory" className="back-link">
          <ArrowLeft size={14} /> Back to Inventory
        </Link>
        <h2>{item.name}</h2>
        <p>{item.category} · {item.zone} · {item.shelfId}</p>
      </div>

      {/* Status Cards */}
      <div className="summary-grid">
        <div className="glass-card summary-card blue" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <StockGauge percentage={item.stockPercentage || 0} size={80} />
          <div className="card-label" style={{ marginTop: 10 }}>Stock Level</div>
        </div>
        <div className="glass-card summary-card emerald" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div className="card-value">{item.currentWeight?.toFixed(1)} <span style={{ fontSize: '1rem', fontWeight: 400, color: 'var(--text-secondary)' }}>kg</span></div>
          <div className="card-label">Current Weight (of {item.fullWeight} {item.unit})</div>
        </div>
        <div className="glass-card summary-card amber" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div className="card-value">{item.depletionRate?.toFixed(2)} <span style={{ fontSize: '1rem', fontWeight: 400, color: 'var(--text-secondary)' }}>kg/h</span></div>
          <div className="card-label">Depletion Rate</div>
        </div>
        <div className="glass-card summary-card crimson" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div className="card-value">{formatTimeLeft()}</div>
          <div className="card-label">Time Remaining</div>
        </div>
      </div>

      {/* Reorder Status */}
      {item.needsReorder && (
        <div className="glass-card reorder-banner">
          <div className="reorder-icon">
            <AlertTriangle size={18} />
          </div>
          <div className="reorder-text">
            <strong>NEEDS REORDER</strong>
            <p>Current weight ({item.currentWeight?.toFixed(1)} kg) is below the reorder point ({item.reorderPoint} kg)</p>
          </div>
        </div>
      )}

      {/* Range Selector + Weight Chart */}
      <div className="glass-card chart-container" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <span className="card-title">Weight History</span>
          <div className="filter-bar" style={{ margin: 0 }}>
            {['24h', '7d', '30d'].map(r => (
              <button
                key={r}
                className={`filter-btn ${range === r ? 'active' : ''}`}
                onClick={() => setRange(r)}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
        <TelemetryChart
          type="line"
          labels={chartLabels}
          datasets={[
            {
              label: 'Weight',
              data: weightData,
              color: '#4f8efa',
              fill: true,
            },
            {
              label: 'Reorder Point',
              data: chartLabels.map(() => item.reorderPoint),
              color: '#f87171',
              overrides: {
                borderDash: [8, 4],
                pointRadius: 0,
                borderWidth: 1.5,
              }
            },
          ]}
          yAxisLabel="Weight (kg)"
        />
      </div>

      {/* Environment */}
      {(item.temperature != null || item.humidity != null) && (
        <div className="glass-card" style={{ padding: 24 }}>
          <div className="card-title" style={{ marginBottom: 18 }}>
            <Thermometer size={14} className="title-icon" /> Environment
          </div>
          <div style={{ display: 'flex', gap: 48 }}>
            {item.temperature != null && (
              <div className="env-metric safe">
                <div className="value" style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Thermometer size={20} style={{ opacity: 0.5 }} />
                  {item.temperature.toFixed(1)}°C
                </div>
                <div className="label" style={{ color: 'var(--text-muted)', marginLeft: 26 }}>Temperature</div>
              </div>
            )}
            {item.humidity != null && (
              <div className="env-metric">
                <div className="value" style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Droplets size={20} style={{ opacity: 0.5 }} />
                  {item.humidity.toFixed(0)}%
                </div>
                <div className="label" style={{ color: 'var(--text-muted)', marginLeft: 26 }}>Humidity</div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
