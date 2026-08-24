/**
 * Animated alert severity badge with pulsing dot.
 */
export default function AlertBadge({ severity, count }) {
  if (!count || count === 0) return null;

  const severityClass = severity === 'CRITICAL' ? 'critical' : 'warning';

  return (
    <span className={`alert-badge ${severityClass}`}>
      <span className="alert-dot"></span>
      {count} {severity === 'CRITICAL' ? 'Critical' : 'Warning'}
    </span>
  );
}
