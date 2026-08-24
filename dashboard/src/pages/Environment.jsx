import { useState, useEffect } from 'react';
import TelemetryChart from '../components/TelemetryChart';

const ZONES = [
  {
    name: 'Refrigerated Zone',
    zone: 'refrigerated',
    shelves: ['shelf-04', 'shelf-05', 'shelf-06', 'shelf-10'],
    tempRange: { min: 0, max: 8 },
    products: ['Whole Milk', 'Cheddar Cheese', 'Chicken Breast', 'Orange Juice'],
    currentTemp: [4.1, 3.8, 2.3, 4.5],
    currentHumidity: [65.2, 60.1, 70.4, 55.8],
  },
  {
    name: 'Frozen Zone',
    zone: 'frozen',
    shelves: ['shelf-07', 'shelf-08'],
    tempRange: { min: -25, max: -12 },
    products: ['Frozen Vegetables', 'Ice Cream'],
    currentTemp: [-17.8, -19.5],
    currentHumidity: [50.2, 45.1],
  },
  {
    name: 'Dry Storage',
    zone: 'dry-storage',
    shelves: ['shelf-01', 'shelf-02', 'shelf-03', 'shelf-09', 'shelf-11', 'shelf-12'],
    tempRange: { min: 15, max: 28 },
    products: ['Basmati Rice', 'Flour', 'Sugar', 'Olive Oil', 'Canned Tomatoes', 'Pasta'],
    currentTemp: [22.1, 22.3, 21.9, 22.0, 22.4, 22.2],
    currentHumidity: [44.8, 39.5, 34.2, 40.1, 42.3, 37.9],
  },
];

export default function Environment() {
  const [selectedZone, setSelectedZone] = useState(null);

  const getTempStatus = (temp, range) => {
    if (temp < range.min || temp > range.max) return 'danger';
    if (temp > range.max - 2 || temp < range.min + 2) return 'warning';
    return 'safe';
  };

  // Demo chart data
  const timeLabels = Array.from({ length: 24 }, (_, i) => {
    const d = new Date();
    d.setHours(d.getHours() - 23 + i);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  });

  return (
    <>
      <div className="page-header">
        <h2>Environment Monitoring</h2>
        <p>Temperature and humidity sensors across all storage zones</p>
      </div>

      {/* Zone Cards */}
      <div className="env-grid" style={{ marginBottom: 28 }}>
        {ZONES.map(zone => (
          <div
            key={zone.zone}
            className="glass-card env-card"
            style={{ cursor: 'pointer', borderColor: selectedZone === zone.zone ? 'var(--border-accent)' : undefined }}
            onClick={() => setSelectedZone(selectedZone === zone.zone ? null : zone.zone)}
          >
            <div className="env-zone">{zone.name}</div>
            <div className="env-values">
              <div className={`env-metric ${getTempStatus(zone.currentTemp[0], zone.tempRange)}`}>
                <div className="value">{zone.currentTemp[0].toFixed(1)}°C</div>
                <div className="label">Avg Temp</div>
              </div>
              <div className="env-metric safe">
                <div className="value">{zone.currentHumidity[0].toFixed(0)}%</div>
                <div className="label">Avg Humidity</div>
              </div>
            </div>
            <div style={{ marginTop: 12, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Safe range: {zone.tempRange.min}°C to {zone.tempRange.max}°C · {zone.shelves.length} shelves
            </div>
          </div>
        ))}
      </div>

      {/* Per-Shelf Details */}
      {ZONES.map(zone => (
        <div key={zone.zone} style={{ display: selectedZone === null || selectedZone === zone.zone ? 'block' : 'none' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 16, color: 'var(--text-secondary)' }}>
            {zone.name} — Shelf Details
          </h3>
          <div className="glass-card" style={{ marginBottom: 20, overflow: 'hidden' }}>
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Shelf</th>
                    <th>Product</th>
                    <th>Temperature</th>
                    <th>Humidity</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {zone.shelves.map((shelf, i) => {
                    const tempStatus = getTempStatus(zone.currentTemp[i], zone.tempRange);
                    return (
                      <tr key={shelf}>
                        <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{shelf}</td>
                        <td>{zone.products[i]}</td>
                        <td style={{
                          color: tempStatus === 'danger' ? 'var(--accent-crimson)' :
                                 tempStatus === 'warning' ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                          fontWeight: 600, fontVariantNumeric: 'tabular-nums'
                        }}>
                          {zone.currentTemp[i].toFixed(1)}°C
                        </td>
                        <td style={{ fontVariantNumeric: 'tabular-nums' }}>{zone.currentHumidity[i].toFixed(1)}%</td>
                        <td>
                          <span className={`badge ${tempStatus === 'danger' ? 'critical' : tempStatus === 'warning' ? 'low' : 'full'}`}>
                            {tempStatus === 'danger' ? 'OUT OF RANGE' : tempStatus === 'warning' ? 'NEAR LIMIT' : 'NORMAL'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Temperature Chart */}
          <div className="glass-card chart-container" style={{ marginBottom: 28 }}>
            <TelemetryChart
              type="line"
              labels={timeLabels}
              datasets={zone.shelves.slice(0, 3).map((shelf, i) => ({
                label: `${shelf} (${zone.products[i]})`,
                data: timeLabels.map(() =>
                  zone.currentTemp[i] + (Math.random() - 0.5) * 1.5
                ),
                color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'][i],
              }))}
              title={`${zone.name} — Temperature (24h)`}
              yAxisLabel="Temperature (°C)"
            />
          </div>
        </div>
      ))}
    </>
  );
}
