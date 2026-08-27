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
  const pctDisplay = Math.round(percentage * 100);

  return (
    <div className={`gauge-container ${level === 'critical' ? 'critical-pulse' : ''}`}>
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
        <text
          className="gauge-center"
          x={size / 2}
          y={size / 2}
          transform={`rotate(90, ${size / 2}, ${size / 2})`}
        >
          {pctDisplay}%
        </text>
      </svg>
      {label && <span className="gauge-label" title={label}>{label}</span>}
    </div>
  );
}
