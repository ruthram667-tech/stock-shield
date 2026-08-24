import { NavLink, useLocation } from 'react-router-dom';

export default function Sidebar() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/inventory', label: 'Inventory', icon: '📦' },
    { path: '/environment', label: 'Environment', icon: '🌡️' },
    { path: '/alerts', label: 'Alerts', icon: '🔔' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">🛡️</div>
        <h1>Stock Shield</h1>
      </div>

      <nav className="sidebar-nav">
        <span className="nav-section-label">Navigation</span>
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            end={item.path === '/'}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}

        <span className="nav-section-label" style={{ marginTop: 'auto' }}>System</span>
        <div className="nav-item">
          <span className="nav-icon">⚙️</span>
          <span>Settings</span>
        </div>
      </nav>
    </aside>
  );
}
