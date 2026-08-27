import { useState } from 'react';
import { Thermometer, Droplets, Info } from 'lucide-react';
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

  const getTempProximity = (temp, range) => {
    const total = range.max - range.min;
    const distFromEdge = Math.min(temp - range.min, range.max - temp);
    return Math.max(0, Math.min(100, (distFromEdge / (total / 2)) * 100));
  };

  const getAvgTemp = (temps) => temps.reduce((a, b) => a + b, 0) / temps.length;
  const getAvgHum = (hums) => hums.reduce((a, b) => a + b, 0) / hums.length;

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
        {ZONES.map(zone => {
          const avgTemp = getAvgTemp(zone.currentTemp);
          const avgHum = getAvgHum(zone.currentHumidity);
          const tempStatus = getTempStatus(avgTemp, zone.tempRange);
          const proximity = getTempProximity(avgTemp, zone.tempRange);
          const proximityStatus = proximity > 60 ? 'safe' : proximity > 30 ? 'warning' : 'danger';
          const isSelected = selectedZone === zone.zone;

          return (
            <div
              key={zone.zone}
              className={`glass-card env-card ${isSelected ? 'selected' : ''}`}
              onClick={() => setSelectedZone(isSelected ? null : zone.zone)}
            >
              <div className="env-zone">
                <span className="zone-dot" style={{ background: tempStatus === 'danger' ? 'var(--accent-crimson)' : tempStatus === 'warning' ? 'var(--accent-amber)' : 'var(--accent-emerald)' }} />
                {zone.name}
              </div>
              <div className="env-values">
                <div className={`env-metric ${tempStatus}`}>
                  <div className="value">
                    <Thermometer size={16} style={{ marginRight: 4, verticalAlign: -2, opacity: 0.6 }} />
                    {avgTemp.toFixed(1)}°C
                  </div>
                  <div className="label">Avg Temperature</div>
                </div>
                <div className="env-metric safe">
                  <div className="value">
                    <Droplets size={16} style={{ marginRight: 4, verticalAlign: -2, opacity: 0.6 }} />
                    {avgHum.toFixed(0)}%
                  </div>
                  <div className="label">Avg Humidity</div>
                </div>
              </div>
              <div className="limit-bar">
                <div className={`limit-bar-fill ${proximityStatus}`} style={{ width: `${100 - proximity}%` }} />
              </div>
              <div className="env-footer">
                <Info size={11} />
                Safe range: {zone.tempRange.min}°C to {zone.tempRange.max}°C · {zone.shelves.length} shelves
              </div>
            </div>
          );
        })}
      </div>

      {/* Per-Shelf Details */}
      {ZONES.map(zone => (
        <div key={zone.zone} style={{ display: selectedZone === null || selectedZone === zone.zone ? 'block' : 'none' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 16, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Thermometer size={16} style={{ opacity: 0.5 }} />
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
                        <td style={{ fontWeight: 500, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{shelf}</td>
                        <td>{zone.products[i]}</td>
                        <td style={{
                          color: tempStatus === 'danger' ? 'var(--accent-crimson)' :
                                 tempStatus === 'warning' ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                          fontWeight: 600, fontVariantNumeric: 'tabular-nums', fontFamily: 'var(--font-mono)', fontSize: '0.82rem'
                        }}>
                          {zone.currentTemp[i].toFixed(1)}°C
                        </td>
                        <td style={{ fontVariantNumeric: 'tabular-nums', fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                          {zone.currentHumidity[i].toFixed(1)}%
                        </td>
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
                color: ['#4f8efa', '#34d399', '#fbbf24', '#f87171'][i],
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
