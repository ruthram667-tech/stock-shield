import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Package, Thermometer, Bell, Settings, Shield } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/inventory', label: 'Inventory', icon: Package },
  { path: '/environment', label: 'Environment', icon: Thermometer },
  { path: '/alerts', label: 'Alerts', icon: Bell },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Shield size={18} strokeWidth={2.5} />
        </div>
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
            <span className="nav-icon">
              <item.icon size={18} />
            </span>
            <span>{item.label}</span>
          </NavLink>
        ))}

        <span className="nav-section-label" style={{ marginTop: 'auto' }}>System</span>
        <div className="nav-item">
          <span className="nav-icon">
            <Settings size={18} />
          </span>
          <span>Settings</span>
        </div>
      </nav>

      <div className="sidebar-user">
        <div className="user-avatar">RS</div>
        <div className="user-info">
          <div className="user-name">Ruth S.</div>
          <div className="user-role">Administrator</div>
        </div>
      </div>
      <div className="sidebar-version">Stock Shield v1.0.0</div>
    </aside>
  );
}
