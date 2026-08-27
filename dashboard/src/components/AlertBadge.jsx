import { AlertTriangle, AlertCircle } from 'lucide-react';

/**
 * Animated alert severity badge with icon.
 */
export default function AlertBadge({ severity, count }) {
  if (!count || count === 0) return null;

  const isCritical = severity === 'CRITICAL';
  const Icon = isCritical ? AlertCircle : AlertTriangle;

  return (
    <span className={`alert-badge ${isCritical ? 'critical' : 'warning'}`}>
      <Icon size={13} />
      {count} {isCritical ? 'Critical' : 'Warning'}
    </span>
  );
}
