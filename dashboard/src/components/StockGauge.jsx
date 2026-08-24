/**
 * Circular gauge component for stock level visualization.
 */
export default function StockGauge({ percentage, label, size = 100 }) {
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.min(1, Math.max(0, percentage)));

  const getLevel = (pct) => {
    if (pct > 0.8) return 'full';
    if (pct > 0.4) return 'adequate';
    if (pct > 0.2) return 'low';
    if (pct > 0.05) return 'critical';
    return 'empty';
  };

  const level = getLevel(percentage);

  return (
    <div className="gauge-container">
      <svg className="gauge-svg" width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          className="gauge-track"
          cx={size / 2}
          cy={size / 2}
          r={radius}
        />
        <circle
          className={`gauge-fill ${level}`}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <span className="gauge-value">{Math.round(percentage * 100)}%</span>
      {label && <span className="gauge-label" title={label}>{label}</span>}
    </div>
  );
}
